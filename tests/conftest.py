import pytest
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def fixture_content(filename):
    path = os.path.join(__location__, "fixtures", filename)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def metadata():
    """OData metadata fixture"""
    return fixture_content("metadata.xml")


@pytest.fixture
def business_page1():
    """OData business data fixture"""
    return fixture_content("business_1.json")


@pytest.fixture
def business_page2():
    """OData business data fixture"""
    return fixture_content("business_2.json")


@pytest.fixture
def openapi_spec():
    """OpenParlData OpenAPI specification fixture"""
    return fixture_content("openapi.json")


@pytest.fixture
def single_person():
    """OpenParlData response fixture for a single person"""
    return fixture_content("single_person.json")


@pytest.fixture
def person_memberships():
    """OpenParlData response fixture for a single person"""
    return fixture_content("person_memberships.json")


@pytest.fixture
def affairs_page1():
    """OData affairs data fixture"""
    return fixture_content("affairs_1.json")


@pytest.fixture
def affairs_page2():
    """OpenParlData affairs data fixture"""
    return fixture_content("affairs_2.json")
