---
title: Home
layout: home
nav_order: 1
---

# swissparlpy

[![PyPI Version](https://img.shields.io/pypi/v/swissparlpy)](https://pypi.org/project/swissparlpy/)
[![Build Status](https://github.com/metaodi/swissparlpy/actions/workflows/build.yml/badge.svg)](https://github.com/metaodi/swissparlpy/actions/workflows/build.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**swissparlpy** is a Python module that provides easy access to the data of the [OData webservice](https://ws.parlament.ch/odata.svc/) of the [Swiss Parliament](https://www.parlament.ch/en) and the [OpenParlData.ch](https://openparldata.ch) REST API.

---

## Quick Start

```bash
pip install swissparlpy
```

```python
import swissparlpy as spp

# List available tables
tables = spp.get_tables()
print(tables[:5])
# ['MemberParty', 'Party', 'Person', 'PersonAddress', 'PersonCommunication']

# Get data from a table
councillors = spp.get_data('MemberCouncil', Language='DE', limit=10)
for c in councillors:
    print(c['LastName'], c['FirstName'])
```

---

## Features

- **Multiple backends** – Use the official parlament.ch OData API or the OpenParlData.ch REST API
- **Simple API** – Intuitive functions to list tables, inspect variables, and query data
- **Filtering** – Filter data by any field, substring, date range, or advanced OData filter expressions
- **Pagination** – Automatically handles large result sets with server-side pagination
- **pandas integration** – Convert results directly to a `DataFrame` with `.to_dataframe()`
- **Visualization** – Plot voting results directly with the optional visualization support

–––

Vizualization of voting results as scoreboard:

![Voting visualization example with scoreboard](https://github.com/user-attachments/assets/314c178c-e281-43b0-84ac-d5da501e218b)

–--

## Credits

This library is inspired by the R package [swissparl](https://github.com/zumbov2/swissparl) by [David Zumbach](https://github.com/zumbov2).
The idea for a Python version was triggered by [Ralph Straumann](https://twitter.com/rastrau) [asking on Twitter](https://twitter.com/rastrau/status/1441048778740432902).

## Similar Libraries

| Language | Library |
|----------|---------|
| R | [zumbov2/swissparl](https://github.com/zumbov2/swissparl) |
| JavaScript | [michaelschoenbaechler/swissparl](https://github.com/michaelschoenbaechler/swissparl) |
