"""Gever backend implementation for swissparlpy (Canton/City of Zurich)"""

import logging
import re
from datetime import datetime
from typing import Any, Callable, Literal, Optional, Sequence, Union, cast

import requests

from .base import BaseBackend, BaseResponse
from .. import errors

log = logging.getLogger(__name__)

NAMESPACES = {
    "sd": "http://www.cmiag.ch/cdws/searchDetailResponse",
    "xsd": "http://www.w3.org/2001/XMLSchema",
}

# Built-in configuration (ported from goifer's config.yml)
_DEFAULT_CONFIG: dict[str, Any] = {
    "canton_zurich": {
        "api_base": "https://parlzhcdws.cmicloud.ch",
        "files_api": {"path": "/cdws/Files"},
        "indexes": {
            "Behoerden": {"section": "parlzh2", "path": "/cdws/Index/BEHOERDEN"},
            "SitzungenDetail": {
                "section": "parlzh3",
                "path": "/cdws/Index/SITZUNGENDETAIL",
            },
            "Geschaeft": {"section": "parlzh5", "path": "/cdws/Index/GESCHAEFT"},
            "Mitglieder": {"section": "parlzh2", "path": "/cdws/Index/MITGLIEDER"},
            "Parteien": {"section": "parlzh2", "path": "/cdws/Index/PARTEIEN"},
            "Wahlkreise": {"section": "parlzh2", "path": "/cdws/Index/WAHLKREISE"},
            "Direktion": {
                "section": "parlzh5",
                "path": "/cdws/Index/GESCHAEFT_DIREKTION",
            },
            "Geschaeftsart": {
                "section": "parlzh5",
                "path": "/cdws/Index/GESCHAEFT_GESCHAEFTSART",
            },
            "Gremiumtyp": {"section": "parlzh3", "path": "/cdws/Index/GREMIUMTYP"},
            "KRVersand": {"section": "parlzh1", "path": "/cdws/Index/KRVERSAND"},
            "Ablaufschritte": {
                "section": "parlzh5",
                "path": "/cdws/Index/ABLAUFSCHRITTE",
            },
        },
    },
    "city_zurich": {
        "api_base": "https://www.gemeinderat-zuerich.ch",
        "files_api": {"path": "/api/files"},
        "indexes": {
            "Ablaufschritt": {"path": "/api/ablaufschritt"},
            "Abstimmung": {"path": "/api/abstimmung"},
            "Behoerdenmandat": {"path": "/api/behoerdenmandat"},
            "Departement": {"path": "/api/departement"},
            "Dokument": {"path": "/api/dokument"},
            "Geschaeft": {"path": "/api/geschaeft"},
            "Geschaeftsart": {"path": "/api/geschaeftsart"},
            # This endpoint seems to be currently unavailable (returns 404)
            # "Geschlecht": {"path": "/api/geschlecht"},
            "Gremiumdetail": {"path": "/api/gremiumdetail"},
            "Gremiumstyp": {"path": "/api/gremiumstyp"},
            "Gremiumsuebersicht": {"path": "/api/gremiumsuebersicht"},
            "Kontakt": {"path": "/api/kontakt"},
            "Partei": {"path": "/api/partei"},
            "PendentBei": {"path": "/api/pendentbei"},
            "Ratspost": {"path": "/api/ratspost"},
            "Referendum": {"path": "/api/referendum"},
            "Sitzung": {"path": "/api/sitzung"},
            "Wahlkreis": {"path": "/api/wahlkreis"},
            "Wohnkreis": {"path": "/api/wohnkreis"},
            "Wortmeldung": {"path": "/api/wortmeldung"},
        },
    },
}


def flatten_dict(
    d: dict[str, Any],
    reducer: Union[Literal["tuple", "path", "underscore", "dot"], Callable] = "tuple",
    inverse: bool = False,
    max_flatten_depth: Optional[int] = None,
    enumerate_types: Sequence[type] = (),
    keep_empty_types: Sequence[type] = (),
) -> dict[str, Any]:
    """Flatten a nested dictionary using the specified reducer."""
    try:
        from flatten_dict import flatten
    except ImportError as e:
        raise ImportError(
            "The Gever backend requires 'muzzle' and 'flatten-dict'. "
            "Install them with: pip install swissparlpy[gever]"
        ) from e

    flat_dict = flatten(
        d,
        reducer=reducer,  # type: ignore
        inverse=inverse,
        max_flatten_depth=max_flatten_depth,
        enumerate_types=enumerate_types,
        keep_empty_types=keep_empty_types,
    )

    return cast(dict[str, Any], flat_dict)  # for type checker


class _NoMoreRecordsError(Exception):
    """Internal exception raised when there are no more records to load."""

    pass


class _GeverDataLoader:
    """Internal helper to load XML data from the Gever API."""

    def __init__(
        self, url: str, params: dict[str, Any], session: requests.Session
    ) -> None:
        self.url = url
        self.params = params
        self.session = session

    def load(self, **kwargs: Any) -> bytes:
        self.params.update(kwargs)
        try:
            res = self.session.get(self.url, params=self.params, timeout=10)
            res.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise errors.SwissParlHttpRequestError(f"HTTP error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise errors.SwissParlHttpRequestError(f"Request error: {e}") from e
        return res.content


class GeverBackend(BaseBackend):
    """Backend implementation for the Gever APIs (Canton/City of Zurich)."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        url: str = "",
        instance: str = "canton_zurich",
        config: Optional[dict[str, Any]] = None,
        maximum_records: int = 500,
    ) -> None:
        # Check optional dependencies
        try:
            import muzzle  # noqa: F401
            from flatten_dict import flatten  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "The Gever backend requires 'muzzle' and 'flatten-dict'. "
                "Install them with: pip install swissparlpy[gever]"
            ) from e

        if not session:
            session = requests.Session()
        self.session = session
        self.maximum_records = maximum_records

        full_config = config if isinstance(config, dict) else _DEFAULT_CONFIG
        if instance not in full_config:
            raise errors.SwissParlError(
                f"Instance '{instance}' not found in config. "
                f"Available instances: {list(full_config.keys())}"
            )
        self.config = full_config[instance]
        self.instance = instance

    def get_tables(self) -> list[str]:
        """Return list of index names."""
        return list(self.config["indexes"].keys())

    def get_variables(self, table: str) -> list[str]:
        """Query the /schema endpoint and extract field names."""
        try:
            import muzzle

            index_url = self._get_index_url(table)
            url = f"{index_url}/schema"
            data_loader = _GeverDataLoader(url, {}, self.session)
            xml_bytes = data_loader.load()
            xsd_ns = {"xsd": "http://www.w3.org/2001/XMLSchema"}
            parser = muzzle.XMLParser(xsd_ns)
            xml = parser.parse(xml_bytes)
            # Extract leaf xsd:element names (skip root wrapper elements with children)
            fields = []
            for elem in parser.findall(xml, ".//xsd:element"):
                name = elem.attrib.get("name")
                if name and not list(elem):
                    fields.append(name)
            return fields
        except errors.SwissParlHttpRequestError as e:
            log.warning(f"HTTP request error: {e}. Falling back to get_data method.")
            res = self.get_data(table)
            if len(res) > 0 and isinstance(res[0], dict):
                return list(res[0].keys())
            raise e

    def get_data(
        self,
        table: str,
        filter: Union[str, Callable, None] = None,
        **kwargs: Any,
    ) -> "GeverResponse":
        """Query the /searchdetails endpoint."""
        query = "seq > 0"
        if filter and isinstance(filter, str):
            query = filter
        elif filter and callable(filter):
            log.warning(
                "Callable filters are not supported for the Gever backend. "
                "The default query will be used."
            )
        if "query" in kwargs:
            query = kwargs.pop("query")

        index_url = self._get_index_url(table)
        url = f"{index_url}/searchdetails"
        params: dict[str, Any] = {
            "q": query,
            "l": "de-CH",
            "m": self.maximum_records,
        }
        data_loader = _GeverDataLoader(url, params, self.session)
        xml_bytes = data_loader.load()
        return GeverResponse(
            xml_bytes=xml_bytes,
            data_loader=data_loader,
            table=table,
            config=self.config,
            is_schema=False,
        )

    def get_glimpse(self, table: str, rows: int = 5) -> "GeverResponse":
        """Get a preview of the first N rows of a table."""
        index_url = self._get_index_url(table)
        url = f"{index_url}/searchdetails"
        params: dict[str, Any] = {
            "q": "seq > 0",
            "l": "de-CH",
            "m": rows,
        }
        data_loader = _GeverDataLoader(url, params, self.session)
        xml_bytes = data_loader.load()
        return GeverResponse(
            xml_bytes=xml_bytes,
            data_loader=data_loader,
            table=table,
            config=self.config,
            is_schema=False,
            maximum_records=rows,
        )

    def _get_index_url(self, index: str) -> str:
        """Build full URL for the given index."""
        try:
            index_config = self.config["indexes"][index]
            base = self.config["api_base"]
            section = index_config.get("section", "")
            path = index_config["path"]
            if section:
                return f"{base}/{section}{path}"
            return f"{base}{path}"
        except KeyError as e:
            raise errors.TableNotFoundError(f"Index '{index}' not found in config: {e}")


class GeverResponse(BaseResponse):
    """Response wrapper for Gever API queries."""

    def __init__(
        self,
        xml_bytes: bytes,
        data_loader: _GeverDataLoader,
        table: str,
        config: dict[str, Any],
        is_schema: bool = False,
        maximum_records: Optional[int] = None,
    ) -> None:
        import muzzle

        self._table = table
        self._original_table = table
        self._config = config
        self._is_schema = is_schema
        self._data_loader = data_loader
        self._maximum_records = maximum_records

        self.namespaces = NAMESPACES
        self.xmlparser = muzzle.XMLParser(self.namespaces)

        self.records: list[dict[str, Any]] = []
        self.count = 0
        self.next_start_record: Optional[int] = None

        self._parse_content(xml_bytes)

    @property
    def _records_loaded_count(self) -> int:
        return len(self.records)

    @property
    def table(self) -> str:
        return self._original_table

    @property
    def variables(self) -> list[str]:
        if self.records:
            return list(self.records[0].keys())
        return []

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        if self._is_schema:
            return f"GeverResponse(table={self._original_table}, type=schema)"
        try:
            return (
                f"GeverResponse(table={self._original_table}, count={self.count}, "
                f"next_start_record={self.next_start_record})"
            )
        except AttributeError:
            return "GeverResponse(empty)"

    def __iter__(self) -> Any:
        i = 0
        while True:
            if i == len(self.records):
                try:
                    self._load_new_data()
                except _NoMoreRecordsError:
                    break
            yield self.records[i]
            i += 1

    def __getitem__(self, key: Union[int, slice]) -> object:
        if isinstance(key, slice):
            limit = max(key.start or 0, key.stop or self.count)
            self._load_new_data_until(limit)
            count = len(self.records)
            return [self.records[k] for k in range(*key.indices(count))]

        if not isinstance(key, int):
            raise TypeError("Index must be an integer or slice")

        limit = key
        if limit < 0:
            limit = self.count
        self._load_new_data_until(limit)
        return self.records[key]

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Convert all data to a list of dictionaries."""
        self._load_new_data_until(self.count)
        return list(self.records)

    # ---- pagination helpers ----

    def _load_new_data_until(self, limit: int) -> None:
        while limit >= len(self.records):
            try:
                self._load_new_data()
            except _NoMoreRecordsError:
                break

    def _load_new_data(self) -> None:
        if self.next_start_record is None:
            raise _NoMoreRecordsError()
        xml_bytes = self._data_loader.load(s=self.next_start_record)
        self._parse_content(xml_bytes)

    # ---- XML parsing (ported from goifer) ----

    def _parse_content(self, xml_bytes: bytes) -> None:
        xml = self.xmlparser.parse(xml_bytes)
        if self._is_schema:
            record: dict[str, Any] = {}
            record.update(self._tag_data(xml))
            self.records = [record]
            self.count = 1
        else:
            self._table = xml.attrib.get("indexName", self._table)
            self.count = self._maybe_int(xml.attrib.get("numHits", "0"))
            maximum_records = self._maybe_int(xml.attrib.get("m", "500"))
            start_record = self._maybe_int(xml.attrib.get("s", "1"))
            if isinstance(start_record, int) and isinstance(maximum_records, int):
                next_start = start_record + maximum_records
            else:
                next_start = None
            if isinstance(next_start, int) and isinstance(self.count, int):
                self.next_start_record = (
                    next_start if next_start <= self.count else None
                )
            else:
                self.next_start_record = None
            # Override with get_glimpse limit if set
            if self._maximum_records is not None:
                self.next_start_record = None
            self._extract_records(xml)

    def _extract_records(self, xml: Any) -> None:
        new_records = []
        xml_recs = self.xmlparser.findall(xml, "./sd:Hit")
        for xml_rec in xml_recs:
            record: dict[str, Any] = {}
            guid = xml_rec.attrib.get("Guid", "")
            safe_guid = guid.replace("'", "&apos;")
            rec = self.xmlparser.find(xml_rec, f"./*[@OBJ_GUID = '{safe_guid}']")
            record.update(self._tag_data(rec))
            new_records.append(record)
        self.records.extend(new_records)

    def _maybe_int(self, s: Any) -> Any:
        try:
            return int(s)
        except (ValueError, TypeError):
            return s

    def _tag_data(self, elem: Any) -> dict[str, Any]:
        if elem is None:
            return {}
        dict_namespaces = self._get_xmlns(elem)
        record_data = self.xmlparser.todict(
            elem, xml_attribs=True, namespaces=dict_namespaces
        )
        if not record_data:
            return {}
        record_data.pop("xmlns", None)
        record_data = self._add_download_to_docs(record_data)

        keys = list(record_data.keys())
        if len(record_data) == 1 and len(keys) > 0 and len(record_data[keys[0]]) > 0:
            record_data = record_data[keys[0]]

        record_data = self._flat_dict(record_data)
        return record_data

    def _add_download_to_docs(self, rec: dict[str, Any]) -> dict[str, Any]:
        new_rec = {}
        doc_pattern = re.compile("eDo(c|k)ument")
        for k, v in rec.items():
            if doc_pattern.match(k) and isinstance(v, dict):
                v["download_url"], v["FileName"] = self._get_download_url(v)
                new_rec[k] = v
            elif isinstance(v, list):
                new_rec[k] = [self._add_download_to_docs(vi) for vi in v]
            elif isinstance(v, dict):
                new_rec[k] = self._add_download_to_docs(v)
            else:
                new_rec[k] = v
        return new_rec

    def _get_download_url(self, doc: dict[str, Any]) -> tuple[str, str]:
        try:
            latest_version = doc["Version"][-1]
        except (KeyError, TypeError):
            latest_version = doc.get("Version", {})
        view = latest_version.get("Rendition", {}).get("Ansicht", "")
        ext = latest_version.get("Rendition", {}).get("Extension", "")
        filename = f"{doc.get('FileName', '')}.{ext}"
        version = latest_version.get("Nr", "")
        file_id = doc.get("ID", "")
        index_config = self._config["indexes"].get(self._table, {})
        if "section" in index_config:
            path = f"/{index_config['section']}{self._config['files_api']['path']}"
        else:
            path = self._config["files_api"]["path"]
        url = f"{self._config['api_base']}{path}/{file_id}/{version}/{view}"
        return (url, filename)

    def _flat_dict(self, d: Any) -> dict[str, Any]:
        def leaf_reducer(k1: Any, k2: Any) -> Any:
            if k1 is None or k2.lower() in k1.lower():
                return k2
            if k2 == "text":
                return k1
            return f"{k1}_{k2}"

        flat_data = flatten_dict(d, max_flatten_depth=2, reducer=leaf_reducer)
        flat_data = self._clean_dict(flat_data)

        for k in ["person_kontakt", "position", "geschaeft"]:
            if k in flat_data and isinstance(flat_data[k], list):
                flat_data[k] = [self._flat_dict(ik) for ik in flat_data[k]]
            elif k in flat_data and isinstance(flat_data[k], dict):
                flat_data.update(
                    flatten_dict(
                        flat_data[k], max_flatten_depth=2, reducer=leaf_reducer
                    )
                )
                del flat_data[k]

        return flat_data

    def _get_xmlns(self, elem: Any) -> dict[str, Any]:
        dict_namespaces: dict[str, Any] = {}
        ns_dict = self.xmlparser.todict(elem, xml_attribs=True)
        if not isinstance(ns_dict, dict):
            raise ValueError("Expected XML element to be converted to a dictionary")
        elem_dict = flatten_dict(ns_dict)
        for k, v in elem_dict.items():
            if "xmlns" in k and v:
                dict_namespaces[v] = None
        return dict_namespaces

    def _clean_dict(self, records: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
        ns_pattern = re.compile("^.+:")

        def clean_name(key: str) -> str:
            return ns_pattern.sub("", key).lower()

        def convert_value(v: str) -> Any:
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                pass
            if v.lower() == "true":
                return True
            if v.lower() == "false":
                return False
            return v

        clean_rec: dict[str, Any] = {}
        for k, v in records.items():
            if k.startswith("xmlns"):
                continue
            clean_k = clean_name(k)
            if isinstance(v, dict):
                if "nil" in v and "text" in v:
                    if v["nil"] == "true":
                        clean_rec[clean_k] = None
                        continue
                    elif v["nil"] == "false":
                        clean_rec[clean_k] = convert_value(v["text"])
                        continue
                clean_rec[clean_k] = self._clean_dict(v)
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                clean_rec[clean_k] = [self._clean_dict(vi) for vi in v]
            elif isinstance(v, str):
                clean_rec[clean_k] = convert_value(v)
            else:
                clean_rec[clean_k] = v

        return clean_rec
