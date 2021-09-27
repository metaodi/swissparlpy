[![PyPI Version][pypi-image]][pypi-url]
[![Build Status][build-image]][build-url]


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

The return value of `get_data` is iterable, so you can easily loop over it. Or you can use indices to access elements, e.g. `data[1]` to get the second element, or `data[-1]` to get the last one.

Even [slicing](https://python-reference.readthedocs.io/en/latest/docs/brackets/slicing.html) is supported, so you can do things like only iterate over the first 5 elements using

```python
for rec in data[:5]:
   print(rec)
```

### Use together with `pandas`

To create a pandas DataFrame from `get_data` simply pass the return value to the constructor:

```python
>>> import swissparlpy as spp
>>> import pandas as pd
>>> parties = spp.get_data('Party', Language='DE')
>>> parties_df = pd.DataFrame(parties)
>>> parties_df
      ID Language  PartyNumber  ...                   EndDate                         Modified PartyAbbreviation
0     12       DE           12  ... 2000-01-01 00:00:00+00:00 2010-12-26 13:05:26.430000+00:00                SP
1     13       DE           13  ... 2000-01-01 00:00:00+00:00 2010-12-26 13:05:26.430000+00:00               SVP
2     14       DE           14  ... 2000-01-01 00:00:00+00:00 2010-12-26 13:05:26.430000+00:00               CVP
3     15       DE           15  ... 2000-01-01 00:00:00+00:00 2010-12-26 13:05:26.430000+00:00      FDP-Liberale
4     16       DE           16  ... 2000-01-01 00:00:00+00:00 2010-12-26 13:05:26.430000+00:00               LDP
..   ...      ...          ...  ...                       ...                              ...               ...
78  1582       DE         1582  ... 2000-01-01 00:00:00+00:00 2015-12-03 08:48:38.250000+00:00             BastA
79  1583       DE         1583  ... 2000-01-01 00:00:00+00:00 2019-03-07 17:24:15.013000+00:00              CVPO
80  1584       DE         1584  ... 2000-01-01 00:00:00+00:00 2019-11-08 17:28:43.947000+00:00                Al
81  1585       DE         1585  ... 2000-01-01 00:00:00+00:00 2019-11-08 17:41:39.513000+00:00               EàG
82  1586       DE         1586  ... 2000-01-01 00:00:00+00:00 2021-08-12 07:59:22.627000+00:00               M-E

[83 rows x 8 columns]
```

### Substrings

**`__startswith`**:

```python
>>> import swissparlpy as spp
>>> persons = spp.get_data("Person", Language="DE", LastName__startswith='Bal')
>>> persons.count
12
```

**`__contains`**
```python
>>> import swissparlpy as spp
>>> co2_business = spp.get_data("Business", Title__contains="CO2", Language = "DE")
>>> co2_business.count
265
```

### Large queries

```python
import swissparlpy as spp
import os

path = os.path.join(__location__, "voting50")

def save_votes_of_session(id):
    if not os.path.exists(path):
        os.mkdir(path)
    data = client.get_data("Voting", Language="DE", IdSession=id)
    print(f"{data.count} rows loaded.")
    df = pd.DataFrame(data)
    pickle_path = os.path.join(path, f'{id}.pks')
    df.to_pickle(pickle_path)
    print(f"Saved pickle at {pickle_path}")


# get all session of the 50 legislative period
sessions50 = client.get_data("Session", Language="DE", LegislativePeriodNumber=50)
sessions50.count

for session in sessions50:
    print(f"Loading session {session['ID']}")
    save_votes_of_session(session['ID'])

# Combine to one dataframe
path = os.path.join(__location__, "voting50")
df_voting50 = pd.concat([pd.read_pickle(os.path.join(path, x)) for x in os.listdir(path)])
```

## Release

To create a new release, follow these steps (please respect [Semantic Versioning](http://semver.org/)):

1. Adapt the version number in `swissparlpy/__init__.py`
1. Update the CHANGELOG with the version
1. Create a [pull request to merge `develop` into `main`](https://github.com/metaodi/swissparlpy/compare/main...develop?expand=1) (make sure the tests pass!)
1. Create a [new release/tag on GitHub](https://github.com/metaodi/swissparlpy/releases) (on the main branch)
1. The [publication on PyPI](https://pypi.python.org/pypi/swissparlpy) happens via [GitHub Actions](https://github.com/metaodi/swissparlpy/actions?query=workflow%3A%22Upload+Python+Package%22) on every tagged commit


<!-- Badges -->
[pypi-image]: https://img.shields.io/pypi/v/swissparlpy
[pypi-url]: https://pypi.org/project/swissparlpy/
[build-image]: https://github.com/metaodi/swissparlpy/actions/workflows/build.yml/badge.svg
[build-url]: https://github.com/metaodi/swissparlpy/actions/workflows/build.yml
