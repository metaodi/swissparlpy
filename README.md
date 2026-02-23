[![PyPI Version][pypi-image]][pypi-url]
[![Build Status][build-image]][build-url]
[![Code style: black][black-image]][black-url]
[![pre-commit][pre-commit-image]][pre-commit-url]


swissparlpy
===========

This module provides easy access to the data of the [OData webservice](https://ws.parlament.ch/odata.svc/) of the [Swiss parliament](https://www.parlament.ch/en) and the [OpenParlData.ch](https://openparldata.ch) REST API.

## Table of Contents

* [Installation](#installation)
* [Usage](#usage)
    * [Backend Selection](#backend-selection)
    * [Get tables and their variables](#get-tables-and-their-variables)
    * [Get data of a table](#get-data-of-a-table)
    * [Use together with `pandas`](#use-together-with-pandas)
    * [Visualize voting results](#visualize-voting-results)
    * [Substrings](#substrings)
    * [Date ranges](#date-ranges)
    * [Advanced filter](#advanced-filter)
    * [Large queries](#large-queries)
    * [API documentation](#documentation)
    * [Similar libraries for other languages](#similar-libraries-for-other-languages)
* [Credits](#credits)
* [Development](#development)
* [Release](#release)

## Installation

[swissparlpy is available on PyPI](https://pypi.org/project/swissparlpy/), so to install it simply use:

```
$ pip install swissparlpy
```

To install with visualization support (for plotting voting results):

```
$ pip install swissparlpy[visualization]
```

## Usage

See the [`examples` directory](/examples) for more scripts.

### Backend Selection

swissparlpy supports multiple data backends. By default, it uses the official OData API of parlament.ch, but you can also use the OpenParlData.ch REST API.

**Using the default OData (parlament.ch) backend:**

```python
>>> import swissparlpy as spp
>>> tables = spp.get_tables()  # Uses OData service of parlament.ch by default
```

**Using the OpenParlData backend:**

```python
>>> import swissparlpy as spp
>>> tables = spp.get_tables(backend='openparldata')
>>> data = spp.get_data('cantons', backend='openparldata')
```

**Using backends with SwissParlClient:**

```python
>>> from swissparlpy import SwissParlClient
>>>
>>> # OData backend
>>> odata_client = SwissParlClient(backend="odata")
>>> tables = odata_client.get_tables()
>>>
>>> # OpenParlData backend
>>> opd_client = SwissParlClient(backend="openparldata")
>>> tables = opd_client.get_tables()
```

All module-level functions (`get_tables()`, `get_variables()`, `get_overview()`, `get_glimpse()`, `get_data()`) support the `backend` parameter.

**Note:** The OpenParlData backend is still under development. The actual API endpoints and query parameters may need to be adjusted based on the final OpenParlData.ch API specification.

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

**Get data from a specific backend**



>>> import swissparlpy as spp
>>> data = spp.get_data('persons', firstname=)
>>> data
<swissparlpy.client.SwissParlResponse object at 0x7f8e38baa610>
>>> data.count
26
>>> data[0]
{'ID': 2, 'Language': 'DE', 'CantonNumber': 2, 'CantonName': 'Bern', 'CantonAbbreviation': 'BE'}
>>> [d['CantonName'] for d in data]
['Bern', 'Neuenburg', 'Genf', 'Wallis', 'Uri', 'Schaffhausen', 'Jura', 'Basel-Stadt', 'St. Gallen', 'Obwalden', 'Appenzell A.-Rh.', 'Solothurn', 'Waadt', 'Zug', 'Aargau', 'Basel-Landschaft', 'Luzern', 'Thurgau', 'Freiburg', 'Appenzell I.-Rh.', 'Schwyz', 'Graubünden', 'Glarus', 'Tessin', 'Zürich', 'Nidwalden']
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

Or the the convinence method `.to_dataframe()`:

```python
>>> import swissparlpy as spp
>>> parties_df = spp.get_data('Party', Language='DE').to_dataframe()
```


### Visualize voting results

The `plot_voting` function allows you to visualize voting results of the Swiss National Council according to the seating order.

**Warning**: The mapping from seats to persons is currently not historized, so "older" votes might not be displayed correctly. You can provide your own mapping with the `seats` parameter.

**Note**: This feature requires matplotlib and pandas. Install with: `pip install swissparlpy[visualization]`

```python
>>> import swissparlpy as spp
>>> import matplotlib.pyplot as plt
>>> 
>>> # Get voting data for a specific vote
>>> votes = spp.get_data("Voting", Language="DE", IdVote=23458)
>>> 
>>> # Create visualization with default scoreboard theme
>>> fig = spp.plot_voting(votes, theme='scoreboard', result=True)
>>> plt.show()
```

![Voting visualization example with scoreboard](https://github.com/user-attachments/assets/314c178c-e281-43b0-84ac-d5da501e218b)

The function supports different themes:
- `scoreboard`: Imitates the council hall scoreboard (neon colors on black background)
- `sym1`, `sym2`: Colored symbols on light background
- `poly1`, `poly2`, `poly3`: Color-filled polygons with different edge styles

You can also highlight specific parliamentary groups:

```python
>>> # Highlight a parliamentary group
>>> fig = spp.plot_voting(
...     votes_df, 
...     theme='poly1',
...     highlight={'ParlGroupCode': ["S"]},
...     result=True
... )
>>> plt.show()
```

![Voting visualization example with poly1 and a highlighted group](https://github.com/user-attachments/assets/a11ecf2b-a966-4e21-b5ec-e99e60f06c89)

See the [visualization example](/examples/visualize_voting.py) for more details.

### Substrings

If you want to query for substrings there are two main operators to use:

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

You can suffix any field with those operators to query the data.

### Date ranges (only available with the `odata` backend)

To query for date ranges you can use the operators...

* `__gt` (greater than)
* `__gte` (greater than or equal)
* `__lt` (less than)
* `__lte` (less than or equal)

...in combination with a `datetime` object.

```python
>>> import swissparlpy as spp
>>> from datetime import datetime
>>> business = spp.get_data(
...     "Business",
...     Language="DE",
...     SubmissionDate__gt=datetime.fromisoformat('2019-09-30'),
...     SubmissionDate__lte=datetime.fromisoformat('2019-10-31')
... )
>>> business.count
22
```

### Advanced filter (only supported by the `odata` backend)

**Text query**

It's possible to write text queries using operators like `eq` (equals), `ne` (not equals), `lt`/`lte` (less than/less than or equals), `gt` / `gte` (greater than/greater than or equals), `startswith()` and `contains`:

```python
import swissparlpy as spp
import pandas as pd
   
persons = spp.get_data(
   "Person",
   filter="(startswith(FirstName, 'Ste') or LastName eq 'Seiler') and Language eq 'DE'"
)

df = pd.DataFrame(persons)
print(df[['FirstName', 'LastName']])
```

**Callable Filter**

You can provide a callable as a filter which allows for more advanced filters.

`swissparlpy.Filter` provides `or_` and `and_`.

```python
import swissparlpy as spp
import pandas as pd

# filter by FirstName = 'Stefan' OR LastName == 'Seiler'
def filter_by_name(ent):
   return spp.Filter.or_(
      ent.FirstName == 'Stefan',
      ent.LastName == 'Seiler'
   )
   
df = spp.get_data("Person", filter=filter_by_name, Language='DE').to_dataframe()
print(df[['FirstName', 'LastName']])
```

### Search with the `OpenParlDataBackend`

The OpenParlDataBackend has the ability to filter and search, all the parameters described in the [API documentation](https://api.openparldata.ch/documentation#/) can be used here.

**Filter by values**
```python
>>> import swissparlpy as spp
>>> 
>>> opd_client = spp.SwissParlClient(backend="openparldata")
>>> response = opd_client.get_data("persons", firstname="Karin", lastname="Keller-Sutter")
>>> df = response.to_dataframe()
>>> print(df[['firstname', 'lastname', "title"]])
  firstname       lastname                         title
0     Karin  Keller-Sutter  Dipl. Konferenzdolmetscherin
```

**Search in the data**

```python
>>> import swissparlpy as spp
>>> 
>>> opd_client = spp.SwissParlClient(backend="openparldata")
>>> response = opd_client.get_data("speeches", search_mode="natural", search_scope="all", search_language="de", search="Budget")
>>> len(response)
457
>>> df = response.to_dataframe()
>>> df[["id", "body_key", "person_id", "meeting_id", "date_start", "date_end", "text_content_de"]]       
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

### Large queries

Large queries (especially the tables Voting and Transcripts) may result in server-side errors (500 Internal Server Error). In these cases it is recommended to download the data in smaller batches, save the individual blocks and combine them after the download.

This is an [example script](/examples/download_votes_in_batches.py) to download all votes of the legislative period 50, session by session, and combine them afterwards in one `DataFrame`:

```python
import swissparlpy as spp
import pandas as pd
import os

__location__ = os.path.realpath(os.getcwd())
path = os.path.join(__location__, "voting50")

# download votes of one session and save as pickled DataFrame
def save_votes_of_session(id, path):
    if not os.path.exists(path):
        os.mkdir(path)
    data = spp.get_data("Voting", Language="DE", IdSession=id)
    print(f"{data.count} rows loaded.")
    df = pd.DataFrame(data)
    pickle_path = os.path.join(path, f'{id}.pks')
    df.to_pickle(pickle_path)
    print(f"Saved pickle at {pickle_path}")


# get all session of the 50 legislative period
sessions50 = spp.get_data("Session", Language="DE", LegislativePeriodNumber=50)
sessions50.count

for session in sessions50:
    print(f"Loading session {session['ID']}")
    save_votes_of_session(session['ID'], path)

# Combine to one dataframe
df_voting50 = pd.concat([pd.read_pickle(os.path.join(path, x)) for x in os.listdir(path)])
```

### Documentation

The referencing table has been created and is available [here](docs/swissparAPY_diagram.pdf). It contains the dependency diagram between all of the tables as well, some exhaustive descriptions as well as the code needed to generate such interactive documentation.
The documentation can indeed be recreated using [dbdiagram.io](https://dbdiagram.io/home).

Below is a first look of what the dependencies are between the tables contained in the API:

![db diagram of swiss parliament API](/docs/swissparAPY_diagram.png "db diagram of swiss parliament API")

### Similar libraries for other languages

* R: [zumbov2/swissparl](https://github.com/zumbov2/swissparl)
* JavaScript: [michaelschoenbaechler/swissparl](https://github.com/michaelschoenbaechler/swissparl)

## Credits

This library is inspired by the R package [swissparl](https://github.com/zumbov2/swissparl) of [David Zumbach](https://github.com/zumbov2).
[Ralph Straumann](https://twitter.com/rastrau) initial [asked about a Python version of `swissparl` on Twitter](https://twitter.com/rastrau/status/1441048778740432902), which led to this project.

## Development

To develop on this project, install `uv`:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e ".[dev,test]"
```

Alternatively, use the provided setup script:

```
./dev_setup.sh
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
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black
[pre-commit-image]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
[pre-commit-url]: https://github.com/pre-commit/pre-commit
