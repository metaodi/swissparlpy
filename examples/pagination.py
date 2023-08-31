import logging
import swissparlpy
from pprint import pprint


# setup logger to see debug messages from swissparlpy
spp_logger = logging.getLogger("swissparlpy.client")
spp_logger.setLevel(logging.DEBUG)

logging.basicConfig(
    format="%(asctime)s  %(levelname)-10s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)


business = swissparlpy.get_data("Business", Language="DE")
print(f"Count: {business.count})")
print(f"Internal data: {len(business.data)}")

pprint(business)
pprint(business[1])
pprint(business[1001])
