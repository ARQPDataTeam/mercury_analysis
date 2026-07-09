import numpy as np
import pandas as pd
import requests
import sqlalchemy
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy.exc import SQLAlchemyError,OperationalError
from sqlalchemy.dialects.postgresql import insert
import os
import logging
import contextvars
import uuid

# local imports
from credentials import get_host_environment, get_credentials

# set up logging
# define a context variable to hold the request ID

request_id = contextvars.ContextVar("request_id", default="global")

# define a logging filter to add the request ID to log records
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id.get()
        return True
    
    # clear existing handlers to prevent duplicate logs if this script is run multiple times in the same session
logging.getLogger().handlers.clear()

# set up file and stream handlers with the request ID filter
file_handler = logging.FileHandler("logs/met_processing.log")
stream_handler = logging.StreamHandler()

# add the request ID filter to both handlers
file_handler.addFilter(RequestIDFilter())
stream_handler.addFilter(RequestIDFilter())

# configure logging with both handlers and a format that includes the request ID
logging.basicConfig(
level=logging.INFO,
format='%(asctime)s - %(levelname)s - %(request_id)s - %(name)s - %(message)s',
handlers=[file_handler, stream_handler]

)

# set a unique request ID for this run of the script
request_id.set(str(uuid.uuid4())[:8])  # short ID for logging 

logger = logging.getLogger(__name__)

# set up path details
parent_dir = os.getcwd()
logger.info(f"parent path: {parent_dir}")
path_prefix = '/' + os.path.basename(os.path.normpath(parent_dir)) + '/'

# set global conditions for app and computer name
# set up the sql connection string
COMPUTER, SERVER, VIEWER_USER, VIEWER_PASSWORD, EDITOR_USER, EDITOR_PASSWORD, DATABASE, URL_PREFIX = get_credentials(parent_dir)

# determine host environment
host = get_host_environment(COMPUTER)

# set up the engine
sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(EDITOR_USER, EDITOR_PASSWORD, SERVER, DATABASE)
logger.info(f"SQL Engine String: {sql_engine_string}")
try:
    engine=create_engine(sql_engine_string,pool_pre_ping=True)
except Exception as e:
    error_occur = True
    logger.error(f"An error occurred trying to create db connection: {e}")    

try:
    with engine.connect() as connection:
        logger.info("Connection successful!")
except OperationalError as e:
    logger.error(f"Connection failed: {e}")

# -------------------------------------------------------
# Read Excel file
# -------------------------------------------------------

excel_file = (
    r"\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects"
    r"\OnGoing\Mercury\Passive Samplers\Analysis"
    r"\gsod_met_data\passives_stations.xlsx"
)

stations_df = pd.read_excel(
    excel_file,
    dtype=str,
    keep_default_na=False
)

# -------------------------------------------------------
# Query metadata.stations
# -------------------------------------------------------

query = text("""
SELECT
    description,
    alternate_siteid,
    wmo_station_id
FROM metadata.stations
             where alternate_siteid is not null
""")

sql_df = pd.read_sql(query, engine)


# -------------------------------------------------------
# Clean names before merge
# -------------------------------------------------------

stations_df["site_name"] = (
    stations_df["site_name"]
    .astype(str)
    .str.strip()
)

sql_df["description"] = (
    sql_df["description"]
    .astype(str)
    .str.strip()
)

# -------------------------------------------------------
# Merge Excel -> SQL
# -------------------------------------------------------

merged_df = stations_df.merge(
    sql_df,
    left_on="site_name",
    right_on="description",
    how="left"
)

# save merged_df for review
merged_output_file = "merged_stations.xlsx"
merged_df.to_excel(merged_output_file, index=False)

# -------------------------------------------------------
# Find stations with missing WMO IDs
# -------------------------------------------------------

missing_wmo_df = merged_df[
    merged_df["wmo_station_id"].isna()
]

# -------------------------------------------------------
# Report
# -------------------------------------------------------

logger.info(
    f"Found {len(missing_wmo_df)} stations "
    f"with missing WMO station IDs"
)

# print missing_wmo_df columns for review
logger.info(f"Columns in missing_wmo_df: {missing_wmo_df.columns.tolist()}")

output_file = "missing_wmo_stations.csv"

# reduce the columns to just site_name and description for easier review
missing_wmo_df = missing_wmo_df[["altsiteid", "site_name","station_id","alternate_siteid", "description", "wmo_station_id"]]
missing_wmo_df.to_csv(output_file, index=False)