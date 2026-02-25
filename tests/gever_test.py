"""Tests for Gever backend"""

import pytest
import responses
from unittest.mock import Mock
from swissparlpy.backends.gever import (
    GeverBackend,
    GeverResponse,
    _DEFAULT_CONFIG,
    _GeverDataLoader,
)
from swissparlpy.client import SwissParlClient
from swissparlpy import errors

CANTON_ZURICH_BASE = "https://parlzhcdws.cmicloud.ch"
CITY_ZURICH_BASE = "https://www.integ.gemeinderat-zuerich.ch"


class TestGeverBackendInit:
    def test_init_canton_zurich(self):
        """Test GeverBackend initializes with canton_zurich instance"""
        backend = GeverBackend(instance="canton_zurich")
        assert backend.instance == "canton_zurich"
        assert backend.config == _DEFAULT_CONFIG["canton_zurich"]

    def test_init_city_zurich(self):
        """Test GeverBackend initializes with city_zurich instance"""
        backend = GeverBackend(instance="city_zurich")
        assert backend.instance == "city_zurich"
        assert backend.config == _DEFAULT_CONFIG["city_zurich"]

    def test_init_unknown_instance(self):
        """Test that unknown instance raises SwissParlError"""
        with pytest.raises(errors.SwissParlError, match="Instance 'unknown'"):
            GeverBackend(instance="unknown")

    def test_init_custom_config(self):
        """Test that a custom config dict can be provided"""
        custom_config = {
            "my_instance": {
                "api_base": "https://example.com",
                "files_api": {"path": "/files"},
                "indexes": {
                    "MyIndex": {"path": "/api/myindex"},
                },
            }
        }
        backend = GeverBackend(instance="my_instance", config=custom_config)
        assert backend.instance == "my_instance"
        assert backend.config == custom_config["my_instance"]

    def test_init_default_maximum_records(self):
        """Test that maximum_records defaults to 500"""
        backend = GeverBackend()
        assert backend.maximum_records == 500

    def test_init_custom_maximum_records(self):
        """Test that maximum_records can be customized"""
        backend = GeverBackend(maximum_records=100)
        assert backend.maximum_records == 100


class TestGeverBackendGetTables:
    def test_get_tables_canton_zurich(self):
        """Test get_tables returns canton zurich indexes"""
        backend = GeverBackend(instance="canton_zurich")
        tables = backend.get_tables()
        assert isinstance(tables, list)
        assert "Wahlkreise" in tables
        assert "Geschaeft" in tables
        assert "Mitglieder" in tables
        assert "Parteien" in tables
        assert len(tables) == 11

    def test_get_tables_city_zurich(self):
        """Test get_tables returns city zurich indexes"""
        backend = GeverBackend(instance="city_zurich")
        tables = backend.get_tables()
        assert isinstance(tables, list)
        assert "geschaeft" in tables
        assert "dokument" in tables
        assert "kontakt" in tables
        assert len(tables) == 18


class TestGeverBackendGetVariables:
    @responses.activate
    def test_get_variables(self, wahlkreise_schema):
        """Test get_variables with mocked schema endpoint"""
        responses.add(
            responses.GET,
            f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/schema",
            body=wahlkreise_schema,
            status=200,
            content_type="application/xml",
        )

        backend = GeverBackend(instance="canton_zurich")
        variables = backend.get_variables("Wahlkreise")

        assert isinstance(variables, list)
        assert "Bezeichnung" in variables
        assert "Nummer" in variables
        assert "Kuerzel" in variables

    @responses.activate
    def test_get_variables_unknown_table(self):
        """Test get_variables with unknown table raises error"""
        backend = GeverBackend(instance="canton_zurich")
        with pytest.raises(errors.SwissParlError, match="Index 'UnknownTable'"):
            backend.get_variables("UnknownTable")


class TestGeverBackendGetData:
    @responses.activate
    def test_get_data(self, wahlkreise_xml):
        """Test get_data with mocked search endpoint"""
        responses.add(
            responses.GET,
            f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/searchdetails",
            body=wahlkreise_xml,
            status=200,
            content_type="application/xml",
        )

        backend = GeverBackend(instance="canton_zurich")
        response = backend.get_data("Wahlkreise")

        assert isinstance(response, GeverResponse)
        assert response.count == 3
        assert len(response.records) == 3

    @responses.activate
    def test_get_data_with_string_filter(self, wahlkreise_xml):
        """Test get_data with a string filter"""
        responses.add(
            responses.GET,
            f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/searchdetails",
            body=wahlkreise_xml,
            status=200,
            content_type="application/xml",
        )

        backend = GeverBackend(instance="canton_zurich")
        response = backend.get_data("Wahlkreise", filter="Bezeichnung = 'Zuerich'")

        assert isinstance(response, GeverResponse)

    @responses.activate
    def test_get_data_with_query_kwarg(self, wahlkreise_xml):
        """Test get_data with query keyword argument"""
        responses.add(
            responses.GET,
            f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/searchdetails",
            body=wahlkreise_xml,
            status=200,
            content_type="application/xml",
        )

        backend = GeverBackend(instance="canton_zurich")
        response = backend.get_data("Wahlkreise", query="Nummer = 1")

        assert isinstance(response, GeverResponse)

    def test_get_data_callable_filter_warns(self, caplog):
        """Test that callable filters emit a log warning"""
        import logging

        backend = GeverBackend(instance="canton_zurich")

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/searchdetails",
                body=b'<?xml version="1.0"?><searchDetailResponse xmlns="http://www.cmiag.ch/cdws/searchDetailResponse" indexName="WAHLKREISE" numHits="0" q="seq &gt; 0" m="500" s="1"></searchDetailResponse>',
                status=200,
                content_type="application/xml",
            )
            with caplog.at_level(logging.WARNING, logger="swissparlpy.backends.gever"):
                backend.get_data("Wahlkreise", filter=lambda x: x)

        assert "Callable filters are not supported" in caplog.text

    @responses.activate
    def test_get_data_unknown_table(self):
        """Test get_data with unknown table raises error"""
        backend = GeverBackend(instance="canton_zurich")
        with pytest.raises(errors.SwissParlError, match="Index 'Unknown'"):
            backend.get_data("Unknown")


class TestGeverBackendGetGlimpse:
    @responses.activate
    def test_get_glimpse(self, wahlkreise_xml):
        """Test get_glimpse returns limited results"""
        responses.add(
            responses.GET,
            f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/searchdetails",
            body=wahlkreise_xml,
            status=200,
            content_type="application/xml",
        )

        backend = GeverBackend(instance="canton_zurich")
        response = backend.get_glimpse("Wahlkreise", rows=2)

        assert isinstance(response, GeverResponse)
        # next_start_record should be None (glimpse doesn't paginate)
        assert response.next_start_record is None


class TestGeverResponse:
    def test_response_len(self, wahlkreise_xml):
        """Test that len() returns the total count"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        assert len(response) == 3

    def test_response_iteration(self, wahlkreise_xml):
        """Test iteration over records"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        items = list(response)
        assert len(items) == 3
        assert items[0]["bezeichnung"] == "Zuerich"
        assert items[1]["bezeichnung"] == "Winterthur"
        assert items[2]["bezeichnung"] == "Uster"

    def test_response_indexing(self, wahlkreise_xml):
        """Test indexing into response"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        assert response[0]["bezeichnung"] == "Zuerich"
        assert response[1]["bezeichnung"] == "Winterthur"
        assert response[2]["bezeichnung"] == "Uster"

    def test_response_slicing(self, wahlkreise_xml):
        """Test slicing of response"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        sliced = response[0:2]
        assert len(sliced) == 2
        assert sliced[0]["bezeichnung"] == "Zuerich"
        assert sliced[1]["bezeichnung"] == "Winterthur"

    def test_response_variables(self, wahlkreise_xml):
        """Test variables property"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        assert "bezeichnung" in response.variables
        assert "nummer" in response.variables

    def test_response_table_property(self, wahlkreise_xml):
        """Test table property"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        assert response.table == "Wahlkreise"

    def test_response_to_dict_list(self, wahlkreise_xml):
        """Test to_dict_list returns list of dicts"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        result = response.to_dict_list()
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], dict)
        assert result[0]["bezeichnung"] == "Zuerich"

    def test_response_records_loaded_count(self, wahlkreise_xml):
        """Test _records_loaded_count property"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        assert response._records_loaded_count == 3

    def test_response_repr(self, wahlkreise_xml):
        """Test __repr__ method"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        repr_str = repr(response)
        assert "GeverResponse" in repr_str
        assert "Wahlkreise" in repr_str

    def test_response_invalid_index_type(self, wahlkreise_xml):
        """Test that non-integer, non-slice index raises TypeError"""
        mock_loader = Mock()
        mock_loader.load.return_value = wahlkreise_xml

        response = GeverResponse(
            xml_bytes=wahlkreise_xml,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        with pytest.raises(TypeError, match="Index must be an integer or slice"):
            response["invalid"]


class TestGeverResponsePagination:
    def test_pagination(self, wahlkreise_page1, wahlkreise_page2):
        """Test that pagination loads next page when needed"""
        mock_loader = Mock()
        # First load returns page1, subsequent loads return page2
        mock_loader.load.side_effect = [wahlkreise_page2]

        response = GeverResponse(
            xml_bytes=wahlkreise_page1,
            data_loader=mock_loader,
            table="Wahlkreise",
            config=_DEFAULT_CONFIG["canton_zurich"],
            is_schema=False,
        )

        assert response.count == 3
        assert response._records_loaded_count == 2
        assert response.next_start_record == 3

        items = list(response)
        assert len(items) == 3
        assert items[0]["bezeichnung"] == "Zuerich"
        assert items[2]["bezeichnung"] == "Uster"
        assert response._records_loaded_count == 3
        assert mock_loader.load.call_count == 1


class TestGeverBackendUrlBuilding:
    def test_get_index_url_with_section(self):
        """Test URL building for canton zurich (has section prefix)"""
        backend = GeverBackend(instance="canton_zurich")
        url = backend._get_index_url("Wahlkreise")
        assert url == f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE"

    def test_get_index_url_without_section(self):
        """Test URL building for city zurich (no section prefix)"""
        backend = GeverBackend(instance="city_zurich")
        url = backend._get_index_url("geschaeft")
        assert url == f"{CITY_ZURICH_BASE}/api/geschaeft"

    def test_get_index_url_unknown_index(self):
        """Test that unknown index raises SwissParlError"""
        backend = GeverBackend(instance="canton_zurich")
        with pytest.raises(errors.SwissParlError):
            backend._get_index_url("UnknownIndex")


class TestSwissParlClientGeverIntegration:
    @responses.activate
    def test_client_gever_canton_zurich(self, wahlkreise_xml):
        """Test SwissParlClient with gever_canton_zurich backend"""
        responses.add(
            responses.GET,
            f"{CANTON_ZURICH_BASE}/parlzh2/cdws/Index/WAHLKREISE/searchdetails",
            body=wahlkreise_xml,
            status=200,
            content_type="application/xml",
        )

        client = SwissParlClient(backend="gever_canton_zurich")
        assert isinstance(client.backend, GeverBackend)
        assert client.backend.instance == "canton_zurich"

        response = client.get_data("Wahlkreise")
        assert len(response) == 3

    @responses.activate
    def test_client_gever_city_zurich(self):
        """Test SwissParlClient with gever_city_zurich backend"""
        client = SwissParlClient(backend="gever_city_zurich")
        assert isinstance(client.backend, GeverBackend)
        assert client.backend.instance == "city_zurich"

    def test_client_gever_direct_backend(self):
        """Test SwissParlClient with directly provided GeverBackend"""
        backend = GeverBackend(instance="canton_zurich")
        client = SwissParlClient(backend=backend)
        assert client.backend is backend
