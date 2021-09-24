import requests
import pyodata

SERVICE_URL = 'https://ws.parlament.ch/odata.svc/'

# Create instance of OData client
client = pyodata.Client(SERVICE_URL, requests.Session())
print(client.entity_sets)

print(client.schema)

for es in client.schema.entity_sets:
    print(es.name)
    proprties = es.entity_type.proprties()
    for prop in proprties:
        print(f' + {prop.name}({prop.typ.name})')
