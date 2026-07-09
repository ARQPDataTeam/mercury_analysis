import pandas as pd
import glob
from geopy import distance

# excel_path='C:/Users/firanskib/OneDrive - EC-EC/mercury/npri_report.xlsx'
# npri_df=pd.read_excel(excel_path)

# print (npri_df.columns)
# npri_df.loc[npri_df.loc[:,'Units']=='tonnes','Total Releases']=npri_df.loc[npri_df.loc[:,'Units']=='tonnes','Total']*1e3
# npri_df.loc[npri_df.loc[:,'Units']=='kg','Total Releases']=npri_df.loc[npri_df.loc[:,'Units']=='kg','Total']

# npri_df.to_csv('C:/Users/firanskib/Documents/Python Scripts/mercury_work/converted_npri_report.csv')

# npri_site_total_df=npri_df.loc[:,['NPRI ID','Total Releases']].groupby("NPRI ID").sum()

# print (npri_site_total_df.index)

# npri_site_total_gps_df=npri_df.loc[:,['NPRI ID','Company Name','City','Latitude','Longitude']].drop_duplicates()
# npri_site_total_gps_df.set_index('NPRI ID', inplace=True)

# print (npri_site_total_gps_df)

# npri_site_total_df=pd.concat([npri_site_total_gps_df,npri_site_total_df],axis=1)


# npri_site_total_df.to_csv('C:/Users/firanskib/Documents/Python Scripts/mercury_work/grouped_npri_report.csv')

# grab the minimata files
file_list=glob.glob('C:/Users/firanskib/OneDrive - EC-EC/mercury/CA_Minimata_Submission_Files/TGM*.xlsx')
# print (file_list)
tgm_tekran_site_list=[]
tekran_site_list=[]
tekran_start_year_list=[]
tekran_end_year_list=[]

for file in file_list:
    tekran_site=file.split('_')[5]
    tekran_start_year=file.split('_')[6]
    tekran_end_year=file.split('_')[7].split('.')[0]
    df=pd.read_excel(file, index_col=0, sheet_name='Template',nrows=40)
    # print (df.columns)
    lat_entry=df.loc['*SITE LATITUDE','Unnamed: 1']
    lon_entry=df.loc['*SITE LONGITUDE','Unnamed: 1']
    tgm_tekran_site_list.append([tekran_site,lat_entry,lon_entry,tekran_start_year,tekran_end_year])

tgm_tekran_site_df=pd.DataFrame(tgm_tekran_site_list, columns=['tekran_site','tekran_lat','tekran_lon','start_year','end_year'])
# print (tgm_tekran_site_df)

mdn_site_df=pd.read_excel('C:/Users/firanskib/OneDrive - EC-EC/mercury/Canada_MDN_sites.xlsx', index_col=0)
print (mdn_site_df)
tgm_tekran_site_df.to_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/CA_Minimata_Submission_Files/tekran_site_gps_list.csv', index=False)

# # grab the two sets of data and do a huge distance comparison between the 2
npri_df=pd.read_excel('C:/Users/firanskib/OneDrive - EC-EC/mercury/npri_report.xlsx')
npri_df.set_index('EntryID', inplace=True)
tekran_df=pd.read_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/CA_Minimata_Submission_Files/tekran_site_gps_list.csv')
tekran_df.set_index('tekran_site', inplace=True)
npri_df.loc[:,tekran_df.index]=""
npri_df.loc[:,mdn_site_df.index]=""
# print (npri_df.columns)
# loop through the sites and calucalate the distance
for npri_site in npri_df.index:
    # print('npri_site',npri_site)
    # for tekran_site in tekran_df.index:
    #     print ('tekran_site',tekran_site)
    #     npri_site_gps=(npri_df.loc[npri_site,'Latitude'],npri_df.loc[npri_site,'Longitude'])
    #     tekran_site_gps=(tekran_df.loc[tekran_site,'tekran_lat'],tekran_df.loc[tekran_site,'tekran_lon'])
    #     # only do a distance check if the emission occured when the tekran site was active
    #     print (npri_site,npri_df.at[npri_site,'ReportYear'],tekran_df.at[tekran_site,'start_year'])
    #     if (tekran_df.at[tekran_site,'start_year']<=npri_df.at[npri_site,'ReportYear'])&(npri_df.at[npri_site,'ReportYear']<=tekran_df.at[tekran_site,'end_year']):
    #         try:
    #             npri_df.loc[npri_site,tekran_site]=distance.distance(npri_site_gps,tekran_site_gps).km
    #         except:
    #             # print ('no gps found for: ',npri_site)
    #             npri_df.loc[npri_site,tekran_site]=1e3
    #             continue
    #     else:
    #         npri_df.loc[npri_site,tekran_site]=1e3 # put a false large distance so it doesn't register

    for mdn_site in mdn_site_df.index:
        print ('mdn_site',mdn_site)
        npri_site_gps=(npri_df.loc[npri_site,'Latitude'],npri_df.loc[npri_site,'Longitude'])
        mdn_site_gps=(mdn_site_df.loc[mdn_site,'MDN_lat'],mdn_site_df.loc[mdn_site,'MDN_lon'])
        # only do a distance check if the emission occured when the mdn site was active
        print (npri_site,npri_df.at[npri_site,'ReportYear'],mdn_site_df.at[mdn_site,'start_year'])
        if (mdn_site_df.at[mdn_site,'start_year']<=npri_df.at[npri_site,'ReportYear'])&(npri_df.at[npri_site,'ReportYear']<=mdn_site_df.at[mdn_site
                                                                                                                                           ,'end_year']):
            try:
                npri_df.loc[npri_site,mdn_site]=distance.distance(npri_site_gps,mdn_site_gps).km
            except:
                # print ('no gps found for: ',npri_site)
                npri_df.loc[npri_site,mdn_site]=1e3
                continue
        else:
            npri_df.loc[npri_site,mdn_site]=1e3 # put a false large distance so it doesn't register

# print (npri_df)

npri_df.to_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/npri_report_distances.csv')

# # grab the distance matrix
npri_df=pd.read_csv('C:/Users/firanskib/OneDrive - EC-EC/mercury/npri_report_distances.csv', index_col=0, header=0)
# for tekran_site in tekran_df.index:
#     print (tekran_site)
#     source_list=npri_df.loc[npri_df.loc[:,tekran_site]<50,['ReportYear','CompanyName','FacilityName','Quantity',tekran_site]]
#     print (source_list)

for mdn_site in mdn_site_df.index:
    print (mdn_site)
    source_list=npri_df.loc[npri_df.loc[:,mdn_site]<50,['ReportYear','CompanyName','FacilityName','Quantity',mdn_site]]
    print (source_list)



