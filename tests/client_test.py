from swissparlpy_test import SwissParlTestCase
from swissparlpy.client import SwissParlClient
from swissparlpy.client import SwissParlResponse
import responses
import pytest

SERVICE_URL = "https://ws.parlament.ch/odata.svc"


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
