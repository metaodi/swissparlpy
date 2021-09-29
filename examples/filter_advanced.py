import swissparlpy as spp
from pprint import pprint
import pandas as pd


filter_fn = lambda e: spp.filter.or_(e.FirstName == 'Stefan', e.LastName == 'Seiler')
persons = spp.get_data("Person", filter=filter_fn, Language='DE')

df = pd.DataFrame(persons)
print(df[['FirstName', 'LastName']])
