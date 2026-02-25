"""
Example of using both backends in the same application

This example demonstrates how to use both OData and OpenParlData
backends in the same application for comparison.
"""

import swissparlpy as spp

print("=== Comparing backends ===\n")

# Get tables from both backends
print("Tables from OData backend:")
odata_tables = spp.get_tables(backend="odata")
print(f"  Count: {len(odata_tables)}")
print(f"  Sample: {odata_tables[:3]}")

print("\nTables from OpenParlData backend:")
try:
    opd_tables = spp.get_tables(backend="openparldata")
    print(f"  Count: {len(opd_tables)}")
    print(f"  Sample: {opd_tables[:3]}")
except Exception as e:
    print(f"  Error: {e}")

# Using SwissParlClient directly with specific backends
print("\n=== Using SwissParlClient directly ===")

# OData backend
from swissparlpy.backends import ODataBackend

odata_backend = ODataBackend()
odata_client = spp.SwissParlClient(backend=odata_backend)
print(f"\nOData client tables count: {len(odata_client.get_tables())}")

# OpenParlData backend
from swissparlpy.backends import OpenParlDataBackend

try:
    opd_backend = OpenParlDataBackend()
    opd_client = spp.SwissParlClient(backend=opd_backend)
    print(f"OpenParlData client tables count: {len(opd_client.get_tables())}")
except Exception as e:
    print(f"OpenParlData error: {e}")

print("\n=== Backends support different query methods ===")
print("OData backend supports callable filters (lambda functions)")
print("OpenParlData backend supports REST query parameters")
print("\nBoth backends implement the same interface:")
print("  - get_tables()")
print("  - get_variables(table)")
print("  - get_data(table, filter, **kwargs)")
print("  - get_glimpse(table, rows)")
