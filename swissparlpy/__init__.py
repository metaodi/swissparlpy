"""Client for Swiss parliament API"""

__version__ = "2.0.0"
__all__ = ["client", "errors", "visualization", "backends"]

from .errors import SwissParlError  # noqa
from .client import SwissParlClient  # noqa
from .client import SwissParlResponse  # noqa
from .client import BackendName  # noqa
from .backends import ODataBackend, OpenParlDataBackend, GeverBackend  # noqa
from .backends import ODataResponse, OpenParlDataResponse  # noqa
from pyodata.v2.service import GetEntitySetFilter as Filter  # noqa
from typing import Callable, Union, Any

# Import visualization function if matplotlib is available
try:
    from .visualization import plot_voting  # noqa
except ImportError:
    # matplotlib not installed, plot_voting will not be available
    pass


def get_tables(backend: BackendName = "odata") -> list[str]:
    client = SwissParlClient(backend=backend)
    return client.get_tables()


def get_variables(table: str, backend: BackendName = "odata") -> list[str]:
    client = SwissParlClient(backend=backend)
    return client.get_variables(table)


def get_overview(
    backend: BackendName = "odata",
) -> dict[str, list[str]]:
    client = SwissParlClient(backend=backend)
    return client.get_overview()


def get_glimpse(
    table: str, rows: int = 5, backend: BackendName = "odata"
) -> "SwissParlResponse":
    client = SwissParlClient(backend=backend)
    return client.get_glimpse(table, rows)


def get_data(
    table: str,
    filter: Union[str, Callable, None] = None,
    backend: BackendName = "odata",
    **kwargs: Any,
) -> "SwissParlResponse":
    client = SwissParlClient(backend=backend)
    return client.get_data(table, filter, **kwargs)
