import pandas as pd
import glob

# this program grabs the des template files that were prepared for minimata
# simplifies the flags to valid or invalid
# standardizes the missing values
# grab the US header information
header_filename = 'C:/Users/firanskib/OneDrive - EC-EC/mercury/US_MDN_Files/US_MDN_header_information.xlsx'

mercury_metatada_header_df=pd.read_excel(header_filename, sheet_name='Template', nrows=108, header=None, index_col=0)
# print (mercury_metatada_header_df.columns)

# grab the network sites
sites_filename='C:/Users/firanskib/OneDrive - EC-EC/mercury/US_MDN_Files/MDN.csv'
mercury_sites_df=pd.read_csv(sites_filename, index_col=0)
# print (mercury_sites_df)

# grab the full data from the csv file for all sites
all_sites_data_filename='C:/Users/firanskib/OneDrive - EC-EC/mercury/US_MDN_Files/MDN-ALL-W-i.csv'
all_sites_data_df=pd.read_csv(all_sites_data_filename, index_col=0)


# loop through the list of sites, insert the relevant metadata entries that are specific to each site
# then grab the data from the all-sites report for each site by index into a dataframe subset
# concatenate the metadata header and the subset
# save the file
for index_item in mercury_sites_df.index:
    print (index_item)
    mercury_metatada_header_df.loc['*SITE IDENTIFICATION',1]=mercury_sites_df.loc[index_item,'siteName']
    mercury_metatada_header_df.loc['*SITE COUNTRY',1]='USA'
    mercury_metatada_header_df.loc['*SITE LATITUDE',1]=mercury_sites_df.loc[index_item,'latitude']
    mercury_metatada_header_df.loc['*SITE LONGITUDE',1]=mercury_sites_df.loc[index_item,'longitude']
    if mercury_sites_df.loc[index_item,'siteClass']=='I':
        mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Isolated (<10 persons per square Km)'
    elif mercury_sites_df.loc[index_item,'siteClass']=='R':
        mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Rural (10 - 99 persons per square Km)'
    elif mercury_sites_df.loc[index_item,'siteClass']=='S':
        mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Suburban (100 - 399 persons per square Km)'
    elif mercury_sites_df.loc[index_item,'siteClass']=='U':
        mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Urban (>=400 persons per square Km)'
    elif mercury_sites_df.loc[index_item,'siteClass']=='P':
        mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Research/Provisional (NA)'
    else:
        pass
    mercury_metatada_header_df.loc['*ELEVATION OF THE SITE',1]=mercury_sites_df.loc[index_item,'elevation']
    mercury_metatada_header_df.loc['*ELEVATION UNIT',1]='METERS'
    mercury_metatada_header_df.loc['*MONITORING PERIOD START (YYYY-MM-DD)',1]=mercury_sites_df.loc[index_item,'startDate']
    mercury_metatada_header_df.loc['*MONITORING PERIOD END (YYYY-MM-DD)',1]=mercury_sites_df.loc[index_item,'stopDate']
    if mercury_sites_df.loc[index_item,'status']=='A':
        print ('active')
        mercury_metatada_header_df.loc['*ONGOING MONITORING',1]='YES'
        mercury_metatada_header_df.loc['*FILE NAME',1]='MDN_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_'+mercury_sites_df.loc[index_item,'startDate'].split('-')[0]+'_'+'2024.csv'
    elif mercury_sites_df.loc[index_item,'status']=='I':
        print ('inactive')
        mercury_metatada_header_df.loc['*ONGOING MONITORING',1]='NO'
        try:
            mercury_sites_df.loc[index_item,'startDate'].split('-')
            try:
                mercury_sites_df.loc[index_item,'stopDate'].split('-')
                mercury_metatada_header_df.loc['*FILE NAME',1]='MDN_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_'+mercury_sites_df.loc[index_item,'startDate'].split('-')[0]+'_'+mercury_sites_df.loc[index_item,'stopDate'].split('-')[0]+'.csv'
            except:
                mercury_metatada_header_df.loc['*FILE NAME',1]='MDN_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_'+mercury_sites_df.loc[index_item,'startDate'].split('-')[0]+'_NA.csv'
        except:
            mercury_metatada_header_df.loc['*FILE NAME',1]='MDN_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_NA_'+mercury_sites_df.loc[index_item,'stopDate'].split('-')[0]+'.csv'
    mercury_metatada_header_df.loc['*MONITORING MATRIX',1]='Precipitation'
    mercury_metatada_header_df.loc['*TIME ZONE',1]='UTC+0:00'

    # set the output filename
    MDN_minimata_filename=mercury_metatada_header_df.loc['*FILE NAME',1].replace(' ','')
    
    print (mercury_metatada_header_df)
    # reindex the dataframe
    mercury_metatada_header_output_df=mercury_metatada_header_df.reset_index() 
    # print (mercury_metatada_header_output_df)

    # slice the all-sites dataframe by site ID
    if index_item in all_sites_data_df.index:
        site_data_df=all_sites_data_df.loc[index_item]
    else:
        print ('site ',index_item, ' not found')
        continue
    # print (site_data_df)

    # concat the metadata with the site data
    site_data_df=pd.concat([pd.DataFrame([site_data_df.columns], columns=site_data_df.columns),site_data_df], ignore_index=True)
    site_data_df.set_axis(range(site_data_df.shape[1]), axis=1)
    site_output_df=pd.concat([mercury_metatada_header_output_df,site_data_df])
    # print (site_output_df)

    # output to file
    site_output_df.to_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/US_MDN_Files/'+MDN_minimata_filename,header=False, index=False)

    



 






# file_list=glob.glob('C:/Users/firanskib/OneDrive - EC-EC/mercury/Minimata Submission Files/SPM10*')
# for filename in file_list:
#     print (filename)
#     csv_filename=filename.replace('xlsx', 'csv')
#     print (csv_filename)
#     # grab the mercury data
#     mercury_metatada_header_df=pd.read_excel(filename, sheet_name='Template', nrows=105, header=None)
#     # print (mercury_metatada_header_df.tail())
#     mercury_df=pd.read_excel(filename, sheet_name='Template', skiprows=105)
#     print (mercury_df.columns)

#     # set date and time to datetime columns
#     # print (pd.to_datetime(mercury_df['Time start: local time'],format='%H:%M:%S').dt.time)
#     mercury_df['local_start_datetime']=pd.to_datetime(mercury_df['Date start: local time'].astype(str)+ " " + mercury_df['Time start: local time'].astype(str))
#     mercury_df['local_end_datetime']=pd.to_datetime(mercury_df['Date end: local time'].astype(str)+ " " + mercury_df['Time end: local time'].astype(str))
#     mercury_df['utc_start_datetime']=pd.to_datetime(mercury_df['Date start: UTC'].astype(str)+ " " + mercury_df['Time start: UTC'].astype(str))
#     mercury_df['utc_end_datetime']=pd.to_datetime(mercury_df['Date end: UTC'].astype(str)+ " " + mercury_df['Time end: UTC'].astype(str))
#     mercury_df.drop(columns=['Date start: local time','Time start: local time','Date end: local time','Time end: local time','Date start: UTC','Time start: UTC','Date end: UTC','Time end: UTC'], inplace=True)
#     # replace V2, V4, V7 with V0 - not bothering with oddball valid flags
#     mercury_df.loc[mercury_df.loc[:,'Mercury GEM Flag'].isin(['V2', 'V4','V7']), 'Mercury GEM Flag']='V0'
#     mercury_df.loc[mercury_df.loc[:,'Mercury GOM Flag'].isin(['V2', 'V4','V7']), 'Mercury GOM Flag']='V0'
#     mercury_df.loc[mercury_df.loc[:,'PCM10 Flag'].isin(['V2', 'V4','V7']), 'PCM10 Flag']='V0'
#     # replace -99.9 with -999
#     mercury_df.loc[mercury_df.loc[:,'Mercury GEM']==-99.9,'Mercury GEM']=-999
#     mercury_df.loc[mercury_df.loc[:,'Mercury GOM']==-99.9,'Mercury GOM']=-999
#     mercury_df.loc[mercury_df.loc[:,'PCM10']==-99.9,'PCM10']=-999
#     # test_df=mercury_df.loc[mercury_df.loc[:,'Mercury Flag'].isin(['V2', 'V4','V7']), 'Mercury Flag']
#     # print (test_df)
#     mercury_df=mercury_df.reindex(columns=['local_start_datetime','local_end_datetime','utc_start_datetime','utc_end_datetime','Mercury GEM','Mercury GEM Flag', 'Mercury GOM',	'Mercury GOM Flag',	'PCM10',	'PCM10 Flag'])
#     mercury_df=pd.concat([pd.DataFrame([mercury_df.columns], columns=mercury_df.columns),mercury_df], ignore_index=True)
#     mercury_df.set_axis(range(mercury_df.shape[1]), axis=1)
#     mercury_df=pd.concat([mercury_metatada_header_df,mercury_df])
#     mercury_df.to_csv(csv_filename, index=False, header=False)

