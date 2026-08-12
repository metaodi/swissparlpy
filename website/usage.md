---
title: Usage
layout: default
nav_order: 3
---

# Usage
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Backend Selection

swissparlpy supports multiple data backends:

| Backend | Description |
|---------|-------------|
| `odata` (default) | Official OData API of [parlament.ch](https://ws.parlament.ch/odata.svc/) |
| `openparldata` | REST API of [OpenParlData.ch](https://openparldata.ch) |
| `gever` / `gever_canton_zurich` | Gever (Geschäftsverwaltungssystem) API of the Kantonsrat of the canton of Zurich |
| `gever_city_zurich` | Gever API of the Gemeinderat of the city of Zurich |

**Using the default OData backend:**

```python
import swissparlpy as spp

tables = spp.get_tables()  # uses OData backend by default
print(tables)
```

<details markdown="1">
<summary>Output</summary>
```
['MemberParty', 'Party', 'Person', 'PersonAddress', 'PersonCommunication', 'PersonInterest', 'Session', 'Committee', 'MemberCommittee', 'Canton', 'Council', 'Objective', 'Resolution', 'Publication', 'External', 'Meeting', 'Subject', 'Citizenship', 'Preconsultation', 'Bill', 'BillLink', 'BillStatus', 'Business', 'BusinessResponsibility', 'BusinessRole', 'LegislativePeriod', 'MemberCouncil', 'MemberParlGroup', 'ParlGroup', 'PersonOccupation', 'RelatedBusiness', 'BusinessStatus', 'BusinessType', 'MemberCouncilHistory', 'MemberCommitteeHistory', 'Vote', 'Voting', 'SubjectBusiness', 'Transcript', 'ParlGroupHistory', 'Tags', 'SeatOrganisationNr', 'PersonEmployee', 'Rapporteur', 'Mutation', 'SeatOrganisationSr', 'MemberParlGroupHistory', 'MemberPartyHistory']
```
</details>

**Using the OpenParlData backend:**

```python
import swissparlpy as spp

tables = spp.get_tables(backend='openparldata')
print(tables)
```

<details markdown="1">
<summary>Output</summary>
```
['bodies', 'speeches', 'persons', 'groups', 'meetings', 'agendas', 'texts', 'votes', 'docs', 'affairs', 'votings', 'interests', 'events', 'external_links', 'contributors', 'person_images', 'memberships', 'access_badges']
```
</details>

**Using the Gever backend:**

The Gever backend has two instances: `gever_canton_zurich` for the Kantonsrat of the canton of Zurich (`gever` is an alias for it) and `gever_city_zurich` for the Gemeinderat of the city of Zurich.

```python
import swissparlpy as spp

tables = spp.get_tables(backend='gever_city_zurich')
data = spp.get_data('geschaeft', backend='gever_city_zurich')
data = spp.get_data('wahlkreise', backend='gever')  # canton of Zurich
```

**Using the `SwissParlClient` class:**

```python
from swissparlpy import SwissParlClient

# OData backend
odata_client = SwissParlClient(backend="odata")
print(odata_client.get_tables())

# OpenParlData backend
opd_client = SwissParlClient(backend="openparldata")
print(opd_client.get_tables())

# Gever backend (canton of Zurich)
gever_client = SwissParlClient(backend="gever_canton_zurich")
print(gever_client.get_tables())
```

All module-level functions (`get_tables()`, `get_variables()`, `get_overview()`, `get_glimpse()`, `get_data()`) accept a `backend` parameter.

---

## Get Tables and Variables

```python
import swissparlpy as spp

# List the first 5 available tables
spp.get_tables()[:5]
# ['MemberParty', 'Party', 'Person', 'PersonAddress', 'PersonCommunication']

# Get the variables (columns) of a table
spp.get_variables('Party')
# ['ID', 'Language', 'PartyNumber', 'PartyName', 'StartDate', 'EndDate', 'Modified', 'PartyAbbreviation']
```

---

## Get Data of a Table

```python
import swissparlpy as spp

# Fetch councillors with a filter
councillors = spp.get_data('MemberCouncil', Language='DE', CantonAbbreviation='ZH')
print(councillors.count)
for c in councillors:
    print(c['LastName'], c['FirstName'])
```

Every keyword argument of `get_data()` is used as a filter on the corresponding variable of the table.

The result is iterable, indexable (`data[0]`, `data[-1]`) and supports [slicing](https://python-reference.readthedocs.io/en/latest/docs/brackets/slicing.html), so you can also work with a subset of the records only:

```python
for c in councillors[:5]:
    print(c['LastName'], c['FirstName'])
```

---

## Use Together with pandas

Convert any result to a pandas `DataFrame` using `.to_dataframe()`:

```python
import swissparlpy as spp

data = spp.get_data('MemberCouncil', Language='DE', limit=10)
df = data.to_dataframe()
print(df[['LastName', 'FirstName', 'CantonName']])
```

Or use the classic `pandas` constructor:

```python
import swissparlpy as spp
import pandas as pd

data = spp.get_data('Party', Language='DE')
df = pd.DataFrame(data)
print(df.shape)
print(df.dtypes)
```

---

## Large Queries

swissparlpy handles server-side pagination transparently: records are only fetched from the API when you actually access them, so slicing a large result set only downloads the records you need.

```python
import swissparlpy as spp

# Only the count is requested, no records are loaded yet
votes = spp.get_data('Voting', Language='DE', IdSession=5101)
print(votes.count)

# Load the first 100 records only
for vote in votes[:100]:
    print(vote['LastName'], vote['DecisionText'])
```

{: .note }
Very large queries emit a `ResultVeryLargeWarning`. During development, slice the result (e.g. `votes[:100]`) instead of iterating over all records.

Very large tables (especially `Voting` and `Transcript`) may still result in server-side errors (500 Internal Server Error). In that case download the data in smaller batches, store the individual blocks and combine them afterwards – see [`download_votes_in_batches.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/download_votes_in_batches.py):

```python
import swissparlpy as spp
import pandas as pd

# Download the votes of the 50th legislative period session by session
sessions50 = spp.get_data("Session", Language="DE", LegislativePeriodNumber=50)
frames = []
for session in sessions50:
    data = spp.get_data("Voting", Language="DE", IdSession=session['ID'])
    frames.append(data.to_dataframe())

df_voting50 = pd.concat(frames)
```

---

## OData Backend: Substrings

To query for substrings, suffix the variable name with one of the following operators:

| Suffix | Description |
|--------|-------------|
| `__startswith` | The value starts with the given string |
| `__contains` | The value contains the given string |

```python
import swissparlpy as spp

# Find all persons whose last name starts with 'Bal'
persons = spp.get_data("Person", Language="DE", LastName__startswith='Bal')
print(persons.count)
# 12

# Find all business items with 'CO2' in the title
co2_business = spp.get_data("Business", Title__contains="CO2", Language="DE")
print(co2_business.count)
# 265
```

---

## OData Backend: Date Ranges

To query for date ranges, suffix the variable name with a comparison operator and pass a `datetime` object:

| Suffix | Description |
|--------|-------------|
| `__gt` | greater than |
| `__gte` | greater than or equal |
| `__lt` | less than |
| `__lte` | less than or equal |

```python
import swissparlpy as spp
from datetime import datetime

business = spp.get_data(
    "Business",
    Language="DE",
    SubmissionDate__gt=datetime.fromisoformat('2019-09-30'),
    SubmissionDate__lte=datetime.fromisoformat('2019-10-31')
)
print(business.count)
# 22
```

---

## OData Backend: Advanced Filter

**Text query**

For complex filter expressions, use the `filter` keyword with a raw OData filter string. Operators like `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `startswith()` and `contains` are supported:

```python
import swissparlpy as spp

persons = spp.get_data(
    "Person",
    filter="(startswith(FirstName, 'Ste') or LastName eq 'Seiler') and Language eq 'DE'"
)
df = persons.to_dataframe()
print(df[['FirstName', 'LastName']])
```

**Escaping values**

A raw filter string is sent to the API as-is. A value containing an apostrophe ends its string literal early, which the service rejects with an HTTP 400, so such values have to be escaped with `escape_odata_string()`:

```python
import swissparlpy as spp

keyword = spp.escape_odata_string("délit d'initié")  # délit d''initié
business = spp.get_data(
    "Business",
    Language="FR",
    filter=f"substringof('{keyword}',Title)"
)
print(business.count)
```

{: .note }
Keyword arguments and `spp.Filter` are pyodata's job, it builds those literals itself, so don't escape those values yourself. That escaping was fixed upstream in [SAP/python-pyodata#313](https://github.com/SAP/python-pyodata/pull/313), which is not part of a pyodata release yet (as of 1.12.0), so until that release lands and the dependency is bumped, those paths can still fail on a value containing an apostrophe.

**Callable filter**

The `filter` keyword also accepts a callable, which allows for more advanced filters. `spp.Filter` provides the `or_` and `and_` helpers:

```python
import swissparlpy as spp

# filter by FirstName == 'Stefan' OR LastName == 'Seiler'
def filter_by_name(ent):
    return spp.Filter.or_(
        ent.FirstName == 'Stefan',
        ent.LastName == 'Seiler'
    )

df = spp.get_data("Person", filter=filter_by_name, Language='DE').to_dataframe()
print(df[['FirstName', 'LastName']])
```

---

## Visualize Voting Results

{: .note }
Requires installation with `pip install swissparlpy[visualization]`.

The `plot_voting()` function visualizes the voting results of the Swiss National Council according to the seating order. It expects the data of the `Voting` table of the OData backend.

```python
import swissparlpy as spp
import matplotlib.pyplot as plt

# Get the voting data of one specific vote
votes = spp.get_data("Voting", Language="DE", IdVote=23458)

# Create the visualization with the default scoreboard theme
fig = spp.plot_voting(votes, theme='scoreboard', result=True)
plt.show()
```

![Voting visualization example with scoreboard](https://github.com/user-attachments/assets/314c178c-e281-43b0-84ac-d5da501e218b)

The following themes are available:

| Theme | Description |
|-------|-------------|
| `scoreboard` (default) | Imitates the council hall scoreboard (neon colors on black background) |
| `sym1`, `sym2` | Colored symbols on light background |
| `poly1`, `poly2`, `poly3` | Color-filled polygons with different edge styles |

Parliamentary groups can be highlighted with the `highlight` parameter:

```python
fig = spp.plot_voting(
    votes,
    theme='poly1',
    highlight={'ParlGroupCode': ["S"]},
    result=True
)
plt.show()
```

![Voting visualization example with poly1 and a highlighted group](https://github.com/user-attachments/assets/a11ecf2b-a966-4e21-b5ec-e99e60f06c89)

{: .warning }
The mapping from seats to persons is currently not historized, so "older" votes might not be displayed correctly. You can provide your own mapping with the `seats` parameter.

---

## OpenParlData Backend

### Search with the OpenParlData Backend

Besides the variables of a table, every query parameter of the [OpenParlData API](https://api.openparldata.ch/documentation#/) (e.g. `limit`, `offset`, `sort_by`, `fields`, `search`, `lang`) can be passed as a keyword argument. swissparlpy only sets `lang_format="flat"` itself, all other parameters use the documented API defaults.

```python
import swissparlpy as spp

opd_client = spp.SwissParlClient(backend="openparldata")

# Simple filter by field value
response = opd_client.get_data("persons", firstname="Karin", lastname="Keller-Sutter")
df = response.to_dataframe()
print(df[['firstname', 'lastname', 'title']])
```

<details markdown="1">
<summary>Output</summary>
```
  firstname       lastname                         title
0     Karin  Keller-Sutter  Dipl. Konferenzdolmetscherin
```
</details>

**Full-text search:**

{: .note }
`search` only looks at the metadata by default (`search_scope="metadata"`). Pass `search_scope="all"` explicitly to search the full-text indexes, e.g. the text of a speech.

```python
import swissparlpy as spp

opd_client = spp.SwissParlClient(backend="openparldata")
response = opd_client.get_data(
    "speeches",
    search_mode="natural",
    search_scope="all",
    search_language="de",
    search="Budget"
)
print(len(response))
df = response.to_dataframe()
print(df[["id", "person_id", "date_start", "text_content_de"]].head())
```

<details markdown="1">
<summary>Output</summary>
```
          id body_key  person_id  meeting_id           date_start date_end                                    text_content_de
0    1100333      351     4256.0        1262  2024-11-14T18:18:52     None  <p><b>Corina Liebi (JGLP)</b> für die PVS: Für...
1    1100301      351     4191.0        1578  2024-05-30T22:24:34     None  <p><b>Ursina Anderegg (GB)</b> für die Fraktio...
2    1100187      351     4139.0        1219  2025-11-20T18:02:10     None  <p><b>Debora Alder-Gasser (EVP)</b> für die Ko...
3    1100167      351     4315.0        1219  2025-11-20T17:11:50     None  <p><b>Simone Richner (FDP)</b> für die Kommiss...
4    1100016      351     4237.0        1628  2024-06-27T13:44:06     None  <p><b>Franziska Geiser (GB)</b> für die FIKO: ...
..       ...      ...        ...         ...                  ...      ...                                                ...
452  1088291      351     4237.0        1193  2025-03-27T21:51:35     None  <p><b>Franziska Geiser (GB)</b> für die Frakti...
453  1088272      351     4162.0        1404  2025-03-20T17:36:23     None  <p><b>Janina Aeberhard (GLP)</b> für die Kommi...
454  1088255      351     4123.0        1870  2023-09-21T15:50:27     None  <p><b>Barbara Keller (SP)</b> für die SBK: Ich...
455  1088206      351     4114.0        1404  2025-03-20T17:50:35     None  <p><b>Laura Curau (Mitte)</b> für die Fraktion...
456  1088186      351     4237.0        1404  2025-03-20T18:39:10     None  <p><b>Franziska Geiser (GB)</b> für die Frakti...

[457 rows x 7 columns]
```
</details>

### `limit` is a Page Size, Not a Cap

`limit` is passed straight to the API, where it controls the size of a single page (500 by default). The response follows the `next_page` links transparently, so iterating a result still yields *all* matching records, no matter which `limit` you set:

```python
import swissparlpy as spp

opd_client = spp.SwissParlClient(backend="openparldata")
response = opd_client.get_data("persons", limit=10)
print(len(response))        # total number of records, taken from the first page
# 26574
print(len(list(response)))  # iterating loads every page
# 26574
```

To only get a few records, use `get_glimpse()` or slice the response (`response[:10]`).

{: .note }
`len(response)` is the total record count reported by the API and is available after a single request, which makes it a cheap way to count records.

### Case Sensitivity of `search_mode="exact"`

{: .warning }
While the API documents `search_mode="exact"` as a case-insensitive exact match, it behaves case-sensitively in practice: `search="Nationalrat"` returns results, while `search="nationalrat"` does not.

### Get Related Data

The OpenParlData API returns related entities alongside main records. You can navigate these relationships easily:

```python
import swissparlpy as spp

opd_client = spp.SwissParlClient(backend="openparldata")
geru = opd_client.get_data("persons", firstname="Gerhard", lastname="Andrey")[0]

# List available related tables
print(geru.get_related_tables())
# ['memberships', 'interests', 'access_badges', ...]

# Load a related table as a DataFrame
member_df = geru.get_related_data('memberships').to_dataframe()
print(member_df[["group_name_de", "role_name_de", "type_harmonized"]].head())
```

<details markdown="1">
<summary>Output</summary>
```

                            external_id               group_name_de      role_name_de   type_harmonized
0              CHE_interest_kultur_4245                      Kultur          Mitglied    interest_group
1  936edfe6-f8fd-4667-a986-ab5200acafb9  Gruppe Parlaments-IT (PIT)          Mitglied  committee_ad_hoc
2  6f42fed7-0dc6-4ed7-b655-b391ad828068  Gruppe Parlaments-IT (PIT)          Mitglied  committee_ad_hoc
3  63898798-ac17-469f-bb21-5e562d76b1de  Gruppe Parlaments-IT (PIT)  Vizepräsident/in  committee_ad_hoc
4  28d9ed41-e55c-4c55-a1f3-ab1300c25d52                     Büro NR  Stimmenzähler/in         committee
```
</details>

---

## Gever Backend

The `GeverBackend` queries the Gever (Geschäftsverwaltungssystem) APIs of the canton and the city of Zurich. It is based on [goifer](https://github.com/metaodi/goifer), a standalone client for the same APIs.

### Instances and Tables

There are two instances, each with its own set of tables (called *indexes* in the API):

```python
import swissparlpy as spp

spp.get_tables(backend='gever')  # canton of Zurich
spp.get_tables(backend='gever_city_zurich')  # city of Zurich
```

Table names are lowercase, but the lookup is case-insensitive, so both of these work:

```python
data = spp.get_data('geschaeft', backend='gever_city_zurich')
data = spp.get_data('Geschaeft', backend='gever_city_zurich')
```

`get_variables()` returns the fields of a table, based on the XSD schema of the API:

```python
spp.get_variables('wahlkreise', backend='gever')
# ['name', 'inaktiv', 'obj_guid', 'seq', 'idx']
```

### Queries

The Gever API uses its own query syntax (CQL). Pass a query as `filter` to use it as-is:

```python
import swissparlpy as spp

data = spp.get_data('wahlkreise', 'inaktiv = false', backend='gever')
print(data[0])
# {'obj_guid': 'dee39e1ccd4c40db82729b3d0762a302', 'seq': '2242344', 'idx': 'Wahlkreise', 'name': 'I      Zürich 1+2', 'inaktiv': False}
```

Keyword arguments are turned into a query, strings are matched with `adj`, numbers and booleans with `=`. String values are quoted and escaped automatically, so values with spaces work as well:

```python
# searches for 'name adj "Marti" and vorname adj "Res"'
data = spp.get_data('mitglieder', name='Marti', vorname='Res', backend='gever')

# searches for 'vorname adj "Hans Peter"'
data = spp.get_data('mitglieder', vorname='Hans Peter', backend='gever')
```

{: .note }
Without a filter, all records are queried (`seq > 0`). Callable filters (`spp.Filter`) are not supported by this backend.

The number of records per request (default 500), the language and the first record can be set on the backend or per query:

```python
import swissparlpy as spp
from swissparlpy import GeverBackend

client = spp.SwissParlClient(backend=GeverBackend(instance='city_zurich', maximum_records=100))
data = client.get_data('geschaeft', maximum_records=10, start_record=20, lang='de-CH')
```

Just like the other backends, the result is iterable, indexable and sliceable, and further pages are loaded lazily. `len(response)` is the total number of hits reported by the API, so iterating over a large table pages through all of it: use `get_glimpse()` (which never loads more than the rows it was asked for) or slice the response to get only a few records.

### Nested and List Fields

Elements the schema of a table declares as repeatable (`maxOccurs` of `unbounded` or greater than 1, whether it is on the element itself or on a wrapping `sequence`/`choice`/`all`) are always returned as a list, even if a record contains only a single one of them. This keeps the records of a table consistent, which matters when converting them to a `DataFrame`:

```python
import swissparlpy as spp

data = spp.get_data('mitglieder', backend='gever')
df = data.to_dataframe()
```

As long as a table has a usable schema, every other nested element is flattened into the record, however deep, e.g. a `mitglieder` record's `Person` -> `Kontakt` wrapper becomes top-level `person_kontakt_*` fields rather than a nested dict.

A list field like `behoerdenmandate` stays as a list-of-dicts column when converted with `to_dataframe()`, which is often not what you want for further analysis. Use `explode()` to turn it into its own `DataFrame` instead, one row per item, with the parent record's `obj_guid` carried along as `parent_obj_guid` so it can be joined back:

```python
import swissparlpy as spp

data = spp.get_data('mitglieder', backend='gever')
mandates = data.explode('behoerdenmandate')
print(mandates.columns.tolist())
# ['parent_obj_guid', 'obj_guid', 'dauer_start', 'dauer_end', 'dauer', 'gremiumtyp', 'name', 'kurzname', 'funktion']
```

The name of the list field is enough, even if it is nested (the mandates above are in `person_kontakt_behoerdenmandate`); the full column name works as well. Pass `parent_columns` to also carry other parent fields along (prefixed with `parent_`), to avoid a separate join for common cases:

```python
mandates = data.explode('behoerdenmandate', parent_columns=['person_kontakt_vorname', 'person_kontakt_name'])
```

### Download Documents

Some tables return documents (`edokument`), for those a download URL and a filename are added automatically:

```python
import swissparlpy as spp

meetings = spp.get_data('sitzungendetail', backend='gever')
doc = meetings[0]['sitzungsdokumente'][0]
print(doc['edokument_download_url'])
# 'https://parlzhcdws.cmicloud.ch/parlzh3/cdws/Files/9db1203429e04a39a233e56eab42feea-332/1/PDF'
print(doc['edokument_filename'])
# '63. KR-Protokoll vom 9.7.2012, Nachmittag.pdf'
```

To build a download URL yourself, use the `file()` method of the backend:

```python
from swissparlpy import GeverBackend

backend = GeverBackend(instance='canton_zurich')
member = backend.get_data('mitglieder', 'Name adj Marti and Vorname adj Res')[0]
print(backend.file('mitglieder', member['foto_id'], member['foto_version']['nr'], 'Original'))
```

### Custom Instances

To query another host (e.g. an integration environment), pass a `url` to override the base URL of the instance:

```python
from swissparlpy import GeverBackend

backend = GeverBackend(instance='city_zurich', url='https://www.integ.gemeinderat-zuerich.ch')
```

Other Gever instances can be used by passing a `config`, either as dict or as path to a YAML file (this requires `pyyaml`). See [`gever_config.py`](https://github.com/metaodi/swissparlpy/blob/main/swissparlpy/backends/gever_config.py) for the structure:

```python
from swissparlpy import GeverBackend

config = {
    'my_instance': {
        'api_base': 'https://example.org',
        'files_api': {'path': '/api/files'},
        'indexes': {'geschaeft': {'path': '/api/geschaeft'}},
    }
}
backend = GeverBackend(instance='my_instance', config=config)
```

See [`gever_backend.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/gever_backend.py) for a full walkthrough of the Gever backend.

---

## API Reference

All public module-level functions:

| Function | Description |
|----------|-------------|
| `spp.get_tables(backend='odata')` | Return a list of available table names |
| `spp.get_variables(table, backend='odata')` | Return the variable names of a table |
| `spp.get_overview(backend='odata')` | Return a dict of all tables and their variables |
| `spp.get_glimpse(table, rows=5, backend='odata')` | Return the first `rows` records of a table |
| `spp.get_data(table, filter=None, backend='odata', **kwargs)` | Fetch data from a table with optional filters |
| `spp.plot_voting(votes, ...)` | Plot a National Council seat map for a vote (OData `Voting` data) |

The same methods are available on a `spp.SwissParlClient` instance (without the `backend` parameter, which is passed to the constructor instead).

`spp.GeverBackend(instance, maximum_records=500, url=None, config=None)` builds a Gever backend instance directly, e.g. to use non-default settings, a custom instance, or the `file()` method to build document download URLs.
