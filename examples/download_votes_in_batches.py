import swissparlpy as spp
import pandas as pd
import os


__location__ = os.path.realpath(os.getcwd())
path = os.path.join(__location__, "voting50")


# download votes of one session and save as pickled DataFrame
def save_votes_of_session(id, path):
    if not os.path.exists(path):
        os.mkdir(path)
    data = spp.get_data("Voting", Language="DE", IdSession=id)
    print(f"{data.count} rows loaded.")
    df = pd.DataFrame(data)
    pickle_path = os.path.join(path, f'{id}.pks')
    df.to_pickle(pickle_path)
    print(f"Saved pickle at {pickle_path}")


# get all session of the 50 legislative period
sessions50 = spp.get_data("Session", Language="DE", LegislativePeriodNumber=50)
sessions50.count

for session in sessions50:
    print(f"Loading session {session['ID']}")
    save_votes_of_session(session['ID'], path)

# Combine to one dataframe
df_voting50 = pd.concat([pd.read_pickle(os.path.join(path, x)) for x in os.listdir(path)])
