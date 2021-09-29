import swissparlpy as spp
from pprint import pprint
import pandas as pd

subjects = spp.get_data(
    table="SubjectBusiness",
    filter="BusinessShortNumber eq '05.057'"
)

df = pd.DataFrame(subjects)
print(df)
