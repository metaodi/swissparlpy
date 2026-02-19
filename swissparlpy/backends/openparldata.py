"""OpenParlData backend implementation"""

import logging
import requests
from .base import BaseBackend
from .. import errors
from typing import Optional, Union, Callable, Any

log = logging.getLogger(__name__)

OPENPARLDATA_URL = "https://api.openparldata.ch/v1"


class OpenParlDataBackend(BaseBackend):
    """Backend implementation for OpenParlData REST API"""

    def __init__(
        self, session: Optional[requests.Session] = None, url: str = OPENPARLDATA_URL
    ) -> None:
        if not session:
            session = requests.Session()
        self.url = url
        self.session = session
        self.cache: dict[str, list[str]] = {}

    def get_tables(self) -> list[str]:
        """
        Get list of available resources/tables from the API.
        This will be implemented based on the API's endpoint discovery mechanism.
        """
        # TODO: Implement based on actual API structure
        # For now, return common parliament data tables
        if self.cache:
            return list(self.cache.keys())

        # Make request to discover available endpoints
        try:
            response = self.session.get(self.url)
            response.raise_for_status()
            data = response.json()

            # Parse available endpoints from response
            # The exact structure depends on the API implementation
            if isinstance(data, dict) and "resources" in data:
                tables = list(data["resources"].keys())
                return tables
            elif isinstance(data, dict):
                # Assume keys are resource names
                return list(data.keys())
            else:
                # Fallback to empty list if we can't parse
                log.warning("Could not parse tables from API response")
                return []
        except requests.exceptions.RequestException as e:
            log.error(f"Error fetching tables: {e}")
            raise errors.SwissParlError(f"Failed to fetch tables: {e}") from e

    def get_variables(self, table: str) -> list[str]:
        """
        Get list of variables/columns for a given table.
        This will be implemented based on the API's schema discovery mechanism.
        """
        if self.cache and table in self.cache:
            return self.cache[table]

        # TODO: Implement based on actual API structure
        # For now, make a sample request and parse the response schema
        try:
            # Try to get a single record to discover the schema
            response = self.session.get(f"{self.url}/{table}", params={"limit": 1})
            response.raise_for_status()
            data = response.json()

            # Parse schema from response
            if isinstance(data, dict) and "results" in data and len(data["results"]) > 0:
                # Results array format
                return list(data["results"][0].keys())
            elif isinstance(data, list) and len(data) > 0:
                # Direct array format
                return list(data[0].keys())
            elif isinstance(data, dict) and "data" in data and len(data["data"]) > 0:
                # Data array format
                return list(data["data"][0].keys())
            else:
                log.warning(f"Could not parse variables for table {table}")
                return []
        except requests.exceptions.RequestException as e:
            log.error(f"Error fetching variables for {table}: {e}")
            raise errors.SwissParlError(
                f"Failed to fetch variables for {table}: {e}"
            ) from e

    def get_glimpse(self, table: str, rows: int = 5) -> "OpenParlDataResponse":
        """Get a preview of the first N rows of a table"""
        params = {"limit": rows}
        return OpenParlDataResponse(
            self.session, f"{self.url}/{table}", params, self.get_variables(table)
        )

    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> "OpenParlDataResponse":
        """Query data from a table with optional filters"""
        params = {}

        # Convert kwargs to query parameters
        # This will need to be adapted based on the actual API's query syntax
        for key, value in kwargs.items():
            # Handle special operators like __startswith, __contains, etc.
            if "__" in key:
                field, operator = key.rsplit("__", 1)
                # Map operators to API query syntax (this is placeholder logic)
                if operator == "startswith":
                    params[f"{field}__startswith"] = value
                elif operator == "contains":
                    params[f"{field}__contains"] = value
                elif operator in ["gt", "gte", "lt", "lte"]:
                    params[f"{field}__{operator}"] = value
                else:
                    params[key] = value
            else:
                params[key] = value

        # Handle text filter
        if filter and isinstance(filter, str):
            params["filter"] = filter
        elif filter and callable(filter):
            # Callable filters are not supported for REST API
            log.warning("Callable filters are not supported for OpenParlData backend")

        return OpenParlDataResponse(
            self.session, f"{self.url}/{table}", params, self.get_variables(table)
        )


class OpenParlDataResponse(object):
    """Response wrapper for OpenParlData queries"""

    def __init__(
        self,
        session: requests.Session,
        url: str,
        params: dict[str, Any],
        variables: list[str],
    ) -> None:
        self.session = session
        self.url = url
        self.params = params
        self.variables = variables
        self.data: list[dict[str, object]] = []
        self.count = 0
        self.next_url: Optional[str] = None
        self._load_first_page()

    def _load_first_page(self) -> None:
        """Load the first page of results"""
        try:
            response = self.session.get(self.url, params=self.params)
            response.raise_for_status()
            self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            log.error(f"Error loading data: {e}")
            raise errors.SwissParlError(f"Failed to load data: {e}") from e

    def _parse_response(self, data: Any) -> None:
        """Parse API response and extract data"""
        # Handle different response formats
        if isinstance(data, dict):
            # Check for common pagination patterns
            if "results" in data:
                # Format: {"results": [...], "next": "...", "count": 123}
                records = data["results"]
                self.count = data.get("count", len(records))
                self.next_url = data.get("next")
            elif "data" in data:
                # Format: {"data": [...], "pagination": {...}}
                records = data["data"]
                pagination = data.get("pagination", {})
                self.count = pagination.get("total", len(records))
                self.next_url = pagination.get("next")
            elif "items" in data:
                # Format: {"items": [...], "total": 123, "next": "..."}
                records = data["items"]
                self.count = data.get("total", len(records))
                self.next_url = data.get("next")
            else:
                # Assume the dict itself is a single record
                records = [data]
                self.count = 1
                self.next_url = None
        elif isinstance(data, list):
            # Direct array of records
            records = data
            self.count = len(records)
            self.next_url = None
        else:
            records = []
            self.count = 0
            self.next_url = None

        self.data.extend(records)

    def _load_next_page(self) -> None:
        """Load the next page of results"""
        if not self.next_url:
            raise errors.NoMoreRecordsError()

        try:
            response = self.session.get(self.next_url)
            response.raise_for_status()
            self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            log.error(f"Error loading next page: {e}")
            raise errors.SwissParlError(f"Failed to load next page: {e}") from e

    def _load_until(self, limit: int) -> None:
        """Load pages until we have at least 'limit' records"""
        while len(self.data) < limit and self.next_url:
            try:
                self._load_next_page()
            except errors.NoMoreRecordsError:
                break

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Any:
        """Iterate over all records, loading pages as needed"""
        i = 0
        while True:
            if i >= len(self.data):
                if self.next_url:
                    try:
                        self._load_next_page()
                    except errors.NoMoreRecordsError:
                        break
                else:
                    break

            if i < len(self.data):
                yield self.data[i]
                i += 1
            else:
                break

    def __getitem__(self, key: Union[int, slice]) -> object:
        if isinstance(key, slice):
            # Load enough data for the slice
            limit = max(key.start or 0, key.stop or self.count)
            self._load_until(limit)
            return self.data[key]

        if not isinstance(key, int):
            raise TypeError("Index must be an integer or slice")

        # Handle negative indexing
        if key < 0:
            # Load all data for negative indexing
            self._load_until(self.count)
        else:
            # Load enough data for positive indexing
            self._load_until(key + 1)

        return self.data[key]

    def to_dict_list(self) -> list[dict[str, object]]:
        """Convert all data to a list of dictionaries"""
        self._load_until(self.count)
        return list(self.data)
