import numpy as np
import pandas as pd
import matplotlib as mp
from matplotlib import pyplot as plt
import matplotlib.dates as md
from datetime import datetime as dt
import seaborn as sns

path ='\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/processed_data/all_dbdata.csv'
continent_df=pd.read_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/iso_2digit_alpha_country_codes.csv',index_col=1)

all_hg_data_df=pd.read_csv(path) # read in the full dataset into one big df
all_hg_data_df.drop(columns=["project","WMO_region","matrix","method"],inplace=True) # drop the unecessary columns
# species_hg_data_df=all_hg_data_df.loc[all_hg_data_df.loc[:,'species'].str.contains('GEM'),:] # look at a particular species
species_hg_data_df=all_hg_data_df # for now grab everything
column_list=["start_time","end_time","project","country","WMO_region","station","matrix","method","species","quantity","Lat-deg","Lon-deg"] # just a column list for info

station_lookup_df=species_hg_data_df.loc[:,['station','country','species','Lat-deg','Lon-deg']].drop_duplicates('station') # create a lookup df for station location info
station_lookup_df.set_index(station_lookup_df['station'], inplace=True)
station_list=all_hg_data_df["station"].unique() # grab a unique list of station names

# create a master actives dataframe that will host monthly data
month_series=pd.Series(pd.date_range('1995', '2024', freq='m')) # set up a monthly data array
actives_monthly_df=pd.DataFrame(index=station_list,columns=month_series) # set up a blank df with station as index

for station in station_list:
    print (station)
    sub_df=species_hg_data_df.loc[species_hg_data_df.loc[:,'station']==station,['start_time','end_time','quantity']] # grab just datetime info and concentration
    sub_df['start_time']=pd.to_datetime(sub_df['start_time']) # set start and end time columns as datetime objects
    sub_df['end_time']=pd.to_datetime(sub_df['end_time'])
    # find the midpoint of the time stamps
    sub_df['mid_time']=[(pd.to_datetime((sub_df.loc[index_item,'start_time'].value + sub_df.loc[index_item,'end_time'].value)/2.0)) for index_item in sub_df.index]
    sub_df.set_index('mid_time',inplace=True) # set the index to the midpoint
    sub_df.drop(columns=['start_time','end_time'],inplace=True) # drop the other datetime columns
    monthly_averaged_df=sub_df.resample('ME').mean().T # do a monthly mean and transpose
    actives_monthly_df.loc[station,monthly_averaged_df.columns]=monthly_averaged_df.iloc[0,:] # transfer the mothnly transpose to the monthly dataframe

# loop thru and set the country for each station
for station in actives_monthly_df.index:
    actives_monthly_df.loc[station,'country']=station_lookup_df.loc[station,'country']
    actives_monthly_df.loc[station,'species']=station_lookup_df.loc[station,'species']

actives_monthly_df.index.name='Station'
actives_monthly_df.to_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/processed_data/actives_monthly_average.csv')

actives_monthly_df=pd.read_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/processed_data/actives_monthly_average.csv', index_col=0)

# test_df=actives_monthly_df.loc[actives_monthly_df.loc[:,'species'].str.contains('GEM'),:] # look at a particular species
# print (test_df)

