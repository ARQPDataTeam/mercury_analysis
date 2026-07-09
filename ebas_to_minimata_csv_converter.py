import pandas as pd
import glob
import os
from pathlib import Path

# this program grabs the ebas files
# maps out the metadata to the minamata header format
# fills in missing information such as country

# grab the country code lookup
country_code_df=pd.read_excel('C:/Users/firanskib/OneDrive - EC-EC/mercury/iso_2digit_alpha_country_codes.xlsx', index_col=0)

# grab the EBAS header template
ebas_minamata_header_df=pd.read_excel('C:/Users/firanskib/OneDrive - EC-EC/mercury/EBAS/_EBAS_header_information.xlsx', sheet_name='Template', nrows=108, header=None, index_col=0)

# grab the excel mapping sheet
ebas_mapping_df=pd.read_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/EBAS/_ebas_minamata_mapping.csv', engine='python', index_col=0) 

# print (ebas_mapping_df.index)
# set a dictionary of WMO regions
wmo_dict={'1':'Africa','2':'Asia','3':'South America','4':'North & Central America & Caribbean', '5':'South West Pacific','6':'Europe'}
# grab the ebas file list and extract the country codes from it
ebas_file_list=glob.glob('C:/Users/firanskib/OneDrive - EC-EC/mercury/EBAS/data_files/original_format/*.csv')


# set up a list of countries in the ebas data pile
country_list=set()

for file in ebas_file_list:
    # clear the minamata dataframe to remove previous stray entries
    ebas_minamata_header_df.loc[:,1]=None
    print (os.path.basename(file))
    path=os.path.dirname(os.path.dirname(file))
    # print (path)
    ebas_minamata_filename=str(path)+'/minamata_format/'+os.path.basename(file)
    # print (file)
    country_code=file.split('/')[7].split('\\')[1][:2] # extract the country code from the filename
    country_name=country_code_df.loc[country_code,'Definition'] # look up the corresponding country name
    country_list.add(country_name)
    # read in the file as a dataframe
    ebas_file_df=pd.read_csv(file, index_col=0, delimiter=':,', engine='python', skiprows=3, header=None, quotechar='"')
    # cut off the header df at 'unit'
    header_end=ebas_file_df.index.get_loc('Unit')+1
    ebas_file_header_df=ebas_file_df[:ebas_file_df.index[header_end]]
    ebas_file_data_df=ebas_file_df[ebas_file_df.index[header_end]:]
    ebas_file_data_df.reset_index(inplace=True)

    # expand the data file df by splitting it by comma to create separate columns to access
    temp_df=ebas_file_data_df[0].str.split(',', expand=True)#.drop(columns=0, inplace=True)
    temp_df.drop(columns=0, inplace=True) # drop the original un-parsed column
    temp_df.columns=ebas_file_header_df.loc['Variable type',1].split(',') # set up headers
    
    # grab the finish datetime to insert into the end date field
    ebas_minamata_header_df.loc['*MONITORING PERIOD END (YYYY-MM-DD)',1]=temp_df['End Time UTC'].iloc[-1].split('T')[0]
    temp_df=temp_df.T.reset_index().T

    ebas_file_header_df.index.rename('Metadata_Entry', inplace=True)
    # loop through the mapping file to map the ebas headers to the minamata headers
    for ebas_index_item in ebas_file_header_df.index:
        # print (ebas_index_item)
        try:
            minamata_index_item=ebas_mapping_df.loc[ebas_index_item,'Minamata']
           # print (minamata_index_item)
            ebas_minamata_header_df.loc[minamata_index_item,1]=ebas_file_header_df.loc[ebas_index_item,1].replace('"','')
            # print (ebas_minamata_header_df.loc[minamata_index_item,1])
        except:
            pass
    
     # manually set some headers
     # geolocation units
    ebas_minamata_header_df.loc['*SITE LATITUE UNITS (DECIMAL degrees)',1]='Decimal' 
    ebas_minamata_header_df.loc['*SITE LONGITUDE UNITS (DECIMAL degrees)',1]='Decimal' 
    ebas_minamata_header_df.loc['*ELEVATION UNIT',1]='METERS'


    # time zone
    ebas_minamata_header_df.loc['*TIME ZONE',1]='UTC+0:00'
    
    # site country
    ebas_minamata_header_df.loc['*SITE COUNTRY',1]=country_name

    # some files have no Originator
    if 'Originator' in ebas_file_header_df.index:
        # check to see if there are more than one Originator, and if so, add the second as co-investigator
        if isinstance(ebas_file_header_df.loc['Originator',1],pd.core.series.Series):
            ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR NAME (LAST,FIRST)',1]=','.join(ebas_file_header_df.loc['Originator',1].iloc[0].split (',')[:2]).replace('"','')
            ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR AFFILIATION',1]=','.join(ebas_file_header_df.loc['Originator',1].iloc[0].split (',')[3:]).replace('"','')
            ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR CONTACT INFORMATION',1]=','.join(ebas_file_header_df.loc['Originator',1].iloc[0].split (',')[2:]).replace('"','')
            ebas_minamata_header_df.loc['*CO-INVESTIGATOR NAME (LAST,FIRST)',1]=','.join(ebas_file_header_df.loc['Originator',1].iloc[1].split (',')[:2]).replace('"','')
            ebas_minamata_header_df.loc['*CO-INVESTIGATOR AFFILIATION',1]=','.join(ebas_file_header_df.loc['Originator',1].iloc[1].split (',')[3:]).replace('"','')
        else: # no other Originator, thus no co-investigator
            ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR NAME (LAST,FIRST)',1]=','.join(ebas_file_header_df.loc['Originator',1].split (',')[:2]).replace('"','')
            ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR AFFILIATION',1]=','.join(ebas_file_header_df.loc['Originator',1].split (',')[3:]).replace('"','')
            ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR CONTACT INFORMATION',1]=','.join(ebas_file_header_df.loc['Originator',1].split (',')[2:]).replace('"','')
    else:
        ebas_minamata_header_df.loc['*PRINCIPAL INVESTIGATOR NAME (LAST,FIRST)',1]='NA'
    # WMO region entry
    try:
        ebas_minamata_header_df.loc['*GEOGRAPHIC SCOPE OF THE STUDY',1]=wmo_dict[ebas_file_header_df.loc['Station WMO region',1]]
    except:
        pass

    print (ebas_minamata_header_df.index[-5:])
    # print (ebas_file_header_df.loc['Matrix',1])
    if ebas_file_header_df.loc['Matrix',1]=='air':
        # print (ebas_file_header_df.loc['Matrix',1])
        ebas_minamata_header_df.loc['*SUGGESTED DATA FLAGS (indicate your flags if different)',1]=' Flags can be found at https://ebas-submit.nilu.no/templates/Mercury-aerosol/lev2'
    elif ebas_file_header_df.loc['Matrix',1]=='precip':
        # print (ebas_file_header_df.loc['Matrix',1])
        ebas_minamata_header_df.loc['*SUGGESTED DATA FLAGS (indicate your flags if different)',1]=' Flags can be found at https://ebas-submit.nilu.no/templates/Mercury-precip/lev2'

    # trim the start date to yyyy-mm-dd
    ebas_minamata_header_df.loc['*MONITORING PERIOD START (YYYY-MM-DD)',1]=ebas_minamata_header_df.loc['*MONITORING PERIOD START (YYYY-MM-DD)',1].split(' ')[0]  

    # concat the metadata with the site data
    ebas_minamata_header_output_df=ebas_minamata_header_df.reset_index() # this resets the index from using the header information so that the two dfs will line up
    # concatenate the header dataframe with the data dataframe
    ebas_output_df=pd.concat([ebas_minamata_header_output_df,temp_df])

    ebas_output_df.to_csv(ebas_minamata_filename, index=False, header=False)
print (country_list)

# header_filename = 'C:/Users/firanskib/OneDrive - EC-EC/mercury/US_AMNET_Files/US_AMNET_header_information.xlsx'

# mercury_metatada_header_df=pd.read_excel(header_filename, sheet_name='Template', nrows=108, header=None, index_col=0)
# # print (mercury_metatada_header_df.columns)

# # grab the network sites
# sites_filename='C:/Users/firanskib/OneDrive - EC-EC/mercury/US_AMNET_Files/amnet.csv'
# mercury_sites_df=pd.read_csv(sites_filename, index_col=0)

# # grab the full data from the csv file for all sites
# all_sites_data_filename='C:/Users/firanskib/OneDrive - EC-EC/mercury/US_AMNET_Files/AMNET-ALL-h.csv'
# all_sites_data_df=pd.read_csv(all_sites_data_filename, index_col=0)


# # loop through the list of sites, insert the relevant metadata entries that are specific to each site
# # then grab the data from the all-sites report for each site by index into a dataframe subset
# # concatenate the metadata header and the subset
# # save the file
# for index_item in mercury_sites_df.index:
#     print (index_item)
#     mercury_metatada_header_df.loc['*SITE IDENTIFICATION',1]=mercury_sites_df.loc[index_item,'siteName']
#     mercury_metatada_header_df.loc['*SITE COUNTRY',1]='USA'
#     mercury_metatada_header_df.loc['*SITE LATITUDE',1]=mercury_sites_df.loc[index_item,'latitude']
#     mercury_metatada_header_df.loc['*SITE LONGITUDE',1]=mercury_sites_df.loc[index_item,'longitude']
#     if mercury_sites_df.loc[index_item,'siteClass']=='I':
#         mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Isolated (<10 persons per square Km)'
#     elif mercury_sites_df.loc[index_item,'siteClass']=='R':
#         mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Rural (10 - 99 persons per square Km)'
#     elif mercury_sites_df.loc[index_item,'siteClass']=='S':
#         mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Suburban (100 - 399 persons per square Km)'
#     elif mercury_sites_df.loc[index_item,'siteClass']=='U':
#         mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Urban (>=400 persons per square Km)'
#     elif mercury_sites_df.loc[index_item,'siteClass']=='P':
#         mercury_metatada_header_df.loc['*SITE CHARACTERISTICS',1]= 'Research/Provisional (NA)'
#     else:
#         pass
#     mercury_metatada_header_df.loc['*ELEVATION OF THE SITE ',1]=mercury_sites_df.loc[index_item,'elevation']
#     mercury_metatada_header_df.loc['*ELEVATION UNIT',1]='METERS'
#     mercury_metatada_header_df.loc['*MONITORING PERIOD START (YYYY-MM-DD)',1]=mercury_sites_df.loc[index_item,'startDate']
#     mercury_metatada_header_df.loc['*MONITORING PERIOD END (YYYY-MM-DD)',1]=mercury_sites_df.loc[index_item,'stopDate']
#     print (mercury_sites_df.loc[index_item,'status'])
#     if mercury_sites_df.loc[index_item,'status']=='A':
#         mercury_metatada_header_df.loc['*ONGOING MONITORING',1]='YES'
#         mercury_metatada_header_df.loc['*FILE NAME ',1]='AMNET_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_'+mercury_sites_df.loc[index_item,'startDate'].split('-')[0]+'_'+'2024.csv'
#     elif mercury_sites_df.loc[index_item,'status']=='I':
#         mercury_metatada_header_df.loc['*ONGOING MONITORING',1]='NO'
#         try:
#             mercury_sites_df.loc[index_item,'startDate'].split('-')
#             try:
#                 mercury_sites_df.loc[index_item,'stopDate'].split('-')
#                 mercury_metatada_header_df.loc['*FILE NAME ',1]='AMNET_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_'+mercury_sites_df.loc[index_item,'startDate'].split('-')[0]+'_'+mercury_sites_df.loc[index_item,'stopDate'].split('-')[0]+'.csv'
#             except:
#                 mercury_metatada_header_df.loc['*FILE NAME ',1]='AMNET_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_'+mercury_sites_df.loc[index_item,'startDate'].split('-')[0]+'_NA.csv'
#         except:
#             mercury_metatada_header_df.loc['*FILE NAME ',1]='AMNET_'+index_item+'_'+mercury_sites_df.loc[index_item,'siteName']+'_NA_'+mercury_sites_df.loc[index_item,'stopDate'].split('-')[0]+'.csv'
#     mercury_metatada_header_df.loc['*MONITORING MATRIX',1]='Air'
#     if mercury_sites_df.loc[index_item,'Species']=='GEM':
#         print ('GEM')
#         mercury_metatada_header_df.loc['*MERCURY OBSERVATIONS/SPECIES',1]='Gaseous Elemental Mercury (Hg0, GEM)'
#         mercury_metatada_header_df.loc['*UNIT OF CONCENTRATION MEASUREMENT ',1]='ng/m3' 
#     elif mercury_sites_df.loc[index_item,'Species']=='PBM_GOM_GEM':
#         print ('PBM_GOM_GEM')
#         mercury_metatada_header_df.loc['*MERCURY OBSERVATIONS/SPECIES',[1,2,3]]=['PM2.5 ','Gaseous Oxidized Mercury (HgII, GOM)','Gaseous Elemental Mercury (Hg0, GEM)']
#         mercury_metatada_header_df.loc['*UNIT OF CONCENTRATION MEASUREMENT ',[1,2,3]]=['pg/m3','pg/m3','ng/m3'] 

#     # set the output filename
#     AMNET_minamata_filename=mercury_metatada_header_df.loc['*FILE NAME ',1].replace(' ','')
    
#     # print (mercury_metatada_header_df)
#     # reindex the dataframe
#     mercury_metatada_header_output_df=mercury_metatada_header_df.reset_index() 
#     # print (mercury_metatada_header_output_df)

#     # slice the all-sites dataframe by site ID
#     if index_item in all_sites_data_df.index:
#         site_data_df=all_sites_data_df.loc[index_item]
#     else:
#         print ('site not found')
#         continue
#     # print (site_data_df)

#     # concat the metadata with the site data
#     site_data_df=pd.concat([pd.DataFrame([site_data_df.columns], columns=site_data_df.columns),site_data_df], ignore_index=True)
#     site_data_df.set_axis(range(site_data_df.shape[1]), axis=1)
#     site_output_df=pd.concat([mercury_metatada_header_output_df,site_data_df])

#     # output to file
#     print ('saved to file')
#     site_output_df.to_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/US_AMNET_Files/'+AMNET_minamata_filename,header=False, index=False)


    



 






# # file_list=glob.glob('C:/Users/firanskib/OneDrive - EC-EC/mercury/minamata Submission Files/SPM10*')
# # for filename in file_list:
# #     print (filename)
# #     csv_filename=filename.replace('xlsx', 'csv')
# #     print (csv_filename)
# #     # grab the mercury data
# #     mercury_metatada_header_df=pd.read_excel(filename, sheet_name='Template', nrows=108, header=None)
# #     # print (mercury_metatada_header_df.tail())
# #     mercury_df=pd.read_excel(filename, sheet_name='Template', skiprows=108)
# #     print (mercury_df.columns)

# #     # set date and time to datetime columns
# #     # print (pd.to_datetime(mercury_df['Time start: local time'],format='%H:%M:%S').dt.time)
# #     mercury_df['local_start_datetime']=pd.to_datetime(mercury_df['Date start: local time'].astype(str)+ " " + mercury_df['Time start: local time'].astype(str))
# #     mercury_df['local_end_datetime']=pd.to_datetime(mercury_df['Date end: local time'].astype(str)+ " " + mercury_df['Time end: local time'].astype(str))
# #     mercury_df['utc_start_datetime']=pd.to_datetime(mercury_df['Date start: UTC'].astype(str)+ " " + mercury_df['Time start: UTC'].astype(str))
# #     mercury_df['utc_end_datetime']=pd.to_datetime(mercury_df['Date end: UTC'].astype(str)+ " " + mercury_df['Time end: UTC'].astype(str))
# #     mercury_df.drop(columns=['Date start: local time','Time start: local time','Date end: local time','Time end: local time','Date start: UTC','Time start: UTC','Date end: UTC','Time end: UTC'], inplace=True)
# #     # replace V2, V4, V7 with V0 - not bothering with oddball valid flags
# #     mercury_df.loc[mercury_df.loc[:,'Mercury GEM Flag'].isin(['V2', 'V4','V7']), 'Mercury GEM Flag']='V0'
# #     mercury_df.loc[mercury_df.loc[:,'Mercury GOM Flag'].isin(['V2', 'V4','V7']), 'Mercury GOM Flag']='V0'
# #     mercury_df.loc[mercury_df.loc[:,'PCM10 Flag'].isin(['V2', 'V4','V7']), 'PCM10 Flag']='V0'
# #     # replace -99.9 with -999
# #     mercury_df.loc[mercury_df.loc[:,'Mercury GEM']==-99.9,'Mercury GEM']=-999
# #     mercury_df.loc[mercury_df.loc[:,'Mercury GOM']==-99.9,'Mercury GOM']=-999
# #     mercury_df.loc[mercury_df.loc[:,'PCM10']==-99.9,'PCM10']=-999
# #     # test_df=mercury_df.loc[mercury_df.loc[:,'Mercury Flag'].isin(['V2', 'V4','V7']), 'Mercury Flag']
# #     # print (test_df)
# #     mercury_df=mercury_df.reindex(columns=['local_start_datetime','local_end_datetime','utc_start_datetime','utc_end_datetime','Mercury GEM','Mercury GEM Flag', 'Mercury GOM',	'Mercury GOM Flag',	'PCM10',	'PCM10 Flag'])
# #     mercury_df=pd.concat([pd.DataFrame([mercury_df.columns], columns=mercury_df.columns),mercury_df], ignore_index=True)
# #     mercury_df.set_axis(range(mercury_df.shape[1]), axis=1)
# #     mercury_df=pd.concat([mercury_metatada_header_df,mercury_df])
# #     mercury_df.to_csv(csv_filename, index=False, header=False)

