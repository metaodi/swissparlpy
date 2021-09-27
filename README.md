swissparlpy
===========

Inspired by the R package [swissparl](https://github.com/zumbov2/swissparl), this module provides easy access to the data of the [OData webservice](https://ws.parlament.ch/odata.svc/) of the [Swiss parliament](https://www.parlament.ch/en).

## Table of Contents

* [Installation](#installation)
* [Usage](#usage)
    * [ Get tables and their variables](##get-tables-and-their-variables)
    * [Get data of a table](#get-data-of-a-table)
* [Release](#release)

## Installation

[swissparlpy is available on PyPI](https://pypi.org/project/swissparlpy/), so to install it simply use:

```
$ pip install swissparlpy
```

## Usage

See the [`examples` directory](/examples) for more scripts.

### Get tables and their variables

```python
>>> import swissparlpy as spp
>>> spp.get_tables()[:5] # get first 5 tables
['MemberParty', 'Party', 'Person', 'PersonAddress', 'PersonCommunication']
>>> spp.get_variables('Party') # get variables of table `Party`
['ID', 'Language', 'PartyNumber', 'PartyName', 'StartDate', 'EndDate', 'Modified', 'PartyAbbreviation']
```

### Get data of a table

```python
>>> import swissparlpy as spp
>>> data = spp.get_data('Canton', Language='DE')
>>> data
<swissparlpy.client.SwissParlResponse object at 0x7f8e38baa610>
>>> data.count
26
>>> data[0]
{'ID': 2, 'Language': 'DE', 'CantonNumber': 2, 'CantonName': 'Bern', 'CantonAbbreviation': 'BE'}
>>> [d['CantonName'] for d in data]
['Bern', 'Neuenburg', 'Genf', 'Wallis', 'Uri', 'Schaffhausen', 'Jura', 'Basel-Stadt', 'St. Gallen', 'Obwalden', 'Appenzell A.-Rh.', 'Solothurn', 'Waadt', 'Zug', 'Aargau', 'Basel-Landschaft', 'Luzern', 'Thurgau', 'Freiburg', 'Appenzell I.-Rh.', 'Schwyz', 'Graubünden', 'Glarus', 'Tessin', 'Zürich', 'Nidwalden']
```

## Release

To create a new release, follow these steps (please respect [Semantic Versioning](http://semver.org/)):

1. Adapt the version number in `swissparlpy/__init__.py`
1. Update the CHANGELOG with the version
1. Create a [pull request to merge `develop` into `main`](https://github.com/metaodi/swissparlpy/compare/main...develop?expand=1) (make sure the tests pass!)
1. Create a [new release/tag on GitHub](https://github.com/metaodi/swissparlpy/releases) (on the main branch)
1. The [publication on PyPI](https://pypi.python.org/pypi/swissparlpy) happens via [GitHub Actions](https://github.com/metaodi/swissparlpy/actions?query=workflow%3A%22Upload+Python+Package%22) on every tagged commit
