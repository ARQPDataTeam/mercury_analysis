"""
Download hourly NOAA ISD meteorological data for a station.

Workflow:
1. User provides an altsiteid
2. Query SQL table wmo_stations to retrieve station_id
3. station_id is the concatenated USAF + WBAN (11 chars with leading zeros)
4. Build NOAA ISD request URL using:
    - station_id
    - start datetime
    - end datetime
5. Download data

Requirements:
    pip install pandas sqlalchemy pyodbc requests
"""

import pandas as pd
import requests
from sqlalchemy import create_engine, text

# -------------------------------------------------------
# USER INPUTS
# -------------------------------------------------------

altsiteid = "SITE_001"

start_datetime = "2024-01-01T00:00:00"
end_datetime   = "2024-01-31T23:59:59"

# -------------------------------------------------------
# SQL CONNECTION
# -------------------------------------------------------
# Example for SQL Server using Windows Authentication

server = "YOUR_SERVER"
database = "YOUR_DATABASE"

connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(connection_string)

# -------------------------------------------------------
# LOOK UP station_id FROM wmo_stations
# -------------------------------------------------------

query = text("""
SELECT station_id
FROM wmo_stations
WHERE altsiteid = :altsiteid
""")

with engine.connect() as conn:
    result = conn.execute(query, {"altsiteid": altsiteid}).fetchone()

if result is None:
    raise ValueError(f"No station found for altsiteid = {altsiteid}")

# Preserve leading zeros
station_id = str(result[0]).zfill(11)

print(f"Station ID: {station_id}")

# -------------------------------------------------------
# BUILD NOAA ISD URL
# -------------------------------------------------------
# NOAA ISD access endpoint
#
# Documentation:
# https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation
#
# dataset = global-hourly

base_url = "https://www.ncei.noaa.gov/access/services/data/v1"

params = {
    "dataset": "global-hourly",
    "stations": station_id,
    "startDate": start_datetime,
    "endDate": end_datetime,
    "format": "json",
    "units": "metric"
}

# Build readable query URL
request_url = requests.Request(
    "GET",
    base_url,
    params=params
).prepare().url

print("\nNOAA Request URL:")
print(request_url)

# -------------------------------------------------------
# DOWNLOAD DATA
# -------------------------------------------------------

response = requests.get(base_url, params=params)

response.raise_for_status()

data = response.json()

# Convert to dataframe
df = pd.DataFrame(data)

print("\nRows downloaded:", len(df))

# Preview
print(df.head())