import pandas as pd
from sqlalchemy import create_engine
import logging

# local module import
from credentials import get_credentials

# set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a console handler for logging debug output
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

################## SQL database stuff ##############################

# set global conditions for app and computer name
# set up the sql connection string
COMPUTER, SERVER, VIEWER_USER, VIEWER_PASSWORD, EDITOR_USER, EDITOR_PASSWORD, DATABASE, URL_PREFIX = get_credentials(parent_dir)

# set up the engine
sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(EDITOR_USER,EDITOR_PASSWORD,SERVER,DATABASE)
try:
    sql_engine=create_engine(sql_engine_string,pool_pre_ping=True)
except Exception as e:
    error_occur = True
    print(f"An error occurred trying to create db connection: {e}")    

# ----------------------------------
#read the csv file with wmo station data

file_path = r"\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\Passive Samplers\Analysis\gsod_met_data/passives_stations.xlsx"

wmo_station_df = pd.read_excel(
    file_path,
    sheet_name="Geolocations",
    dtype={
        'station_id': str,
        'altsiteid': str
    }
)

# ----------------------------------
# Upload to database
# ----------------------------------
wmo_station_df.to_sql(
    "wmo_stations",
    engine,
    schema="data",     # change if needed
    if_exists="append",  # or "replace" on first load
    index=False,
    method="multi"
)
