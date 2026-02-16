"""Client for Swiss parliament API"""

__version__ = "1.0.0"
__all__ = ["client", "errors", "visualization"]

from .errors import SwissParlError  # noqa
from .client import SwissParlClient  # noqa
from .client import SwissParlResponse  # noqa
from .visualization import plot_voting  # noqa
from pyodata.v2.service import GetEntitySetFilter as Filter  # noqa
from typing import Callable, Union, Any


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
    table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
) -> "SwissParlResponse":
    client = SwissParlClient()
    return client.get_data(table, filter, **kwargs)
