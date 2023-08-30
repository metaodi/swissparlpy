import warnings
import requests
import pyodata
from . import errors

SERVICE_URL = 'https://ws.parlament.ch/odata.svc/'


class SwissParlClient(object):
    def __init__(self, session=None, url=SERVICE_URL):
        if not session:
            session = requests.Session()
        self.url = url
        self.client = pyodata.Client(url, session)
        self.cache = {}
        self.get_overview()

    def get_tables(self):
        if self.cache:
            return list(self.cache.keys())
        return [es.name for es in self.client.schema.entity_sets]

    def get_variables(self, table):
        if self.cache and table in self.cache:
            return self.cache[table]
        return [p.name for p in self.client.schema.entity_type(table).proprties()]

    def get_overview(self):
        if self.cache:
            return self.cache
        self.cache = {}
        for t in self.get_tables():
            self.cache[t] = self.get_variables(t)
        return self.cache

    def get_glimpse(self, table, rows=5):
        entities = self._get_entities(table)
        return SwissParlResponse(
            entities.top(rows).count(inline=True),
            self.get_variables(table)
        )

    def get_data(self, table, filter=None, **kwargs):
        entities = self._get_entities(table)
        if filter and callable(filter):
            entities = entities.filter(filter(entities))
        elif filter:
            entities = entities.filter(filter)

        if kwargs:
            entities = entities.filter(**kwargs)
        return SwissParlResponse(
            entities.count(inline=True),
            self.get_variables(table)
        )

    def _get_entities(self, table):
        return getattr(self.client.entity_sets, table).get_entities()


class SwissParlResponse(object):
    def __init__(self, entity_request, variables):
        self.variables = variables
        self.data = []
        self.entity_request = entity_request
        entities = self.load()
        self._parse_data(entities)

    def load(self, next_url=None):
        if next_url:
            entities = self.entity_request.next_url(next_url).execute()
        else:
            entities = self.entity_request.execute()

        return entities

    def _load_new_data_until(self, limit):
        if limit >= 10000:
            warnings.warn(
		f"""
                More than 10'000 items are loaded, this will use a lot of memory.
                Consider to query a subset of the data to improve performance.
		""",
		errors.ResultVeryLargeWarning,
	    )
        while limit >= len(self.data):
            try:
                self._load_new_data()
            except errors.NoMoreRecordsError:
                break

    def _load_new_data(self):
        if self.next_url is None:
            raise errors.NoMoreRecordsError()
        entities = self.load(next_url=self.next_url)
        self._parse_data(entities)

    def _parse_data(self, entities):
        self.count = entities.total_count
        self._setup_proxies(entities)
        self.next_url = entities.next_url
            
    def _setup_proxies(self, entities):
        for e in entities:
            self.data.append(SwissParlDataProxy(e))

    def __len__(self):
        return self.count

    def __iter__(self):
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

    def __getitem__(self, key):
        if isinstance(key, slice):
            limit = max(key.start or 0, key.stop or self.count)
            self._load_new_data_until(limit)
            count = len(self.data)
            return [{k: self.data[i](k) for k in self.variables} for i in range(*key.indices(count))]

        if not isinstance(key, int):
            raise TypeError("Index must be an integer or slice")

        limit = key
        if limit < 0:
            # if we get a negative index, load all data
            limit = self.count
        self._load_new_data_until(limit)
        return {k: self.data[key](k) for k in self.variables}


class SwissParlDataProxy(object):
    def __init__(self, proxy):
        self.proxy = proxy

    def __call__(self, attribute):
        return getattr(self.proxy, attribute)
