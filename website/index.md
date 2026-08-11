---
title: Python library for the Swiss Parliament API, OpenParlData.ch API & Gever Canton and City of Zurich
layout: home
nav_order: 1
---

# swissparlpy

[![PyPI Version](https://img.shields.io/pypi/v/swissparlpy?1)](https://pypi.org/project/swissparlpy/)
[![Build Status](https://github.com/metaodi/swissparlpy/actions/workflows/build.yml/badge.svg)](https://github.com/metaodi/swissparlpy/actions/workflows/build.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**swissparlpy** is a Python module that provides easy access to the data of the [OData webservice](https://ws.parlament.ch/odata.svc/) of the [Swiss Parliament](https://www.parlament.ch/en), the [OpenParlData.ch](https://openparldata.ch) REST API and the Gever (Geschäftsverwaltungssystem) APIs of the [canton](https://www.kantonsrat.zh.ch) and the [city](https://www.gemeinderat-zuerich.ch) of Zurich.

![swissparlpy]({{ "assets/images/swissparlpy_social.png" | relative_url }})

---

## Quick Start

{: .note }
Current release: **2.1.0** – requires Python 3.10 or higher. See the [changelog](https://github.com/metaodi/swissparlpy/blob/main/CHANGELOG.md) for all changes.

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
councillors = spp.get_data('MemberCouncil', Language='DE', CantonAbbreviation='ZH')
for c in councillors[:10]:
    print(f"{c['FirstName']} {c['LastName']}")
```

---

## Features

- **Multiple backends** – Use the official parlament.ch OData API, the OpenParlData.ch REST API or the Gever APIs of the canton and the city of Zurich
- **Simple API** – Intuitive functions to list tables, inspect variables, and query data
- **Filtering** – Filter data by any field, substring, date range, or advanced OData filter expressions
- **Pagination** – Automatically handles large result sets with server-side pagination
- **pandas integration** – Convert results directly to a `DataFrame` with `.to_dataframe()`
- **Visualization** – Plot voting results directly with the optional visualization support

---

Vizualization of voting results as scoreboard:

![Voting visualization example with scoreboard](https://github.com/user-attachments/assets/314c178c-e281-43b0-84ac-d5da501e218b)

---

## Credits

This library is inspired by the R package [swissparl](https://github.com/zumbov2/swissparl) by [David Zumbach](https://github.com/zumbov2).
The idea for a Python version was triggered by [Ralph Straumann](https://twitter.com/rastrau) [asking on Twitter](https://web.archive.org/web/20210923211621/https://twitter.com/rastrau/status/1441048778740432902).

## Similar Libraries

| Language | Library |
|----------|---------|
| R | [zumbov2/swissparl](https://github.com/zumbov2/swissparl) |
| JavaScript | [michaelschoenbaechler/swissparl](https://github.com/michaelschoenbaechler/swissparl) |
