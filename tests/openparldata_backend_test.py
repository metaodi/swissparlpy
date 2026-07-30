"""Tests for OpenParlData backend"""

import logging
import pytest
import responses
from responses import matchers
from unittest.mock import Mock
from swissparlpy.backends.openparldata import (
    FALLBACK_QUERY_PARAMS,
    OpenParlDataBackend,
    OpenParlDataResponse,
    OpenParlDataProxy,
)
from swissparlpy.client import SwissParlClient
from swissparlpy import errors
import re
from typing import cast


OPENPARLDATA_URL = "https://api.openparldata.ch/v1"
OPENPARLDATA_OPENAPI_URL = "https://api.openparldata.ch/openapi.json"


class TestOpenParlDataBackend:
    @responses.activate
    def test_get_tables_with_openapi(self, openapi_spec):
        """Test getting tables from OpenAPI spec"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        backend = OpenParlDataBackend()
        tables = backend.get_tables()

        assert isinstance(tables, list)
        assert "affairs" in tables, "affairs not in tables"
        assert "groups" in tables, "groups not in tables"
        assert "persons" in tables, "persons not in tables"

        assert len(tables) == 18, f"Table count {len(tables)} != 19"

    @responses.activate
    def test_get_variables_from_data(self, openapi_spec, single_person):
        """Test getting variables by inspecting data"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the cantons data endpoint
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            body=single_person,
            content_type="application/json",
            status=200,
        )

        backend = OpenParlDataBackend()
        variables = backend.get_variables("persons")

        assert isinstance(variables, list)
        assert "id" in variables
        assert "fullname" in variables
        assert "firstname" in variables
        assert "lastname" in variables

    @responses.activate
    def test_get_glimpse(self, openapi_spec):
        """Test getting a glimpse of data"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the cantons data endpoint for getting variables
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json={
                "data": [
                    {
                        "id": 1,
                        "fullname": "Maya Graf",
                        "firstname": "Maya",
                        "lastname": "Graf",
                    },
                    {
                        "id": 2,
                        "fullname": "John Doe",
                        "firstname": "John",
                        "lastname": "Doe",
                    },
                ],
                "meta": {
                    "total_records": 26,
                    "has_more": False,
                },
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_glimpse("persons", rows=2)

        assert isinstance(response, OpenParlDataResponse)
        assert len(response.data) == 2
        assert response[0]["fullname"] == "Maya Graf"
        assert response[1]["fullname"] == "John Doe"

    @responses.activate
    def test_get_related_data(self, openapi_spec, single_person, person_memberships):
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the cantons data endpoint for getting variables
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            body=single_person,
            status=200,
        )

        # Mock the person-memberships data endpoint for getting related data
        responses.add(
            responses.GET,
            "https://api.openparldata.ch/v1/persons/9527/memberships",
            body=person_memberships,
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("persons")
        person = cast(OpenParlDataProxy, response[0])
        related_tables = person.get_related_tables()
        related_memberships = person.get_related_data("memberships")
        membership = cast(OpenParlDataProxy, related_memberships[0])

        assert isinstance(
            response, OpenParlDataResponse
        ), "Response should be an instance of OpenParlDataResponse"
        assert isinstance(
            person, OpenParlDataProxy
        ), "Person should be an instance of OpenParlDataProxy"
        assert isinstance(
            related_memberships, OpenParlDataResponse
        ), "Related memberships should be an instance of OpenParlDataResponse"
        assert len(response) == 1
        assert (
            len(related_tables) == 10
        ), f"Expected 10 related tables, got {len(related_tables)}"
        assert (
            "memberships" in related_tables
        ), f"Expected 'memberships' in related tables, got {related_tables}"
        assert person["fullname"] == "Maya Graf"
        assert (
            response.table == "persons"
        ), f"Response should have persons as table name, got {response.table}"
        assert (
            related_memberships.table == "memberships"
        ), f"Related memberships should have memberships as table name, got {related_memberships.table}"  # noqa: E501
        assert (
            len(related_memberships) == 115
        ), f"Related memberships should have 115 records, got {len(related_memberships)}"
        assert (
            membership["group_name_de"] == "World Winter Games Switzerland 2029 (WWG)"
        ), f"First membership group_name_de should be 'World Winter Games Switzerland 2029 (WWG)', got {membership['group_name_de']}"  # noqa: E501
        assert (
            membership["type_harmonized"] == "interest_group"
        ), f"First membership type_harmonized should be 'interest_group', got {membership['type_harmonized']}"  # noqa: E501

    @responses.activate
    def test_get_data_with_filters(self, openapi_spec):
        """Test getting data with filter parameters"""
        # Mock the OpenAPI spec endpoint
        oap_resp = responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the persons data endpoint for actual query
        pers_data = {
            "data": [
                {"id": 1, "firstname": "Stefan", "lastname": "Müller"},
            ],
            "meta": {
                "total_records": 1,
                "has_more": False,
            },
        }
        pers_var_resp = responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json=pers_data,
            match=[matchers.query_param_matcher({"limit": 1, "lang_format": "flat"})],
            status=200,
        )

        params = {"firstname": "Stefan"}
        pers_resp = responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json=pers_data,
            match=[matchers.query_param_matcher(params, strict_match=False)],
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("persons", firstname="Stefan")
        person = cast(OpenParlDataProxy, response[0])

        assert isinstance(response, OpenParlDataResponse)
        assert len(response.data) == 1
        assert isinstance(
            response[0], OpenParlDataProxy
        ), "First record should be an instance of OpenParlDataProxy"
        assert (
            person["firstname"] == "Stefan"
        ), f"First record firstname should be 'Stefan', got {person['firstname']}"

        assert (
            oap_resp.call_count == 1
        ), f"OpenAPI spec endpoint should be called once, was called {oap_resp.call_count} times"  # noqa: E501
        assert (
            pers_var_resp.call_count == 1
        ), f"Persons variables endpoint should be called once, was called {pers_var_resp.call_count} times"  # noqa: E501
        assert (
            pers_resp.call_count == 1
        ), f"Persons data endpoint should be called once, was called {pers_resp.call_count} times"  # noqa: E501

    @responses.activate
    def test_response_iteration(self, openapi_spec):
        """Test iterating over response data"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the cantons data endpoint for getting variables
        affairs_data = {
            "data": [
                {"id": 1, "affair": "Zürich"},
                {"id": 2, "affair": "Bern"},
            ],
            "meta": {
                "total_records": 2,
                "has_more": False,
            },
        }
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/affairs",
            json=affairs_data,
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("affairs")

        assert len(response.data) == 2
        items = list(response)
        assert len(items) == 2
        assert items[0]["affair"] == "Zürich"
        assert items[1]["affair"] == "Bern"

    @responses.activate
    def test_response_slicing(self, openapi_spec):
        """Test slicing response data"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the cantons data endpoint for getting variables
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/affair",
            json={
                "data": [
                    {"id": 1, "name": "Zürich"},
                    {"id": 2, "name": "Bern"},
                    {"id": 3, "name": "Luzern"},
                ],
                "meta": {
                    "total_records": 3,
                    "has_more": False,
                },
            },
            status=200,
        )

        # Mock the cantons data endpoint for actual query
        affairs_data = {
            "data": [
                {"id": 1, "affair": "Zürich"},
                {"id": 2, "affair": "Bern"},
            ],
            "meta": {
                "total_records": 2,
                "has_more": False,
            },
        }
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/affairs",
            json=affairs_data,
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("affairs")

        assert (
            len(response[0:2]) == 2
        ), f"Slicing response should return 2 records, got {len(response[0:2])}"
        slice_result = list(response[0:2])
        assert (
            len(slice_result) == 2
        ), f"Slicing response should return 2 records, got {len(slice_result)}"
        assert (
            slice_result[0]["affair"] == "Zürich"
        ), f"First record name should be 'Zürich', got {slice_result[0]['affair']}"
        assert (
            slice_result[1]["affair"] == "Bern"
        ), f"Second record name should be 'Bern', got {slice_result[1]['affair']}"

    @responses.activate
    def test_response_pagination(self, openapi_spec, affairs_page1, affairs_page2):
        """Test pagination handling"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        call_count = {"count": 0}

        def affairs_callback(request):
            call_count["count"] += 1
            print(
                f"Affairs endpoint called {call_count['count']} times with URL: {request.url} and params: {request.params}"  # noqa: E501
            )
            if call_count["count"] > 10:
                raise Exception(
                    "Affairs endpoint called too many times, possible infinite loop"
                )

            # page 1
            if "offset" not in request.params:
                return (
                    200,
                    {},
                    affairs_page1,
                )
            # page 2
            elif "offset" in request.params and request.params["offset"] == "2":
                print(affairs_page2)
                return (
                    200,
                    {},
                    affairs_page2,
                )
            return (404, {}, '{"error": "Not found"}')

        responses.add_callback(
            responses.GET,
            re.compile("https://api.openparldata.ch/v1/affairs/?"),
            callback=affairs_callback,
            content_type="application/json",
        )

        assert (
            call_count["count"] == 0
        ), f"Affairs endpoint should not have been called yet, was called {call_count['count']} times"  # noqa: E501

        backend = OpenParlDataBackend()
        response = backend.get_data("affairs")

        # Iterate through all pages
        assert response.count == 4, f"Total count should be 4, got {response.count}"
        assert (
            response._records_loaded_count == 2
        ), f"After first page, records loaded count should be 2, got {response._records_loaded_count}"  # noqa: E501

        items = list(response)
        assert (
            len(items) == 4
        ), f"Total items should be 4 after pagination, got {len(items)}"
        assert items[0]["affair"] == "Zürich"
        assert items[1]["affair"] == "Bern"
        assert items[2]["affair"] == "Luzern"
        assert items[3]["affair"] == "Basel"
        assert (
            response._records_loaded_count == 4
        ), f"After all pages, records loaded count should be 4, got {response._records_loaded_count}"  # noqa: E501

    @responses.activate
    def test_response_pagination_wrong_next_page(self, openapi_spec, affairs_page1):
        """Test pagination handling with wrong next_page"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        call_count = {"count": 0}

        def affairs_callback(request):
            call_count["count"] += 1
            print(
                f"Affairs endpoint called {call_count['count']} times with URL: {request.url} and params: {request.params}"  # noqa: E501
            )
            if call_count["count"] > 10:
                raise Exception(
                    "Affairs endpoint called too many times, possible infinite loop"
                )

            return (
                200,
                {},
                affairs_page1,
            )

        responses.add_callback(
            responses.GET,
            re.compile("https://api.openparldata.ch/v1/affairs/?"),
            callback=affairs_callback,
            content_type="application/json",
        )

        assert (
            call_count["count"] == 0
        ), f"Affairs endpoint should not have been called yet, was called {call_count['count']} times"  # noqa: E501

        backend = OpenParlDataBackend()
        response = backend.get_data("affairs")

        # Iterate through all pages
        assert response.count == 4, f"Total count should be 4, got {response.count}"
        assert (
            response._records_loaded_count == 2
        ), f"After first page, records loaded count should be 2, got {response._records_loaded_count}"  # noqa: E501

        # when all entries are loaded, it should stop and
        # not enter an infinite loop, even if next_page is wrong
        with pytest.warns(errors.PaginationWarning) as record:
            items = list(response)

        assert len(record) == 1, f"Expected one pagination warning, got {len(record)}"
        assert "Loaded more records" in str(
            record[0].message
        ), f"Expected warning message to contain 'Loaded more records', got {record[0].message}"  # noqa: E501

        assert (
            len(items) == 6
        ), f"Total items should be 6 after pagination, got {len(items)}"
        assert items[0]["affair"] == "Zürich"
        assert items[1]["affair"] == "Bern"
        assert (
            response._records_loaded_count == 6
        ), f"After all pages, records loaded count should be 6, got {response._records_loaded_count}"  # noqa: E501

    @responses.activate
    def test_error_table_not_found(self, openapi_spec):
        """Test error handling for failed requests"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the invalid endpoint to return 404
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/invalid",
            json={"error": "Not found"},
            status=404,
        )

        backend = OpenParlDataBackend()

        # 'invalid' is not in the tables list, so this should raise TableNotFoundError
        with pytest.raises(
            errors.TableNotFoundError, match="Table 'invalid' not found"
        ):
            backend.get_data("invalid")

    @responses.activate
    def test_error_http_request_fails(self, openapi_spec):
        """Test error handling for failed requests"""
        # Mock the OpenAPI spec endpoint
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the invalid endpoint to return 404
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json={"details": "Not found"},
            status=404,
        )

        backend = OpenParlDataBackend()

        # 'invalid' is not in the tables list, so this should raise TableNotFoundError
        error_msg = f"Failed to make GET request to {OPENPARLDATA_URL}/persons"
        with pytest.raises(errors.SwissParlHttpRequestError, match=error_msg):
            backend.get_data("persons")

    @responses.activate
    def test_get_variables_with_empty_data(self, openapi_spec):
        """Test get_variables when API returns empty data array"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the endpoint to return empty data
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json={
                "data": [],  # Empty array
                "meta": {"total_records": 0, "has_more": False},
            },
            status=200,
        )

        backend = OpenParlDataBackend()

        # This should trigger the IndexError exception path (lines 108-110)
        with pytest.raises(errors.SwissParlError, match="Failed to get variables"):
            backend.get_variables("persons")

    @responses.activate
    def test_get_variables_with_invalid_json(self, openapi_spec):
        """Test get_variables when API returns invalid JSON structure"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        # Mock the endpoint to return JSON without 'data' key
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json={
                "invalid": "structure",  # Missing 'data' key
            },
            status=200,
        )

        backend = OpenParlDataBackend()

        # This should trigger the KeyError exception path (lines 108-110)
        with pytest.raises(errors.SwissParlError, match="Failed to get variables"):
            backend.get_variables("persons")

    @responses.activate
    def test_get_tables_when_cache_empty(self, openapi_spec):
        """Test get_tables when cache is initially empty (lines 88-89)"""
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

        backend = OpenParlDataBackend()

        # Clear the cache to simulate empty state
        backend.cache = {}

        # This should trigger line 88-89: _load_openapi_config
        tables = backend.get_tables()

        assert isinstance(tables, list)
        assert len(tables) > 0


class TestOpenParlDataQueryParams:
    """Test the query parameters sent to the API (Issue #52)"""

    def _mock_openapi(self, openapi_spec):
        responses.add(
            responses.GET,
            OPENPARLDATA_OPENAPI_URL,
            body=openapi_spec,
            status=200,
            content_type="application/json",
        )

    def _mock_variables(self, single_person):
        return responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            body=single_person,
            match=[matchers.query_param_matcher({"limit": 1, "lang_format": "flat"})],
            status=200,
        )

    def _mock_persons(self, params, strict_match=True):
        return responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json={
                "data": [{"id": 1, "firstname": "Stefan"}],
                "meta": {"total_records": 1, "has_more": False},
            },
            match=[matchers.query_param_matcher(params, strict_match=strict_match)],
            status=200,
        )

    @responses.activate
    def test_default_params_are_only_lang_format(self, openapi_spec, single_person):
        """No lang, lang_fallback, search, search_mode or search_scope is sent"""
        self._mock_openapi(openapi_spec)
        self._mock_variables(single_person)
        data_resp = self._mock_persons({"lang_format": "flat"})

        backend = OpenParlDataBackend()
        response = backend.get_data("persons")

        assert len(response) == 1
        assert (
            data_resp.call_count == 1
        ), "Data endpoint should be called with 'lang_format' as only param"

    @responses.activate
    def test_string_filter_sets_search(self, openapi_spec, single_person):
        """A string filter is passed as 'search', without a search scope override"""
        self._mock_openapi(openapi_spec)
        self._mock_variables(single_person)
        data_resp = self._mock_persons({"lang_format": "flat", "search": "Müller"})

        backend = OpenParlDataBackend()
        backend.get_data("persons", "Müller")

        assert data_resp.call_count == 1, "Search should be sent as 'search' param"

    @responses.activate
    def test_lang_can_be_set_by_caller(self, openapi_spec, single_person):
        """The caller can still request a single language explicitly"""
        self._mock_openapi(openapi_spec)
        self._mock_variables(single_person)
        data_resp = self._mock_persons({"lang_format": "flat", "lang": "de"})

        backend = OpenParlDataBackend()
        backend.get_data("persons", lang="de")

        assert data_resp.call_count == 1, "lang should be forwarded to the API"

    @responses.activate
    def test_get_glimpse_uses_same_lang_params(self, openapi_spec, single_person):
        """get_glimpse() uses the same language params as get_data()"""
        self._mock_openapi(openapi_spec)
        self._mock_variables(single_person)
        glimpse_resp = self._mock_persons({"lang_format": "flat", "limit": 3})

        backend = OpenParlDataBackend()
        backend.get_glimpse("persons", rows=3)

        assert glimpse_resp.call_count == 1, "Glimpse should send 'lang_format'"

    @responses.activate
    def test_no_warning_for_documented_query_params(
        self, openapi_spec, single_person, caplog
    ):
        """Documented query params like 'limit' or 'sort_by' don't warn"""
        self._mock_openapi(openapi_spec)
        self._mock_variables(single_person)
        self._mock_persons(
            {"lang_format": "flat", "limit": 10, "sort_by": "-id"},
        )

        backend = OpenParlDataBackend()
        with caplog.at_level(logging.WARNING):
            backend.get_data("persons", limit=10, sort_by="-id")

        assert caplog.text == "", f"Expected no warnings, got: {caplog.text}"

    @responses.activate
    def test_warning_for_unknown_attribute(self, openapi_spec, single_person, caplog):
        """An unknown attribute warns and the table name is interpolated"""
        self._mock_openapi(openapi_spec)
        self._mock_variables(single_person)
        self._mock_persons({"lang_format": "flat", "firstnam": "Stefan"})

        backend = OpenParlDataBackend()
        with caplog.at_level(logging.WARNING):
            backend.get_data("persons", firstnam="Stefan")

        assert "firstnam" in caplog.text, f"Expected a warning, got: {caplog.text}"
        assert (
            "for table 'persons'" in caplog.text
        ), f"Table name should be interpolated, got: {caplog.text}"
        assert "{table}" not in caplog.text, "Table name should not be a literal"

    @responses.activate
    def test_get_query_params_from_spec(self, openapi_spec):
        """Query params are read from the OpenAPI spec"""
        self._mock_openapi(openapi_spec)

        backend = OpenParlDataBackend()
        params = backend.get_query_params("persons")

        assert "limit" in params
        assert "sort_by" in params
        assert "search_scope" in params

    @responses.activate
    def test_get_query_params_fallback(self, openapi_spec):
        """Unknown tables fall back to the documented query params"""
        self._mock_openapi(openapi_spec)

        backend = OpenParlDataBackend()
        params = backend.get_query_params("does_not_exist")

        assert params == FALLBACK_QUERY_PARAMS

    @responses.activate
    def test_related_data_does_not_add_lang(
        self, openapi_spec, single_person, person_memberships
    ):
        """Related data requests don't invent language params"""
        self._mock_openapi(openapi_spec)
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            body=single_person,
            status=200,
        )
        memberships_resp = responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons/9527/memberships",
            body=person_memberships,
            match=[matchers.query_param_matcher({"lang_format": "flat"})],
            status=200,
        )

        backend = OpenParlDataBackend()
        person = cast(OpenParlDataProxy, backend.get_data("persons")[0])
        person.get_related_data("memberships")

        assert (
            memberships_resp.call_count == 1
        ), "Related data should be requested without a 'lang' param"


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
