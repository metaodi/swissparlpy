import swissparlpy as spp
from pprint import pprint

subjects = spp.get_data(
    table="Voting",
)

print(f"Total rows: {len(subjects)}")
for subject in subjects[5:10]:
    pprint(subject)
