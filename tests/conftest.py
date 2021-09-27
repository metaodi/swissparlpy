import pytest
import os

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


def fixture_content(filename):
    path = os.path.join(__location__, 'fixtures', filename)
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()


@pytest.fixture
def metadata():
    """OData metadata fixture"""
    return fixture_content("metadata.xml")
