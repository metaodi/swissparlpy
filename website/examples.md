---
title: Examples
layout: default
nav_order: 4
---

# Examples
{: .no_toc }

The [`examples/`](https://github.com/metaodi/swissparlpy/tree/main/examples) directory in the repository contains a number of ready-to-run scripts and notebooks.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scripts

| File | Description |
|------|-------------|
| [`filter.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/filter.py) | Basic filtering by field value |
| [`filter_advanced.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/filter_advanced.py) | Advanced OData filter expressions |
| [`filter_query.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/filter_query.py) | Filter with raw OData `$filter` query strings |
| [`glimpse.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/glimpse.py) | Use `get_glimpse()` to preview a table |
| [`list_all_tables_and_properties.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/list_all_tables_and_properties.py) | List all tables and their variables |
| [`pagination.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/pagination.py) | Handling large result sets with pagination |
| [`slice.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/slice.py) | Slicing results with `limit` and `offset` |
| [`download_votes_in_batches.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/download_votes_in_batches.py) | Download all votes in batches |
| [`visualize_voting.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/visualize_voting.py) | Plot a National Council seat map |
| [`compare_backends.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/compare_backends.py) | Compare the OData and OpenParlData backends |
| [`openparldata_backend.py`](https://github.com/metaodi/swissparlpy/blob/main/examples/openparldata_backend.py) | Using the OpenParlData backend |

---

## Jupyter Notebooks

| Notebook | Description |
|----------|-------------|
| [Swiss Parliament API.ipynb](https://github.com/metaodi/swissparlpy/blob/main/examples/Swiss%20Parliament%20API.ipynb) | Comprehensive walkthrough of the OData API |
| [OpenParlData_vs_OData_Backend.ipynb](https://github.com/metaodi/swissparlpy/blob/main/examples/OpenParlData_vs_OData_Backend.ipynb) | Side-by-side comparison of both backends |

---

## Quick Example: List Councillors

```python
import swissparlpy as spp

councillors = spp.get_data('MemberCouncil', Language='DE', CantonAbbreviation='ZH')
for c in councillors:
    print(f"{c['FirstName']} {c['LastName']}")
```

## Quick Example: Search Speeches

```python
import swissparlpy as spp

opd_client = spp.SwissParlClient(backend="openparldata")
response = opd_client.get_data(
    "speeches",
    search_mode="natural",
    search_scope="all",
    search_language="de",
    search="Klimawandel"
)
df = response.to_dataframe()
print(df[["id", "date_start", "text_content_de"]].head())
```

## Quick Example: Plot Voting Results

```python
import swissparlpy as spp

votes = spp.get_data('Vote', Language='DE', IdVotingNumber=24189)
spp.plot_voting(votes)
```
