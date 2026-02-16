import logging
import warnings
import requests
import pyodata
from . import errors
from typing import Optional, Union, Callable, Iterator, Any

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

SERVICE_URL = "https://ws.parlament.ch/odata.svc/"
log = logging.getLogger(__name__)


class SwissParlClient(object):
    def __init__(
        self, session: Optional[requests.Session] = None, url: str = SERVICE_URL
    ) -> None:
        if not session:
            session = requests.Session()
        self.url = url
        self.client = pyodata.Client(url, session)
        self.cache: dict[str, list[str]] = {}
        self.get_overview()

    def get_tables(self) -> list[str]:
        if self.cache:
            return list(self.cache.keys())
        return [es.name for es in self.client.schema.entity_sets]

    def get_variables(self, table: str) -> list[str]:
        if self.cache and table in self.cache:
            return self.cache[table]
        entity_type = self.client.schema.entity_type(table)
        return [p.name for p in entity_type.proprties()]

    def get_overview(self) -> dict[str, list[str]]:
        log.debug("Load tables and variables from OData...")
        if self.cache:
            return self.cache
        self.cache = {}
        for t in self.get_tables():
            self.cache[t] = self.get_variables(t)
        return self.cache

    def get_glimpse(self, table: str, rows: int = 5) -> "SwissParlResponse":
        entities = self._get_entities(table)
        return SwissParlResponse(
            entities.top(rows).count(inline=True),  # type: ignore
            self.get_variables(table),
        )

    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> "SwissParlResponse":
        entities = self._get_entities(table)
        if filter and callable(filter):
            entities = entities.filter(filter(entities))  # type: ignore
        elif filter:
            entities = entities.filter(filter)  # type: ignore

        if kwargs:
            entities = entities.filter(**kwargs)  # type: ignore
        return SwissParlResponse(
            entities.count(inline=True),  # type: ignore
            self.get_variables(table),
        )

    def _get_entities(self, table: str) -> object:
        return getattr(self.client.entity_sets, table).get_entities()


class SwissParlResponse(object):
    def __init__(self, entity_request: object, variables: list[str]) -> None:
        self.variables = variables
        self.data: list[SwissParlDataProxy] = []
        self.count = 0
        self.entity_request = entity_request
        entities = self.load()
        self._parse_data(entities)

    def load(self, next_url: Union[str, None] = None) -> object:
        log.debug(f"Load data, next_url={next_url}")
        try:
            if next_url:
                entities = self.entity_request.next_url(next_url).execute()
            else:
                entities = self.entity_request.execute()
        except pyodata.exceptions.HttpError as e:
            if "Execution Timeout Expired." in e.response.content.decode("utf-8"):
                raise errors.TimeoutError("The server returned a timeout error") from e
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
            self.data.append(SwissParlDataProxy(e))

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[dict[str, object]]:
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

    def to_dataframe(self) -> "pd.DataFrame":
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is not installed. Install it with "
                "'pip install pandas' to use to_dataframe()."
            )

        self._load_new_data_until(self.count)
        return pd.DataFrame(list(self))


class SwissParlDataProxy(object):
    def __init__(self, proxy: object) -> None:
        self.proxy = proxy

    def __call__(self, attribute: str) -> object:
        return getattr(self.proxy, attribute)
