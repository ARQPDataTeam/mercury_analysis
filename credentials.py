# this function differentiates host environments

import socket
import logging
import os
import dash
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

def get_credentials(parent_dir):
    env_path = Path(parent_dir).parent / ".env"

    # 1. Try loading .env if it exists
    if env_path.exists():
        load_dotenv(env_path, override=True)
        source = ".env file"
    else:
        source = "OS environment"

    # 2. Read variables from environment (same code path either way)
    COMPUTER   = os.getenv("COMPUTER")
    SERVER = os.getenv("SERVER")
    VIEWER_USER = os.getenv("VIEWER_USER")
    VIEWER_PASSWORD   = os.getenv("VIEWER_PASSWORD")
    MPN_EDITOR_USER = os.getenv("MPN_EDITOR_USER")
    MPN_EDITOR_PASSWORD   = os.getenv("MPN_EDITOR_PASSWORD")
    MPN_DATABASE   = os.getenv("MPN_DATABASE")
    HGEE_EDITOR_USER = os.getenv("HGEE_EDITOR_USER")
    HGEE_EDITOR_PASSWORD   = os.getenv("HGEE_EDITOR_PASSWORD")
    HGEE_DATABASE   = os.getenv("HGEE_DATABASE")

    URL_PREFIX= os.getenv("URL_PREFIX")

    # 3. Validate
    vars_dict = {
        "COMPUTER": COMPUTER,
        "SERVER": SERVER,
        "VIEWER_USER": VIEWER_USER,
        "VIEWER_PASSWORD": VIEWER_PASSWORD,
        "MPN_EDITOR_USER": MPN_EDITOR_USER,
        "MPN_EDITOR_PASSWORD": MPN_EDITOR_PASSWORD,
        "MPN_DATABASE": MPN_DATABASE,
        "HGEE_EDITOR_USER": HGEE_EDITOR_USER,
        "HGEE_EDITOR_PASSWORD": HGEE_EDITOR_PASSWORD,
        "HGEE_DATABASE": HGEE_DATABASE,
        "URL_PREFIX": URL_PREFIX,
    }

    missing = [name for name, value in vars_dict.items() if not value]

    if missing:
        raise ValueError(
            f"Missing environment variables ({source}): {', '.join(missing)}"
        )

    logger.info(f"Credentials loaded from {source}")
    logger.debug(f"DATABASE_SERVER: {SERVER}")
    logger.debug(f"DATABASE_USER: {VIEWER_USER}")
    logger.debug(f"MPN_DATABASE_EDITOR: {MPN_EDITOR_USER}")
    logger.debug(f"MPN_DATABASE_NAME: {MPN_DATABASE}")
    logger.debug(f"HGEE_DATABASE_EDITOR: {HGEE_EDITOR_USER}")
    logger.debug(f"HGEE_DATABASE_NAME: {HGEE_DATABASE}")

    return COMPUTER, SERVER, VIEWER_USER, VIEWER_PASSWORD, MPN_EDITOR_USER, MPN_EDITOR_PASSWORD, MPN_DATABASE, HGEE_EDITOR_USER, HGEE_EDITOR_PASSWORD, HGEE_DATABASE, URL_PREFIX

def get_host_environment(local_computer_name):

    # set a local switch to select host environment
    computer = socket.gethostname().lower()
    if computer == local_computer_name:
        host = 'local'
    elif 'qpdata' in computer:
        host = 'qpdata'
    elif 'sandbox' in computer:
        host = 'sandbox'
    else:
        host = 'fsdh'

    # display host info
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Host environment detected: {host}")

    return host

def create_dash_app(host, path_prefix, url_prefix):
    if host == "fsdh":
        app = dash.Dash(
            __name__,
            requests_pathname_prefix=url_prefix,
            routes_pathname_prefix=url_prefix,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )

    elif host == "qpdata":
        url_prefix = path_prefix
        app = dash.Dash(
            __name__,
            requests_pathname_prefix=url_prefix,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
            eager_loading=True
        )

    elif host == "sandbox":
        url_prefix = path_prefix
        app = dash.Dash(
            __name__,
            requests_pathname_prefix=url_prefix,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
            eager_loading=True
        )

    else:
        app = dash.Dash(
            __name__,
            url_base_pathname=None,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )

    logger.info(f"url_prefix: {url_prefix}")
    return app, app.server
