import requests
import pyodata

SERVICE_URL = 'https://ws.parlament.ch/odata.svc/'


class SwissParlClient(object):
    def __init__(self, session=None):
        if not session:
            session = requests.Session()
        self.client = pyodata.Client(SERVICE_URL, session)
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

    def get_data(self, table, **kwargs):
        entities = self._get_entities(table)
        return SwissParlResponse(
            entities.count(inline=True).filter(**kwargs),
            self.get_variables(table)
        )

    def _get_entities(self, table):
        return getattr(self.client.entity_sets, table).get_entities()


class SwissParlResponse(object):
    def __init__(self, entity_request, variables):
        self.entities = entity_request.execute()
        self.count = self.entities.total_count
        self.variables = variables

        self.data = []
        self._setup_proxies()

    def _setup_proxies(self):
        for e in self.entities:
            row = {k: SwissParlDataProxy(e, k) for k in self.variables}
            self.data.append(row)

    def __len__(self):
        return self.count

    def __iter__(self):
        for row in self.data:
            yield {k: v() for k, v in row.items()}

    def __getitem__(self, key):
        items = self.data[key]
        if isinstance(key, slice):
            return [{k: v() for k, v in i.items()} for i in items]
        return {k: v() for k, v in items.items()}


class SwissParlDataProxy(object):
    def __init__(self, proxy, attribute):
        self.proxy = proxy
        self.attribute = attribute

    def __call__(self):
        return getattr(self.proxy, self.attribute)
