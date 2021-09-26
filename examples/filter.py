import swissparlpy as spp
from pprint import pprint

subjects = spp.get_data(
    table="SubjectBusiness",
    BusinessShortNumber="05.057",
    Language="DE"
)

print(f"Total rows: {len(subjects)}")
for subject in subjects:
    pprint(subject)
