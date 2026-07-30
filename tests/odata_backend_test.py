import pytest
import responses
from unittest.mock import Mock
from swissparlpy.backends.odata import ODataBackend
from swissparlpy.backends.odata import ODataResponse
from swissparlpy import errors


SERVICE_URL = "https://ws.parlament.ch/odata.svc"
OPENPARLDATA_URL = "https://api.openparldata.ch/v1"
OPENPARLDATA_OPENAPI_URL = "https://api.openparldata.ch/openapi.json"


class TestODataCallableFilter:
    """Test callable filter functionality in OData backend"""

    @responses.activate
    def test_get_data_with_callable_filter(self, metadata, business_page1):
        """Test get_data with a callable filter (covers line 62 in odata.py)"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )

        # The callable filter will generate a filter expression
        # For testing, we'll provide a response that matches
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",  # noqa: E501
            content_type="text/xml",
            body=business_page1,
            status=200,
        )

        backend = ODataBackend()

        # Create a callable filter that checks Language == 'DE'
        def my_filter(entities):
            return entities.Language == "DE"

        # This should execute line 62: entities = entities.filter(filter(entities))
        response = backend.get_data("Business", filter=my_filter)

        # Just verify the response is valid - the exact count depends on the mock data
        assert len(response) > 0
        assert response.count > 0


class TestODataResponseIterator:
    """Test ODataResponse iterator edge cases"""

    def test_odata_response_to_dict_list(self):
        """Test to_dict_list method loads all data"""
        mock_request = Mock()

        # Create mock entities
        mock_entities = Mock()
        mock_entities.total_count = 3
        mock_entities.next_url = None

        # Create mock data items
        mock_items = []
        for i in range(3):
            mock_item = Mock()
            mock_item.__call__ = Mock(side_effect=lambda k, idx=i: f"value_{idx}")
            mock_items.append(mock_item)

        mock_entities.__iter__ = Mock(return_value=iter(mock_items))
        mock_request.execute.return_value = mock_entities

        response = ODataResponse(mock_request, "Test", ["id"])

        # to_dict_list should load all data and return a list
        dict_list = response.to_dict_list()

        assert isinstance(dict_list, list)
        assert len(dict_list) == 3


class TestODataBackendEdgeCases:
    """Test edge cases in ODataBackend"""

    @responses.activate
    def test_odata_get_glimpse_with_custom_rows(self, metadata, business_page1):
        """Test get_glimpse with custom row count"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24top=10&%24inlinecount=allpages",
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        backend = ODataBackend()
        response = backend.get_glimpse("Business", rows=10)
        assert isinstance(response, ODataResponse)

    @responses.activate
    def test_odata_get_data_with_string_filter(self, metadata, business_page1):
        """Test get_data with string filter"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",  # noqa: E501
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        backend = ODataBackend()
        response = backend.get_data("Business", filter="Language eq 'DE'")
        assert isinstance(response, ODataResponse)

    @responses.activate
    def test_odata_response_table_property(self, metadata, business_page1):
        """Test ODataResponse table property"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",  # noqa: E501
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        backend = ODataBackend()
        response = backend.get_data("Business", Language="DE")
        assert response.table == "Business"

    def test_odata_response_getitem_with_invalid_type(self):
        """Test ODataResponse __getitem__ with invalid key type"""
        mock_request = Mock()

        # Create properly iterable mock entities
        mock_entities = Mock()
        mock_entities.total_count = 0
        mock_entities.next_url = None
        mock_entities.__iter__ = Mock(return_value=iter([]))

        mock_request.execute.return_value = mock_entities
        response = ODataResponse(mock_request, "Test", ["ID"])

        with pytest.raises(TypeError, match="Index must be an integer or slice"):
            _ = response["invalid"]  # type: ignore

    def test_odata_response_large_result_warning(self):
        """Test warning for large result sets (>10000 records)"""
        mock_request = Mock()

        # Create mock entities with large count
        mock_entities = Mock()
        mock_entities.total_count = 15000
        mock_entities.next_url = (
            None  # No next page, so it will raise NoMoreRecordsError
        )
        mock_entities.__iter__ = Mock(return_value=iter([]))

        mock_request.execute.return_value = mock_entities

        # This should trigger the warning when loading large dataset
        response = ODataResponse(mock_request, "Test", ["ID"])

        # Try to access many elements which will trigger the warning
        with pytest.warns(errors.ResultVeryLargeWarning):
            response._load_new_data_until(10001)


class TestODataResponseSlicing:
    """Test slicing functionality in ODataResponse"""

    def test_odata_response_slice_with_start_and_stop(self):
        """Test slicing with both start and stop"""
        mock_request = Mock()

        # Create mock entities
        mock_entities = Mock()
        mock_entities.total_count = 10
        mock_entities.next_url = None

        # Create mock data items
        mock_items = []
        for i in range(10):
            mock_item = Mock()
            mock_item.__call__ = Mock(side_effect=lambda k, i=i: f"value_{i}")
            mock_items.append(mock_item)

        mock_entities.__iter__ = Mock(return_value=iter(mock_items))
        mock_request.execute.return_value = mock_entities

        response = ODataResponse(mock_request, "Test", ["id"])

        # Test slicing
        sliced = response[2:5]
        assert len(sliced) == 3

    def test_odata_response_negative_index(self):
        """Test negative indexing loads all data"""
        mock_request = Mock()

        # Create mock entities
        mock_entities = Mock()
        mock_entities.total_count = 5
        mock_entities.next_url = None

        # Create mock data items
        mock_items = []
        for i in range(5):
            mock_item = Mock()
            mock_item.__call__ = Mock(side_effect=lambda k, i=i: f"value_{i}")
            mock_items.append(mock_item)

        mock_entities.__iter__ = Mock(return_value=iter(mock_items))
        mock_request.execute.return_value = mock_entities

        response = ODataResponse(mock_request, "Test", ["id"])

        # Access with negative index
        item = response[-1]
        assert isinstance(item, dict)


class TestODataCaching:
    """Test caching behavior in ODataBackend"""

    @responses.activate
    def test_odata_cache_returns_early(self, metadata):
        """Test that cache prevents redundant metadata loads"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )

        backend = ODataBackend()
        # Cache should now be populated

        # Call _load_overview again - should return early
        backend._load_overview()

        # Metadata should only be called once
        assert len(responses.calls) == 1

    @responses.activate
    def test_odata_get_tables_from_cache(self, metadata):
        """Test getting tables from cache"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )

        backend = ODataBackend()
        tables1 = backend.get_tables()
        tables2 = backend.get_tables()

        assert tables1 == tables2
        # Should use cache on second call
        assert (
            len(responses.calls) == 1
        ), f"Metadata endpoint should only be called once, was called {len(responses.calls)} times"

    @responses.activate
    def test_odata_get_variables_from_cache(self, metadata):
        """Test getting variables from cache"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )

        backend = ODataBackend()
        vars1 = backend.get_variables("Party")
        vars2 = backend.get_variables("Party")

        assert vars1 == vars2, "Variables should be the same on repeated calls"
        # Should use cache on second call
        assert (
            len(responses.calls) == 1
        ), f"Metadata endpoint should only be called once, was called {len(responses.calls)} times"
