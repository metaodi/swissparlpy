"""Tests for the Gever backend"""

import pytest
import responses
from responses import matchers

import swissparlpy as spp
from swissparlpy import errors
from swissparlpy.backends.gever import GeverBackend, GeverResponse
from swissparlpy.client import SwissParlClient

CANTON_URL = "https://parlzhcdws.cmicloud.ch"
CITY_URL = "https://www.gemeinderat-zuerich.ch"

WAHLKREISE_URL = f"{CANTON_URL}/parlzh2/cdws/Index/WAHLKREISE"
MITGLIEDER_URL = f"{CANTON_URL}/parlzh2/cdws/Index/MITGLIEDER"
SITZUNGEN_URL = f"{CANTON_URL}/parlzh3/cdws/Index/SITZUNGENDETAIL"
CITY_GESCHAEFT_URL = f"{CITY_URL}/api/geschaeft"

ABLAUF_URL = f"{CANTON_URL}/parlzh5/cdws/Index/ABLAUFSCHRITTE"

SD_NS = "http://www.cmiag.ch/cdws/searchDetailResponse"

EMPTY_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<SearchDetailResponse q="seq &gt; 0" l="de-CH" s="1" m="500" numHits="0" '
    f'indexName="Wahlkreise" xmlns="{SD_NS}"/>'
)

# a response that reports fewer hits than it actually contains
LYING_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<SearchDetailResponse q="seq &gt; 0" l="de-CH" s="1" m="500" numHits="1" '
    f'indexName="Ablaufschritte" xmlns="{SD_NS}">'
    '<Hit Guid="1111" SEQ="1"><Ablaufschritt OBJ_GUID="1111" SEQ="1" '
    'xmlns="http://www.cmiag.ch/cdws/Ablaufschritte">'
    "<Schritt>Eingang</Schritt></Ablaufschritt></Hit>"
    '<Hit Guid="2222" SEQ="2"><Ablaufschritt OBJ_GUID="2222" SEQ="2" '
    'xmlns="http://www.cmiag.ch/cdws/Ablaufschritte">'
    "<Schritt>Überweisung</Schritt></Ablaufschritt></Hit>"
    "</SearchDetailResponse>"
)

# a document element without a version, so no download URL can be built
BROKEN_DOC_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<SearchDetailResponse q="seq &gt; 0" l="de-CH" s="1" m="500" numHits="1" '
    f'indexName="SitzungenDetail" xmlns="{SD_NS}">'
    '<Hit Guid="3333" SEQ="3"><SitzungDetail OBJ_GUID="3333" SEQ="3" '
    'xmlns="http://www.cmiag.ch/cdws/SitzungenDetail">'
    '<Dokument><eDokument ID="no-version-1" FileName="Protokoll"/></Dokument>'
    "</SitzungDetail></Hit></SearchDetailResponse>"
)


def add_xml_response(url, body, status=200, match=None):
    responses.add(
        responses.GET,
        url,
        body=body,
        status=status,
        content_type="text/xml",
        match=match or [],
    )


def add_wahlkreise(schema, search):
    add_xml_response(f"{WAHLKREISE_URL}/schema", schema)
    add_xml_response(f"{WAHLKREISE_URL}/searchdetails", search)


def add_mitglieder(schema, search):
    add_xml_response(f"{MITGLIEDER_URL}/schema", schema)
    add_xml_response(f"{MITGLIEDER_URL}/searchdetails", search)


class TestGeverBackendConfig:
    def test_get_tables_canton(self):
        backend = GeverBackend(instance="canton_zurich")
        tables = backend.get_tables()

        assert len(tables) == 11, f"Table count {len(tables)} != 11"
        assert "wahlkreise" in tables
        assert "geschaeft" in tables
        assert tables == [t.lower() for t in tables], "tables are not lowercase"

    def test_get_tables_city(self):
        backend = GeverBackend(instance="city_zurich")
        tables = backend.get_tables()

        assert len(tables) == 19, f"Table count {len(tables)} != 19"
        assert "geschaeft" in tables
        assert "ratspost" in tables
        assert "wortmeldung" in tables
        assert tables == [t.lower() for t in tables], "tables are not lowercase"

    def test_default_instance_is_canton(self):
        assert GeverBackend().instance == "canton_zurich"

    def test_city_uses_production_url(self):
        backend = GeverBackend(instance="city_zurich")
        assert backend.config["api_base"] == CITY_URL
        assert backend._get_index_url("geschaeft") == CITY_GESCHAEFT_URL

    def test_unknown_instance(self):
        with pytest.raises(errors.SwissParlError):
            GeverBackend(instance="canton_bern")

    def test_custom_config(self):
        config = {
            "my_instance": {
                "api_base": "https://example.org",
                "files_api": {"path": "/files"},
                "indexes": {"Things": {"path": "/api/things"}},
            }
        }
        backend = GeverBackend(instance="my_instance", config=config)

        assert backend.get_tables() == ["things"]
        assert backend._get_index_url("things") == "https://example.org/api/things"

    def test_incomplete_config(self):
        config = {"my_instance": {"api_base": "https://example.org"}}
        with pytest.raises(errors.SwissParlError):
            GeverBackend(instance="my_instance", config=config)

    def test_config_from_yaml_file(self, tmp_path):
        pytest.importorskip("yaml")
        config_file = tmp_path / "config.yml"
        config_file.write_text(
            "my_instance:\n"
            "  api_base: https://example.org\n"
            "  files_api:\n"
            "    path: /files\n"
            "  indexes:\n"
            "    Things:\n"
            "      path: /api/things\n",
            encoding="utf-8",
        )
        backend = GeverBackend(instance="my_instance", config=str(config_file))
        assert backend.get_tables() == ["things"]

    def test_url_overrides_api_base(self):
        backend = GeverBackend(url="https://example.org/")
        assert backend._get_index_url("wahlkreise") == (
            "https://example.org/parlzh2/cdws/Index/WAHLKREISE"
        )

    def test_index_url_is_case_insensitive(self):
        backend = GeverBackend()
        assert backend._get_index_url("wahlkreise") == WAHLKREISE_URL
        assert backend._get_index_url("Wahlkreise") == WAHLKREISE_URL
        assert backend._get_index_url("WAHLKREISE") == WAHLKREISE_URL

    def test_unknown_table(self):
        backend = GeverBackend()
        with pytest.raises(errors.TableNotFoundError):
            backend._get_index_url("does_not_exist")

    def test_index_config_without_path(self):
        config = {
            "my_instance": {
                "api_base": "https://example.org",
                "indexes": {"things": {"section": "abc"}},
            }
        }
        backend = GeverBackend(instance="my_instance", config=config)
        with pytest.raises(errors.SwissParlError):
            backend._get_index_url("things")

    def test_file_url_with_section(self):
        backend = GeverBackend(instance="canton_zurich")
        url = backend.file("mitglieder", "abc-1", "1", "Original")
        assert url == f"{CANTON_URL}/parlzh2/cdws/Files/abc-1/1/Original"

    def test_file_url_without_section(self):
        backend = GeverBackend(instance="city_zurich")
        url = backend.file("geschaeft", "abc-1", "2", "PDF")
        assert url == f"{CITY_URL}/api/files/abc-1/2/PDF"


class TestGeverSchema:
    @responses.activate
    def test_get_variables(self, gever_wahlkreise_schema):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)

        backend = GeverBackend()
        variables = backend.get_variables("wahlkreise")

        assert variables == ["name", "inaktiv", "obj_guid", "seq", "idx"]

    @responses.activate
    def test_get_variables_is_cached(self, gever_wahlkreise_schema):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)

        backend = GeverBackend()
        backend.get_variables("wahlkreise")
        backend.get_variables("Wahlkreise")

        assert len(responses.calls) == 1, "schema was requested more than once"

    @responses.activate
    def test_get_variables_of_unknown_table(self):
        backend = GeverBackend()
        with pytest.raises(errors.TableNotFoundError):
            backend.get_variables("does_not_exist")

    @responses.activate
    def test_get_variables_http_error(self):
        add_xml_response(f"{WAHLKREISE_URL}/schema", "error", status=500)

        backend = GeverBackend()
        with pytest.raises(errors.SwissParlHttpRequestError):
            backend.get_variables("wahlkreise")

    @responses.activate
    def test_list_fields_from_schema(self, gever_mitglieder_schema):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_schema)

        backend = GeverBackend()
        backend.get_variables("mitglieder")

        assert backend.list_fields["mitglieder"] == {"position", "kontakt"}

    @responses.activate
    def test_invalid_schema(self):
        add_xml_response(f"{WAHLKREISE_URL}/schema", "no xml at all")

        backend = GeverBackend()
        with pytest.raises(errors.SwissParlError):
            backend.get_variables("wahlkreise")


class TestGeverData:
    @responses.activate
    def test_get_data(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_wahlkreise(gever_wahlkreise_schema, gever_wahlkreise)

        backend = GeverBackend()
        result = backend.get_data("wahlkreise")

        assert isinstance(result, GeverResponse)
        assert len(result) == 18
        assert result.table == "wahlkreise"
        assert result.variables == ["name", "inaktiv", "obj_guid", "seq", "idx"]
        assert result[0]["name"] == "I      Zürich 1+2"
        assert result[0]["inaktiv"] is False
        assert result[0]["obj_guid"] == "dee39e1ccd4c40db82729b3d0762a302"

    @responses.activate
    def test_get_data_is_case_insensitive(
        self, gever_wahlkreise_schema, gever_wahlkreise
    ):
        add_wahlkreise(gever_wahlkreise_schema, gever_wahlkreise)

        backend = GeverBackend()
        assert backend.get_data("Wahlkreise")[0] == backend.get_data("wahlkreise")[0]

    @responses.activate
    def test_get_data_of_unknown_table(self):
        backend = GeverBackend()
        with pytest.raises(errors.TableNotFoundError):
            backend.get_data("does_not_exist")

    @responses.activate
    def test_default_query(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[
                matchers.query_param_matcher(
                    {"q": "seq > 0", "l": "de-CH", "m": "500", "s": "1"}
                )
            ],
        )

        backend = GeverBackend()
        assert len(backend.get_data("wahlkreise")) == 18

    @responses.activate
    def test_filter_string_is_used_as_query(
        self, gever_wahlkreise_schema, gever_wahlkreise
    ):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[
                matchers.query_param_matcher(
                    {"q": "inaktiv = false"}, strict_match=False
                )
            ],
        )

        backend = GeverBackend()
        assert len(backend.get_data("wahlkreise", "inaktiv = false")) == 18

    @responses.activate
    def test_kwargs_are_turned_into_a_query(
        self, gever_mitglieder_schema, gever_mitglieder
    ):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_schema)
        add_xml_response(
            f"{MITGLIEDER_URL}/searchdetails",
            gever_mitglieder,
            match=[
                matchers.query_param_matcher(
                    {"q": "name adj Marti and vorname adj Res"}, strict_match=False
                )
            ],
        )

        backend = GeverBackend()
        assert len(backend.get_data("mitglieder", name="Marti", vorname="Res")) == 2

    @responses.activate
    def test_boolean_kwargs(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[
                matchers.query_param_matcher(
                    {"q": "inaktiv = false"}, strict_match=False
                )
            ],
        )

        backend = GeverBackend()
        assert len(backend.get_data("wahlkreise", inaktiv=False)) == 18

    @responses.activate
    def test_numeric_kwargs(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[matchers.query_param_matcher({"q": "seq = 42"}, strict_match=False)],
        )

        backend = GeverBackend()
        assert len(backend.get_data("wahlkreise", seq=42)) == 18

    @responses.activate
    def test_filter_wins_over_kwargs(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[matchers.query_param_matcher({"q": "seq > 0"}, strict_match=False)],
        )

        backend = GeverBackend()
        assert len(backend.get_data("wahlkreise", "seq > 0", name="Marti")) == 18

    @responses.activate
    def test_callable_filter_is_ignored(
        self, gever_wahlkreise_schema, gever_wahlkreise
    ):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[matchers.query_param_matcher({"q": "seq > 0"}, strict_match=False)],
        )

        backend = GeverBackend()
        assert len(backend.get_data("wahlkreise", lambda x: x)) == 18

    @responses.activate
    def test_get_glimpse(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(
            f"{WAHLKREISE_URL}/searchdetails",
            gever_wahlkreise,
            match=[matchers.query_param_matcher({"m": "3"}, strict_match=False)],
        )

        backend = GeverBackend()
        assert len(backend.get_glimpse("wahlkreise", rows=3)) == 18

    @responses.activate
    def test_http_error(self, gever_wahlkreise_schema):
        add_xml_response(f"{WAHLKREISE_URL}/schema", gever_wahlkreise_schema)
        add_xml_response(f"{WAHLKREISE_URL}/searchdetails", "error", status=500)

        backend = GeverBackend()
        with pytest.raises(errors.SwissParlHttpRequestError):
            backend.get_data("wahlkreise")

    @responses.activate
    def test_empty_result(self, gever_wahlkreise_schema):
        add_wahlkreise(gever_wahlkreise_schema, EMPTY_RESPONSE)

        backend = GeverBackend()
        result = backend.get_data("wahlkreise")

        assert len(result) == 0
        assert list(result) == []
        assert result.to_dict_list() == []

    @responses.activate
    def test_schema_error_does_not_break_get_data(self, gever_sitzungendetail):
        add_xml_response(f"{SITZUNGEN_URL}/schema", "error", status=500)
        add_xml_response(f"{SITZUNGEN_URL}/searchdetails", gever_sitzungendetail)

        backend = GeverBackend()
        result = backend.get_data("sitzungendetail")

        assert len(result) == 1
        # without a schema the variables are taken from the first record
        assert "titel" in result.variables

    @responses.activate
    def test_document_download_url(self, gever_sitzungendetail):
        add_xml_response(f"{SITZUNGEN_URL}/schema", "error", status=500)
        add_xml_response(f"{SITZUNGEN_URL}/searchdetails", gever_sitzungendetail)

        backend = GeverBackend()
        doc = backend.get_data("sitzungendetail")[0]["dokument"]["edokument"]

        assert doc["download_url"] == (
            f"{CANTON_URL}/parlzh3/cdws/Files/"
            "9db1203429e04a39a233e56eab42feea-332/1/PDF"
        )
        assert doc["filename"] == "63. KR-Protokoll vom 9.7.2012, Nachmittag.pdf"
        # nested structures are preserved
        assert doc["version"]["rendition"]["extension"] == "pdf"


class TestGeverListFields:
    @responses.activate
    def test_single_occurrence_is_a_list(
        self, gever_mitglieder_schema, gever_mitglieder
    ):
        add_mitglieder(gever_mitglieder_schema, gever_mitglieder)

        backend = GeverBackend()
        result = backend.get_data("mitglieder")

        first = result[0]
        assert isinstance(first["position"], list)
        assert isinstance(first["kontakt"], list)
        assert len(first["position"]) == 1
        assert first["position"][0]["gremium"].startswith("Kommission für Justiz")

    @responses.activate
    def test_multiple_occurrences_stay_a_list(
        self, gever_mitglieder_schema, gever_mitglieder
    ):
        add_mitglieder(gever_mitglieder_schema, gever_mitglieder)

        backend = GeverBackend()
        second = backend.get_data("mitglieder")[1]

        assert isinstance(second["position"], list)
        assert len(second["position"]) == 2
        assert [p["name"] for p in second["position"]] == ["Präsidentin", "Mitglied"]

    @responses.activate
    def test_list_fields_are_consistent(
        self, gever_mitglieder_schema, gever_mitglieder
    ):
        add_mitglieder(gever_mitglieder_schema, gever_mitglieder)

        backend = GeverBackend()
        records = backend.get_data("mitglieder").to_dict_list()

        for field in ("position", "kontakt"):
            types = {type(record[field]) for record in records}
            assert types == {list}, f"'{field}' is not always a list: {types}"

    @responses.activate
    def test_values_are_converted(self, gever_mitglieder_schema, gever_mitglieder):
        add_mitglieder(gever_mitglieder_schema, gever_mitglieder)

        backend = GeverBackend()
        records = backend.get_data("mitglieder").to_dict_list()

        assert records[0]["eintritt"].year == 2019
        assert records[0]["partei"] == "SP"
        # nil elements are None
        assert records[1]["eintritt"] is None
        assert records[1]["partei"] is None

    @responses.activate
    def test_to_dataframe(self, gever_mitglieder_schema, gever_mitglieder):
        pd = pytest.importorskip("pandas")
        add_mitglieder(gever_mitglieder_schema, gever_mitglieder)

        backend = GeverBackend()
        df = backend.get_data("mitglieder").to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "position" in df.columns
        assert df["position"].map(type).unique().tolist() == [list]


class TestGeverNestedWrapperFlattening:
    """Regression tests for the real `mitglieder` shape of the canton API

    Unlike the flat `gever_mitglieder` fixture, the real API nests almost
    all of a member's data under `Person` -> `Kontakt`, and declares
    repeatable fields via `maxOccurs` on the wrapping `choice`/`sequence`
    rather than on the element itself (see PR #51 discussion).
    """

    @responses.activate
    def test_max_occurs_on_wrapping_choice_is_a_list_field(
        self, gever_mitglieder_nested_schema
    ):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)

        backend = GeverBackend()
        backend.get_variables("mitglieder")

        # 'Behoerdenmandat' only declares maxOccurs on the wrapping <choice>,
        # not on the <element> itself
        assert backend.list_fields["mitglieder"] == {"behoerdenmandat"}

    @responses.activate
    def test_single_occurrence_wrapper_is_flattened(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        first = backend.get_data("mitglieder")[0]

        # 'person' -> 'kontakt' is a two-level single-occurrence wrapper and
        # is fully reachable as top-level columns, not a nested dict
        assert "person" not in first
        assert first["person_kontakt_vorname"] == "Peter"
        assert first["person_kontakt_name"] == "Abplanalp"

    @responses.activate
    def test_list_field_shape_is_consistent_across_records(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        records = backend.get_data("mitglieder").to_dict_list()

        # record 0 has a single Behoerdenmandat, record 1 has two - both
        # must come back as a list, not a dict vs. list of dicts
        assert len(records[0]["behoerdenmandat"]) == 1
        assert len(records[1]["behoerdenmandat"]) == 2
        types = {type(record["behoerdenmandat"]) for record in records}
        assert types == {list}

    @responses.activate
    def test_nested_structure_inside_list_items_is_flattened(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        first = backend.get_data("mitglieder")[0]
        mandat = first["behoerdenmandat"][0]

        # the 'Dauer' sub-structure inside each list item is flattened too
        assert "dauer" not in mandat or not isinstance(mandat["dauer"], dict)
        assert mandat["dauer_start"].year == 1991
        assert mandat["name"] == "Kantonsrat"

    @responses.activate
    def test_to_dataframe_with_nested_wrapper(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        pd = pytest.importorskip("pandas")
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        df = backend.get_data("mitglieder").to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert "person_kontakt_vorname" in df.columns
        assert "behoerdenmandat" in df.columns
        assert df["behoerdenmandat"].map(type).unique().tolist() == [list]


class TestGeverExplode:
    @responses.activate
    def test_explode_one_row_per_item(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        pd = pytest.importorskip("pandas")
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        df = backend.get_data("mitglieder").explode("behoerdenmandat")

        assert isinstance(df, pd.DataFrame)
        # Peter has 1 mandate, Christian has 2 -> 3 rows total
        assert len(df) == 3
        assert df["name"].tolist() == ["Kantonsrat", "Fraktion SVP", "Kantonsrat"]

    @responses.activate
    def test_explode_includes_parent_foreign_key(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        pytest.importorskip("pandas")
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        records = backend.get_data("mitglieder")
        df = records.explode("behoerdenmandat")

        # parent_obj_guid does not collide with the child's own obj_guid
        assert "parent_obj_guid" in df.columns
        assert "obj_guid" in df.columns
        assert df.iloc[0]["parent_obj_guid"] == records[0]["obj_guid"]
        assert df.iloc[0]["obj_guid"] == records[0]["behoerdenmandat"][0]["obj_guid"]

    @responses.activate
    def test_explode_with_parent_columns(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        pytest.importorskip("pandas")
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        df = backend.get_data("mitglieder").explode(
            "behoerdenmandat", parent_columns=["person_kontakt_vorname"]
        )

        assert df["parent_person_kontakt_vorname"].tolist() == [
            "Peter",
            "Christian",
            "Christian",
        ]

    @responses.activate
    def test_explode_unknown_list_field_raises(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested
    ):
        pytest.importorskip("pandas")
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)

        backend = GeverBackend()
        result = backend.get_data("mitglieder")

        with pytest.raises(errors.SwissParlError):
            result.explode("funktion")

    @responses.activate
    def test_explode_without_schema_uses_runtime_shape(self, gever_ablaufschritte):
        pytest.importorskip("pandas")
        add_xml_response(f"{ABLAUF_URL}/schema", "error", status=500)
        add_xml_response(f"{ABLAUF_URL}/searchdetails", gever_ablaufschritte)

        backend = GeverBackend()
        df = backend.get_data("ablaufschritte").explode("geschaeft")

        # without a schema, a single 'geschaeft' is merged into its record
        # rather than kept as a list (see TestGeverNormalizationFallback), so
        # only the record with several ends up in the exploded result
        assert len(df) == 2
        assert df["nr"].tolist() == ["KR-Nr. 2/2024", "KR-Nr. 3/2024"]

    @responses.activate
    def test_explode_requires_pandas(
        self, gever_mitglieder_nested_schema, gever_mitglieder_nested, monkeypatch
    ):
        add_xml_response(f"{MITGLIEDER_URL}/schema", gever_mitglieder_nested_schema)
        add_xml_response(f"{MITGLIEDER_URL}/searchdetails", gever_mitglieder_nested)
        monkeypatch.setattr("swissparlpy.backends.gever.PANDAS_AVAILABLE", False)

        backend = GeverBackend()
        result = backend.get_data("mitglieder")

        with pytest.raises(ImportError):
            result.explode("behoerdenmandat")


class TestGeverPagination:
    def _add_city_responses(self, schema, page1, page2):
        add_xml_response(f"{CITY_GESCHAEFT_URL}/schema", schema)
        add_xml_response(
            f"{CITY_GESCHAEFT_URL}/searchdetails",
            page1,
            match=[matchers.query_param_matcher({"s": "1"}, strict_match=False)],
        )
        add_xml_response(
            f"{CITY_GESCHAEFT_URL}/searchdetails",
            page2,
            match=[matchers.query_param_matcher({"s": "3"}, strict_match=False)],
        )

    @responses.activate
    def test_iterate_over_pages(
        self, gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
    ):
        self._add_city_responses(
            gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
        )

        backend = GeverBackend(instance="city_zurich", maximum_records=2)
        result = backend.get_data("geschaeft")

        assert len(result) == 3
        assert result._records_loaded_count == 2, "loaded more than the first page"

        records = list(result)
        assert len(records) == 3
        assert result._records_loaded_count == 3
        assert [r["titel"] for r in records] == [
            "Postulat zur Verkehrsberuhigung",
            "Motion zum Wohnraum",
            "Interpellation zur Schulraumplanung",
        ]

    @responses.activate
    def test_index_loads_pages_lazily(
        self, gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
    ):
        self._add_city_responses(
            gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
        )

        backend = GeverBackend(instance="city_zurich", maximum_records=2)
        result = backend.get_data("geschaeft")

        assert result[0]["titel"] == "Postulat zur Verkehrsberuhigung"
        assert result._records_loaded_count == 2
        assert result[2]["titel"] == "Interpellation zur Schulraumplanung"
        assert result._records_loaded_count == 3

    @responses.activate
    def test_negative_index(
        self, gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
    ):
        self._add_city_responses(
            gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
        )

        backend = GeverBackend(instance="city_zurich", maximum_records=2)
        result = backend.get_data("geschaeft")

        assert result[-1]["titel"] == "Interpellation zur Schulraumplanung"

    @responses.activate
    def test_slice(
        self, gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
    ):
        self._add_city_responses(
            gever_geschaeft_schema, gever_geschaeft_page1, gever_geschaeft_page2
        )

        backend = GeverBackend(instance="city_zurich", maximum_records=2)
        result = backend.get_data("geschaeft")

        assert len(result[:3]) == 3
        assert [r["titel"] for r in result[1:3]] == [
            "Motion zum Wohnraum",
            "Interpellation zur Schulraumplanung",
        ]

    @responses.activate
    def test_invalid_index(self, gever_geschaeft_schema, gever_geschaeft_page1):
        add_xml_response(f"{CITY_GESCHAEFT_URL}/schema", gever_geschaeft_schema)
        add_xml_response(f"{CITY_GESCHAEFT_URL}/searchdetails", gever_geschaeft_page1)

        backend = GeverBackend(instance="city_zurich", maximum_records=2)
        result = backend.get_data("geschaeft")

        with pytest.raises(TypeError):
            result["not_an_index"]

    @responses.activate
    def test_repr(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_wahlkreise(gever_wahlkreise_schema, gever_wahlkreise)

        backend = GeverBackend()
        assert "Zürich" in repr(backend.get_data("wahlkreise"))


class TestGeverNormalizationFallback:
    @responses.activate
    def test_numeric_max_occurs_is_a_list_field(
        self, gever_ablaufschritte_schema, gever_ablaufschritte
    ):
        add_xml_response(f"{ABLAUF_URL}/schema", gever_ablaufschritte_schema)
        add_xml_response(f"{ABLAUF_URL}/searchdetails", gever_ablaufschritte)

        backend = GeverBackend()
        records = backend.get_data("ablaufschritte").to_dict_list()

        # 'geschaeft' has maxOccurs="5", so it is always a list
        assert backend.list_fields["ablaufschritte"] == {"geschaeft"}
        assert [len(r["geschaeft"]) for r in records] == [1, 2]
        assert records[0]["geschaeft"][0]["nr"] == "KR-Nr. 1/2024"

    @responses.activate
    def test_without_schema_the_special_keys_are_flattened(self, gever_ablaufschritte):
        add_xml_response(f"{ABLAUF_URL}/schema", "error", status=500)
        add_xml_response(f"{ABLAUF_URL}/searchdetails", gever_ablaufschritte)

        backend = GeverBackend()
        records = backend.get_data("ablaufschritte").to_dict_list()

        # this is the goifer fallback: a single 'geschaeft' is merged into the
        # record, several of them stay a list - the schema based normalization
        # above is what makes this consistent
        assert "geschaeft" not in records[0]
        assert records[0]["nr"] == "KR-Nr. 1/2024"
        assert isinstance(records[1]["geschaeft"], list)

    @responses.activate
    def test_pagination_warning(self):
        # the API reports fewer hits than it returns
        add_xml_response(f"{ABLAUF_URL}/schema", "error", status=500)
        add_xml_response(f"{ABLAUF_URL}/searchdetails", LYING_RESPONSE)

        backend = GeverBackend()
        result = backend.get_data("ablaufschritte")

        assert len(result) == 1
        with pytest.warns(errors.PaginationWarning):
            assert len(list(result)) == 2

    @responses.activate
    def test_document_without_version(self):
        add_xml_response(f"{SITZUNGEN_URL}/schema", "error", status=500)
        add_xml_response(f"{SITZUNGEN_URL}/searchdetails", BROKEN_DOC_RESPONSE)

        backend = GeverBackend()
        doc = backend.get_data("sitzungendetail")[0]["dokument"]["edokument"]

        assert "download_url" not in doc
        assert doc["id"] == "no-version-1"


class TestGeverClient:
    @responses.activate
    def test_client_with_backend_name(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_wahlkreise(gever_wahlkreise_schema, gever_wahlkreise)

        client = SwissParlClient(backend="gever")
        assert len(client.get_tables()) == 11
        assert client.get_variables("wahlkreise")[0] == "name"
        assert client.get_data("wahlkreise").count == 18

    @responses.activate
    def test_client_with_city_backend(
        self, gever_geschaeft_schema, gever_geschaeft_page1
    ):
        add_xml_response(f"{CITY_GESCHAEFT_URL}/schema", gever_geschaeft_schema)
        add_xml_response(f"{CITY_GESCHAEFT_URL}/searchdetails", gever_geschaeft_page1)

        client = SwissParlClient(backend="gever_city_zurich")
        assert len(client.get_tables()) == 19
        assert client.get_data("geschaeft")[0]["titel"] == (
            "Postulat zur Verkehrsberuhigung"
        )

    @responses.activate
    def test_client_with_backend_instance(
        self, gever_wahlkreise_schema, gever_wahlkreise
    ):
        add_wahlkreise(gever_wahlkreise_schema, gever_wahlkreise)

        client = SwissParlClient(backend=GeverBackend(instance="canton_zurich"))
        assert len(client.get_data("wahlkreise")) == 18

    @responses.activate
    def test_module_level_functions(
        self, gever_geschaeft_schema, gever_geschaeft_page1
    ):
        add_xml_response(f"{CITY_GESCHAEFT_URL}/schema", gever_geschaeft_schema)
        add_xml_response(f"{CITY_GESCHAEFT_URL}/searchdetails", gever_geschaeft_page1)

        assert "geschaeft" in spp.get_tables(backend="gever_city_zurich")
        assert spp.get_variables("geschaeft", backend="gever_city_zurich") == [
            "titel",
            "geschaeftsart",
            "beginn",
            "obj_guid",
            "seq",
            "idx",
        ]
        data = spp.get_data("geschaeft", backend="gever_city_zurich")
        assert data[0]["titel"] == "Postulat zur Verkehrsberuhigung"

    @responses.activate
    def test_pascal_case_table_name(
        self, gever_geschaeft_schema, gever_geschaeft_page1
    ):
        add_xml_response(f"{CITY_GESCHAEFT_URL}/schema", gever_geschaeft_schema)
        add_xml_response(f"{CITY_GESCHAEFT_URL}/searchdetails", gever_geschaeft_page1)

        lower = spp.get_data("geschaeft", backend="gever_city_zurich")[0]
        pascal = spp.get_data("Geschaeft", backend="gever_city_zurich")[0]
        assert lower == pascal

    @responses.activate
    def test_glimpse_via_client(self, gever_wahlkreise_schema, gever_wahlkreise):
        add_wahlkreise(gever_wahlkreise_schema, gever_wahlkreise)

        glimpse = spp.get_glimpse("wahlkreise", rows=2, backend="gever")
        assert glimpse.count == 18
