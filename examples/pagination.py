import swissparlpy
from pprint import pprint

business = swissparlpy.get_data("Business", Language="DE")

print(f"Count: {business.count})")
print(f"Internal data: {len(business.data)}")

pprint(business)
pprint(business[1])
pprint(business[1001])
