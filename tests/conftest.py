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
    """OpenParlData response fixture for a person's memberships"""
    return fixture_content("person_memberships.json")


@pytest.fixture
def gever_wahlkreise():
    """Gever search response of the canton (single page)"""
    return fixture_content("gever_wahlkreise.xml")


@pytest.fixture
def gever_wahlkreise_schema():
    """Gever schema of the table 'wahlkreise'"""
    return fixture_content("gever_wahlkreise_schema.xml")


@pytest.fixture
def gever_mitglieder():
    """Gever search response with single and multiple occurrence list fields"""
    return fixture_content("gever_mitglieder.xml")


@pytest.fixture
def gever_mitglieder_schema():
    """Gever schema of the table 'mitglieder' (with list fields)"""
    return fixture_content("gever_mitglieder_schema.xml")


@pytest.fixture
def gever_geschaeft_schema():
    """Gever schema of the table 'geschaeft'"""
    return fixture_content("gever_geschaeft_schema.xml")


@pytest.fixture
def gever_geschaeft_page1():
    """Gever search response of the city (page 1 of 2)"""
    return fixture_content("gever_geschaeft_page1.xml")


@pytest.fixture
def gever_geschaeft_page2():
    """Gever search response of the city (page 2 of 2)"""
    return fixture_content("gever_geschaeft_page2.xml")


@pytest.fixture
def gever_ablaufschritte():
    """Gever search response with a repeated element ('geschaeft')"""
    return fixture_content("gever_ablaufschritte.xml")


@pytest.fixture
def gever_ablaufschritte_schema():
    """Gever schema with a numeric 'maxOccurs'"""
    return fixture_content("gever_ablaufschritte_schema.xml")


@pytest.fixture
def gever_sitzungendetail():
    """Gever search response with a document (eDokument)"""
    return fixture_content("gever_sitzungendetail.xml")


@pytest.fixture
def affairs_page1():
    """OpenParlData affairs data fixture (page 1)"""
    return fixture_content("affairs_1.json")


@pytest.fixture
def affairs_page2():
    """OpenParlData affairs data fixture (page 2)"""
    return fixture_content("affairs_2.json")
