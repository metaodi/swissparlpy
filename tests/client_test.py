from swissparlpy_test import SwissParlTestCase
from swissparlpy.client import SwissParlClient
import responses

SERVICE_URL = 'https://ws.parlament.ch/odata.svc'


class TestClient(SwissParlTestCase):
    @responses.activate
    def test_get_overview(self, metadata):
        responses.add(
            responses.GET,
            f"{SERVICE_URL}/$metadata",
            content_type='text/xml',
            body=metadata,
            status=200
        )
        client = SwissParlClient()
        overview = client.get_overview()
        assert isinstance(overview, dict), "Overview is not a dict"
        assert len(overview) == 44
