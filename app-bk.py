import base64
import io
import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, callback, dash_table 
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError,OperationalError
import logging
import socket
import os
import textwrap

# local module import
from credentials import get_host_environment, get_credentials, create_dash_app



# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s"
)

logger = logging.getLogger(__name__)

# set up path details
parent_dir = os.getcwd()
logger.info(f"parent path: {parent_dir}")
path_prefix = '/' + os.path.basename(os.path.normpath(parent_dir)) + '/'
logger.info(f"path_prefix: {path_prefix}") 

# set global conditions for app and computer name
# set up the sql connection string
COMPUTER, SERVER, VIEWER_USER, VIEWER_PASSWORD, EDITOR_USER, EDITOR_PASSWORD, DATABASE, URL_PREFIX = get_credentials(parent_dir)

# determine host environment
host = get_host_environment(COMPUTER)

# set up the hgpas engine
hgpas_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(EDITOR_USER,EDITOR_PASSWORD,SERVER,DATABASE)

# set up the dcp engine
dcp_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(  VIEWER_USER,VIEWER_PASSWORD,SERVER,'dcp')

# create sql engine function
def sql_connection(engine_string):
    try:
        sql_engine=create_engine(engine_string,pool_pre_ping=True)
    except Exception as e:
        error_occur = True
        logger.info(f"An error occurred trying to create db connection: {e}")    

    try:
        with sql_engine.connect() as connection:
            logger.info("Connection successful!")
    except OperationalError as e:
        logger.info(f"Connection failed: {e}")
    return sql_engine

# create the sql engines
hgpas_engine = sql_connection(hgpas_engine_string)
dcp_engine = sql_connection(dcp_engine_string)

#------------------------------
# UPLOAD CALLBACK   
#------------------------------
def handle_csv_upload(contents, clear_clicks, filename):
    # Determine which component triggered the callback
    trigger = ctx.triggered_id

    # -----------------------------
    # CLEAR BUTTON LOGIC
    # -----------------------------
    if trigger == "clear-btn":
        return None, ""  # reset upload and clear message

    # -----------------------------
    # UPLOAD LOGIC
    # -----------------------------
    if contents is None:
        msg = "No file uploaded."
        logger.info(msg)
        return None, msg

    try:
        # Decode Base64
        content_type, content_string = contents.split(",")
        raw_bytes = base64.b64decode(content_string)

        # Try multiple encodings
        encodings = ["utf-8", "cp1252", "latin1"]
        text = None
        for enc in encodings:
            try:
                text = raw_bytes.decode(enc)
                used_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            msg =  f"ERROR: Unable to decode file \n'{filename}'\n"
            logger.info(msg)
            return None, msg
        
        # grab the header line
        lines = text.splitlines()

        header_row = next(
            (i for i, line in enumerate(lines[:25])
            if line.split(",")[:3] == ["Nr","Pos","SampleName"]),
            None
        )

        logger.info(f"Header row found at line: {header_row}")

        if header_row is None:
            msg =  f"ERROR: Could not find header row in \n'{filename}'\n"
            logger.info(msg)
            return None, msg
        
        # Read CSV while skipping specific rows
        df = pd.read_csv(io.StringIO(text), skiprows=header_row)

        msg =  f"Reading in \n'{filename}'\n"
        logger.info(msg)

    except Exception as e:
        msg =  f"ERROR while reading CSV \n'{filename}'\n: {str(e)}"
        logger.info(msg)
        return None, msg

    # -----------------------------
    # PROCESSING & VALIDATION
    # -----------------------------
    try:
        df = df.dropna(how='all')  # drop completely empty rows
        df = df.drop(columns=[c for c in df.columns if "unit" in c.lower()])
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        column_list = ['num','pos','samplename','crt_dt','proc_dt','amnt','conc_amt',
                       'extr_type','state','cal_file','meth_file','pk_ht','cell',
                       'hg','conc','dil_wt','fin_vol','cal_fac','dil_fac',
                       'stat','grp','rem']

        if len(df.columns) != len(column_list):
            msg =  (f"ERROR: Unexpected number of columns in \n'{filename}'\n "
                   f"Expected {len(column_list)}, found {len(df.columns)}.")
            logger.info(msg)
            return None, msg

        df.columns = column_list

    except Exception as e:
        msg =  f"Unable to resolve columns \n'{filename}'\n: {str(e)}"
        logger.info(msg)
        return None, msg

    missing_mask = df['crt_dt'].isna() | df['proc_dt'].isna()

    if missing_mask.any():
        bad_rows = df.loc[missing_mask, ['samplename', 'crt_dt', 'proc_dt']]

        msg = (
            f"ERROR: Missing or invalid dates in '{filename}'.\n"
            "Affected rows:\n"
            f"{bad_rows.to_string(index=True)}"
        )

        logger.info(msg)
        return None, msg    
    
    # convert date columns
    try:
        df['crt_dt'] = pd.to_datetime(df['crt_dt'], errors='raise',
                                      format="%Y-%m-%d-%H-%M-%S")
        df['proc_dt'] = pd.to_datetime(df['proc_dt'], errors='raise',
                                       format="%Y-%m-%d-%H-%M-%S")
        df['datetime'] = df['proc_dt']
    except Exception as e:
        msg =  f"ERROR converting dates in \n'{filename}'\n: {str(e)}"
        logger.info(msg)
        return None, msg
    
    # check for duplicate entries in the file based on proc_dt
    dup_in_file = df.loc[df['proc_dt'].duplicated(keep=False), 'proc_dt']

    if not dup_in_file.empty:
        # Format timestamps nicely
        dup_list = dup_in_file.dt.strftime('%Y-%m-%d %H:%M:%S').unique().tolist()[:5]
        msg =  (f"ERROR: Duplicate proc_dt values found in the uploaded file \n'{filename}'\n"
               f"There may be more duplicates, showing up to 5 of them: \n"
            f"{dup_list}")
        logger.info(msg)
        return None, msg    


    # validate sample IDs
    mask_invalid = (
        df['samplename'].str.startswith('ECCC', na=False)
        & ~df['samplename'].str.match(r'^ECCC\d{4}EC-\d{4}', na=False)
    )
    if mask_invalid.any():
        bad_values = df.loc[mask_invalid, 'samplename'].unique()
        bad_list = "\n".join(map(str, bad_values))
        msg = (
            "ERROR: Invalid ECCC sample ID format in samplename:\n"
            f"{bad_list}"
        )
        logger.info(msg)
        return None, msg

    # extract sample and kit IDs
    try:
        df['samplerid'] = df['samplename'].where(df['samplename'].str.startswith('ECCC')).str.slice(0,8)
        df['kitid'] = df['samplename'].where(df['samplename'].str.startswith('ECCC')).str.slice(8,15)
    except Exception as e:
        msg =  f"Unable to parse sample and kit IDs in \n'{filename}'\n: {str(e)}"
        logger.info(msg)
        return None, msg

    # combine kitid and samplerid by kitid_samplerid into a full sampleid to match the tracking table
    df['sampleid'] = df['kitid'] + '_' + df['samplerid']


    # determine sample type
    def determine_sample_type(s):
        if pd.isna(s): return None
        if s.startswith('ECCC'): return 'sample'
        if 'bb' in s: return 'blank'
        if s.endswith('ng'): return 'standard'
        if s.startswith('na2co3'): return 'flush'
        return 'other'

    df['sampletype'] = df['samplename'].apply(determine_sample_type)

    msg =  f"Uploaded file \n'{filename}'\n read successfully. Processing. (encoding={used_encoding}, rows={len(df)})."
    logger.info(msg)

    #------------------------------
    # check for duplicates in the database
    #------------------------------
    existing = pd.read_sql("SELECT proc_dt FROM mpn__tgm_v0", hgpas_engine)

    # Make uploaded dataframe timestamps timezone-aware (UTC)
    df['proc_dt'] = df['proc_dt'].dt.tz_localize('UTC')

    # Ensure existing DB timestamps are also UTC (they already are, but this is safe)
    existing['proc_dt'] = pd.to_datetime(existing['proc_dt'], utc=True)

    # Identify new rows to insert
    df_new = df[~df['proc_dt'].isin(existing['proc_dt'])]

    logger.info(f"Rows in file: {len(df)}, New rows to add: {len(df_new)}")

    # report duplicates if any
    num_duplicates = len(df) - len(df_new)
    if num_duplicates > 0:
        msg =  (f"WARNING: {num_duplicates} duplicate rows found in \n'{filename}'\n "
               f"based on 'proc_dt' and will be skipped.")
        logger.info(msg)
    
    # -----------------------------
    # SQL UPLOAD
    # -----------------------------
    try:
        if not df_new.empty:
            df_new.to_sql("mpn__tgm_v0", hgpas_engine, if_exists="append", index=False)
            
        # Success message only if insert completes without error
        # create the full message first
        msg = (f"✅ File \n'{filename}'\n processed successfully. "
                    f"(encoding={used_encoding}, rows in file={len(df)}, new rows added={len(df_new)}).")

        # wrap it to 80 characters per line
        logger.info(msg)
        return None, msg

    except SQLAlchemyError as e:
        # Only show concise DB error
        core_msg = str(getattr(e, "orig", e)).splitlines()[0]
        msg =  f"SQL ERROR inserting into database: {core_msg}"
        logger.info(msg)
        return None, msg

#-----------------------------
# RETRIEVE TRACKING INFORMATION FUNCTION
# -----------------------------
def retrieve_tracking_info(engine):
    tracking_df = pd.read_sql(
        """
        SELECT sampleid, sample_start, sample_end, siteid
        FROM dcp_passive_sample_tracking
        """,
        engine
    )
    tracking_df["sample_start"] = pd.to_datetime(
        tracking_df["sample_start"], utc=True, errors="coerce"
    )
    tracking_df["sample_end"] = pd.to_datetime(
        tracking_df["sample_end"], utc=True, errors="coerce"
    )
    return tracking_df

#-----------------------------
# RETRIEVE WMO STATIONS FUNCTION
# -----------------------------
def retrieve_wmo_stations(engine):
    wmo_df = pd.read_sql(
        """
        SELECT siteid, wmo_id
        FROM stations
        """,
        engine
    )
    return wmo_df

#-----------------------------
# PULL WMO MET DATA FUNCTION
# -----------------------------
def pull_wmo_met_data(wmo_ids, start_date, end_date):
    base_url = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access"
    url = f"{base_url}/2026/{station_code}.csv"


    
# initialize the app based on host, specify the url_prefix if needed
app, server = create_dash_app(host, path_prefix, URL_PREFIX)

app.layout = html.Div(
    style={
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",   # center content horizontally
        "gap": "20px",
        "padding": "20px",
        "backgroundColor": "#f0f2f5",
        "minHeight": "100vh",
    },
    children=[
        # ----------------------------------------------------
        # Banner Card
        # ----------------------------------------------------
        html.Div(
            style={
                "width": "100%",
                "maxWidth": "800px",
                "backgroundImage": f"url('{app.get_asset_url('Mauna_Loa_banner.jpg')}')",
                "backgroundSize": "cover",
                "backgroundPosition": "center",
                "padding": "40px 20px",
                "borderRadius": "12px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.2)",
                "textAlign": "center",
                "display": "flex",
                "flexDirection": "column",
                "gap": "10px",
            },
            children=[
                html.H1(
                    "MERCURY PASSIVES DMA DATA UPLOADER",
                    style={
                        "color": "black",
                        "textShadow": "2px 2px 8px #333",
                        "margin": 0,
                    },
                ),
            ],
        ),

        # ----------------------------------------------------
        # Upload Card
        # ----------------------------------------------------
        html.Div(
            style={
                "width": "100%",
                "maxWidth": "600px",
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                "display": "flex",
                "flexDirection": "column",
                "gap": "15px",
                "alignItems": "center",
            },
            children=[
                dcc.Upload(
                    id="upload-csv",
                    children=html.Div(
                        ["Drag/drop your CSV file here. The app will process the data "
                    "and insert it into the database automatically",
                        html.Br(),
                        html.Br(),
                        "This tool will only process one file at a time."
                    ],
                        style={"color": "#555"},
                    ),
                    style={
                        "width": "100%",
                        "height": "150px",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "8px",
                        "textAlign": "center",
                        "backgroundColor": "#f8f9fa",
                        "cursor": "pointer",
                        "transition": "0.2s",  # smooth hover effect
                    },
                    multiple=False,
                ),
                dcc.Loading(
                    id="loading-msg",
                    type="circle",
                    children=html.Div(
                        id="output-msg",
                        style={
                            "width": "100%",
                            "whiteSpace": "pre-wrap",    # keeps line breaks (\n) and wraps long lines
                            "overflowWrap": "break-word",
                            "textAlign": "left",         # optional, easier to read for long messages
                            "color": "#333"
                        }
                    )
                ),
                html.Button(
                    "Clear",
                    id="clear-btn",
                    n_clicks=0,
                    style={
                        "marginTop": "10px",
                        "padding": "8px 20px",
                        "borderRadius": "6px",
                        "border": "none",
                        "backgroundColor": "#d9534f",
                        "color": "white",
                        "fontWeight": "bold",
                        "cursor": "pointer"
                    },
                ),
            ],
        ),
    ],
)

@app.callback(
    Output("upload-csv", "contents"),
    Output("output-msg", "children"),
    Input("upload-csv", "contents"),
    Input("clear-btn", "n_clicks"),
    State("upload-csv", "filename"),
    prevent_initial_call=True
)


# Run the app
if __name__ == "__main__":
    if host == 'qpdata':
        app.run_server(debug=False)
    else:
        app.run(debug=False,port=8080)
    hgpas_engine.dispose()
    dcp_engine.dispose()