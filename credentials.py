import os
from dotenv import load_dotenv 

# function to generate sql engine string

def sql_engine_string_generator(qp_host, qp_hgee_user, qp_hgee_pwd, datahub_db): 

    # load the .env file using the dotenv module remove this when running a powershell script to confirue system environment vars
    parent_dir=os.path.dirname(os.getcwd())
    load_dotenv(os.path.join(parent_dir, '.env')) # default is relative local directory 
    DB_HOST = os.getenv(qp_host)
    DB_USER = os.getenv(qp_hgee_user)
    DB_PASS = os.getenv(qp_hgee_pwd)
    print ('Credentials loaded locally')

    # set the sql engine string
    sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(DB_USER,DB_PASS,DB_HOST,datahub_db)
    return sql_engine_string

