"""Base backend interface for swissparlpy"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Union

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class BaseBackend(ABC):
    """Abstract base class for backend implementations"""

    @abstractmethod
    def get_tables(self) -> list[str]:
        """Return list of available tables/datasets"""
        pass

    @abstractmethod
    def get_variables(self, table: str) -> list[str]:
        """Return list of variables/columns for a given table"""
        pass

    @abstractmethod
    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> Any:
        """Query data from a table with optional filters"""
        pass

    @abstractmethod
    def get_glimpse(self, table: str, rows: int = 5) -> Any:
        """Get a preview of the first N rows of a table"""
        pass


class BaseResponse(ABC):
    """Abstract base class for backend responses"""

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of records in the response"""
        pass

    @property
    @abstractmethod
    def _records_loaded_count(self) -> int:
        """Return the internal records count"""
        pass

    @abstractmethod
    def __iter__(self) -> Any:
        """Return an iterator over the records in the response"""
        pass

    @abstractmethod
    def __getitem__(self, key: Union[int, slice]) -> object:
        """Get a specific record or slice of records from the response"""
        pass

    @abstractmethod
    def to_dict_list(self) -> list[dict[str, Any]]:
        """Convert all data to a list of dictionaries"""
        pass

    @property
    @abstractmethod
    def variables(self) -> list[str]:
        """Return the list of variable names in the response"""
        pass

    def to_dataframe(self) -> "pd.DataFrame":
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is not installed. Install it with "
                "'pip install pandas' to use to_dataframe()."
            )
        return pd.DataFrame(self.to_dict_list())
