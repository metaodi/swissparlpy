import logging
import requests
from . import errors
from .backends import ODataBackend
from .backends.base import BaseBackend
from typing import Optional, Union, Callable, Any

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

SERVICE_URL = "https://ws.parlament.ch/odata.svc/"
log = logging.getLogger(__name__)


class SwissParlClient(object):
    def __init__(
        self,
        session: Optional[requests.Session] = None,
        url: str = SERVICE_URL,
        backend: Optional[BaseBackend] = None,
    ) -> None:
        if backend:
            self.backend = backend
        else:
            # Default to OData backend for backward compatibility
            self.backend = ODataBackend(session, url)
        self.url = getattr(self.backend, "url", url)

    def get_tables(self) -> list[str]:
        return self.backend.get_tables()

    def get_variables(self, table: str) -> list[str]:
        return self.backend.get_variables(table)

    def get_overview(self) -> dict[str, list[str]]:
        tables = self.get_tables()
        return {t: self.get_variables(t) for t in tables}

    def get_glimpse(self, table: str, rows: int = 5) -> "SwissParlResponse":
        backend_response = self.backend.get_glimpse(table, rows)
        return SwissParlResponse(backend_response)

    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> "SwissParlResponse":
        backend_response = self.backend.get_data(table, filter, **kwargs)
        return SwissParlResponse(backend_response)


class SwissParlResponse(object):
    """Wrapper for backend responses that provides a unified interface"""

    def __init__(self, backend_response: object) -> None:
        # Delegate to the backend response object
        self._backend_response = backend_response

    @property
    def count(self) -> int:
        return len(self._backend_response)

    @property
    def variables(self) -> list[str]:
        return self._backend_response.variables

    def __len__(self) -> int:
        return len(self._backend_response)

    def __iter__(self) -> Any:
        return iter(self._backend_response)

    def __getitem__(self, key: Union[int, slice]) -> object:
        return self._backend_response[key]

    def to_dataframe(self) -> "pd.DataFrame":
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is not installed. Install it with "
                "'pip install pandas' to use to_dataframe()."
            )
        # Convert backend response to dict list then to DataFrame
        data_list = self._backend_response.to_dict_list()
        return pd.DataFrame(data_list)
