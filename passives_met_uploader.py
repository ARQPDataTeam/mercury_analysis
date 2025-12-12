import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import glob
import pandas as pd
from sqlalchemy import create_engine, text, update, Table, MetaData, func, insert
from sqlalchemy.exc import SQLAlchemyError
import logging

# local module import
from credentials import sql_engine_string_generator

# grab all the files
# path = r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data\daily_averages"
# all_files = glob.glob(path + "/*.csv")

# # set up an empty list of dfs
# dataframes = []

# for file in all_files:
#     print(f"Processing file: {file}")
#     df = pd.read_csv(file, usecols=['STATION','DATE','LATITUDE','LONGITUDE','NAME','TEMP','WDSP'])
#     dataframes.append(df)


# # concatenate all dataframes
# combined_df = pd.concat(dataframes, ignore_index=True)

# # basic cleaning
# combined_df['DATE'] = pd.to_datetime(combined_df['DATE'], errors='coerce')
# combined_df = combined_df.dropna(subset=['DATE'])
# combined_df['TEMP'] = pd.to_numeric(combined_df['TEMP'], errors='coerce')
# combined_df['WDSP'] = pd.to_numeric(combined_df['WDSP'], errors='coerce')

# new_column_names = {
#     'STATION': 'station_id',
#     'DATE': 'datetime',
#     'LATITUDE': 'station_latdecd',
#     'LONGITUDE': 'station_londecd',
#     'NAME': 'station_description',
#     'TEMP': 'tempav',
#     'WDSP': 'ws_smean'
# }

# # rename columns
# combined_df = combined_df.rename(columns=new_column_names)

# # reorder columns
# combined_df = combined_df[['station_id', 'station_description', 'datetime', 'station_latdecd', 'station_londecd', 'tempav', 'ws_smean']]

# # load the passives_stations csv to get mapping
# nearest_stations_df = pd.read_csv(r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data\nearest_stations.csv", usecols=['site_name', 'site_latdecd','site_londecd', 'station_id'])
# # merge to get passives_site_name
# df_merged = pd.merge(combined_df, nearest_stations_df[['site_name', 'site_latdecd','site_londecd', 'station_id']], on='station_id', how='left')

# print("Final dataframe columns:", df_merged.columns.tolist())

# # reorder columns to have site_name first
# df_merged = df_merged[['site_name','datetime','site_latdecd','site_londecd','station_id','station_description','station_latdecd','station_londecd','tempav','ws_smean']]

# # print(df_merged.head())

# # save to csv
# output_folder = r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data"
# df_merged.to_csv(output_folder + r"\passives_met_data_combined.csv", index=False)
# print("Combined data saved to CSV.")


path = r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data\passives_met_data.csv"

# read the combined csv
df = pd.read_csv(path)

print (df.columns)

# # read the excel file passives_stations to get mapping for siteid
# sites_df = pd.read_excel(r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data\passives_stations.xlsx", usecols=['siteid', 'passives_site_name'])

# # insert siteid by merging
# df = pd.merge(df, sites_df, left_on='site_description', right_on='passives_site_name', how='left')

# # drop passives_site_name column
# df = df.drop(columns=['passives_site_name'])

# # reorder columns to have siteid first
# df = df[['siteid','site_description','datetime','site_latdecd','site_londecd','station_id','station_description','station_latdecd','station_londecd','tempav','ws_smean']]

# # print out site_description values without matching siteid
# missing_siteids = df[df['siteid'].isna()]['site_description'].unique()

# if len(missing_siteids) > 0:
#     print("The following site_description values do not have matching siteid:")
#     for desc in missing_siteids:
#         print(f"- {desc}")
# else:
#     print("All site_description values have matching siteid.")

# # save the df with siteid to csv
# output_folder = r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data"
# df.to_csv(output_folder + r"\passives_met_data.csv", index=False)

# connect to database
engine_string = sql_engine_string_generator('QP_SERVER','QP_EDIT','QP_EDIT_PASSWORD','mercury_passive')
engine = create_engine(engine_string)

# insert data into database
try:
    with engine.begin() as connection:   # <-- auto-commit
        # set timezone to GMT
        connection.execute(text("SET TIME ZONE 'GMT';"))
        # insert data
        df.to_sql('passives_met', con=connection, if_exists='append', index=False)
        print(f"Data inserted successfully.")
except SQLAlchemyError as e:
    logging.error(f"Error inserting data: {e}")

