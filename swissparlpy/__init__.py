"""Client for Swiss parliament API"""

__version__ = "0.3.0"
__all__ = ["client", "errors", "visualization"]

from .errors import SwissParlError  # noqa
from .client import SwissParlClient  # noqa
from .client import SwissParlResponse  # noqa
from pyodata.v2.service import GetEntitySetFilter as filter  # noqa
from typing import Callable, Union

# Import visualization function if matplotlib is available
try:
    from .visualization import plot_voting  # noqa
except ImportError:
    # matplotlib not installed, plot_voting will not be available
    pass


def get_tables() -> list[str]:
    client = SwissParlClient()
    return client.get_tables()


def get_variables(table: str) -> list[str]:
    client = SwissParlClient()
    return client.get_variables(table)


def get_overview() -> dict[str, list[str]]:
    client = SwissParlClient()
    return client.get_overview()


def get_glimpse(table: str, rows: int = 5) -> object:
    client = SwissParlClient()
    return client.get_glimpse(table, rows)


def get_data(
    table: str, filter: Union[str, Callable, None] = None, **kwargs: dict
) -> "SwissParlResponse":
    client = SwissParlClient()
    return client.get_data(table, filter, **kwargs)
