import numpy as np
import pandas as pd
from datetime import datetime as dt

italy_site_df=pd.read_excel('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/Data/Passives/data_files/Italy_passives_mercury_monitoring.xlsx',sheet_name='SitesMetadata',index_col=1)
italy_passives_df=pd.read_excel('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/Data/Passives/data_files/Italy_passives_mercury_monitoring.xlsx',sheet_name='PASHgData')

# create a master passives dataframe that will host monthly data
month_series=pd.Series(pd.date_range('2022', '2024', freq='ME'))
passives_monthly_df=pd.DataFrame(index=italy_passives_df['Sitename'].unique(),columns=month_series)

# SITE	id-SITE	YEAR	Sampling time_START	Sampling time_END	SEASONs	Sampling-Frequency	Hg ngm-3


italy_passives_df['Start_Datetime']=pd.to_datetime(italy_passives_df['Start_Datetime']).dt.normalize()	
italy_passives_df['End_Datetime']=pd.to_datetime(italy_passives_df['End_Datetime']).dt.normalize()	

# loop through the site list 
for site in italy_passives_df['Sitename']:
    # print (site)
    sub_df=italy_passives_df.loc[italy_passives_df['Sitename']==site] # produce a sub-df for each site
    # loop through each entry in the sub-df
    date_series=pd.Series()
    concentration_list=[]
    for entry in sub_df.index:
        start_date=sub_df.loc[entry,'Start_Datetime'] # grab the start date
        end_date=sub_df.loc[entry,'End_Datetime'] # grab the end date
        # print (start_date,end_date)
        # print (len(date_series))
        date_series=pd.concat([date_series,pd.Series(pd.date_range(start_date, end_date, freq='D'))]) # create a day-frequency datetime series 
        concentration_list+=[sub_df.loc[entry,'Hg ngm-3']]*len(pd.Series(pd.date_range(start_date, end_date, freq='D'))) # create a copy-filled list of the concentration that matches the date range for each entry
    if site=='Schivenoglia':
        for i,date in enumerate(date_series):
            print (date,concentration_list[i])
    expanded_site_df=pd.DataFrame(concentration_list, index=date_series) # create a dataframe with a daily fequency 
    expanded_site_df.index=pd.to_datetime(expanded_site_df.index) # set the index as a datetime object so it can be averaged
    monthly_averaged_df=expanded_site_df.resample('ME').mean().T # sample the expanded site dataframe monthly and transpose it    
    # print (monthly_averaged_df.iloc[0,:])
    passives_monthly_df.loc[site,monthly_averaged_df.columns]=monthly_averaged_df.iloc[0,:]


# print (passives_monthly_df)

for site in passives_monthly_df.index:
    passives_monthly_df.loc[site,'sitecode']=italy_site_df.loc[site,'Sitecode']
    passives_monthly_df.loc[site,'lat']=italy_site_df.loc[site,'Lat']
    passives_monthly_df.loc[site,'lon']=italy_site_df.loc[site,'Lon']    
    passives_monthly_df.loc[site,'country']='Italy'
    passives_monthly_df.loc[site,'continent']='Europe'

passives_monthly_df.to_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/Data/Passives/data_files/Italy_passives_monthly_average.csv')


