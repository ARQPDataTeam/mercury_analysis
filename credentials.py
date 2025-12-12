import os
from dotenv import load_dotenv 

# function to generate sql engine string

def sql_engine_string_generator(host, user, pwd, database): 

    # load the .env file using the dotenv module remove this when running a powershell script to confirue system environment vars
    parent_dir=os.path.dirname(os.getcwd())
    load_dotenv(os.path.join(parent_dir, '.env')) # default is relative local directory 
    DB_HOST = os.getenv(host)
    DB_USER = os.getenv(user)
    DB_PASS = os.getenv(pwd)
    print ('Credentials loaded locally')

    # set the sql engine string
    sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(DB_USER,DB_PASS,DB_HOST,database)
    return sql_engine_string

