"""Instance configuration for the Gever backend

The configuration describes the two known Gever (Geschaeftsverwaltungssystem)
instances of the canton and the city of Zurich. It is the swissparlpy
counterpart of the ``config.yml`` of goifer (https://github.com/metaodi/goifer).

Table (index) names are lowercase, the paths of the API are kept as-is.
"""

from typing import Any

# Namespaces used by the CMI CDWS API for search and schema responses
DEFAULT_NAMESPACES = {
    "sd": "http://www.cmiag.ch/cdws/searchDetailResponse",
    "xsd": "http://www.w3.org/2001/XMLSchema",
}

INSTANCES: dict[str, dict[str, Any]] = {
    "canton_zurich": {
        "api_base": "https://parlzhcdws.cmicloud.ch",
        "files_api": {"path": "/cdws/Files"},
        "indexes": {
            "behoerden": {"section": "parlzh2", "path": "/cdws/Index/BEHOERDEN"},
            "sitzungendetail": {
                "section": "parlzh3",
                "path": "/cdws/Index/SITZUNGENDETAIL",
            },
            "geschaeft": {"section": "parlzh5", "path": "/cdws/Index/GESCHAEFT"},
            "mitglieder": {"section": "parlzh2", "path": "/cdws/Index/MITGLIEDER"},
            "parteien": {"section": "parlzh2", "path": "/cdws/Index/PARTEIEN"},
            "wahlkreise": {"section": "parlzh2", "path": "/cdws/Index/WAHLKREISE"},
            "direktion": {
                "section": "parlzh5",
                "path": "/cdws/Index/GESCHAEFT_DIREKTION",
            },
            "geschaeftsart": {
                "section": "parlzh5",
                "path": "/cdws/Index/GESCHAEFT_GESCHAEFTSART",
            },
            "gremiumtyp": {"section": "parlzh3", "path": "/cdws/Index/GREMIUMTYP"},
            "krversand": {"section": "parlzh1", "path": "/cdws/Index/KRVERSAND"},
            "ablaufschritte": {
                "section": "parlzh5",
                "path": "/cdws/Index/ABLAUFSCHRITTE",
            },
        },
    },
    "city_zurich": {
        "api_base": "https://www.gemeinderat-zuerich.ch",
        "files_api": {"path": "/api/files"},
        "indexes": {
            "geschaeft": {"path": "/api/geschaeft"},
            "dokument": {"path": "/api/dokument"},
            "departement": {"path": "/api/departement"},
            "gremiumsuebersicht": {"path": "/api/gremiumsuebersicht"},
            "gremium": {"path": "/api/gremium"},
            "gremiumstyp": {"path": "/api/gremiumstyp"},
            "geschaeftsart": {"path": "/api/geschaeftsart"},
            "partei": {"path": "/api/partei"},
            "pendentbei": {"path": "/api/pendentbei"},
            "geschaeftvorstoesser": {"path": "/api/geschaeftsvorstoesser"},
            "kontakt": {"path": "/api/kontakt"},
            "behoerdenmandat": {"path": "/api/behoerdenmandat"},
            "wohnkreis": {"path": "/api/wohnkreis"},
            "wahlkreis": {"path": "/api/wahlkreis"},
            "ablaufschritt": {"path": "/api/ablaufschritt"},
            "referendum": {"path": "/api/referendum"},
            "sitzung": {"path": "/api/sitzung"},
            "ratspost": {"path": "/api/ratspost"},
        },
    },
}
