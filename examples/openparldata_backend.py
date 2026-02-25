"""
Example of using swissparlpy with OpenParlData backend

This example demonstrates how to use the OpenParlData.ch API
as an alternative backend to the default OData API.
"""

import swissparlpy as spp

# Get tables/resources using OpenParlData backend
print("=== Getting available tables from OpenParlData ===")
tables = spp.get_tables(backend="openparldata")
print(f"Available tables: {tables[:5]}...")  # Show first 5

# Get variables/columns for a specific table
print("\n=== Getting variables for a table ===")
if tables:
    table_name = tables[0]
    variables = spp.get_variables(table_name, backend="openparldata")
    print(f"Variables in '{table_name}': {variables}")

# Get a glimpse of data
print("\n=== Getting a glimpse of data ===")
if tables:
    table_name = tables[0]
    glimpse = spp.get_glimpse(table_name, rows=3, backend="openparldata")
    print(f"First 3 rows of '{table_name}':")
    for row in glimpse:
        print(row)

# Get data with filters
print("\n=== Getting filtered data ===")
# Note: The actual filter syntax depends on the OpenParlData API implementation
# This is a placeholder example
if tables:
    table_name = tables[0]
    data = spp.get_data(table_name, backend="openparldata")
    print(f"Total records in '{table_name}': {data.count}")
    if data.count > 0:
        print(f"First record: {data[0]}")
