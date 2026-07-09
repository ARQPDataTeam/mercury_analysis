from doctest import master
from locale import normalize
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy
from sklearn.feature_selection import mutual_info_regression, f_regression, r_regression
from sklearn.metrics import adjusted_mutual_info_score
import ennemi
import calendar


master_mercury_df=pd.read_csv('C:/mutual_information/mercury/alert/master_filtered_monthly_data.csv') # read the current international site into dataframe)
# enso_df=pd.read_excel('C:\\Users\\haos\\Documents\\Python Scripts\\Mutual Information\\mercury\\ENSO-record.xlsx', index_col=0)
ao_df=pd.read_excel('C:/mutual_information/mercury/AO-record.xlsx', index_col=0)


# master_mercury_df['datetime'] = master_mercury_df.loc[:, 'datetime'].str.replace(pat = ' (.*)', repl = '', regex = True)
master_mercury_df = master_mercury_df.drop_duplicates()
ao_df = ao_df.drop_duplicates()

master_mercury_df = master_mercury_df.astype({'Date': 'datetime64[ns]'})

master_mercury_df = master_mercury_df.set_index('Date')

combined_df = pd.merge_asof(master_mercury_df, ao_df, on = 'Date')
combined_df = combined_df.dropna()

# do an annual average for each month
month_list=[] # initialize a blank month list
for i in range(1,13):
    month_list.append(calendar.month_name[i][:3])
months=np.arange(1,13)
years=np.arange(1995,2020)

annual_hg_df=pd.DataFrame(index=years,columns=months)
annual_ao_df=pd.DataFrame(index=years,columns=months)

for month in months:
    print ()
    monthly_hg_slice_series=master_mercury_df.loc[master_mercury_df.index.month.isin([month])]
    monthly_ao_slice_series=ao_df.loc[ao_df.index.month.isin([month])]
    
    print (month,monthly_hg_slice_series)
    annual_hg_df.loc[:,month]=monthly_hg_slice_series.to_numpy()
    annual_ao_df.loc[:,month]=monthly_ao_slice_series.to_numpy()
       
print(annual_ao_df.mean(axis=0))

# Date Conc/Index Graph & Scatter Plot
figure, ((ax, ax_scat), (ax_mi_lag, ax4)) = plt.subplots(2, 2)
x_date_data, y_Hg_data, y_AO_data = (combined_df['Date'], combined_df['Mercury_concentration'], combined_df['AO Index'])
ax.set_title("Mercury Concentration at Alert and AO Index over Time")
ax.plot(x_date_data, y_Hg_data, color='red')
ax.set_xlabel("Date", fontsize=14)
ax.set_ylabel("Alert Hg Concentration (ppm)", fontsize=14, color="red")
ax2=ax.twinx()
ax2.plot(x_date_data, y_AO_data, color="blue")
ax2.set_ylabel("AO Coefficient", color="blue", fontsize=14)

# Histograms
# ax_AO_hist.hist(y_AO_data, bins=18)
# ax_AO_hist.set_xlabel("AO Index", fontsize=14)
# ax_AO_hist.set_ylabel("Frequency", fontsize=14)
# ax_Hg_hist.hist(y_Hg_data, bins=18, color='red')
# ax_Hg_hist.set_xlabel("Hg Index", fontsize=14)
# ax_Hg_hist.set_ylabel("Frequency", fontsize=14)

# Scatter plot
ax_scat.set_title('Mercury Concentration vs. AO Index')
ax_scat.scatter(combined_df['Mercury_concentration'], combined_df['AO Index'])
ax_scat.set_xlabel("Alert Mercury_concentration (ppm)", fontsize=14, color="red")
ax_scat.set_ylabel("AO Coefficient", fontsize=14, color="blue")

# Lag array; calculate the NMI between data with x months lag / lead
lagArr = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 10]
ennMI = ennemi.estimate_corr(combined_df['Mercury_concentration'], combined_df['AO Index'], lag=lagArr)

ax_mi_lag.set_title("NMI Score at Different Lag Values")
ax_mi_lag.plot(lagArr, ennMI)
ax_mi_lag.set_xlabel("Lag (Months)")
ax_mi_lag.set_ylabel("NMI Score [0, 1]")

print (ennMI)

# for i, j in zip(lagArr, ennMI):
#     print(i, " ", j)
#     # ax_mi_lag.annotate("hello", xy=(i, j))

ax4.set_title("Mercury Concentration Shifted -2 months vs. AO Index")
ax4.plot(combined_df['Date'], combined_df['Mercury_concentration'].shift(-2), color="red")
ax4.set_xlabel("Date", fontsize=14)
ax4.set_ylabel("Alert Hg Concentration (ppm)", fontsize=14, color="red")
ax5=ax4.twinx()
ax5.plot(combined_df['Date'], y_AO_data, color="blue")
ax5.set_ylabel("AO Coefficient", color="blue", fontsize=14)

# print('NMI Binned Score: ', adjusted_mutual_info_score(ax_AO_hist.hist(y_AO_data, bins=18)[0], ax_Hg_hist.hist(y_Hg_data, bins=18)[0]))

# print('NMI Score: ', adjusted_mutual_info_score(y_AO_data, y_Hg_data))

# y_AO_array = y_AO_data.to_numpy().reshape(-1, 1)
# print('MI regression Score: ', mutual_info_regression(y_AO_array, y_Hg_data))
# print("Generalized Correlation Coefficient (RMI) Score: ", np.power(1 - np.exp((-2 * mutual_info_regression(y_AO_array, y_Hg_data))/1 ) , -0.5) )

# print('Pandas Pearson\'s correlation matrix:\n', combined_df.corr())

# print('Ennemi MI Score: ', ennemi.estimate_mi(combined_df['Mercury_concentration'], combined_df['AO Index']))



# y_AO_array = y_AO_data.to_numpy().reshape(-1, 1)
# print(mutual_info_regression(y_AO_array, y_Hg_data, discrete_features=False))

# AO_data, Hg_data = (combined_df[''])

# print('Pearson\'s Coefficient (r): ', scipy.stats.pearsonr(AO_data, Hg_data))


# print('Spearmans: ', scipy.stats.spearmanr(AO_data, mercury_data))
# print('Kendalls: ', scipy.stats.kendalltau(AO_data, mercury_data))



# print('Adjusted MI  Score: ', adjusted_mutual_info_score(AO_data, mercury_data))
# print('MI regression Score: ', mutual_info_regression(AO_data, mercury_data))
# print('Pearson\'s Coefficient: ', r_regression(AO_data, mercury_data))

plt.show()
