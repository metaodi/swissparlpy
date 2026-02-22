"""OData backend implementation"""

import logging
import warnings
import requests
import pyodata
from .base import BaseBackend, BaseResponse
from .. import errors
from typing import Optional, Union, Callable, Any

log = logging.getLogger(__name__)

SERVICE_URL = "https://ws.parlament.ch/odata.svc/"


class ODataBackend(BaseBackend):
    """Backend implementation for OData API"""

    def __init__(
        self, session: Optional[requests.Session] = None, url: str = SERVICE_URL
    ) -> None:
        if not session:
            session = requests.Session()
        self.url = url
        self.client = pyodata.Client(url, session)
        self.cache: dict[str, list[str]] = {}
        self._load_overview()

    def _load_overview(self) -> None:
        """Load tables and variables into cache"""
        log.debug("Load tables and variables from OData...")
        if self.cache:
            return
        self.cache = {}
        for t in self.get_tables():
            self.cache[t] = self.get_variables(t)

    def get_tables(self) -> list[str]:
        if self.cache:
            return list(self.cache.keys())
        return [es.name for es in self.client.schema.entity_sets]

    def get_variables(self, table: str) -> list[str]:
        if self.cache and table in self.cache:
            return self.cache[table]
        entity_type = self.client.schema.entity_type(table)
        return [p.name for p in entity_type.proprties()]

    def get_glimpse(self, table: str, rows: int = 5) -> "ODataResponse":
        entities = self._get_entities(table)
        return ODataResponse(
            entities.top(rows).count(inline=True),  # type: ignore
            self.get_variables(table),
        )

    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> "ODataResponse":
        entities = self._get_entities(table)
        if filter and callable(filter):
            entities = entities.filter(filter(entities))  # type: ignore
        elif filter:
            entities = entities.filter(filter)  # type: ignore

        if kwargs:
            entities = entities.filter(**kwargs)  # type: ignore
        return ODataResponse(
            entities.count(inline=True),  # type: ignore
            self.get_variables(table),
        )

    def _get_entities(self, table: str) -> object:
        return getattr(self.client.entity_sets, table).get_entities()


class ODataResponse(BaseResponse):
    """Response wrapper for OData queries"""

    def __init__(self, entity_request: object, variables: list[str]) -> None:
        self._variables = variables
        self.data: list["ODataProxy"] = []
        self.count = 0
        self.entity_request = entity_request
        entities = self.load()
        self._parse_data(entities)

    @property
    def _records_loaded_count(self) -> int:
        return len(self.data)

    @property
    def variables(self) -> list[str]:
        return self._variables

    def load(self, next_url: Union[str, None] = None) -> object:
        log.debug(f"Load data, next_url={next_url}")
        try:
            if next_url:
                entities = self.entity_request.next_url(  # type: ignore[attr-defined]
                    next_url
                ).execute()
            else:
                entities = self.entity_request.execute()  # type: ignore[attr-defined]
        except pyodata.exceptions.HttpError as e:
            is_timeout = False
            response = getattr(e, "response", None)
            if response is not None:
                status_code = getattr(response, "status_code", None)
                # Treat common HTTP timeout / gateway timeout status codes as timeouts.
                if status_code in (408, 504):
                    is_timeout = True
                else:
                    content = getattr(response, "content", b"")
                    if isinstance(content, str):
                        content_bytes = content.encode("utf-8", errors="replace")
                    else:
                        content_bytes = content or b""
                    if b"Execution Timeout Expired." in content_bytes:
                        is_timeout = True
            if is_timeout:
                raise errors.SwissParlTimeoutError(
                    "The server returned a timeout error"
                ) from e

            raise errors.SwissParlError("The server returned a HTTP error") from e

        return entities

    def _load_new_data_until(self, limit: int) -> None:
        if limit >= 10000:
            warnings.warn(
                """
                More than 10'000 items are loaded, this will use a lot
                of memory. Consider to query a subset of the data to
                improve performance.
                """,
                errors.ResultVeryLargeWarning,
            )
        log.debug(f"Load new data, limit={limit}")
        while limit >= len(self.data):
            try:
                self._load_new_data()
                log.debug(
                    f"""
                    New data loaded:
                    - limit={limit}
                    - len(data)={len(self.data)}
                    - count={self.count}
                    """
                )
            except errors.NoMoreRecordsError:
                break

    def _load_new_data(self) -> None:
        if self.next_url is None:
            raise errors.NoMoreRecordsError()
        entities = self.load(next_url=self.next_url)
        self._parse_data(entities)

    def _parse_data(self, entities: object) -> None:
        self.count = entities.total_count  # type: ignore
        self._setup_proxies(entities)
        self.next_url = entities.next_url  # type: ignore

    def _setup_proxies(self, entities: object) -> None:
        for e in entities:  # type: ignore
            self.data.append(ODataProxy(e))

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Any:
        # use while loop since self.data could grow while iterating
        i = 0
        while True:
            # load new data when near end
            if i == len(self.data):
                try:
                    self._load_new_data()
                except errors.NoMoreRecordsError:
                    break
            yield {k: self.data[i](k) for k in self.variables}
            i += 1

    def __getitem__(self, key: Union[int, slice]) -> object:
        if isinstance(key, slice):
            limit = max(key.start or 0, key.stop or self.count)
            self._load_new_data_until(limit)
            count = len(self.data)
            return [
                {k: self.data[i](k) for k in self.variables}
                for i in range(*key.indices(count))
            ]

        if not isinstance(key, int):
            raise TypeError("Index must be an integer or slice")

        limit = key
        if limit < 0:
            # if we get a negative index, load all data
            limit = self.count
        self._load_new_data_until(limit)
        return {k: self.data[key](k) for k in self.variables}

    def to_dict_list(self) -> list[dict[str, object]]:
        """Convert all data to a list of dictionaries"""
        self._load_new_data_until(self.count)
        return list(self)


class ODataProxy(object):
    """Proxy for OData entity objects"""

    def __init__(self, proxy: object) -> None:
        self.proxy = proxy

    def __call__(self, attribute: str) -> object:
        return getattr(self.proxy, attribute)
