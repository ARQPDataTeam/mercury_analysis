import numpy as np
import pandas as pd
import matplotlib as mp
from matplotlib import pyplot as plt
import matplotlib.dates as md
from datetime import datetime as dt
import seaborn as sns

"""
# grab the passives data from the excel sheet
passives_df=pd.read_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/Katrina Macsween/ECCC_PAS_2024-10-17.csv',skiprows=114, usecols=['SiteName', 'Country', 'Site_code', 'StartDate, YYYY-MM-DD',
       'StartTime HH:MM:SS (24hr)', 'EndDate YYYY-MM-DD', 'EndTime, hh:mm:ss',
       'Year YYYY', 'Quarter', 'MetAdj_GEM ng/m^3', 'GEM, ng m/m^3', 'Flag'])
# print (passives_df.columns)

# country_df=passives_df.groupby('Site_code')#.[['Country',''Site_code'']]
# print (country_df)

geolocation_df=pd.read_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/Katrina Macsween/ECCC_PAS_2024-10-17.csv',index_col=0,skiprows=27,nrows=6,usecols=['* SITE IDENTIFICATION','AF04', 'AF07', 'AF10', 'AF11', 'AF12', 'AS21', 'AS28', 'AS27', 'EE03',
       'GR03', 'GR04', 'GR12', 'GR16', 'WE12', 'WE13', 'WE14', 'WE30', 'WE37',
       'WE41', 'WE44', 'AP1', 'AP2', 'AP4', 'HG2', 'MN16', 'HG3', 'MD99',
       'CA75', 'MO46', 'AK96', 'HG4', 'HG5', 'HG6', 'FS4', 'NCP1', 'NCP2',
       'NCP3', 'NCP4', 'NCP5', 'NCP6', 'NCP7', 'NCP8', 'NCP9', 'HG13', 'HG18',
       'HG21', 'HG19', 'HG22', 'HG20', 'HG23', 'HG24', 'CB2', 'CB3', 'CB1',
       'CB4', 'HG27', 'HG28', 'HG29', 'HG30', 'HG32', 'HG34', 'HG35', 'HG36',
       'HG37', 'HG38', 'CB5', 'EU1', 'EU2', 'EU3', 'EU4', 'EU5', 'EU6', 'EU7',
       'EU8', 'EU9', 'EU10', 'EU11', 'EU12', 'EU13', 'EU14', 'EU15', 'EU16',
       'EU17', 'EU18', 'EU19', 'EU20', 'EU21', 'EU22', 'EU23', 'EU24', 'EU25',
       'HG40'])
# print (geolocation_df.index)

# lat_list=geolocation_df.loc['*SITE LATITUDE',:].tolist()
# lon_list=geolocation_df.loc['*SITE LONGITUDE',:].tolist()

# grab the unique site lite
site_list=passives_df['Site_code'].unique()
# print (site_list)

# create a master passives dataframe that will host monthly data
month_series=pd.Series(pd.date_range('2018', '2024', freq='m'))
passives_monthly_df=pd.DataFrame(index=site_list,columns=month_series)

passives_df['Start_Datetime_1']=passives_df['StartDate, YYYY-MM-DD']+' '+passives_df['StartTime HH:MM:SS (24hr)']
passives_df['Start_Datetime']=pd.to_datetime(passives_df['Start_Datetime_1'],dayfirst=True)
passives_df['End_Datetime_1']=passives_df['EndDate YYYY-MM-DD']+' '+passives_df['EndTime, hh:mm:ss']
passives_df['End_Datetime']=pd.to_datetime(passives_df['End_Datetime_1'],dayfirst=True)

# print (passives_df['End_Datetime'])
site_label=[]

# loop through the site list 
for site in site_list:
    print (site)
    sub_df=passives_df.loc[passives_df['Site_code']==site] # produce a sub-df for each site
    # loop through each entry in the sub-df
    date_series=pd.Series()
    concentration_list=[]
    for entry in sub_df.index:
        start_date=sub_df.loc[entry,'Start_Datetime'] # grab the start date
        end_date=sub_df.loc[entry,'End_Datetime'] # grab the end date
        date_series=pd.concat([date_series,pd.Series(pd.date_range(start_date, end_date, freq='D'))]) # create a day-frequency datetime series 
        # check to see if the data are met corrected
        if np.isnan(sub_df.loc[entry,'MetAdj_GEM ng/m^3']):
            concentration_list+=[sub_df.loc[entry,'GEM, ng m/m^3']]*len(pd.Series(pd.date_range(start_date, end_date, freq='D'))) # create a copy-filled list of the non-met corrected concentration that matches the date range for each entry
            site_label.append(site+'*')
        else:
            site_label.append(site)
            concentration_list+=[sub_df.loc[entry,'MetAdj_GEM ng/m^3']]*len(pd.Series(pd.date_range(start_date, end_date, freq='D'))) # create a copy-filled list of the concentration that matches the date range for each entry
    expanded_site_df=pd.DataFrame(concentration_list, index=date_series) # create a dataframe with a daily fequency 
    expanded_site_df.index=pd.to_datetime(expanded_site_df.index) # set the index as a datetime object so it can be averaged
    monthly_averaged_df=expanded_site_df.resample('ME').mean().T # sample the expanded site dataframe monthly and transpose it    
    # print (monthly_averaged_df.iloc[0,:])
    passives_monthly_df.loc[site,monthly_averaged_df.columns]=monthly_averaged_df.iloc[0,:]
country_df=passives_df.groupby('Site_code')[['Country','SiteName']].first()
# print (country_df)

for site in passives_monthly_df.index:
    passives_monthly_df.loc[site,'lat']=geolocation_df.loc['*SITE LATITUDE',site]
    passives_monthly_df.loc[site,'lon']=geolocation_df.loc['*SITE LONGITUDE',site]
    passives_monthly_df.loc[site,'country']=country_df.loc[site,'Country']
    passives_monthly_df.loc[site,'site_name']=country_df.loc[site,'SiteName']


site_label=['AF04', 'AF07', 'AF10*', 'AF11*', 'AF12', 'AK96*', 'AP1*', 'AP2', 'AP4*', 'AS21', 'AS27', 'AS28*', 'CA75', 'CB1', 'CB2*', 'CB3', 'CB4*', 'CB5*', 'EE03', 'EU1*', 'EU10*', 'EU11*', 'EU12', 'EU13*', 'EU14', 'EU15*', 'EU16*', 'EU17', 'EU18', 'EU19*', 'EU2', 'EU20', 'EU21*', 'EU22', 'EU23', 'EU24', 'EU25*', 'EU3', 'EU4', 'EU5', 'EU6*', 'EU7', 'EU8*', 'EU9', 'FS4*', 'GR03*', 'GR04', 'GR12', 'GR16', 'HG13', 'HG18*', 'HG19*', 'HG2*', 'HG20*', 'HG21*', 'HG22*', 'HG23*', 'HG24', 'HG27', 'HG28', 'HG29', 'HG3*', 'HG30*', 'HG32*', 'HG34*', 'HG35*', 'HG36*', 'HG37*', 'HG38', 'HG4', 'HG40*', 'HG5', 'HG6*', 'MD99', 'MN16', 'MO46', 'NCP1*', 'NCP2', 'NCP3', 'NCP4*', 'NCP6*', 'NCP5*', 'NCP9', 'NCP7', 'NCP8', 'WE12', 'WE13', 'WE14', 'WE30', 'WE37', 'WE41', 'WE44']
print (site_label)
# add the site label list which identifies which stations didn't use met corrected
passives_monthly_df['site_label']=site_label


passives_monthly_df.to_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/Katrina Macsween/passives_monthly_average.csv')
"""
passives_monthly_df=pd.read_csv('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/Data/Passives/data_files/global_passives_mercury_monthly_average.csv', index_col=0)

# set a continent sub-index
passives_monthly_df.set_index(['Continent',passives_monthly_df.index],inplace=True)
passives_monthly_df=passives_monthly_df.sort_index(axis=0)
# print (passives_monthly_df)
# set up 6 sub_dataframes for the continents
continent_list=['Africa','Asia','Europe','North America','Pacific','South America']
for continent in continent_list:
    passives_monthly_continent_df=passives_monthly_df.loc[(continent),:]
    passives_for_plotting_df=passives_monthly_continent_df.drop(columns=['Sitecode','Country','Lat','Lon'])

    # print (passives_monthly_df)
    if continent=='Africa - Kenyase':
        fig, ax=plt.subplots(figsize=(6,6))
        ax.set_position([.2, .1, .7, 1])
        v_max=40
    else:
        fig, ax=plt.subplots(figsize=(6,6))
        v_max=15
    sns.heatmap(passives_for_plotting_df,cmap='jet',cbar=True, cbar_kws={'label': 'Concentration (ng/m3)'},ax=ax,vmin=0, vmax=v_max)
    ax.set_title('Passive Mercury Concentrations: '+continent)
    ax.set_ylabel('Station Name')
    ax.set_yticklabels(ax.get_yticklabels(),rotation=0)
    ax.set_xlabel('Date')
    xlabels=[label.get_text()[:7] for label in ax.get_xticklabels()]
    ax.set_xticklabels(xlabels,rotation=90)
    plt.tight_layout()
    plt.savefig('\\\econm3hwvfsp008.ncr.int.ec.gc.ca/arqp_data/Projects/OnGoing/Mercury/HGEE-Minamata/Results and Plots/monthly_passives_average_'+continent+'.png')

# index=['a','b','c']
# columns=['d','e','f','h']
# data=[[1,2,np.nan,3],[4,5,6,10],[7,np.nan,8,9]]
# test_df=pd.DataFrame(data,index=index,columns=columns)
# ax=sns.heatmap(test_df)
# plt.show()


    

