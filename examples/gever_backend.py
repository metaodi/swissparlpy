"""
Example of using swissparlpy with the Gever backend

This example demonstrates how to query the Gever
(Geschaeftsverwaltungssystem) APIs of the canton of Zurich (Kantonsrat)
and the city of Zurich (Gemeinderat).
"""

import swissparlpy as spp
from swissparlpy import GeverBackend

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

# Fields that can occur repeatedly are always lists, which makes the
# records consistent enough to put them into a DataFrame
print("\n=== Business of the city of Zurich as a DataFrame ===")
business = spp.get_glimpse("geschaeft", rows=10, backend="gever_city_zurich")
try:
    df = business.to_dataframe()
    print(df.head())
except ImportError:
    print("Install pandas to convert the result to a DataFrame")

# Documents get a download URL and a filename
print("\n=== Documents of a meeting ===")
meetings = spp.get_data("sitzungendetail", backend="gever")
document = meetings[0].get("dokument", {}).get("edokument", {})
if document.get("download_url"):
    print(f"{document['filename']}: {document['download_url']}")

# Use the backend directly to build a download URL yourself
print("\n=== Build a download URL ===")
backend = GeverBackend(instance="canton_zurich")
member = backend.get_data("mitglieder", "Name adj Marti and Vorname adj Res")[0]
if "foto_id" in member:
    print(
        backend.file(
            "mitglieder",
            member["foto_id"],
            member["foto_version"]["nr"],
            "Original",
        )
    )
