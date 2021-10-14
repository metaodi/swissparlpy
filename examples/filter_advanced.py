import swissparlpy as spp
import pandas as pd


def name_filter(e):
    return spp.filter.or_(
        e.FirstName == 'Stefan',
        e.LastName == 'Seiler'
    )


persons = spp.get_data("Person", filter=name_filter, Language='DE')

df = pd.DataFrame(persons)
print(df[['FirstName', 'LastName']])
