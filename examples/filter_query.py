import swissparlpy as spp
import pandas as pd

persons = spp.get_data(
    table="Person",
    filter="(FirstName eq 'Stefan' or LastName eq 'Seiler') and Language eq 'DE'"
)

df = pd.DataFrame(persons)
print(df[['FirstName', 'LastName']])
