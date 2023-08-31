from swissparlpy_test import SwissParlTestCase
from swissparlpy.client import SwissParlClient
from swissparlpy.client import SwissParlResponse
import responses

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
