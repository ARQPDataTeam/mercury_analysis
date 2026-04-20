# this program grabs sql data and plots a windrose
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
from sqlalchemy import create_engine




# set global conditions for app and computer name
# set up the sql connection string
COMPUTER, SERVER, VIEWER_USER, VIEWER_PASSWORD, EDITOR_USER, EDITOR_PASSWORD, DATABASE, URL_PREFIX = get_credentials(parent_dir)

# set up the engine
sql_engine_string=('postgresql://{}:{}@{}/{}?sslmode=require').format(EDITOR_USER,EDITOR_PASSWORD,SERVER,DATABASE)
try:
    sql_engine=create_engine(sql_engine_string,pool_pre_ping=True)
except Exception as e:
    error_occur = True
    print(f"An error occurred trying to create db connection: {e}")    

wd_sql_query = """
SELECT datetime, wind_speed, wind_dir
FROM hourly_wind_data
WHERE datetime >= '2023-01-01' AND datetime < '2024-01-01'
ORDER BY datetime;
""" 



# example: load data
# df = pd.read_csv("wind.csv", parse_dates=["datetime"])

ws = df["wind_speed"]
wd = df["wind_dir"]

fig = plt.figure(figsize=(8,8))
ax = WindroseAxes.from_ax(fig=fig)

ax.bar(
    wd,
    ws,
    normed=True,        # frequency %
    opening=0.8,
    edgecolor="white",
    bins=[0,2,4,6,8,10,15]
)

ax.set_legend(title="Wind speed")
plt.title("Wind Rose - Hourly Wind Data")
plt.show()