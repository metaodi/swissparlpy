# Plan: `GeverBackend` for swissparlpy

Integrate the functionality of [goifer](https://github.com/metaodi/goifer) as a third
swissparlpy backend, giving access to the Gever (Geschäftsverwaltungssystem) APIs of the
**Canton of Zurich** (Kantonsrat) and the **City of Zurich** (Gemeinderat).

This is a planning document; it should be removed (or moved into the README) before the
feature branch is merged.

## 1. Key decision: port the code, don't depend on `goifer`

Two options were considered:

| | (A) depend on `goifer` and wrap it | (B) port the code into swissparlpy |
|---|---|---|
| deps | `goifer` (pulls `muzzle`, `pyyaml`, `flatten-dict`) | `muzzle`, `flatten-dict` |
| control over normalization | none — needs upstream PRs | full |
| duplication | none | ~350 lines |

**Recommendation: (B) port.** The integration needs behavioural changes that goifer cannot
make without breaking its own API — schema-driven list normalization, a different
`max_flatten_depth`, case-insensitive index lookup, swissparlpy error/warning types, and
type hints for mypy (`disallow_untyped_defs = true`). Wrapping goifer would mean pinning
a version and shipping post-processing on top of output we want changed anyway.

The ported modules keep an attribution header pointing at goifer and its MIT licence.
`goifer` stays the standalone library; swissparlpy carries a swissparlpy-shaped variant.

### New dependencies

Added to `[project.dependencies]` in `pyproject.toml`:

- `muzzle` — XML→dict parsing with namespace handling (same author, already used by goifer)
- `flatten-dict` — the `flatten()` used for record flattening

`pyyaml` is **not** added: the instance config ships as a plain Python dict in
`swissparlpy/backends/gever_config.py` instead of a `config.yml`. That removes the
package-data/`hatchling` wiring and one dependency; a caller can still pass their own
config as a `dict` to `GeverBackend(config=...)`. (Loading a YAML path stays available
only if `pyyaml` happens to be installed — optional import, no hard requirement.)

## 2. Files

```
swissparlpy/backends/gever.py           new — GeverBackend, GeverResponse
swissparlpy/backends/gever_config.py    new — INSTANCES dict (canton_zurich, city_zurich)
swissparlpy/backends/__init__.py        export GeverBackend
swissparlpy/client.py                   backend string mapping + Literal type
swissparlpy/__init__.py                 export + Literal on the 5 module-level functions
tests/gever_backend_test.py             new
tests/conftest.py                       new fixtures
tests/fixtures/gever_*.xml              new — recorded API responses
examples/gever_backend.py               new
README.md                               new sections
CHANGELOG.md                            Unreleased entry
pyproject.toml                          muzzle + flatten-dict
```

## 3. Concept mapping

| goifer | swissparlpy | notes |
|---|---|---|
| `Client(instance=...)` | `GeverBackend(instance=...)` | instance selects canton vs. city |
| `indexes()` | `get_tables()` | from config, lowercased |
| `schema(index)` | `get_variables(table)` | XSD → field names; also drives list normalization |
| `search(index, query, ...)` | `get_data(table, filter, **kwargs)` | `filter` is the CQL query string |
| — | `get_glimpse(table, rows)` | `search` with `maximum_records=rows` |
| `SearchResponse` | `GeverResponse(BaseResponse)` | lazy paging, indexing, slicing |
| `file(...)` | `GeverBackend.file(...)` | backend-specific extra, kept |
| `GoiferError` etc. | `swissparlpy.errors.*` | mapped, see §7 |

## 4. Backend selection API

Gever has two instances but swissparlpy selects a backend by a single string. Solution: one
class, two aliases.

```python
GeverBackend(session=None, instance="canton_zurich", config=None, maximum_records=500)
```

`SwissParlClient` / the module-level functions accept:

- `"gever"` → canton of Zurich (default instance)
- `"gever_canton_zurich"` → canton of Zurich
- `"gever_city_zurich"` → city of Zurich

```python
import swissparlpy as spp

spp.get_tables(backend="gever_city_zurich")
spp.get_data("geschaeft", backend="gever_city_zurich")

from swissparlpy import SwissParlClient, GeverBackend
client = SwissParlClient(backend=GeverBackend(instance="city_zurich"))
```

The `Literal[...]` type in `client.py` and `__init__.py` gains the three new values.
An unknown instance raises `SwissParlError` (goifer's `ConfigError` has no counterpart and
does not warrant a new error class).

## 5. Table-name casing

goifer's config mixes conventions: `canton_zurich` uses PascalCase index keys
(`Geschaeft`, `Wahlkreise`), `city_zurich` uses lowercase (`geschaeft`, `kontakt`).
swissparlpy exposes **lowercase table names for both instances** — this matches the City
API convention and the rest of swissparlpy's non-OData backend (`openparldata` uses
lowercase `persons`, `affairs`, …).

- config keys are stored lowercase; the URL path is unchanged (it is already uppercase in
  the canton API: `/cdws/Index/GESCHAEFT`)
- `_get_index_url()` does a **case-insensitive** lookup, so `"Geschaeft"` and `"geschaeft"`
  both resolve — users porting goifer code keep working
- `get_tables()` returns the lowercase names
- `get_data()` raises `TableNotFoundError` for an unknown table (case-insensitively checked),
  consistent with `OpenParlDataBackend.get_data`

Expected counts to assert in tests: canton_zurich **11**, city_zurich **19** (the 18 indexes
in goifer's config plus `mitglieder`, which the City API exposes but goifer's config omits —
to be confirmed against the live API while recording fixtures; if it is not there, the
assertion becomes 18).

Base URL for the city instance switches from goifer's integration host
`https://www.integ.gemeinderat-zuerich.ch` to production
`https://www.gemeinderat-zuerich.ch`. Tests assert the production URL.

## 6. Record normalization (the substantive change vs. goifer)

goifer's `Response._flat_dict` flattens with `max_flatten_depth=2` and then re-flattens a
hard-coded set of keys (`person_kontakt`, `position`, `geschaeft`). Two problems for
swissparlpy:

1. **dict/list inconsistency** — a field that the XSD declares as repeatable
   (`maxOccurs="unbounded"` or `> 1`) arrives as a `dict` when a record has exactly one of
   them and a `list` when it has several. `to_dataframe()` then produces a column holding
   a mixture of dicts and lists.
2. **over-flattening** — depth 2 collapses nested structures that are more useful kept
   nested once the records go into a DataFrame.

The plan:

- `get_variables()` parses the schema XSD once per table and caches, alongside the plain
  field-name list, the set of **list fields**: elements whose `maxOccurs` is `unbounded`
  or an int `> 1`. The backend hands this set to `GeverResponse`.
- In `_flat_dict`, **wrap list fields into a list before flattening**, not after — a
  single-occurrence value becomes `[value]` at the point where the schema is authoritative.
  Doing it after flattening is what produces the dict/list mixture today.
- **Skip the special-case re-flattening** for any field the schema already declares as a
  list. The hard-coded `["person_kontakt", "position", "geschaeft"]` loop stays only as a
  fallback for instances/tables whose schema fetch failed.
- **`max_flatten_depth` 2 → 1**, preserving one level of nesting.

Result:

```python
response = backend.get_data("mitglieder")
first = response[0]
assert isinstance(first["position"], list)   # always a list, even for a single entry
assert isinstance(first["kontakt"], list)
```

Everything else from goifer's `Response` is carried over unchanged: namespace stripping,
lowercasing of keys, `nil`/`text` leaf collapsing, ISO-datetime and boolean coercion, and
`download_url`/`FileName` injection for `eDokument`/`eDocument` nodes.

If the schema request fails, `get_data()` still works — it logs a warning and falls back to
the goifer behaviour rather than raising, so a schema-endpoint outage does not take the
backend down.

## 7. Response, paging, errors

`GeverResponse(BaseResponse)` implements the full abstract interface:

| member | behaviour |
|---|---|
| `__len__` | `numHits` from the search response (total, not loaded) |
| `_records_loaded_count` | `len(self.records)` |
| `__iter__` | yields lazily, loading the next page via the `s` (start record) param |
| `__getitem__` | int + slice; negative index loads everything first |
| `to_dict_list()` | loads all pages, returns `list(self)` |
| `variables` / `table` | from the backend |
| `to_dataframe()` | inherited from `BaseResponse` |

Paging follows goifer: `next_start_record = start_record + maximum_records`, `None` once it
exceeds `count`. `__iter__` additionally emits `errors.PaginationWarning` if more records
load than `count` — same guard `OpenParlDataResponse.__iter__` has.

Error mapping:

| goifer | swissparlpy |
|---|---|
| `GoiferError` (HTTP error) | `SwissParlHttpRequestError` |
| `GoiferError` (request error) | `SwissParlHttpRequestError` |
| `NoMoreRecordsError` | `errors.NoMoreRecordsError` |
| `ConfigError` | `errors.SwissParlError` |
| unknown table | `errors.TableNotFoundError` |

Note `pyproject.toml` has `filterwarnings = ["error", ...]` — any warning raised on a happy
path fails the suite, so warnings must be confined to genuinely degraded paths.

## 8. Query / filter semantics

The Gever API uses CQL-ish queries (`seq > 0`, `Name adj Marti and Vorname adj Res`).

- `filter` as `str` → passed through as `q`, verbatim
- `filter` as callable → not supported; log a warning and ignore (mirrors
  `OpenParlDataBackend`)
- `filter is None` → default `"seq > 0"` (goifer's default: everything)
- `**kwargs` → joined into the query as `field adj value` for strings and `field = value`
  for numbers/bools, `and`-combined. Ignored when an explicit `filter` string is given
  (with a warning), since mixing raw CQL and generated clauses is ambiguous.
- `maximum_records` is a constructor arg on the backend (default 500) and overridable per
  call via `get_data(..., maximum_records=...)`.

`GeverBackend.file(table, file_id, version, view)` is kept as a backend-specific method for
constructing document download URLs, as in goifer.

## 9. Tests

New `tests/gever_backend_test.py`, `responses`-mocked like the OpenParlData tests. Fixtures
recorded from the live APIs into `tests/fixtures/`:

- `gever_wahlkreise.xml` — canton search response (can start from goifer's fixture)
- `gever_wahlkreise_schema.xml` — canton schema response
- `gever_mitglieder.xml` + `gever_mitglieder_schema.xml` — the list-field cases
  (`position`, `kontakt`), including one record with a single occurrence and one with several
- `gever_geschaeft_page1.xml` / `gever_geschaeft_page2.xml` — city instance, paging
- `gever_sitzungen_detail.xml` — `eDokument` / `download_url` case

Cases to cover:

1. `get_tables()` — count per instance (11 / 19), all lowercase
2. case-insensitive lookup — `get_data("Geschaeft")` == `get_data("geschaeft")`
3. unknown table → `TableNotFoundError`; unknown instance → `SwissParlError`
4. `get_variables()` — parses schema, caches (assert a single HTTP call on the second use)
5. **list normalization** — single-occurrence field still comes back as a `list`; nested
   dicts survive at depth 1
6. `to_dataframe()` — column dtypes are uniform across a mixed single/multi-occurrence set
7. paging — `__iter__` across two pages, `len()` == `numHits`, `_records_loaded_count`
   grows lazily
8. `__getitem__` — int, negative int, slice
9. `get_glimpse(table, rows=3)` — sends `m=3`
10. errors — 500 → `SwissParlHttpRequestError`; empty result set → `len() == 0`, no warning
11. `file()` — URL shape for both the `section` and no-`section` config forms
12. schema fetch fails → `get_data` still returns records (fallback path), warns
13. `SwissParlClient(backend="gever_city_zurich")` and
    `spp.get_data(..., backend="gever_city_zurich")` wire through

Target: keep the suite's existing coverage level for the new module (the repo runs
`--cov=swissparlpy`).

`mypy` runs with `disallow_untyped_defs`; `muzzle`/`flatten_dict` are untyped but
`ignore_missing_imports = true` is already set, so no stub work is needed.

## 10. Docs

- README: new "Gever backend" section under Backend Selection — the two instances, table
  names, query syntax, `file()` for downloads, plus TOC entries and a line in the intro
  paragraph naming the Gever APIs
- `examples/gever_backend.py` — list tables, query the canton's `wahlkreise`, query the
  city's `geschaeft`, build a DataFrame, download a document
- CHANGELOG under `## [Unreleased] / ### Added`:
  `Add support for the Gever APIs of the canton and city of Zurich as a backend (based on goifer)`

## 11. Sequencing

1. config module + `GeverBackend` skeleton (`get_tables`, `_get_index_url`, casing) + tests
2. schema parsing → `get_variables` + list-field detection + tests
3. `GeverResponse`: parsing, normalization, paging, indexing + tests
4. `get_data` / `get_glimpse` / `file`, query building, error mapping + tests
5. wiring: `backends/__init__`, `client.py`, `__init__.py`, `Literal` types + tests
6. deps, README, example, CHANGELOG
7. full run: `./validate.sh` (black, flake8, mypy, pytest)

Steps 1–5 are each independently testable; the branch stays green throughout.

## 12. Open questions / risks

- **City instance table count** — 18 in goifer's config vs. 19 expected; confirm against
  the live API when recording fixtures and settle the assertion.
- **Production vs. integration host for the City API** — plan assumes
  `https://www.gemeinderat-zuerich.ch` is the correct public host; verify before pinning it
  in tests.
- **`muzzle` as a dependency** — small, single-author package. Acceptable here (same author
  as swissparlpy), but worth a conscious nod; the alternative is `xmltodict` + manual
  namespace handling, which is roughly what `muzzle` already is.
- **Namespace differences between instances** — the canton API uses the
  `http://www.cmiag.ch/cdws/searchDetailResponse` namespace; confirm the city API matches
  before hard-coding it, and make the namespace map part of the per-instance config if not.
- **`to_dict_list()` on a large table** loads every page into memory. Same behaviour as the
  other backends; document it rather than solve it here.
- **Divergence from goifer** — the ported normalization intentionally differs. Worth a note
  in goifer's README (or an issue) so the two do not silently drift further.
