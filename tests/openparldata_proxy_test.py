import pytest
from swissparlpy.backends.openparldata import OpenParlDataProxy, OpenParlDataResponse
from swissparlpy import errors

class DummyParent:
    def __init__(self):
        self.params = {}
        self.session = None

def test_get_related_tables_basic():
    record = {
        'id': 1,
        'links': {'affairs': '/affairs/1', 'business': '/business/1'}
    }
    proxy = OpenParlDataProxy(record, DummyParent())
    related = proxy.get_related_tables()
    assert isinstance(related, list)
    assert set(related) == {'affairs', 'business'}

def test_get_related_tables_empty():
    record = {'id': 2, 'links': {}}
    proxy = OpenParlDataProxy(record, DummyParent())
    related = proxy.get_related_tables()
    assert related == []

def test_get_related_tables_missing_links():
    record = {'id': 3}
    proxy = OpenParlDataProxy(record, DummyParent())
    related = proxy.get_related_tables()
    assert related == []

def test_get_related_tables_links_not_dict():
    record = {'id': 4, 'links': 'not_a_dict'}
    proxy = OpenParlDataProxy(record, DummyParent())
    with pytest.raises(errors.SwissParlError):
        proxy.get_related_tables()
