import pandas as pd
import numpy as np
from pathlib import Path
import requests

# Define output folder
output_folder = Path(r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data")
output_folder.mkdir(exist_ok=True)

# -------------------------
# 1) Load data
# -------------------------
# passives = pd.read_excel(r"\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\Passive Samplers\passives_stations.xlsx", usecols=['passives_site_name', 'site_latdecd','site_londecd'])
# stations = pd.read_csv(r"\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\Passive Samplers\isd-history.csv", usecols=['USAF','WBAN','STATION NAME','LAT','LON'], dtype={'USAF': str, 'WBAN': str})

passives = pd.read_excel(r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data\passives_stations.xlsx", usecols=['passives_site_name', 'site_latdecd','site_londecd'])
stations = pd.read_csv(r"C:\Users\firanskib\Documents\Python Scripts\mercury_analysis\gsod_data\isd-history.csv", usecols=['USAF','WBAN','STATION NAME','LAT','LON'], dtype={'USAF': str, 'WBAN': str})

stations['LAT'] = pd.to_numeric(stations['LAT'], errors='coerce')
stations['LON'] = pd.to_numeric(stations['LON'], errors='coerce')
passives['site_latdecd'] = pd.to_numeric(passives['site_latdecd'], errors='coerce')
passives['site_londecd'] = pd.to_numeric(passives['site_londecd'], errors='coerce')

stations = stations.dropna(subset=['LAT','LON'])
passives = passives.dropna(subset=['site_latdecd','site_londecd'])

# -------------------------
# 2) Find nearest station for each passive site
# -------------------------
def find_nearest_station(lat, lon, stations_df):
    distances = np.sqrt((stations_df['LAT'] - lat)**2 + (stations_df['LON'] - lon)**2)
    idx = distances.idxmin()
    # add the distance value if needed
    distance = distances.min()
    return stations_df.loc[idx], distance

nearest_stations = []
for _, row in passives.iterrows():
    nearest, dist = find_nearest_station(row['site_latdecd'], row['site_londecd'], stations)
    print (f"Nearest station to {row['passives_site_name']} is {nearest['STATION NAME']} at distance {dist:.4f} USAF: {nearest['USAF']} WBAN: {nearest['WBAN']} ")
    nearest_stations.append({
        'passives_site_name': row['passives_site_name'],
        'nearest_station_name': nearest['STATION NAME'],
        'USAF': nearest['USAF'],
        'WBAN': nearest['WBAN'],
        'station_latdecd': nearest['LAT'],
        'station_londecd': nearest['LON'],
        'site_latdecd': row['site_latdecd'],
        'site_londecd': row['site_londecd'],
        'distance': dist    # ← add distance here
    })

nearest_df = pd.DataFrame(nearest_stations)

# -------------------------
# 3) Build 11-digit station code
# -------------------------
def format_station_code(usaf, wban):
    usaf_str = str(usaf).zfill(6)
    wban_str = str(wban).zfill(5)
    return usaf_str + wban_str

nearest_df['station_code'] = nearest_df.apply(lambda x: format_station_code(x['USAF'], x['WBAN']), axis=1)

print (nearest_df)

# save nearest stations to csv
nearest_df.to_csv(output_folder / "nearest_stations.csv", index=False)

# -------------------------
# 4) Download NOAA GSOD CSVs 2020 onward
# -------------------------


years = range(2018, 2020)  # 2018 to 2019 (adjust as needed)
base_url = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access"
results = []

for _, row in nearest_df.iterrows():
    station_code = row['station_code']
    station_name = row['nearest_station_name']
    site_name = row['passives_site_name']
    
    for year in years:
        url = f"{base_url}/{year}/{station_code}.csv"
        out_file = output_folder / f"{station_code}_{year}.csv"
        if out_file.exists():
            continue
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                print(f"Downloading data for station: {station_name} ({station_code})")
                out_file.write_bytes(resp.content)
            else:
                print(f"File not found: {url} (status {resp.status_code})")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

print("Download complete.")