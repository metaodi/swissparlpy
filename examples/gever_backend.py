"""
Example of using swissparlpy with the Gever backend

This example demonstrates how to query the Gever
(Geschaeftsverwaltungssystem) APIs of the canton of Zurich (Kantonsrat)
and the city of Zurich (Gemeinderat).
"""

from pprint import pprint, pformat

import swissparlpy as spp
from swissparlpy import GeverBackend
import logging
import argparse

parser = argparse.ArgumentParser(description="Gever backend example")
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()

print(args.verbose)

log = logging.getLogger(__name__)
loglevel = logging.INFO
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    level=loglevel,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

# of --verbose is passed to the script, set the log level to DEBUG
if args.verbose:
    log.setLevel(logging.DEBUG)

# Get the tables of both instances
print("=== Available tables ===")
print(f"Canton of Zurich: {spp.get_tables(backend='gever')}")
print(f"City of Zurich: {spp.get_tables(backend='gever_city_zurich')}")

# Get the variables of a table, they are read from the schema of the API
print("\n=== Variables of 'wahlkreise' (canton of Zurich) ===")
print(spp.get_variables("wahlkreise", backend="gever"))

# Query a table, the table name is case-insensitive
print("\n=== Electoral districts of the canton of Zurich ===")
districts = spp.get_data("Wahlkreise", "inaktiv = false", backend="gever")
print(f"Total: {districts.count}")
for district in districts[:5]:
    print(district["name"])

# Keyword arguments are turned into a query of the API
print("\n=== Search for a member ===")

members = spp.get_data("mitglieder", name="Marti", backend="gever")
print(f"Found {members.count} members")
log.debug(pformat(members[0]))
print(
    members.to_dataframe()[
        ["person_kontakt_vorname", "person_kontakt_name", "funktion", "gremium"]
    ]
)

# Documents get a download URL and a filename
print("\n=== Documents of a meeting ===")
meetings = spp.get_data("sitzungendetail", obj_guid='44a6d9a9ba494fb88923d04d66255b7d', backend="gever")
log.debug(pformat(meetings[0]))
documents = meetings.explode("sitzungsdokumente")
print(documents.head()[["edokument_filename", "edokument_download_url"]])
log.debug(pformat(documents))

# Use the backend directly to build a download URL yourself
print("\n=== Build a download URL ===")
backend = GeverBackend(instance="canton_zurich")
member = backend.get_data("mitglieder", "Name adj Marti and Vorname adj Res")[0]
log.debug(pformat(member))
if "person_kontakt_foto_id" in member:
    print(
        backend.file(
            "mitglieder",
            member["person_kontakt_foto_id"],
            member["person_kontakt_foto_version"][0]["nr"],
            "Original",
        )
    )

# Fields that can occur repeatedly are always lists, which makes the
# records consistent enough to put them into a DataFrame
print("\n=== Business of the city of Zurich as a DataFrame ===")
business = spp.get_glimpse("geschaeft", rows=10, backend="gever_city_zurich")
log.debug(pformat(business[0]))
try:
    df = business.to_dataframe()
    print(df.head())
except ImportError:
    print("Install pandas to convert the result to a DataFrame")


# Use the `explode` method to turn a list field into multiple rows in a DataFrame
# (it returns a DataFrame directly). The name of the list field is enough,
# the full column name 'person_kontakt_behoerdenmandate' works as well.
print("\n=== Explode a list field into multiple rows ===")
krnr = "118/2026"
data = spp.get_data("geschaeft", krnr=krnr, backend="gever")
log.debug(pformat(data[0]))
print(f"\nGeschäft {krnr}:")
print(data.to_dataframe())
print("\nAblaufschritte:")
steps = data.explode("ablaufschritte")
print(steps)
print("\nBeteiligungen:")
beteiligungen = data.explode("beteiligungen")
print(beteiligungen)
