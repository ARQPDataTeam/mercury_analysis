import pandas as pd
import glob


# grab the minimata files
file_list=glob.glob('C:/Users/firanskib/OneDrive - EC-EC/mercury/Canada_Air_Files/data_files/TGM_PQ_MINGAN_1997_2000.xlsx')

for filename in file_list:
    print (filename)
    csv_filename=filename.replace('xlsx', 'csv')
    print (csv_filename)
    # grab the mercury data
    mercury_metatada_header_df=pd.read_excel(filename, sheet_name='Template', nrows=105, header=None)
    # print (mercury_metatada_header_df.tail())
    mercury_df=pd.read_excel(filename, sheet_name='Template', skiprows=105)
    print (mercury_df.columns)

    # set date and time to datetime columns
    # print (pd.to_datetime(mercury_df['Time start: local time'],format='%H:%M:%S').dt.time)
    mercury_df['local_start_datetime']=pd.to_datetime(mercury_df['Date start: local time'].astype(str)+ " " + mercury_df['Time start: local time'].astype(str))
    mercury_df['local_end_datetime']=pd.to_datetime(mercury_df['Date end: local time'].astype(str)+ " " + mercury_df['Time end: local time'].astype(str))
    mercury_df['utc_start_datetime']=pd.to_datetime(mercury_df['Date start: UTC'].astype(str)+ " " + mercury_df['Time start: UTC'].astype(str))
    mercury_df['utc_end_datetime']=pd.to_datetime(mercury_df['Date end: UTC'].astype(str)+ " " + mercury_df['Time end: UTC'].astype(str))
    mercury_df.drop(columns=['Date start: local time','Time start: local time','Date end: local time','Time end: local time','Date start: UTC','Time start: UTC','Date end: UTC','Time end: UTC'], inplace=True)
    # replace V2, V4, V7 with V0 - not bothering with oddball valid flags
    # mercury_df.loc[mercury_df.loc[:,'Mercury GEM Flag'].isin(['V2', 'V4','V7']), 'Mercury GEM Flag']='V0'
    # mercury_df.loc[mercury_df.loc[:,'Mercury GOM Flag'].isin(['V2', 'V4','V7']), 'Mercury GOM Flag']='V0'
    # mercury_df.loc[mercury_df.loc[:,'PCM10 Flag'].isin(['V2', 'V4','V7']), 'PCM10 Flag']='V0'
    # # replace -99.9 with -999
    # mercury_df.loc[mercury_df.loc[:,'Mercury GEM']==-99.9,'Mercury GEM']=-999
    # mercury_df.loc[mercury_df.loc[:,'Mercury GOM']==-99.9,'Mercury GOM']=-999
    # mercury_df.loc[mercury_df.loc[:,'PCM10']==-99.9,'PCM10']=-999
    # test_df=mercury_df.loc[mercury_df.loc[:,'Mercury Flag'].isin(['V2', 'V4','V7']), 'Mercury Flag']
    # print (test_df)
    mercury_df=mercury_df.reindex(columns=['local_start_datetime','local_end_datetime','utc_start_datetime','utc_end_datetime','Mercury','Mercury Flag'])
    mercury_df=pd.concat([pd.DataFrame([mercury_df.columns], columns=mercury_df.columns),mercury_df], ignore_index=True)
    mercury_df.set_axis(range(mercury_df.shape[1]), axis=1)
    mercury_df=pd.concat([mercury_metatada_header_df,mercury_df])
    mercury_df.to_csv(csv_filename, index=False, header=False)

