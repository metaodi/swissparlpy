"""Client for Swiss parliament API"""

__version__ = "0.3.0"
__all__ = ["client", "errors", "visualization"]

from .errors import SwissParlError  # noqa
from .client import SwissParlClient
from pyodata.v2.service import GetEntitySetFilter as filter  # noqa

# Import visualization function if matplotlib is available
try:
    from .visualization import plot_voting  # noqa
except ImportError:
    # matplotlib not installed, plot_voting will not be available
    pass


def get_tables():
    client = SwissParlClient()
    return client.get_tables()


def get_variables(table):
    client = SwissParlClient()
    return client.get_variables(table)


def get_overview():
    client = SwissParlClient()
    return client.get_overview()


def get_glimpse(table, rows=5):
    client = SwissParlClient()
    return client.get_glimpse(table, rows)


def get_data(table, filter=None, **kwargs):  # noqa
    client = SwissParlClient()
    return client.get_data(table, filter, **kwargs)
