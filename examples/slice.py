import swissparlpy as spp
from pprint import pprint

sessions = spp.get_data(
    table="Session"
)

print(f"Total rows: {len(sessions)}")
for session in sessions[5:10]:
    pprint(session)


# print any element
print('')
pprint(sessions[587])
