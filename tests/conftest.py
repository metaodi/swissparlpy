import pytest
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def fixture_content(filename):
    path = os.path.join(__location__, "fixtures", filename)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def fixture_bytes(filename):
    path = os.path.join(__location__, "fixtures", filename)
    if not os.path.exists(path):
        return b""
    with open(path, "rb") as f:
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
    """OpenParlData response fixture for a person's memberships"""
    return fixture_content("person_memberships.json")


@pytest.fixture
def affairs_page1():
    """OpenParlData affairs data fixture (page 1)"""
    return fixture_content("affairs_1.json")


@pytest.fixture
def affairs_page2():
    """OpenParlData affairs data fixture (page 2)"""
    return fixture_content("affairs_2.json")


@pytest.fixture
def wahlkreise_xml():
    """Gever Wahlkreise search response fixture"""
    return fixture_bytes("wahlkreise.xml")


@pytest.fixture
def wahlkreise_schema():
    """Gever Wahlkreise schema fixture"""
    return fixture_bytes("wahlkreise_schema.xml")


@pytest.fixture
def wahlkreise_page1():
    """Gever Wahlkreise paginated response - page 1"""
    return fixture_bytes("wahlkreise_page1.xml")


@pytest.fixture
def wahlkreise_page2():
    """Gever Wahlkreise paginated response - page 2"""
    return fixture_bytes("wahlkreise_page2.xml")
