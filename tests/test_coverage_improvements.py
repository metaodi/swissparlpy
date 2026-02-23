"""
Tests to improve code coverage for swissparlpy.

This test file targets uncovered code paths identified in the coverage report.
"""

import pytest
import responses
from unittest.mock import Mock, patch
import swissparlpy as spp
from swissparlpy.client import SwissParlClient, SwissParlResponse
from swissparlpy.backends.odata import ODataBackend, ODataResponse
from swissparlpy.backends.openparldata import OpenParlDataBackend
from swissparlpy.backends.base import BaseResponse
from swissparlpy import errors

SERVICE_URL = "https://ws.parlament.ch/odata.svc"
OPENPARLDATA_URL = "https://api.openparldata.ch/v1"
OPENPARLDATA_OPENAPI_URL = "https://api.openparldata.ch/openapi.json"


class TestModuleLevelFunctions:
    """Test module-level convenience functions from __init__.py"""

    @responses.activate
    def test_get_tables(self, metadata):
        """Test get_tables() module function with default backend"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        tables = spp.get_tables()
        assert isinstance(tables, list)
        assert len(tables) == 44

    @responses.activate
    def test_get_tables_openparldata(self, openapi_spec):
        """Test get_tables() module function with openparldata backend"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )
        tables = spp.get_tables(backend="openparldata")
        assert isinstance(tables, list)
        assert "persons" in tables

    @responses.activate
    def test_get_variables(self, metadata):
        """Test get_variables() module function"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        variables = spp.get_variables("Party")
        assert isinstance(variables, list)
        assert "PartyName" in variables

    @responses.activate
    def test_get_overview(self, metadata):
        """Test get_overview() module function"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        overview = spp.get_overview()
        assert isinstance(overview, dict)
        assert len(overview) == 44

    @responses.activate
    def test_get_glimpse(self, metadata, business_page1):
        """Test get_glimpse() module function"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24top=3&%24inlinecount=allpages",
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        glimpse = spp.get_glimpse("Business", rows=3)
        assert type(glimpse).__name__ == "SwissParlResponse"

    @responses.activate
    def test_get_data(self, metadata, business_page1):
        """Test get_data() module function"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        data = spp.get_data("Business", Language="DE")
        assert type(data).__name__ == "SwissParlResponse"


class TestSwissParlClientEdgeCases:
    """Test edge cases in SwissParlClient"""

    @responses.activate
    def test_client_with_backend_instance(self, metadata):
        """Test creating client with backend instance"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        backend = ODataBackend()
        client = SwissParlClient(backend=backend)
        assert client.backend == backend

    @responses.activate
    def test_client_with_openparldata_string(self, openapi_spec):
        """Test creating client with 'openparldata' string"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )
        client = SwissParlClient(backend="openparldata")
        assert isinstance(client.backend, OpenParlDataBackend)

    @responses.activate
    def test_response_variables_property(self, metadata, business_page1):
        """Test SwissParlResponse variables property"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        client = SwissParlClient()
        data = client.get_data("Business", Language="DE")
        variables = data.variables
        assert isinstance(variables, list)
        assert "Title" in variables

    @responses.activate
    def test_response_records_loaded_count_property(self, metadata, business_page1):
        """Test SwissParlResponse _records_loaded_count property"""
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",
            content_type="text/xml",
            body=business_page1,
            status=200,
        )
        client = SwissParlClient()
        data = client.get_data("Business", Language="DE")
        count = data._records_loaded_count
        assert isinstance(count, int)
        assert count > 0


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
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",
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
            f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",
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
            _ = response["invalid"]

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


class TestOpenParlDataBackendEdgeCases:
    """Test edge cases in OpenParlDataBackend"""

    @responses.activate
    def test_openparldata_user_agent_header(self, openapi_spec):
        """Test that user-agent header is set correctly"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Create a new session without user-agent
        import requests

        session = requests.Session()
        # Explicitly remove user-agent if it exists
        if "user-agent" in session.headers:
            del session.headers["user-agent"]

        backend = OpenParlDataBackend(session=session)
        assert "user-agent" in backend.session.headers
        assert "swissparlpy" in backend.session.headers["user-agent"]

    @responses.activate
    def test_openparldata_with_existing_user_agent(self, openapi_spec):
        """Test that existing user-agent header is preserved"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        import requests

        session = requests.Session()
        session.headers["user-agent"] = "CustomAgent/1.0"

        backend = OpenParlDataBackend(session=session)
        assert backend.session.headers["user-agent"] == "CustomAgent/1.0"

    @responses.activate
    def test_openparldata_get_tables_from_cache(self, openapi_spec):
        """Test getting tables from cache on second call"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        backend = OpenParlDataBackend()
        tables1 = backend.get_tables()
        # Second call should use cache
        tables2 = backend.get_tables()

        assert tables1 == tables2
        # OpenAPI endpoint should only be called once
        assert len(responses.calls) == 1

    @responses.activate
    def test_openparldata_get_variables_from_cache(self, openapi_spec, single_person):
        """Test getting variables from cache"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            body=single_person,
            status=200,
        )

        backend = OpenParlDataBackend()
        vars1 = backend.get_variables("persons")
        # Second call should use cache
        vars2 = backend.get_variables("persons")

        assert vars1 == vars2

    @responses.activate
    def test_openparldata_table_not_found_error(self, openapi_spec):
        """Test TableNotFoundError for non-existent table"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        backend = OpenParlDataBackend()

        with pytest.raises(
            errors.TableNotFoundError, match="Table 'nonexistent' not found"
        ):
            backend.get_data("nonexistent")


class TestBaseBackendAbstractMethods:
    """Test that BaseBackend and BaseResponse are properly abstract"""

    def test_base_backend_cannot_be_instantiated(self):
        """Test that BaseBackend cannot be instantiated directly"""
        from swissparlpy.backends.base import BaseBackend

        with pytest.raises(TypeError):
            BaseBackend()  # type: ignore

    def test_base_response_cannot_be_instantiated(self):
        """Test that BaseResponse cannot be instantiated directly"""
        from swissparlpy.backends.base import BaseResponse

        with pytest.raises(TypeError):
            BaseResponse()  # type: ignore

    def test_base_response_to_dataframe_without_pandas(self):
        """Test BaseResponse.to_dataframe() without pandas"""
        from swissparlpy.backends.base import BaseResponse, PANDAS_AVAILABLE
        import swissparlpy.backends.base as base_module

        # Create a mock concrete implementation
        class MockResponse(BaseResponse):
            def __len__(self):
                return 1

            @property
            def _records_loaded_count(self):
                return 1

            def __iter__(self):
                return iter([{"id": 1}])

            def __getitem__(self, key):
                return {"id": 1}

            def to_dict_list(self):
                return [{"id": 1}]

            @property
            def variables(self):
                return ["id"]

            @property
            def table(self):
                return "test"

        mock_response = MockResponse()

        # Temporarily disable pandas
        original_pandas = base_module.PANDAS_AVAILABLE
        try:
            base_module.PANDAS_AVAILABLE = False

            with pytest.raises(ImportError, match="pandas is not installed"):
                mock_response.to_dataframe()
        finally:
            base_module.PANDAS_AVAILABLE = original_pandas


class TestErrorHandling:
    """Test custom error classes"""

    def test_swissparl_error(self):
        """Test SwissParlError can be raised and caught"""
        with pytest.raises(errors.SwissParlError):
            raise errors.SwissParlError("Test error")

    def test_swissparl_timeout_error(self):
        """Test SwissParlTimeoutError can be raised and caught"""
        with pytest.raises(errors.SwissParlTimeoutError):
            raise errors.SwissParlTimeoutError("Timeout error")

    def test_table_not_found_error(self):
        """Test TableNotFoundError can be raised and caught"""
        with pytest.raises(errors.TableNotFoundError):
            raise errors.TableNotFoundError("Table not found")

    def test_swissparl_http_request_error(self):
        """Test SwissParlHttpRequestError can be raised and caught"""
        with pytest.raises(errors.SwissParlHttpRequestError):
            raise errors.SwissParlHttpRequestError("HTTP request failed")

    def test_no_more_records_error(self):
        """Test NoMoreRecordsError can be raised and caught"""
        with pytest.raises(errors.NoMoreRecordsError):
            raise errors.NoMoreRecordsError("No more records")

    def test_result_very_large_warning(self):
        """Test ResultVeryLargeWarning can be raised"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Large result", errors.ResultVeryLargeWarning)
            assert len(w) == 1
            assert issubclass(w[0].category, errors.ResultVeryLargeWarning)

    def test_pagination_warning(self):
        """Test PaginationWarning can be raised"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Pagination issue", errors.PaginationWarning)
            assert len(w) == 1
            assert issubclass(w[0].category, errors.PaginationWarning)


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
        assert len(responses.calls) == 1

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

        assert vars1 == vars2
