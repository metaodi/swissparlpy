"""Base backend interface for swissparlpy"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Union


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
