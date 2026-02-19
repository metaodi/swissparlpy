"""Tests for OpenParlData backend"""

import pytest
import responses
from unittest.mock import Mock
from swissparlpy.backends.openparldata import OpenParlDataBackend, OpenParlDataResponse
from swissparlpy.client import SwissParlClient
from swissparlpy import errors

OPENPARLDATA_URL = "https://api.openparldata.ch/v1"


class TestOpenParlDataBackend:
    @responses.activate
    def test_get_tables_with_resources(self):
        """Test getting tables when API returns resources"""
        responses.add(
            responses.GET,
            OPENPARLDATA_URL,
            json={"resources": {"cantons": {}, "parties": {}, "persons": {}}},
            status=200,
        )

        backend = OpenParlDataBackend()
        tables = backend.get_tables()

        assert isinstance(tables, list)
        assert "cantons" in tables
        assert "parties" in tables
        assert "persons" in tables

    @responses.activate
    def test_get_tables_with_dict_keys(self):
        """Test getting tables when API returns dict with keys as resources"""
        responses.add(
            responses.GET,
            OPENPARLDATA_URL,
            json={"cantons": "...", "parties": "...", "persons": "..."},
            status=200,
        )

        backend = OpenParlDataBackend()
        tables = backend.get_tables()

        assert isinstance(tables, list)
        assert "cantons" in tables
        assert "parties" in tables
        assert "persons" in tables

    @responses.activate
    def test_get_variables_results_format(self):
        """Test getting variables when API returns results array"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich", "abbreviation": "ZH"},
                ]
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        variables = backend.get_variables("cantons")

        assert isinstance(variables, list)
        assert "id" in variables
        assert "name" in variables
        assert "abbreviation" in variables

    @responses.activate
    def test_get_variables_direct_array(self):
        """Test getting variables when API returns direct array"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/parties",
            json=[
                {"id": 1, "name": "SP", "fullName": "Sozialdemokratische Partei"},
            ],
            status=200,
        )

        backend = OpenParlDataBackend()
        variables = backend.get_variables("parties")

        assert isinstance(variables, list)
        assert "id" in variables
        assert "name" in variables
        assert "fullName" in variables

    @responses.activate
    def test_get_glimpse(self):
        """Test getting a glimpse of data"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich"},
                    {"id": 2, "name": "Bern"},
                ],
                "count": 26,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_glimpse("cantons", rows=2)

        assert isinstance(response, OpenParlDataResponse)
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Zürich"
        assert response.data[1]["name"] == "Bern"

    @responses.activate
    def test_get_data_with_filters(self):
        """Test getting data with filter parameters"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/persons",
            json={
                "results": [
                    {"id": 1, "firstName": "Stefan", "lastName": "Müller"},
                ],
                "count": 1,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("persons", firstName="Stefan")

        assert isinstance(response, OpenParlDataResponse)
        assert len(response.data) == 1
        assert response.data[0]["firstName"] == "Stefan"

    @responses.activate
    def test_response_iteration(self):
        """Test iterating over response data"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich"},
                    {"id": 2, "name": "Bern"},
                ],
                "count": 2,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("cantons")

        items = list(response)
        assert len(items) == 2
        assert items[0]["name"] == "Zürich"
        assert items[1]["name"] == "Bern"

    @responses.activate
    def test_response_indexing(self):
        """Test indexing response data"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich"},
                    {"id": 2, "name": "Bern"},
                    {"id": 3, "name": "Luzern"},
                ],
                "count": 3,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("cantons")

        assert response[0]["name"] == "Zürich"
        assert response[1]["name"] == "Bern"
        assert response[2]["name"] == "Luzern"

    @responses.activate
    def test_response_slicing(self):
        """Test slicing response data"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich"},
                    {"id": 2, "name": "Bern"},
                    {"id": 3, "name": "Luzern"},
                ],
                "count": 3,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("cantons")

        slice_result = response[0:2]
        assert len(slice_result) == 2
        assert slice_result[0]["name"] == "Zürich"
        assert slice_result[1]["name"] == "Bern"

    @responses.activate
    def test_response_pagination(self):
        """Test pagination handling"""
        # First page
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich"},
                    {"id": 2, "name": "Bern"},
                ],
                "count": 4,
                "next": f"{OPENPARLDATA_URL}/cantons?page=2",
            },
            status=200,
        )

        # Second page
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons?page=2",
            json={
                "results": [
                    {"id": 3, "name": "Luzern"},
                    {"id": 4, "name": "Uri"},
                ],
                "count": 4,
                "next": None,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        response = backend.get_data("cantons")

        # Iterate through all pages
        items = list(response)
        assert len(items) == 4
        assert items[0]["name"] == "Zürich"
        assert items[3]["name"] == "Uri"

    @responses.activate
    def test_client_integration_with_openparldata(self):
        """Test SwissParlClient with OpenParlData backend"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/cantons",
            json={
                "results": [
                    {"id": 1, "name": "Zürich"},
                ],
                "count": 1,
            },
            status=200,
        )

        backend = OpenParlDataBackend()
        client = SwissParlClient(backend=backend)
        response = client.get_data("cantons")

        assert response.count == 1
        assert response[0]["name"] == "Zürich"

    @responses.activate
    def test_error_handling(self):
        """Test error handling for failed requests"""
        responses.add(
            responses.GET,
            f"{OPENPARLDATA_URL}/invalid",
            json={"error": "Not found"},
            status=404,
        )

        backend = OpenParlDataBackend()

        with pytest.raises(errors.SwissParlError, match="Failed to fetch variables"):
            backend.get_variables("invalid")
