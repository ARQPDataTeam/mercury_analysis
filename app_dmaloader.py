# This is a Dash application for uploading DMA data and 
# processing data postgresql tables, with a focus on user-friendly design 
# and robust error handling. 
# The app includes two main sections: one for uploading CSV files related to DMA data, 
# and another for running the V1 table upload process. 
# Both sections feature clear instructions, loading indicators, 
# and styled message boxes for output. 
# The app is designed to be responsive and visually appealing, with a banner image and consistent styling throughout.
import dash
from dash import Dash, html, dcc, Input, Output, State
from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError,OperationalError
import logging
import contextvars
import os
import uuid
import textwrap
import re
import base64
import io
import socket


# local module import
from credentials import get_host_environment, get_credentials, create_dash_app
from v0_table_utils import handle_csv_upload
from v1_table_utils import v1_table_upload


# define a context variable to hold the request ID
request_id = contextvars.ContextVar("request_id", default="global")

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id.get()
        return True

# clear existing handlers
logging.getLogger().handlers.clear()

# create handlers
file_handler = logging.FileHandler("processing.log")
stream_handler = logging.StreamHandler()

# attach filter to handlers
file_handler.addFilter(RequestIDFilter())
stream_handler.addFilter(RequestIDFilter())

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(request_id)s - %(name)s - %(message)s',
    handlers=[file_handler, stream_handler]
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

# set up the engine
sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(EDITOR_USER,EDITOR_PASSWORD,SERVER,DATABASE)
try:
    sql_engine=create_engine(sql_engine_string,pool_pre_ping=True)
except Exception as e:
    error_occur = True
    print(f"An error occurred trying to create db connection: {e}")    

try:
    with sql_engine.connect() as connection:
        print("Connection successful!")
except OperationalError as e:
    print(f"Connection failed: {e}")

# # test the v1 table upload function
# v1_df, diagnostics_df = v1_table_upload(sql_engine)

# logger.info(v1_df.head())
# logger.info(diagnostics_df.head())


# initialize the app based on host, specify the url_prefix if needed
app, server = create_dash_app(host, path_prefix, URL_PREFIX)

# Reusable message box style for dashed boxes
MESSAGE_BOX_STYLE = {
    "width": "100%",
    "minWidth": "400px",
    "minHeight": "150px",
    "borderWidth": "2px",
    "borderStyle": "dashed",
    "borderRadius": "8px",
    "padding": "15px",
    "backgroundColor": "#f8f9fa",
    "overflowY": "auto",
    "display": "flex",
    "alignItems": "flex-start",
}

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
                html.H3(
                    "DMA File Processing",
                    style={"margin": 0, "color": "#333"}
                ),
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
                        style=MESSAGE_BOX_STYLE,   # 👈 reusable style here
                        children=html.Div(
                            id="output-msg",
                            children="Output Message",  # default placeholder text
                            style={
                                "whiteSpace": "pre-wrap",
                                "overflowWrap": "break-word",
                                "textAlign": "left",
                                "color": "#888",          # lighter gray for placeholder
                                "fontStyle": "italic",
                                "width": "100%"
                            }
                        )
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
        # ----------------------------------------------------
        # V1 Processing Card
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

                html.H3(
                    "V1 Table Processing",
                    style={"margin": 0, "color": "#333"}
                ),

                html.Button(
                    "Run V1 Table Upload",
                    id="run-v1-btn",
                    n_clicks=0,
                    style={
                        "padding": "8px 20px",
                        "borderRadius": "6px",
                        "border": "none",
                        "backgroundColor": "#0275d8",
                        "color": "white",
                        "fontWeight": "bold",
                        "cursor": "pointer"
                    },
                ),
                dcc.Loading(
                    id="v1-loading",
                    type="circle",
                    children=html.Div(
                        style=MESSAGE_BOX_STYLE,  # reuse here too
                        children=html.Div(
                            id="v1-output-msg",
                            children="Output Message",  # default placeholder text
                            style={
                                "whiteSpace": "pre-wrap",
                                "overflowWrap": "break-word",
                                "textAlign": "left",
                                "color": "#888",          # lighter gray for placeholder
                                "fontStyle": "italic",
                                "width": "100%"
                            }
                        )
                    )
                ),
                html.Button(
                    "Clear",
                    id="v1-clear-btn",
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

# ----------------------------------------------------
# Callbacks
# ----------------------------------------------------

# v0 upload callback - handles both file upload and clear button, determines action based on triggered_id
@app.callback(
    Output("output-msg", "children"),
    Input("upload-csv", "contents"),
    Input("clear-btn", "n_clicks"),
    State("upload-csv", "filename"),
    prevent_initial_call=True
)

# callback function to handle both file upload and clear button for v0 table
def v0_upload_callback(contents, clear_clicks, filename):
    request_id.set(str(uuid.uuid4())[:8])  # short ID for logging
    logger.info("Starting v0 callback")
    triggered_id = ctx.triggered_id

    # Clear button
    if triggered_id == "clear-btn":
        return ""

    # Upload button
    if triggered_id == "upload-csv" and contents is not None:
        # handle_csv_upload should **return only the message**
        msg = handle_csv_upload(contents, filename, sql_engine)
        return msg

    return dash.no_update

# v1 upload callback - handles both run and clear buttons, determines action based on triggered_id
@app.callback(
    Output("v1-output-msg", "children"),
    Input("run-v1-btn", "n_clicks"),
    Input("v1-clear-btn", "n_clicks"),
    prevent_initial_call=True
)

# callback function to handle both run and clear buttons for v1 table processing
def v1_upload_callback(run_clicks, clear_clicks):
    request_id.set(str(uuid.uuid4())[:8])  # short ID for logging
    logger.info("Starting v1 callback")
    triggered_id = ctx.triggered_id
    if triggered_id == "v1-clear-btn":
        return ""

    if triggered_id == "run-v1-btn":
        try:
            logger.info("Starting V1 table upload from Dash card...")
            msg,diagnostics_df = v1_table_upload(sql_engine)

            problem_kits = diagnostics_df[diagnostics_df["issues"].notna()]

            if not problem_kits.empty:
                msg.append("")
                msg.append("Kits with issues detected:")
                msg.append(problem_kits.to_string(index=False))
            else:
                msg.append("")
                msg.append("No kit validation issues detected.")

            return "\n".join(msg)

        except Exception as e:
            logger.error(f"V1 upload failed: {str(e)}")
            return f"Error running V1 upload:\n{str(e)}"

    raise dash.exceptions.PreventUpdate
      
# Run the app
if __name__ == "__main__":
    if host == 'qpdata':
        app.run_server(debug=False)
    else:
        app.run(debug=False,port=8080)
    sql_engine.dispose()

