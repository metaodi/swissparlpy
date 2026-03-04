import logging
import requests
from .backends import ODataBackend, OpenParlDataBackend, GeverBackend
from .backends import BaseBackend, BaseResponse
from typing import Optional, Union, Callable, Any, Literal

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

log = logging.getLogger(__name__)


class SwissParlClient(object):
    def __init__(
        self,
        session: Optional[requests.Session] = None,
        backend: Optional[
            Union[
                BaseBackend,
                Literal[
                    "odata", "openparldata", "gever_canton_zurich", "gever_city_zurich"
                ],
            ]
        ] = None,
    ) -> None:
        if isinstance(backend, BaseBackend):
            self.backend = backend
        elif backend == "openparldata":
            self.backend = OpenParlDataBackend(session)
        elif backend == "gever_canton_zurich":
            self.backend = GeverBackend(session, instance="canton_zurich")
        elif backend == "gever_city_zurich":
            self.backend = GeverBackend(session, instance="city_zurich")
        else:
            # Default to OData backend for backward compatibility
            self.backend = ODataBackend(session)

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

    def __init__(self, backend_response: BaseResponse) -> None:
        # Delegate to the backend response object
        self._backend_response = backend_response

    @property
    def count(self) -> int:
        return len(self._backend_response)

    @property
    def _records_loaded_count(self) -> int:
        return self._backend_response._records_loaded_count

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
