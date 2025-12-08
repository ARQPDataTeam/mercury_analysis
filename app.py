import base64
import io
import dash
from dash import Dash, html, dcc, Input, Output, State, callback, dash_table 
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging
import socket
import os

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s"
)

logger = logging.getLogger(__name__)

# set a local switch to select host environment
computer = socket.gethostname().lower()
if computer == 'wontn74902':
    host = 'local'
elif 'qpdata' in computer:
    host = 'qpdata'
else:
    host = 'fsdh'

# display host info
logging.basicConfig(level=logging.INFO)
logger.info(f"Host environment detected: {computer}")

# initialize the app based on host
if host == 'fsdh':
    url_prefix = "/app/dma_loader/"
    app = dash.Dash(__name__,  
                    requests_pathname_prefix=url_prefix,
                    routes_pathname_prefix=url_prefix,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True            
                    )
    server = app.server
elif host == 'qpdata':
    url_prefix = "/dash/"
    app = dash.Dash(__name__, 
                    requests_pathname_prefix=url_prefix,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True,
                    eager_loading=True
                    )
    server = app.server
    
else:
    url_prefix = "/app/dma_loader/"
    app = dash.Dash(__name__, 
                    url_base_pathname=url_prefix,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True
                    ) 

# set up the sql connection string
if host == 'fsdh':
    # Load OS environment variables
    DB_HOST = os.getenv('DATAHUB_PSQL_SERVER')
    DB_USER = os.getenv('DATAHUB_PSQL_USER')
    DB_PASS = os.getenv('DATAHUB_PSQL_PASSWORD')

else:
    # Load variables from .env into environment
    load_dotenv()
    DB_HOST = os.getenv('QP_SERVER')
    DB_USER = os.getenv('QP_VIEWER_USER')
    DB_PASS = os.getenv('QP_VIEWER_PASSWORD')


# set up the engine
sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(DB_USER,DB_PASS,DB_HOST,'borden')
sql_engine=create_engine(sql_engine_string,pool_pre_ping=True)


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
                    "and insert it into the database automatically"],
                        style={"color": "#555"},
                    ),
                    style={
                        "width": "100%",
                        "height": "150px",
                        "lineHeight": "60px",
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
                html.Div(id="output-msg"),
            ],
        ),
    ],
)

@app.callback(
    Output("output-msg", "children"),
    Input("upload-csv", "contents"),
    State("upload-csv", "filename")
)

def handle_csv_upload(contents, filename):

    if contents is None:
        return ""

    try:
        # -----------------------------------
        # Decode Base64
        # -----------------------------------
        content_type, content_string = contents.split(",")
        raw_bytes = base64.b64decode(content_string)

        # -----------------------------------
        # Try multiple encodings (UTF-8, cp1252, latin-1)
        # -----------------------------------
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
            return f"❌ ERROR: Unable to decode file '{filename}'. Unsupported character encoding."

        # Read CSV into DataFrame
        df = pd.read_csv(io.StringIO(text), skiprows=[0,1,2,4])

    except Exception as e:
        return f"❌ ERROR while reading CSV '{filename}': {str(e)}"

    try:
        # check for column names containing 'Unit' and remove them
        df = df.drop(columns=[col for col in df.columns if "unit" in col.lower()])

        # drop any unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        # rename columns to match database schema
        df.columns = ['num','pos','smpnm','crt_dt','proc_dt','amnt','conc_amt','extr_type','state','cal_file','meth_file','pk_ht','cell','hg','conc','dil_wt','fin_vol','cal_fac','dil_fac','stat','grp','rem']

        # convert date columns to datetime where current format is YYYY-MM-DD-HH-MM-SS

        df['crt_dt'] = pd.to_datetime(df['crt_dt'], errors='coerce', format="%Y-%m-%d-%H-%M-%S")
        df['proc_dt'] = pd.to_datetime(df['proc_dt'], errors='coerce', format="%Y-%m-%d-%H-%M-%S")  

        # create a samplerID and kit ID based on the SampleName only in rows where smpnm starts with 'ECCC' otherwise set to NaN
        df['smpid'] = df['smpnm'].where(df['smpnm'].str.startswith('ECCC')).str.slice(0,8)
        df['kitid'] = df['smpnm'].where(df['smpnm'].str.startswith('ECCC')).str.slice(8,15)

        # create a sample type based on the SampleName
        def determine_sample_type(smpnm):
            if pd.isna(smpnm):
                return None
            elif smpnm.startswith('ECCC'):
                return 'sample'
            elif 'bb' in smpnm:
                return 'blank'
            elif smpnm.endswith('ng'):
                return 'standard'
            elif smpnm.startswith('na2co3'):
                return 'flush'
            else:
                return 'Other'
        
        df['smptyp'] = df['smpnm'].apply(determine_sample_type)

        # check for errors in date conversion
        if df['crt_dt'].isnull().any() or df['proc_dt'].isnull().any():
            return f"❌ ERROR: Date conversion failed for some rows in file '{filename}'. Please check date formats."
        
        # check for typos in the sampler name:
        # df['smpid'] should start with 'ECCC' for rows where smptyp is 'sample'
        typo_rows = df[(df['smptyp'] == 'sample') & (~df['smpid'].str.startswith('ECCC', na=False))]
        if not typo_rows.empty:
            return f"❌ ERROR: Potential typos found in sampler names in file '{filename}'. Please check the following rows:\n{typo_rows[['smpnm', 'smpid']].to_string(index=False)}"
        
        # df['kitid'] should look like 'EC-####' for rows where smptyp is 'sample'
        typo_rows_kit = df[(df['smptyp'] == 'sample') & (~df['kitid'].str.match(r'EC-\d{4}', na=False))]
        if not typo_rows_kit.empty:
            return f"❌ ERROR: Potential typos found in kit IDs in file '{filename}'. Please check the following rows:\n{typo_rows_kit[['smpnm', 'kitid']].to_string(index=False)}"
        

        # If all checks pass, return the processed DataFrame
        return df

    except Exception as e:
        return f"❌ ERROR during processing: {str(e)}"

    # -----------------------------------
    # SQL UPLOAD with error handling
    # -----------------------------------
    # try:
    #     df.to_sql(
    #         "my_table",
    #         sql_engine,
    #         if_exists="append",
    #         index=False
    #     )

    # except SQLAlchemyError as e:
    #     return f"❌ SQL ERROR inserting into database: {str(e.__cause__ or e)}"

    # except Exception as e:
    #     return f"❌ Unexpected SQL error: {str(e)}"

    # -----------------------------------
    # SUCCESS
    # -----------------------------------
    return (
        f"✅ File '{filename}' processed and uploaded successfully "
        f"(encoding={used_encoding}, rows={len(df)})."
    )

# Run the app
if __name__ == "__main__":
    if host == 'qpdata':
        app.run_server(debug=False)
    else:
        app.run(debug=False,port=8080)
    sql_engine.dispose()
