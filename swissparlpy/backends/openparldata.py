"""OpenParlData backend implementation"""

import logging
import requests
import warnings
from .base import BaseBackend, BaseResponse
from .. import errors
from typing import Optional, Union, Callable, Any
from urllib.parse import urlparse, parse_qs

log = logging.getLogger(__name__)

OPENPARLDATA_URL = "https://api.openparldata.ch/"
OPENPARLDATA_OPENAPI_URL = "https://api.openparldata.ch/openapi.json"


class OpenParlDataBackend(BaseBackend):
    """Backend implementation for OpenParlData REST API"""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        url: str = OPENPARLDATA_OPENAPI_URL,
    ) -> None:
        if not session:
            session = requests.Session()
        self.session = session
        self.cache: dict[str, list[str]] = {}
        self.openapi_url = url
        api_config = self._load_openapi_config(url)
        # use v1 of the API
        self.base_url = f"{api_config['base_url']}v1"

    def _load_openapi_config(self, openapi_url: str) -> dict[str, Any]:
        """Load OpenAPI configuration from the given URL"""
        resp = self._http_get_request(openapi_url)
        data = resp.json()

        api_paths = []
        entities = set()
        for api_path, api_details in data["paths"].items():
            get_config = api_details.get("get", {})
            tags = get_config.get("tags", [])
            summary = get_config.get("summary", "")
            api_paths.append(api_path)

            # check if the path corresponds to a table/resource endpoint
            if "List" in summary:
                entities.update(tags)

        api_config = {
            "base_url": data.get("servers", [{"url": OPENPARLDATA_URL}])[0]["url"],
            "tables": list(entities),
            "endpoints": api_paths,
        }
        # Initialize cache with empty variable lists
        self.cache = {table: [] for table in api_config["tables"]}
        return api_config

    def _http_get_request(
        self, url: str, params: Optional[dict] = None
    ) -> requests.Response:
        """Helper method to make HTTP requests with error handling"""
        if params is None:
            params = {}
        headers = {"user-agent": "Mozilla Firefox Mozilla/5.0; metaodi swissparlpy"}
        if "user-agent" not in self.session.headers:
            self.session.headers["user-agent"] = headers["user-agent"]

        try:
            r = self.session.get(url, timeout=10, params=params)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            log.error(f"Error making GET request to {url}: {e}")
            raise errors.SwissParlHttpRequestError(
                f"Failed to make GET request to {url}: {e}"
            ) from e

    def get_tables(self) -> list[str]:
        """
        Get list of available resources/tables from the API.
        """
        if self.cache:
            return list(self.cache.keys())

        # Make request to discover available endpoints
        self._load_openapi_config(self.openapi_url)
        return list(self.cache.keys())

    def get_variables(self, table: str) -> list[str]:
        """
        Get list of variables/columns for a given table.
        """
        if self.cache and table in self.cache and self.cache[table]:
            return self.cache[table]

        # Try to get a single record to discover the schema
        response = self._http_get_request(
            f"{self.base_url}/{table}", params={"limit": 1}
        )
        try:
            data = response.json()["data"][0]
            if data:
                self.cache[table] = list(data.keys())

            return self.cache[table]
        except (KeyError, IndexError, TypeError) as e:
            log.error(f"Error parsing response for variables of table '{table}': {e}")
            raise errors.SwissParlError(
                f"Failed to get variables for table '{table}': {e}"
            ) from e

    def get_glimpse(self, table: str, rows: int = 5) -> "OpenParlDataResponse":
        """Get a preview of the first N rows of a table"""
        params = {"limit": rows}
        return OpenParlDataResponse(
            session=self.session,
            url=f"{self.base_url}/{table}",
            params=params,
            table=table,
            variables=self.get_variables(table),
        )

    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> "OpenParlDataResponse":
        """Query data from a table with optional filters"""
        if table not in self.get_tables():
            raise errors.TableNotFoundError(
                f"Table '{table}' not found in OpenParlData API"
            )
        variables = self.get_variables(table)

        params = {
            "lang_format": "flat",
            "lang": "en",
            "lang_fallback": "de",
            "search_mode": "partial",
            "search_scope": "all",
        }

        params["search"] = ""

        # Handle text filter
        if filter and isinstance(filter, str):
            params["search"] = filter
        elif filter and callable(filter):
            # Callable filters are not supported for REST API
            log.warning("Callable filters are not supported for OpenParlData backend")

        # Convert kwargs to query parameters
        for key, value in kwargs.items():
            if (key not in variables) and (key not in params):
                log.warning(
                    f"Attribute '{key}' is not a variable "
                    "or search param for table '{table}'"
                )
            params[key] = value

        return OpenParlDataResponse(
            session=self.session,
            url=f"{self.base_url}/{table}",
            params=params,
            table=table,
            variables=variables,
        )


class OpenParlDataResponse(BaseResponse):
    """Response wrapper for OpenParlData queries"""

    def __init__(
        self,
        session: requests.Session,
        url: str,
        params: dict[str, Any],
        table: str,
        variables: Optional[list[str]] = None,
    ) -> None:
        self.session = session
        self._table = table
        self._variables = variables or []
        self.data: list[OpenParlDataProxy] = []
        self.count = 0
        self.next_url: Optional[str] = None

        # Extract query parameters from URL if present
        parsed_url = urlparse(url)
        url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            for key, values in query_params.items():
                params[key] = values[0] if values else ""

        self.url = url
        self.params = params
        self._load_first_page()

    @property
    def _records_loaded_count(self) -> int:
        return len(self.data)

    @property
    def table(self) -> str:
        return self._table

    @property
    def variables(self) -> list[str]:
        return self._variables

    def _load_first_page(self) -> None:
        """Load the first page of results"""
        try:
            log.debug(
                f"Loading first page of data from {self.url} with params {self.params}"
            )
            response = self.session.get(self.url, params=self.params)
            response.raise_for_status()
            self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            log.error(f"Error loading data: {e}")
            raise errors.SwissParlError(f"Failed to load data: {e}") from e

    def _parse_response(self, data: Any) -> None:
        """Parse API response and extract data"""
        if isinstance(data, dict):
            records = data["data"]
            pagination = data.get("meta", {})
            self.count = pagination.get("total_records", len(records))
            self.next_url = pagination.get("next_page")
            if not pagination.get("has_more", False):
                self.next_url = None  # Ensure next_url is None if has_more is False

            # Update variables if not already set
            if not self._variables and len(records) > 0:
                self._variables = list(records[0].keys())

        else:
            records = []
            self.count = 0
            self.next_url = None

        # Wrap each record in a proxy object
        for record in records:
            self.data.append(OpenParlDataProxy(record, self))

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

    def __repr__(self) -> str:
        return self.data.__repr__()

    def __iter__(self) -> Any:
        """Iterate over all records, loading pages as needed"""
        i = 0
        while True:
            if i >= len(self.data):
                if i > self.count:
                    warnings.warn(
                        f"Loaded more records ({i}) than total count ({self.count}),"
                        "stopping iteration",
                        errors.PaginationWarning,
                    )
                    break
                if self.next_url:
                    try:
                        log.debug(
                            f"Reached end of current data {i}/{len(self.data)}, "
                            f"loading next page: {self.next_url}"
                        )
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
        return list(self)


class OpenParlDataProxy(dict):
    """Proxy for OpenParlData entity objects"""

    def __init__(
        self, record: dict[str, object], parent: "OpenParlDataResponse"
    ) -> None:
        super().__init__(record)
        self.record = record
        self.parent = parent

    def __call__(self, attribute: str) -> object:
        return self.record.get(attribute)

    def __getitem__(self, key: str) -> object:
        return self.record[key]

    def get_related_data(self, table: str) -> Optional[OpenParlDataResponse]:
        """Get related data and return its data as OpenParlDataResponse"""
        links = self.record.get("links", {})

        if not isinstance(links, dict):
            raise errors.SwissParlError(
                f"'links' field is not a dict, type: {type(links)}"
            )

        if table not in links:
            raise errors.TableNotFoundError(
                f"Table {table} not found in links for this entry, "
                f"available links: {list(links.keys())}"
            )

        params = {
            "lang_format": self.parent.params.get("lang_format", "flat"),
            "lang": self.parent.params.get("lang", "en"),
            "lang_fallback": self.parent.params.get("lang_fallback", "de"),
        }

        url = links[table]
        return OpenParlDataResponse(
            session=self.parent.session,
            url=url,
            params=params,
            table=table,
            variables=[],  # Let the response discover variables
        )
