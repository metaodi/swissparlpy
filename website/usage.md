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
```

**Using the OpenParlData backend:**

```python
import swissparlpy as spp

tables = spp.get_tables(backend='openparldata')
data = spp.get_data('cantons', backend='openparldata')
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
councillors = spp.get_data('MemberCouncil', Language='DE', CantonAbbreviation='ZH', limit=10)
for c in councillors:
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
# (17, 8)
print(df.dtypes)
```

---

## Large Queries

For large result sets, use the `limit` and `offset` parameters or iterate over pages manually using `get_data` with batched calls. swissparlpy handles server-side pagination transparently:

```python
import swissparlpy as spp

# Download all votes in a session (can be large)
votes = spp.get_data('Vote', Language='DE', IdSession='5101')
print(len(votes))
```

{: .note }
Very large queries will emit a `ResultVeryLargeWarning`. Consider using `limit` to cap results during development.

---

## OData Backend: Substrings

Use `spp.Filter` (a callable) to filter by substring:

```python
import swissparlpy as spp

# Find all councillors whose last name contains 'Müller'
data = spp.get_data(
    'MemberCouncil',
    Language='DE',
    LastName=spp.Filter('substringof', 'Müller')
)
for d in data:
    print(d['LastName'], d['FirstName'])
```

---

## OData Backend: Date Ranges

```python
import swissparlpy as spp
from datetime import datetime

start = datetime(2020, 1, 1)
end = datetime(2020, 12, 31)

data = spp.get_data(
    'Session',
    Language='DE',
    StartDate=spp.Filter('between', start, end)
)
for d in data:
    print(d['SessionName'], d['StartDate'])
```

---

## OData Backend: Advanced Filter

For complex filter expressions, use the `filter` keyword with a raw OData filter string:

```python
import swissparlpy as spp

# Use a raw OData filter expression
data = spp.get_data(
    'Vote',
    Language='DE',
    filter="IdSession eq '5101' and PersonNumber eq 902"
)
print(len(data))
```

---

## Visualize Voting Results

{: .note }
Requires installation with `pip install swissparlpy[visualization]`.

```python
import swissparlpy as spp

votes = spp.get_data('Vote', Language='DE', IdVotingNumber=24189)
spp.plot_voting(votes)
```

This produces a seat map of the Swiss National Council coloured by vote (yes / no / abstain).

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

---

## API Reference

All public module-level functions:

| Function | Description |
|----------|-------------|
| `spp.get_tables(backend='odata')` | Return a list of available table names |
| `spp.get_variables(table, backend='odata')` | Return the variable names for a table |
| `spp.get_overview(table, backend='odata')` | Print an overview of a table |
| `spp.get_glimpse(table, backend='odata')` | Print a glimpse (first few rows) of a table |
| `spp.get_data(table, backend='odata', **kwargs)` | Fetch data from a table with optional filters |
| `spp.plot_voting(votes)` | Plot a National Council seat map for a vote |
