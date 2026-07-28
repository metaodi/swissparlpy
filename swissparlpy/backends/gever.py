"""Gever backend implementation

Provides access to the Gever (Geschaeftsverwaltungssystem) APIs of the canton
of Zurich (Kantonsrat) and the city of Zurich (Gemeinderat).

The parsing of the CMI CDWS XML responses is based on
`goifer <https://github.com/metaodi/goifer>`_ (MIT licensed, same author),
adapted to the swissparlpy backend interface.
"""

import logging
import re
import requests
import warnings
from collections import defaultdict
from datetime import datetime
from pprint import pformat
from typing import Any, Callable, Iterator, Optional, Union

from flatten_dict import flatten
import muzzle

from .base import BaseBackend, BaseResponse
from .gever_config import DEFAULT_NAMESPACES, INSTANCES
from .. import errors

log = logging.getLogger(__name__)

DEFAULT_INSTANCE = "canton_zurich"
DEFAULT_QUERY = "seq > 0"
DEFAULT_LANGUAGE = "de-CH"
DEFAULT_MAXIMUM_RECORDS = 500

# Keep one level of nesting intact, deeper structures are flattened
MAX_FLATTEN_DEPTH = 1

# Fields that are flattened additionally if the schema does not declare
# them as a list (fallback for tables without a usable schema)
SPECIAL_FLATTEN_KEYS = ["person_kontakt", "position", "geschaeft"]

DOC_PATTERN = re.compile("eDo(c|k)ument")
NS_PATTERN = re.compile("^.+:")


def _clean_name(key: str) -> str:
    """Remove the namespace prefix of a tag and lowercase it"""
    return NS_PATTERN.sub("", key).lower()


def _as_list(value: Any) -> list[Any]:
    """Return the value as a list, wrapping single values"""
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _is_multi_occurrence(max_occurs: Any) -> bool:
    """Check if a `maxOccurs` value of a schema means 'more than one'"""
    if max_occurs is None:
        return False
    if isinstance(max_occurs, str) and max_occurs.lower() == "unbounded":
        return True
    try:
        return int(max_occurs) > 1
    except (TypeError, ValueError):
        return False


class GeverXmlParser(object):
    """Thin wrapper around muzzle to turn XML elements into dicts"""

    def __init__(self, namespaces: Optional[dict[str, str]] = None) -> None:
        self.namespaces = namespaces or dict(DEFAULT_NAMESPACES)
        self.parser = muzzle.XMLParser(self.namespaces)

    def parse(self, content: Union[str, bytes]) -> Any:
        try:
            return self.parser.parse(content)
        except muzzle.MuzzleError as e:
            raise errors.SwissParlError(f"Failed to parse XML response: {e}") from e

    def find(self, xml: Any, path: str) -> Any:
        return self.parser.find(xml, path)

    def findall(self, xml: Any, path: str) -> list[Any]:
        return list(self.parser.findall(xml, path))

    def element_namespaces(self, elem: Any) -> dict[str, None]:
        """Collect all xmlns values of an element, to strip them when parsing"""
        dict_namespaces: dict[str, None] = {}
        elem_dict = flatten(self.parser.todict(elem, xml_attribs=True))
        for key, value in elem_dict.items():
            if "xmlns" in key and value:
                dict_namespaces[value] = None
        return dict_namespaces

    def to_dict(self, elem: Any) -> dict[str, Any]:
        """Convert an element to a dict, without any namespace prefixes"""
        if not elem:
            return {}
        namespaces = self.element_namespaces(elem)
        data = self.parser.todict(elem, xml_attribs=True, namespaces=namespaces)
        if not data:
            return {}
        data.pop("xmlns", None)
        return dict(data)


class GeverBackend(BaseBackend):
    """Backend implementation for the Gever APIs of Zurich

    :param session: requests session to use for all requests
    :param url: override the ``api_base`` of the configured instance
    :param instance: name of the Gever instance, either ``canton_zurich``
        or ``city_zurich``
    :param config: custom configuration, a dict of instances (see
        :mod:`swissparlpy.backends.gever_config`) or a path to a YAML file
    :param maximum_records: number of records to load per request
    :param lang: language of the response
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        url: str = "",
        instance: str = DEFAULT_INSTANCE,
        config: Union[dict[str, Any], str, None] = None,
        maximum_records: int = DEFAULT_MAXIMUM_RECORDS,
        lang: str = DEFAULT_LANGUAGE,
    ) -> None:
        if not session:
            session = requests.Session()
        self.session = session
        self.instance = instance
        self.maximum_records = maximum_records
        self.lang = lang
        self.config = self._load_config(config, instance)
        if url:
            self.config["api_base"] = url.rstrip("/")

        # table names are lowercase, no matter what the config says
        self.indexes: dict[str, dict[str, Any]] = {
            str(name).lower(): index_config
            for name, index_config in self.config.get("indexes", {}).items()
        }
        self.xmlparser = GeverXmlParser(self.config.get("namespaces"))

        self.cache: dict[str, list[str]] = {}
        self.list_fields: dict[str, set[str]] = {}

    def _load_config(
        self, config: Union[dict[str, Any], str, None], instance: str
    ) -> dict[str, Any]:
        """Get the configuration of a single instance"""
        if isinstance(config, dict):
            full_config = config
        elif isinstance(config, str):
            full_config = self._load_yaml_file(config)
        else:
            full_config = INSTANCES

        try:
            instance_config = dict(full_config[instance])
        except KeyError as e:
            raise errors.SwissParlError(
                f"Gever instance '{instance}' not found in config, "
                f"available instances: {list(full_config.keys())}"
            ) from e

        if "indexes" not in instance_config or "api_base" not in instance_config:
            raise errors.SwissParlError(
                f"Config of Gever instance '{instance}' is incomplete, "
                "'api_base' and 'indexes' are required"
            )
        return instance_config

    def _load_yaml_file(self, path: str) -> dict[str, Any]:
        try:
            import yaml
        except ImportError as e:  # pragma: no cover - depends on environment
            raise errors.SwissParlError(
                "PyYAML is required to load a config file, "
                "install it with 'pip install pyyaml' or pass a dict instead"
            ) from e

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise errors.SwissParlError(f"Config file '{path}' is not a mapping")
        return data

    def _http_get_request(
        self, url: str, params: Optional[dict[str, Any]] = None
    ) -> requests.Response:
        """Make a GET request and map the errors to swissparlpy errors"""
        headers = {"user-agent": "Mozilla Firefox Mozilla/5.0; metaodi swissparlpy"}
        if "user-agent" not in self.session.headers:
            self.session.headers["user-agent"] = headers["user-agent"]

        try:
            r = self.session.get(url, timeout=30, params=params or {})
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            log.error(f"Error making GET request to {url}: {e}")
            raise errors.SwissParlHttpRequestError(
                f"Failed to make GET request to {url}: {e}"
            ) from e

    def get_tables(self) -> list[str]:
        """Return the list of available tables (indexes) of the instance"""
        return list(self.indexes.keys())

    def _get_index_config(self, table: str) -> dict[str, Any]:
        """Get the config of a table, the lookup is case-insensitive"""
        try:
            return self.indexes[str(table).lower()]
        except (KeyError, AttributeError) as e:
            raise errors.TableNotFoundError(
                f"Table '{table}' not found in Gever instance '{self.instance}', "
                f"available tables: {self.get_tables()}"
            ) from e

    def _get_index_url(self, table: str) -> str:
        """Build the URL of a table, the lookup of the table is case-insensitive"""
        index_config = self._get_index_config(table)
        try:
            path = index_config["path"]
        except KeyError as e:
            raise errors.SwissParlError(
                f"Config of table '{table}' is missing the 'path' key"
            ) from e

        base = self.config["api_base"].rstrip("/")
        section = index_config.get("section", "")
        if section:
            return f"{base}/{section}{path}"
        return f"{base}{path}"

    def _get_files_base(self, table: str) -> str:
        """Build the base URL to download files of a table"""
        index_config = self._get_index_config(table)
        base = self.config["api_base"].rstrip("/")
        files_path = self.config.get("files_api", {}).get("path", "")
        section = index_config.get("section", "")
        if section:
            return f"{base}/{section}{files_path}"
        return f"{base}{files_path}"

    def file(self, table: str, file_id: str, version: str, view: str) -> str:
        """Build the download URL of a document"""
        return f"{self._get_files_base(table)}/{file_id}/{version}/{view}"

    def _load_schema(self, table: str) -> None:
        """Load and cache the variables and list fields of a table"""
        key = str(table).lower()
        if key in self.cache:
            return

        url = f"{self._get_index_url(table)}/schema"
        response = self._http_get_request(url)
        variables, list_fields = self._parse_schema(response.content)
        self.cache[key] = variables
        self.list_fields[key] = list_fields

    def _parse_schema(self, content: bytes) -> tuple[list[str], set[str]]:
        """Parse an XSD schema into a list of variables and a set of list fields

        A field is a list field if the schema declares it with a `maxOccurs`
        of `unbounded` or a number greater than 1. Those fields are always
        returned as a list, even if a record contains only one of them.
        """
        xml = self.xmlparser.parse(content)
        schema = self._normalize_keys(self.xmlparser.to_dict(xml))

        # unwrap the root element (i.e. `schema`) if there is only one
        keys = list(schema.keys())
        if len(keys) == 1 and isinstance(schema[keys[0]], dict):
            schema = schema[keys[0]]

        list_fields: set[str] = set()
        self._collect_list_fields(schema, list_fields)

        complex_type = self._get_root_complex_type(schema)
        variables = []
        for element in self._get_schema_elements(complex_type):
            name = element.get("name")
            if isinstance(name, str):
                variables.append(name.lower())
        for attribute in _as_list(complex_type.get("attribute")):
            if isinstance(attribute, dict) and isinstance(attribute.get("name"), str):
                variables.append(attribute["name"].lower())

        # keep the order, but remove duplicates
        return list(dict.fromkeys(variables)), list_fields

    def _normalize_keys(self, node: Any) -> Any:
        """Recursively strip namespaces of all keys and lowercase them"""
        if isinstance(node, dict):
            return {_clean_name(k): self._normalize_keys(v) for k, v in node.items()}
        if isinstance(node, list):
            return [self._normalize_keys(item) for item in node]
        return node

    def _get_root_complex_type(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Find the complexType that describes a record of the table"""
        complex_types = [
            ct for ct in _as_list(schema.get("complextype")) if isinstance(ct, dict)
        ]
        if not complex_types:
            return {}

        root_elements = [
            el for el in _as_list(schema.get("element")) if isinstance(el, dict)
        ]
        for root_element in root_elements:
            type_name = _clean_name(str(root_element.get("type", "")))
            for complex_type in complex_types:
                if _clean_name(str(complex_type.get("name", ""))) == type_name:
                    return complex_type
        return complex_types[0]

    def _get_schema_elements(
        self, complex_type: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get all element definitions of a complexType"""
        elements = []
        for container_key in ("sequence", "all", "choice"):
            for container in _as_list(complex_type.get(container_key)):
                if not isinstance(container, dict):
                    continue
                for element in _as_list(container.get("element")):
                    if isinstance(element, dict):
                        elements.append(element)
        return elements

    def _collect_list_fields(self, node: Any, list_fields: set[str]) -> None:
        """Recursively collect all fields of a schema that can occur repeatedly"""
        if isinstance(node, dict):
            name = node.get("name")
            if isinstance(name, str) and _is_multi_occurrence(node.get("maxoccurs")):
                list_fields.add(name.lower())
            for value in node.values():
                self._collect_list_fields(value, list_fields)
        elif isinstance(node, list):
            for value in node:
                self._collect_list_fields(value, list_fields)

    def get_variables(self, table: str) -> list[str]:
        """Return the list of variables of a table, based on its schema"""
        self._load_schema(table)
        return self.cache[str(table).lower()]

    def _get_schema_info(self, table: str) -> tuple[list[str], set[str]]:
        """Get variables and list fields, without failing on schema errors"""
        key = str(table).lower()
        try:
            self._load_schema(table)
        except errors.TableNotFoundError:
            raise
        except errors.SwissParlError as e:
            log.warning(
                f"Could not load the schema of table '{table}': {e}. "
                "Records are returned without schema based normalization."
            )
            return [], set()
        return self.cache[key], self.list_fields[key]

    def _build_query(
        self, filter: Union[str, Callable, None], kwargs: dict[str, Any]
    ) -> str:
        """Build a CQL query out of the filter and the given keyword arguments"""
        if callable(filter):
            log.warning("Callable filters are not supported for the Gever backend")
            filter = None

        if filter and isinstance(filter, str):
            if kwargs:
                log.warning(
                    "Ignoring the keyword arguments "
                    f"{list(kwargs.keys())}, since an explicit filter is used"
                )
            return filter

        clauses = []
        for key, value in kwargs.items():
            if isinstance(value, bool):
                clauses.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                clauses.append(f"{key} = {value}")
            else:
                clauses.append(f"{key} adj {value}")

        if not clauses:
            return DEFAULT_QUERY
        return " and ".join(clauses)

    def get_data(
        self, table: str, filter: Union[str, Callable, None] = None, **kwargs: Any
    ) -> "GeverResponse":
        """Query a table with an optional CQL filter

        Keyword arguments are turned into a CQL query, e.g.
        ``get_data('mitglieder', name='Marti')`` searches for ``name adj Marti``.
        A filter given as string is used as query as-is.
        """
        maximum_records = kwargs.pop("maximum_records", self.maximum_records)
        start_record = kwargs.pop("start_record", 1)
        lang = kwargs.pop("lang", self.lang)

        variables, list_fields = self._get_schema_info(table)
        for key in kwargs:
            if variables and key.lower() not in variables:
                log.warning(f"Attribute '{key}' is not a variable of table '{table}'")

        params = {
            "q": self._build_query(filter, kwargs),
            "l": lang,
            "m": maximum_records,
            "s": start_record,
        }
        return GeverResponse(
            session=self.session,
            url=f"{self._get_index_url(table)}/searchdetails",
            params=params,
            table=str(table).lower(),
            variables=variables,
            list_fields=list_fields,
            files_base=self._get_files_base(table),
            xmlparser=self.xmlparser,
        )

    def get_glimpse(self, table: str, rows: int = 5) -> "GeverResponse":
        """Get a preview of the first N rows of a table"""
        return self.get_data(table, maximum_records=rows)


class GeverResponse(BaseResponse):
    """Response wrapper for Gever search queries"""

    def __init__(
        self,
        session: requests.Session,
        url: str,
        params: dict[str, Any],
        table: str,
        variables: Optional[list[str]] = None,
        list_fields: Optional[set[str]] = None,
        files_base: str = "",
        xmlparser: Optional[GeverXmlParser] = None,
    ) -> None:
        self.session = session
        self.url = url
        self.params = dict(params)
        self._table = table
        self._variables = variables or []
        self.list_fields = list_fields or set()
        self.files_base = files_base
        self.xmlparser = xmlparser or GeverXmlParser()

        self.records: list[dict[str, Any]] = []
        self.count = 0
        self.index_name = table
        self.query = str(self.params.get("q", ""))
        self.maximum_records = int(self.params.get("m", DEFAULT_MAXIMUM_RECORDS))
        self.start_record = int(self.params.get("s", 1))
        self.next_start_record: Optional[int] = None

        self._load_content()

    @property
    def table(self) -> str:
        return self._table

    @property
    def variables(self) -> list[str]:
        return self._variables

    @property
    def _records_loaded_count(self) -> int:
        return len(self.records)

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return pformat(self.records, width=80, sort_dicts=False)

    def _load_content(self, **kwargs: Any) -> None:
        """Load a page of records and parse it"""
        self.params.update(kwargs)
        log.debug(f"Loading data from {self.url} with params {self.params}")
        try:
            response = self.session.get(self.url, params=self.params, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.error(f"Error loading data from {self.url}: {e}")
            raise errors.SwissParlHttpRequestError(
                f"Failed to load data from {self.url}: {e}"
            ) from e
        self._parse_content(response.content)

    def _load_next_page(self) -> None:
        if self.next_start_record is None:
            raise errors.NoMoreRecordsError()
        self._load_content(s=self.next_start_record)

    def _load_until(self, limit: int) -> None:
        while len(self.records) < limit and self.next_start_record is not None:
            try:
                self._load_next_page()
            except errors.NoMoreRecordsError:  # pragma: no cover - guarded above
                break

    def _maybe_int(self, value: Any) -> Any:
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    def _parse_content(self, content: bytes) -> None:
        """Parse a search response and extract its records"""
        xml = self.xmlparser.parse(content)
        self.index_name = xml.attrib.get("indexName", self._table)
        self.count = int(self._maybe_int(xml.attrib.get("numHits", 0)) or 0)
        self.query = xml.attrib.get("q", self.query)
        self.maximum_records = int(
            self._maybe_int(xml.attrib.get("m", self.maximum_records)) or 0
        )
        self.start_record = int(
            self._maybe_int(xml.attrib.get("s", self.start_record)) or 1
        )

        self.next_start_record = self.start_record + self.maximum_records
        if self.next_start_record > self.count:
            self.next_start_record = None

        self._extract_records(xml)

        if not self._variables and self.records:
            self._variables = list(self.records[0].keys())

    def _extract_records(self, xml: Any) -> None:
        """Extract all hits of a search response"""
        new_records = []
        for xml_rec in self.xmlparser.findall(xml, "./sd:Hit"):
            record: defaultdict = defaultdict()
            guid = xml_rec.attrib["Guid"]
            rec = self.xmlparser.find(xml_rec, f"./*[@OBJ_GUID = '{guid}']")
            record.update(self._tag_data(rec))
            new_records.append(dict(record))
        self.records.extend(new_records)

    def _tag_data(self, elem: Any) -> dict[str, Any]:
        """Turn a single record element into a normalized dict"""
        record_data = self.xmlparser.to_dict(elem)
        if not record_data:
            return {}

        record_data = self._add_download_to_docs(record_data)

        # check if there is only one element on the top level
        keys = list(record_data.keys())
        if len(record_data) == 1 and len(keys) > 0 and len(record_data[keys[0]]) > 0:
            record_data = record_data[keys[0]]

        return self._flat_dict(record_data)

    def _add_download_to_docs(self, rec: dict[str, Any]) -> dict[str, Any]:
        """Add a download URL and a filename to all document elements"""
        new_rec: dict[str, Any] = {}
        for k, v in rec.items():
            if DOC_PATTERN.match(k) and isinstance(v, dict):
                download_url, filename = self._get_download_url(v)
                if download_url:
                    v["download_url"] = download_url
                    v["FileName"] = filename
                new_rec[k] = v
            elif isinstance(v, list):
                new_rec[k] = [
                    self._add_download_to_docs(vi) if isinstance(vi, dict) else vi
                    for vi in v
                ]
            elif isinstance(v, dict):
                new_rec[k] = self._add_download_to_docs(v)
            else:
                new_rec[k] = v
        return new_rec

    def _get_download_url(self, doc: dict[str, Any]) -> tuple[str, str]:
        """Build the download URL and filename of a document element"""
        try:
            version = doc["Version"]
            latest_version = version[-1] if isinstance(version, list) else version
            view = latest_version["Rendition"]["Ansicht"]
            ext = latest_version["Rendition"]["Extension"]
            filename = f"{doc['FileName']}.{ext}"
            nr = latest_version["Nr"]
            file_id = doc["ID"]
        except (KeyError, IndexError, TypeError) as e:
            log.debug(f"Could not build a download URL for a document: {e}")
            return ("", "")
        return (f"{self.files_base}/{file_id}/{nr}/{view}", filename)

    def _wrap_list_fields(self, data: Any) -> Any:
        """Wrap all fields the schema declares as repeatable into a list

        This happens *before* flattening, so that a field with a single
        occurrence and a field with multiple occurrences result in the same
        structure (a list), which keeps the records consistent.
        """
        if isinstance(data, list):
            return [self._wrap_list_fields(item) for item in data]
        if not isinstance(data, dict):
            return data

        wrapped = {}
        for key, value in data.items():
            value = self._wrap_list_fields(value)
            if _clean_name(key) in self.list_fields and not isinstance(value, list):
                value = _as_list(value)
            wrapped[key] = value
        return wrapped

    def _flat_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        """Flatten and clean a record"""

        def leaf_reducer(k1: Optional[str], k2: str) -> str:
            if k1 is None or k2.lower() in k1.lower():
                return k2
            if k2 == "text":
                return k1
            return f"{k1}_{k2}"

        d = self._wrap_list_fields(d)
        flat_data = flatten(
            d, max_flatten_depth=MAX_FLATTEN_DEPTH, reducer=leaf_reducer
        )
        flat_data = self._clean_dict(flat_data)

        # make some special cases more flat, but never touch a field that the
        # schema declares as a list, those are already normalized
        for k in SPECIAL_FLATTEN_KEYS:
            if k in self.list_fields or k not in flat_data:
                continue
            if isinstance(flat_data[k], list):
                flat_data[k] = [
                    self._flat_dict(ik) if isinstance(ik, dict) else ik
                    for ik in flat_data[k]
                ]
            elif isinstance(flat_data[k], dict):
                flat_data.update(
                    flatten(
                        flat_data[k],
                        max_flatten_depth=MAX_FLATTEN_DEPTH,
                        reducer=leaf_reducer,
                    )
                )
                del flat_data[k]

        return flat_data

    def _convert_value(self, value: str) -> Any:
        """Convert a string to a datetime or bool, if possible"""
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        return value

    def _clean_dict(self, records: dict[str, Any]) -> dict[str, Any]:
        """Remove namespaces, lowercase keys and convert values"""
        clean_rec: dict[str, Any] = {}
        for k, v in records.items():
            if k.startswith("xmlns"):
                continue
            clean_k = _clean_name(k)
            if isinstance(v, dict):
                # an element marked as nil is empty, an element that is not
                # nil and has no children is a plain value
                nil = str(v.get("nil", "")).lower()
                if nil == "true":
                    clean_rec[clean_k] = None
                    continue
                elif nil == "false" and "text" in v:
                    clean_rec[clean_k] = self._convert_value(v["text"])
                    continue
                clean_rec[clean_k] = self._clean_dict(v)
            elif isinstance(v, list):
                clean_rec[clean_k] = [
                    (
                        self._clean_dict(vi)
                        if isinstance(vi, dict)
                        else self._convert_value(vi) if isinstance(vi, str) else vi
                    )
                    for vi in v
                ]
            elif isinstance(v, str):
                clean_rec[clean_k] = self._convert_value(v)
            else:
                clean_rec[clean_k] = v

        return clean_rec

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over all records, loading pages as needed"""
        i = 0
        while True:
            if i >= len(self.records):
                if i > self.count:
                    warnings.warn(
                        f"Loaded more records ({i}) than total count ({self.count}),"
                        "stopping iteration",
                        errors.PaginationWarning,
                    )
                    break
                if self.next_start_record is not None:
                    try:
                        self._load_next_page()
                    except errors.NoMoreRecordsError:  # pragma: no cover
                        break
                else:
                    break

            if i < len(self.records):
                yield self.records[i]
                i += 1
            else:
                break

    def __getitem__(
        self, key: Union[int, slice]
    ) -> Union[dict[str, Any], list[dict[str, Any]]]:
        if isinstance(key, slice):
            limit = max(key.start or 0, key.stop or self.count)
            self._load_until(limit)
            return self.records[key]

        if not isinstance(key, int):
            raise TypeError("Index must be an integer or slice")

        if key < 0:
            self._load_until(self.count)
        else:
            self._load_until(key + 1)

        return self.records[key]

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Convert all data to a list of dictionaries"""
        self._load_until(self.count)
        return list(self)
