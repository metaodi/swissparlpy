from swissparlpy_test import SwissParlTestCase
from swissparlpy.client import SwissParlClient
from swissparlpy.client import SwissParlResponse
from swissparlpy.backends.odata import ODataResponse
from swissparlpy.backends.openparldata import OpenParlDataBackend
from swissparlpy.backends.odata import ODataBackend
from swissparlpy import errors
import responses
import pytest
from unittest.mock import Mock
import pyodata.exceptions

SERVICE_URL = "https://ws.parlament.ch/odata.svc"
OPENPARLDATA_URL = "https://api.openparldata.ch/v1"
OPENPARLDATA_OPENAPI_URL = "https://api.openparldata.ch/openapi.json"


class TestClient(SwissParlTestCase):
    @responses.activate
    def test_get_overview(self, metadata):
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        client = SwissParlClient()
        overview = client.get_overview()
        assert isinstance(overview, dict), "Overview is not a dict"
        assert len(overview) == 44

    @responses.activate
    def test_overview_with_backend(self, metadata):
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type="text/xml",
            body=metadata,
            status=200,
        )
        backend = ODataBackend()
        client = SwissParlClient(backend=backend)
        overview = client.get_overview()
        assert isinstance(overview, dict), "Overview is not a dict"
        assert len(overview) == 44

    @responses.activate
    def test_get_data(self, metadata, business_page1, business_page2):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/$metadata",
                content_type="text/xml",
                body=metadata,
                status=200,
            )
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",  # noqa
                content_type="text/xml",
                body=business_page1,
                status=200,
            )
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/Business?$filter=Language%20eq%20'DE'&$inlinecount=allpages&$skiptoken=19943083,'DE'",  # noqa
                content_type="text/xml",
                body=business_page2,
                status=200,
            )
            client = SwissParlClient()
            business = client.get_data("Business", Language="DE")
            assert isinstance(
                business, SwissParlResponse
            ), "business is not a SwissParlResponse"
            assert business.count == 52
            assert isinstance(business[1], dict), "business[1] is not a dict"
            assert business[1]["Title"] == "BV. Unternehmensrecht (Jelmini)"

            # trigger the 2nd page to load
            assert isinstance(business[-1], dict), "business[-1] is not a dict"
            assert business[-1]["Title"] == "Ausdruck der Abstimmungsergebnisse"

    @responses.activate
    def test_to_dataframe(self, metadata, business_page1, business_page2):
        """Test that to_dataframe() returns a DataFrame with expected data"""
        pytest.importorskip("pandas")
        import pandas as pd

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/$metadata",
                content_type="text/xml",
                body=metadata,
                status=200,
            )
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",  # noqa
                content_type="text/xml",
                body=business_page1,
                status=200,
            )
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/Business?$filter=Language%20eq%20'DE'&$inlinecount=allpages&$skiptoken=19943083,'DE'",  # noqa
                content_type="text/xml",
                body=business_page2,
                status=200,
            )
            client = SwissParlClient()
            business = client.get_data("Business", Language="DE")

            # Convert to DataFrame
            df = business.to_dataframe()

            # Validate it's a DataFrame
            assert isinstance(df, pd.DataFrame), "Result is not a DataFrame"

            # Validate row count matches the count
            assert (
                len(df) == business.count
            ), f"Expected {business.count} rows, got {len(df)}"
            assert len(df) == 52, "Expected 52 rows"

            # Validate expected columns exist
            assert "Title" in df.columns, "Title column not in DataFrame"

            # Validate data integrity - check some values
            assert df.iloc[1]["Title"] == "BV. Unternehmensrecht (Jelmini)"
            assert df.iloc[-1]["Title"] == "Ausdruck der Abstimmungsergebnisse"

    @responses.activate
    def test_to_dataframe_without_pandas(self, metadata, business_page1):
        """Test that to_dataframe() raises ImportError when pandas is not available"""
        # Mock the PANDAS_AVAILABLE flag
        import swissparlpy.client as client_module

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/$metadata",
                content_type="text/xml",
                body=metadata,
                status=200,
            )
            rsps.add(
                responses.GET,
                f"{SERVICE_URL}/Business?%24filter=Language+eq+%27DE%27&%24inlinecount=allpages",  # noqa
                content_type="text/xml",
                body=business_page1,
                status=200,
            )

            client = SwissParlClient()
            business = client.get_data("Business", Language="DE")

            # Temporarily set PANDAS_AVAILABLE to False
            original_pandas_available = client_module.PANDAS_AVAILABLE
            try:
                client_module.PANDAS_AVAILABLE = False

                # Attempt to call to_dataframe() should raise ImportError
                with pytest.raises(ImportError, match="pandas is not installed"):
                    business.to_dataframe()
            finally:
                # Restore original value
                client_module.PANDAS_AVAILABLE = original_pandas_available

    def test_timeout_http_status_408(self):
        """Test that HTTP 408 status code is treated as a timeout"""
        # Create a mock entity request
        mock_request = Mock()

        # Create a mock HttpError with status code 408
        mock_response = Mock()
        mock_response.status_code = 408
        mock_response.content = b"Request Timeout"

        http_error = pyodata.exceptions.HttpError("Request Timeout", mock_response)
        mock_request.execute.side_effect = http_error

        # Create an ODataResponse with the mock request
        with pytest.raises(
            errors.SwissParlTimeoutError, match="The server returned a timeout error"
        ):
            ODataResponse(mock_request, "Test", ["ID", "Title"])

    def test_timeout_http_status_504(self):
        """Test that HTTP 504 status code is treated as a timeout"""
        # Create a mock entity request
        mock_request = Mock()

        # Create a mock HttpError with status code 504
        mock_response = Mock()
        mock_response.status_code = 504
        mock_response.content = b"Gateway Timeout"

        http_error = pyodata.exceptions.HttpError("Gateway Timeout", mock_response)
        mock_request.execute.side_effect = http_error

        # Create an ODataResponse with the mock request
        with pytest.raises(
            errors.SwissParlTimeoutError, match="The server returned a timeout error"
        ):
            ODataResponse(mock_request, "Test", ["ID", "Title"])

    def test_timeout_execution_timeout_message(self):
        """Test that 'Execution Timeout Expired.' message is detected as timeout"""
        # Create a mock entity request
        mock_request = Mock()

        # Create a mock HttpError with the timeout message
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b"Error: Execution Timeout Expired. Please try again."

        http_error = pyodata.exceptions.HttpError(
            "Internal Server Error", mock_response
        )
        mock_request.execute.side_effect = http_error

        # Create an ODataResponse with the mock request
        with pytest.raises(
            errors.SwissParlTimeoutError, match="The server returned a timeout error"
        ):
            ODataResponse(mock_request, "Test", ["ID", "Title"])

    def test_timeout_no_response_object(self):
        """Test that HttpError without response object is handled correctly"""
        # Create a mock entity request
        mock_request = Mock()

        # Create a HttpError without a response attribute
        http_error = pyodata.exceptions.HttpError("Network error", None)
        mock_request.execute.side_effect = http_error

        # Create an ODataResponse with the mock request
        # Should raise SwissParlError, not TimeoutError
        with pytest.raises(
            errors.SwissParlError, match="The server returned a HTTP error"
        ):
            ODataResponse(mock_request, "Test", ["ID", "Title"])

    def test_timeout_string_content(self):
        """Test that string content is handled correctly"""
        # Create a mock entity request
        mock_request = Mock()

        # Create a mock HttpError with string content
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = "Error: Execution Timeout Expired. Please try again."

        http_error = pyodata.exceptions.HttpError(
            "Internal Server Error", mock_response
        )
        mock_request.execute.side_effect = http_error

        # Create an ODataResponse with the mock request
        with pytest.raises(
            errors.SwissParlTimeoutError, match="The server returned a timeout error"
        ):
            ODataResponse(mock_request, "Test", ["ID", "Title"])

    def test_non_timeout_http_error(self):
        """Test that non-timeout HTTP errors are handled correctly"""
        # Create a mock entity request
        mock_request = Mock()

        # Create a mock HttpError with a non-timeout error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = b"Not Found"

        http_error = pyodata.exceptions.HttpError("Not Found", mock_response)
        mock_request.execute.side_effect = http_error

        # Create an ODataResponse with the mock request
        # Should raise SwissParlError, not TimeoutError
        with pytest.raises(
            errors.SwissParlError, match="The server returned a HTTP error"
        ):
            ODataResponse(mock_request, "Test", ["ID", "Title"])

    @responses.activate
    def test_client_integration_with_openparldata(self, openapi_spec):
        """Test SwissParlClient with OpenParlData backend"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the bodies data endpoint for getting variables
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/bodies",
            json={
                "data": [
                    {"id": 1, "name": "Schweiz"},
                ],
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        client = SwissParlClient(backend=backend)
        response = client.get_data("bodies")

        assert response.count == 1
        assert response[0]["name"] == "Schweiz"
