"""Client for Swiss parliament API"""

__version__ = "1.0.0"
__all__ = ["client", "errors", "visualization", "backends"]

from .errors import SwissParlError  # noqa
from .client import SwissParlClient  # noqa
from .client import SwissParlResponse  # noqa
from .backends import ODataBackend, OpenParlDataBackend  # noqa
from pyodata.v2.service import GetEntitySetFilter as Filter  # noqa
from typing import Callable, Union, Any, Literal

# Import visualization function if matplotlib is available
try:
    from .visualization import plot_voting  # noqa
except ImportError:
    # matplotlib not installed, plot_voting will not be available
    pass


def get_tables(backend: Literal["odata", "openparldata"] = "odata") -> list[str]:
    client = SwissParlClient(backend=_get_backend_instance(backend))
    return client.get_tables()


def get_variables(
    table: str, backend: Literal["odata", "openparldata"] = "odata"
) -> list[str]:
    client = SwissParlClient(backend=_get_backend_instance(backend))
    return client.get_variables(table)


def get_overview(
    backend: Literal["odata", "openparldata"] = "odata",
) -> dict[str, list[str]]:
    client = SwissParlClient(backend=_get_backend_instance(backend))
    return client.get_overview()


def get_glimpse(
    table: str, rows: int = 5, backend: Literal["odata", "openparldata"] = "odata"
) -> "SwissParlResponse":
    client = SwissParlClient(backend=_get_backend_instance(backend))
    return client.get_glimpse(table, rows)


def get_data(
    table: str,
    filter: Union[str, Callable, None] = None,
    backend: Literal["odata", "openparldata"] = "odata",
    **kwargs: Any,
) -> "SwissParlResponse":
    client = SwissParlClient(backend=_get_backend_instance(backend))
    return client.get_data(table, filter, **kwargs)


def _get_backend_instance(backend: Literal["odata", "openparldata"]) -> Any:
    """Helper function to instantiate the appropriate backend"""
    if backend == "openparldata":
        return OpenParlDataBackend()
    else:
        return ODataBackend()
