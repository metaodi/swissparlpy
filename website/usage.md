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

swissparlpy supports two data backends:

| Backend | Description |
|---------|-------------|
| `odata` (default) | Official OData API of [parlament.ch](https://ws.parlament.ch/odata.svc/) |
| `openparldata` | REST API of [OpenParlData.ch](https://openparldata.ch) |

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

**Using the `SwissParlClient` class:**

```python
from swissparlpy import SwissParlClient

# OData backend
odata_client = SwissParlClient(backend="odata")
print(odata_client.get_tables())

# OpenParlData backend
opd_client = SwissParlClient(backend="openparldata")
print(opd_client.get_tables())
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
"meeting_id", "date_start", "date_end", "text_content_de"]]       
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
