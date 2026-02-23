"""Tests for OpenParlData backend"""

import pytest
import responses
from responses import matchers
from unittest.mock import Mock
from swissparlpy.backends.openparldata import (
    OpenParlDataBackend,
    OpenParlDataResponse,
    OpenParlDataProxy,
)
from swissparlpy.client import SwissParlClient
from swissparlpy import errors
import re

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
        assert response.data[0]["fullname"] == "Maya Graf"
        assert response.data[1]["fullname"] == "John Doe"

    @responses.activate
    def test_get_related_data(self, openapi_spec, single_person, person_memberships):
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
            body=single_person,
            status=200,
        )

        # Mock the cantons data endpoint for getting variables
        responses.add(
            responses.GET,
            "https://api.openparldata.ch/v1/persons/9527/memberships",
            body=person_memberships,
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("persons")
        person = response[0]
        related_memberships = person.get_related_data("memberships")

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
        assert response.data[0]["fullname"] == "Maya Graf"
        assert (
            response.table == "persons"
        ), f"Response should have persons as table name, got {response.table}"
        assert (
            related_memberships.table == "memberships"
        ), f"Related memberships should have memberships as table name, got {related_memberships.table}"
        assert (
            len(related_memberships) == 115
        ), f"Related memberships should have 115 records, got {len(related_memberships)}"
        assert (
            related_memberships.data[0]["group_name_de"]
            == "World Winter Games Switzerland 2029 (WWG)"
        ), f"First membership group_name_de should be 'World Winter Games Switzerland 2029 (WWG)', got {related_memberships.data[0]['group_name_de']}"
        assert (
            related_memberships.data[0]["type_harmonized"] == "interest_group"
        ), f"First membership type_harmonized should be 'interest_group', got {related_memberships.data[0]['type_harmonized']}"

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
            match=[matchers.query_param_matcher({"limit": 1})],
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

        assert isinstance(response, OpenParlDataResponse)
        assert len(response.data) == 1
        assert response.data[0]["firstname"] == "Stefan"

        assert (
            oap_resp.call_count == 1
        ), f"OpenAPI spec endpoint should be called once, was called {oap_resp.call_count} times"
        assert (
            pers_var_resp.call_count == 1
        ), f"Persons variables endpoint should be called once, was called {pers_var_resp.call_count} times"
        assert (
            pers_resp.call_count == 1
        ), f"Persons data endpoint should be called once, was called {pers_resp.call_count} times"

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
                f"Affairs endpoint called {call_count['count']} times with URL: {request.url} and params: {request.params}"
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
        ), f"Affairs endpoint should not have been called yet, was called {call_count['count']} times"

        backend = OpenParlDataBackend()
        response = backend.get_data("affairs")

        # Iterate through all pages
        assert response.count == 4, f"Total count should be 4, got {response.count}"
        assert (
            response._records_loaded_count == 2
        ), f"After first page, records loaded count should be 2, got {response._records_loaded_count}"

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
        ), f"After all pages, records loaded count should be 4, got {response._records_loaded_count}"

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
                f"Affairs endpoint called {call_count['count']} times with URL: {request.url} and params: {request.params}"
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
        ), f"Affairs endpoint should not have been called yet, was called {call_count['count']} times"

        backend = OpenParlDataBackend()
        response = backend.get_data("affairs")

        # Iterate through all pages
        assert response.count == 4, f"Total count should be 4, got {response.count}"
        assert (
            response._records_loaded_count == 2
        ), f"After first page, records loaded count should be 2, got {response._records_loaded_count}"

        # when all entries are loaded, it should stop and not enter an infinite loop, even if next_page is wrong
        with pytest.warns(errors.PaginationWarning) as record:
            items = list(response)

        assert len(record) == 1, f"Expected one pagination warning, got {len(record)}"
        assert "Loaded more records" in str(
            record[0].message
        ), f"Expected warning message to contain 'Loaded more records', got {record[0].message}"

        assert (
            len(items) == 6
        ), f"Total items should be 6 after pagination, got {len(items)}"
        assert items[0]["affair"] == "Zürich"
        assert items[1]["affair"] == "Bern"
        assert (
            response._records_loaded_count == 6
        ), f"After all pages, records loaded count should be 6, got {response._records_loaded_count}"

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
