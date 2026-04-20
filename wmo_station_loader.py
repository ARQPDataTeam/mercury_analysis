import pandas as pd
from sqlalchemy import create_engine

# ----------------------------------
# DB engine
# ----------------------------------
engine = create_engine("postgresql://dcp_hgpassive:qEikLwFyXP3@qpdatadb.cmc.ec.gc.ca/mercury_passive")

# ----------------------------------
# Read ISD history
# ----------------------------------
wmo_station_df = pd.read_csv(
    "isd-history.csv",
    dtype={
        "USAF": str,
        "WBAN": str,
        "BEGIN": str,
        "END": str,
    }
)

# ----------------------------------
# Drop unwanted columns
# ----------------------------------
wmo_station_df = wmo_station_df.drop(
    columns=["STATE", "ICAO", "ELEV (M)"],
    errors="ignore"
)

# ----------------------------------
# Zero-pad USAF and WBAN
# ----------------------------------
wmo_station_df["USAF"] = wmo_station_df["USAF"].str.zfill(6)
wmo_station_df["WBAN"] = wmo_station_df["WBAN"].str.zfill(5)

# ----------------------------------
# Create WMO station ID
# ----------------------------------
wmo_station_df["wmo_station_id"] = (
    wmo_station_df["USAF"] + wmo_station_df["WBAN"]
)

# Drop source ID columns
wmo_station_df = wmo_station_df.drop(columns=["USAF", "WBAN"])

# ----------------------------------
# Convert BEGIN / END to datetime
# ----------------------------------
wmo_station_df["BEGIN"] = pd.to_datetime(
    wmo_station_df["BEGIN"], format="%Y%m%d", errors="coerce"
)
wmo_station_df["END"] = pd.to_datetime(
    wmo_station_df["END"], format="%Y%m%d", errors="coerce"
)

# ----------------------------------
# Drop stations ending before 2000
# ----------------------------------
wmo_station_df = wmo_station_df[
    wmo_station_df["END"] >= pd.Timestamp("2000-01-01")
]

# Drop BEGIN / END
wmo_station_df = wmo_station_df.drop(columns=["BEGIN", "END"])

# ----------------------------------
# Rename columns
# ----------------------------------
wmo_station_df.columns = [
    "station_name",
    "country_code",
    "latdecd",
    "londecd",
    "elevation",
    "wmo_station_id",
]

# ----------------------------------
# Reorder columns
# ----------------------------------
wmo_station_df = wmo_station_df[
    [
        "wmo_station_id",
        "station_name",
        "country_code",
        "latdecd",
        "londecd",
        "elevation",
    ]
]

# ----------------------------------
# Add country name
# ----------------------------------
countries_df = pd.read_csv("iso_2digit_alpha_country_codes.csv")

wmo_station_df = wmo_station_df.merge(
    countries_df[["country_code", "country"]],
    on="country_code",
    how="left"
)

missing_country = wmo_station_df[wmo_station_df["country"].isna()].copy()

missing_country["country_code_count"] = missing_country["country_code"].map(
    missing_country["country_code"].value_counts()
)

print(
    missing_country
    .sort_values(["country_code_count", "country_code"], ascending=[False, True])
    [["station_name", "country_code", "country_code_count"]]
)
# Drop country_code
wmo_station_df = wmo_station_df.drop(columns=["country_code"])

# ----------------------------------
# Final column order
# ----------------------------------
wmo_station_df = wmo_station_df[
    [
        "wmo_station_id",
        "station_name",
        "country",
        "latdecd",
        "londecd",
        "elevation",
    ]
]


# ----------------------------------
# Upload to database
# ----------------------------------
# wmo_station_df.to_sql(
#     "wmo_stations",
#     engine,
#     schema="data",     # change if needed
#     if_exists="append",  # or "replace" on first load
#     index=False,
#     method="multi"
# )
