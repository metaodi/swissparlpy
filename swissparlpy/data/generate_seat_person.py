import pandas as pd
from datetime import datetime
import swissparlpy as spp
import os

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)

seats = spp.get_data("SeatOrganisationNr", filter="Language eq 'DE'").to_dataframe()
columns = [
    "SeatNumber",
    "PersonNumber",
    "PersonIdCode",
    "FirstName",
    "LastName",
]
subset_seats = seats[columns]
subset_seats["ValidFrom"] = pd.to_datetime(datetime(2025, 12, 1))
subset_seats["ValidUntil"] = None
subset_seats.to_csv(os.path.join(__location__, "seat_person_nr.csv"), index=False)
