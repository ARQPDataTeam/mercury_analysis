# this program does OESG analysis:
# average and std dev for sites
# box plots of sites for ipcc_regions
# Mann Kendall trends
# pick what this program does by turning various functions on and off


import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import calendar
from calendar import monthrange
import glob
import pandas as pd
from pandas.tseries.offsets import MonthEnd
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.ion()
import pymannkendall as mk
from pymannkendall import original_test  # original MK
from sqlalchemy import create_engine, text, update, Table, MetaData, func, insert
from sqlalchemy.exc import SQLAlchemyError
import geopandas as gp
import matplotlib.dates as md
from shapely import Point
from shapely.geometry import box 
import matplotlib as mpl
from scipy import stats
from scipy.stats import linregress
import os
import re
import shutil
from collections import defaultdict
from libpysal.weights import KNN
from esda.moran import Moran
import logging
from scipy.stats import chi2
from matplotlib.patches import Patch

# local module import
from credentials import get_credentials

# set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a console handler for logging debug output
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

################## SQL database stuff ##############################

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

################### common data IO elements ##########################

# import the ipcc_regions as a dataframe
sql_data_query = """
                select distinct on (ipcc_region) ipcc_region from sites order by ipcc_region;
                """
with sql_engine.connect() as conn:
    ipcc_analysis_df = pd.read_sql_query(sql_data_query, conn)


# initialize the dataframe for ipcc mann_kendall results
ipcc_analysis_df.set_index('ipcc_region', drop=True, inplace=True) # set the ipcc_regions as the index
ipcc_analysis_df['mk_slope']=np.nan # add a blank list for the MK results

ipcc_regions_list = ipcc_analysis_df.index.to_list()
ipcc_regions_list = ['N.W.North-America']#,'N.E.North-America','W.North-America'] # a temporary list for testing

# initialize a dataframe for monthly averages 
ipcc_master_df=pd.DataFrame() # create an empty dataframe to house each concentration query by ipcc_region column

# grab the sites list from the sites table
sql_data_query = """
                SELECT CONCAT( sites.site, ' (', sites.country_code, ')') AS site_name_full
                from sites
                where ipcc_region = '{}'
                order by site_name_full
                """
with sql_engine.connect() as conn:
    sites_df = pd.read_sql_query(sql_data_query, conn)

def gantt_plotter(sql_engine):
    # # set the psql query
    # sql_data_query = """
    #             WITH species_summary AS (
    #                 SELECT
    #                     site,
    #                     COUNT(DISTINCT species) AS species_count,
    #                     BOOL_OR(species = 'TGM') AS has_tgm,
    #                     BOOL_OR(species = 'GEM') AS has_gem
    #                 FROM hgee_active
    #                 GROUP BY site
    #             )

    #             SELECT DISTINCT ON (h.site)
    #                 h.site AS "SITE",
    #                 h.country AS "COUNTRY",
    #                 TO_CHAR(MIN(h.datetime), 'YYYY-MM-DD') AS start_dt,
    #                 TO_CHAR(MAX(h.datetime), 'YYYY-MM-DD') AS end_dt,
    #                 h.ipcc_region
    #             FROM hgee_active h
    #             JOIN species_summary s ON h.site = s.site
    #             WHERE
    #                 (s.species_count = 2 AND h.species = 'TGM')
    #                 OR (s.species_count = 1 AND s.has_tgm AND h.species = 'TGM')
    #                 OR (s.species_count = 1 AND s.has_gem AND h.species = 'GEM')
    #             GROUP BY h.site, h.country, h.ipcc_region
    #             ORDER BY h.site;            
    #             """

    # with sql_engine.connect() as conn:
    # # create the dataframes from the sql query
    #     sites_df = pd.read_sql_query(sql_data_query, conn)
    

    # # grab the sites from the gantt_dates csv
    # sites_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_gantt_dates.csv', encoding='utf-8')
  
    # # grab the sites and trends from the annual summary
    # annual_summary_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_annual_M-K_results_2025-10-02.csv', encoding='utf-8')


    # # clean up SITE names
    # sites_df['SITE'] = sites_df['SITE'].str.replace(" ", "", regex=False)
    # annual_summary_df['SITE'] = annual_summary_df['SITE'].str.replace(" ", "", regex=False)
    # sites_df['SITE'] = sites_df['SITE'].str.replace("'", "", regex=False)
    # annual_summary_df['SITE'] = annual_summary_df['SITE'].str.replace("'", "", regex=False)

    # # create a list of sites that are not in each dataframe
    # site_list = annual_summary_df['SITE'].tolist()
    # site_list_sql = sites_df['SITE'].tolist()
    # missing_sites = list(set(site_list) - set(site_list_sql))
    # not_in_annual = list(set(site_list_sql) - set(site_list))   
    # print ("Sites in annual summary not in sql sites list: ", missing_sites)
    # print ("Sites in sql sites list not in annual summary: ", not_in_annual)   

    # # merge the two dataframes to get the trends with the start and end dates
    # merged_df = annual_summary_df.merge(sites_df, on=['SITE', 'COUNTRY'], how='right')

    # # print (merged_df.columns)

    # # # # include the missing sites from the wet_dep_trends dataframe in the merged dataframe
    # merged_df = pd.concat([merged_df, annual_summary_df[annual_summary_df['SITE'].isin(missing_sites)]], ignore_index=True)


    # # # # replace 'ipcc_region' where '*Europe*' in 'ipcc_region' with 'Europe'
    # merged_df['ipcc_region'] = merged_df['ipcc_region'].replace(r'.*Europe', 'Europe', regex=True)

    # merged_df.to_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_gantt_data_merged.csv', index=False, encoding='utf-8')

    merged_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_gantt_data_merged.csv', encoding='utf-8')


    # set the start_dt and end_dt to datetime
    merged_df['start_dt'] = pd.to_datetime(merged_df['start_dt'])
    merged_df['end_dt'] = pd.to_datetime(merged_df['end_dt'])  

    # replace Nan with 'NOT MEASURED' in the trend column
    merged_df['trend'] = merged_df['trend'].fillna('NOT MEASURED')

    # create a dictionary to assign a colour to each site based on whether the trend is increasing, decreasing or no trend
    trend_colors = {
        'increasing': 'red',
        'decreasing': 'blue',
        'no trend': 'gray',
        'NOT MEASURED': 'black'
    }

    # create a dictionary to assign a colour to each site based on whether the trend is increasing, decreasing or no trend    # add the line colour column to the dataframe
    merged_df['line_color'] = merged_df['ANNUAL TREND'].map(trend_colors)

    # grab the country-codes
    country_code_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\iso_2digit_alpha_country_codes.csv', encoding='utf-8')

    # merge the two dfs together on 'country'
    merged_df = merged_df.merge(country_code_df, left_on  = 'COUNTRY', right_on = 'country', how = 'left')
                                   
    # find and print sites with missing country codes
    missing_countries = merged_df[merged_df['country_code'].isna()]
    if not missing_countries.empty:
        print("⚠️ Sites with missing country codes:")
        print(missing_countries[['SITE', 'COUNTRY']])
    else:
        print("✅ All sites have country codes")

    # merge the site and country columns
    merged_df['SITE'] = merged_df['SITE'] + ', ' + merged_df['country_code']

    # dictionary of figure sizes based on number of sites
    region_figsizes = {
        "C.North-America": (10, 8),
        "E.North-America": (10, 8),
        "W.North-America": (10, 4),
        "N.W.North-America": (10, 4),
        "Europe": (10, 10),
        "E.Asia": (10, 8),
        "Asia": (10, 8),
        "Southern-Hemisphere": (10, 4),
        "Polar-Regions": (10, 4),
        "Central-America": (10, 6),
        "Mediterranean": (10, 6),
        "Africa": (10, 6),
        "default": (10, 6)
    }
    for region in merged_df['ipcc_region'].unique():
        region_df = merged_df[merged_df['ipcc_region'] == region]

        # sort the dataframe by end date then start date descending
        region_df = region_df.sort_values(by=['end_dt', 'start_dt'], ascending=[True, True])
        # reset the index
        region_df = region_df.reset_index(drop=True)
        fig, ax = plt.subplots(figsize=region_figsizes.get(region, region_figsizes["default"]))
        # set line colour based on trend
    # --- Plot each site's data availability as a horizontal line ---
        for _, row in region_df.iterrows():
            ax.hlines(
                y=row['SITE'],
                xmin=row['start_dt'],
                xmax=row['end_dt'],
                color=row['line_color'],
                linewidth=4  # adjust thickness
            )
        ax.xaxis_date()  # ensures proper datetime axis
        ax.set_xlabel('Date')
        ax.set_ylabel('Site')
        ax.set_title(f'Total Gaseoous Data Availability Gantt Chart - {region}')
        handles = [Patch(color=c, label=trend) for trend, c in trend_colors.items()]
        ax.legend(handles=handles, title="TGM Trend", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.tight_layout()
        out_dir = r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots'
        outfile = os.path.join(out_dir, f"tgm_gantt_chart_{region}.png")
        plt.savefig(outfile)
        plt.close()


def table_pivot():
    # read in the tgm daily averages
    tgm_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_daily_averages.csv', index_col=0, encoding='utf-8')
    tgm_df.index = pd.to_datetime(tgm_df.index)
    tgm_df.drop(columns = ['country', 'species'], inplace=True)

    # pivot the dataframe to have sites as columns and dates as index
    tgm_pivot_df = tgm_df.pivot_table(index="date", columns="site", values="daily_avg", aggfunc='first')

    # Reindex to full daily range
    full_range = pd.date_range(start=tgm_pivot_df.index.min(), end=tgm_pivot_df.index.max(), freq="D")
    tgm_pivot_df = tgm_pivot_df.reindex(full_range)

    # Rename index for clarity
    tgm_pivot_df.index.name = "date"

    # save the pivoted dataframe to a new CSV file
    tgm_pivot_df.to_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_daily_averages_pivoted.csv', encoding='utf-8')
    print(tgm_pivot_df.head())

def daily_averaging():
    raw_data_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_full_output.csv', index_col=0, encoding='utf-8')

    target_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\daily_average_targets.csv', encoding='utf-8')

    # create a dictionary from the target dataframe for easy lookup
    target_dict = target_df.set_index('site')['target_count'].to_dict()

    # Ensure datetime is parsed
    raw_data_df["datetime"] = pd.to_datetime(raw_data_df["datetime"])

    default_threshold = 18
    daily_results = {}

    # Build a global date range (min→max across all sites)
    global_min = raw_data_df["datetime"].min().normalize()
    global_max = raw_data_df["datetime"].max().normalize()
    global_index = pd.date_range(global_min, global_max, freq="D")

    for site, site_df in raw_data_df.groupby("site"):
        site_df = site_df.set_index("datetime").sort_index()
        site_df.index = site_df.index.normalize()
        site_df['concentration'] = site_df['concentration'].where(site_df['concentration'] >= 0, np.nan)

        print (site_df.head())

        # Daily mean + count
        daily = site_df["concentration"].resample("D").agg(["mean", "count"])
        
        # Site-specific threshold
        count_threshold = target_dict.get(site, default_threshold)
        
        # Mask means below threshold
        daily.loc[daily["count"] < count_threshold, "mean"] = pd.NA
        
        # Reindex to global index
        daily = daily.reindex(global_index)
        
        # Store under site key
        daily_results[site] = daily

        # drop the count column for final output
        daily_results[site] = daily_results[site].drop(columns=['count'])

    # Concatenate with hierarchical columns (site → ["mean","count"])
    result_df = pd.concat(daily_results, axis=1)

    # Flatten index to yyyy-mm-dd
    result_df.index = result_df.index.date

    print(result_df.head(15))
    result_df.to_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_daily_averages.csv', encoding='utf-8')


def monthly_average():
    raw_data_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_full_output_2025-10-02.csv', index_col=0, encoding='utf-8')
    raw_data_df["datetime"] = pd.to_datetime(raw_data_df["datetime"])
    raw_data_df['concentration'] = raw_data_df['concentration'].where(raw_data_df['concentration'] >= 0, np.nan)

    # Build a global date range (min→max across all sites)
    global_min = raw_data_df["datetime"].min().normalize()
    global_max = raw_data_df["datetime"].max().normalize()
    global_index = pd.date_range(global_min, global_max, freq="ME")

    monthly_results = {}
    # group by site
    for site, site_df in raw_data_df.groupby('site'):
        # do a monthly mean
        monthly_mean = site_df.resample('M', on='datetime').mean()
        monthly_mean = monthly_mean.reindex(global_index)
        # Store under site key
        monthly_results[site] = monthly_mean
    
    # Concatenate with hierarchical columns (site → ["mean","count"])
    result_df = pd.concat(monthly_results, axis=1)

    # Flatten index to yyyy-mm-dd
    result_df.index = result_df.index.date

    print(result_df.head(15))
    result_df.to_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_monthly_averages.csv', encoding='utf-8')


def tgm_mk_analysis(sql_engine):
    # Load daily average data
    tgm_df = pd.read_csv(
        r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_monthly_averages.csv',
        index_col=0, encoding='utf-8'
    )
    tgm_df.index = pd.to_datetime(tgm_df.index)

    def annual_slope_from_monthly(monthly_slopes, month_counts=None):
        """
        Compute annual slope as a weighted average of monthly slopes.

        Parameters
        ----------
        monthly_slopes : dict or list
            - If dict: {month_number: slope}
            - If list: slopes[0] = January, ..., slopes[11] = December
            (but can be shorter than 12 if sparse)
        month_counts : dict, optional
            Mapping of {month_number: days_in_month}.
            If None, defaults to days in leap year (2000).

        Returns
        -------
        float
            Weighted mean annual slope using only available months.
        """

        # Handle list input (can be shorter than 12 months)
        if isinstance(monthly_slopes, list):
            slopes = {i+1: monthly_slopes[i] for i in range(len(monthly_slopes))}
        else:
            slopes = monthly_slopes

        # Default month_lengths = leap year
        if month_counts is None:
            month_counts = {m: calendar.monthrange(2000, m)[1] for m in range(1, 13)}

        # Keep only months where we actually have slope data
        valid_months = {m: slopes[m] for m in slopes if slopes[m] is not None and not np.isnan(slopes[m])}

        if not valid_months:
            return np.nan  # No data → can't compute slope

        # Restrict weights (days) to the months with data
        total_days = sum(month_counts[m] for m in valid_months.keys())

        annual_slope = sum(
            valid_months[m] * (month_counts[m] / total_days)
            for m in valid_months
        )

        return annual_slope

    results = []

    

    for site in tgm_df.columns:
        site_series = tgm_df[site].dropna()
        site_series.index = pd.to_datetime(site_series.index)
        site_series = pd.to_numeric(site_series, errors="coerce")

        # skip sites with too few observations
        # if len(site_series) < 12:
        #     print(f"⚠️ Skipping {site} — too few data points ({len(site_series)})")
        #     continue

        # check timespan coverage
        span_years = (site_series.index.max() - site_series.index.min()).days / 365.25
        if span_years < 5:
            print(f"⚠️ Skipping {site} — only {span_years:.1f} years of data")
            continue

        # Group by month
        site_df = site_series.to_frame(name="value")
        site_df["month"] = site_df.index.month
        monthly_results = []

        for month, month_df in site_df.groupby("month"):
            if month_df.index.year.nunique() < 5:  # require at least 5 years for that month
                continue

            try:
                res = mk.original_test(month_df["value"].values)  # ordinary MK
                monthly_results.append({
                    "month": month,
                    "trend": res.trend,
                    "p_value": res.p,
                    "slope": res.slope,
                    "n": len(month_df)
                })
            except Exception as e:
                print(f"❌ Error processing {site}, month {month}: {e}")
                continue

        if monthly_results:
            # Build dictionary of month → slope
            monthly_slopes = {mr["month"]: mr["slope"] for mr in monthly_results}
            annual_slope = annual_slope_from_monthly(monthly_slopes)

            # Calculate first year’s mean concentration for this site
            first_year = site_series.index.year.min()
            print (site, first_year)
            first_year_mean = site_series[site_series.index.year == first_year].mean()
            if first_year_mean == 0 or pd.isna(first_year_mean):
                print (site, "first year mean is zero or NaN, cannot compute annual slope normalized")
            else:
                annual_slope = annual_slope / first_year_mean * 100  # normalize to first year mean
                print (site,first_year_mean)
            
            # calculate the mean, max, min, 25th and 75th concentration percentiles
            mean_conc = site_series.mean()
            max_conc = site_series.max()    
            min_conc = site_series.min()
            p25_conc = site_series.quantile(0.25)
            p75_conc = site_series.quantile(0.75) 

            # find start and end dates
            start_date = site_series.index.min().date()  
            end_date = site_series.index.max().date()

            for mr in monthly_results:
                results.append({
                        "site": site,
                        "month": mr["month"],
                        "trend": mr["trend"],
                        "p_value": mr["p_value"],
                        "significant": mr["p_value"] < 0.05,
                        "slope": mr["slope"],
                        "n": mr["n"],
                        "years_span": span_years,
                        "annual_slope": annual_slope,
                    })

    results_df = pd.DataFrame(results)

    def combine_pvalues_fisher(pvalues):
        """Combine p-values with Fisher’s method."""
        pvalues = [p for p in pvalues if not pd.isna(p)]
        if len(pvalues) == 0:
            return np.nan
        chi_stat = -2 * np.sum(np.log(pvalues))
        return chi2.sf(chi_stat, 2 * len(pvalues))

    def annual_significance(mk_df):
        """
        Combine monthly MK results into annual significance using Fisher’s method.
        
        mk_df: DataFrame with columns [site, month, p_value, slope, annual_slope]
        Returns: DataFrame with one row per site and annual trend summary
        """
        results = []
        for site, group in mk_df.groupby("site"):
            combined_p = combine_pvalues_fisher(group["p_value"])
            annual_slope = group["annual_slope"].iloc[0]  # already computed

            # trend direction from slope
            if annual_slope > 0 and combined_p < 0.05:
                annual_trend = "increasing"
            elif annual_slope < 0 and combined_p < 0.05:
                annual_trend = "decreasing"
            else:
                annual_trend = "no trend"

            results.append({
                "SITE": site,
                "slope": annual_slope,
                "p": combined_p,
                "ANNUAL TREND": annual_trend
            })

        return pd.DataFrame(results)

    annual_results_df = annual_significance(results_df)


    
    # add site stats
    site_stats = []

    for site in tgm_df.columns:
        site_series = tgm_df[site].dropna()
        site_series.index = pd.to_datetime(site_series.index)
        site_series = pd.to_numeric(site_series, errors="coerce")

        # remove negative values
        site_series = site_series[site_series >= 0]

        if len(site_series) == 0:
            continue

        start_date = site_series.index.min().date()
        end_date = site_series.index.max().date()
        mean_conc = site_series.mean()
        max_conc = site_series.max()
        min_conc = site_series.min()
        p25_conc = site_series.quantile(0.25)
        p75_conc = site_series.quantile(0.75)

        site_stats.append({
            "SITE": site,
            "START DATE": start_date,
            "END DATE": end_date,
            "MEAN CONC": mean_conc,
            "MAX CONC": max_conc,
            "MIN CONC": min_conc,
            "25TH CONC": p25_conc,
            "75TH CONC": p75_conc
        })

    site_stats_df = pd.DataFrame(site_stats)

    annual_results_df = annual_results_df.merge(site_stats_df, on="SITE", how="left")

    # grab the sites list from the sites table
    sql_data_query = """
                    SELECT DISTINCT ON (site) 
                    site AS "SITE",
                    country AS "COUNTRY", 
                    latdecd AS "LAT", 
                    londecd AS "LON"
                    FROM hgee_active
                    ORDER BY site;
                    """
    with sql_engine.connect() as conn:
        sites_df = pd.read_sql_query(sql_data_query, conn)
    
    # merge the lat/lon into the annual results
    annual_results_df = annual_results_df.merge(sites_df, on='SITE', how='left')

    # sort the dataframe by country, then site
    annual_results_df.sort_values(by=['COUNTRY', 'SITE'], inplace=True)

    # reorder the columns
    annual_results_df = annual_results_df[[
        "SITE", "COUNTRY", "LAT", "LON", "START DATE", "END DATE",
        "MEAN CONC", "MAX CONC", "MIN CONC", "25TH CONC", "75TH CONC",
        "slope", "p", "ANNUAL TREND"
    ]]

    annual_results_df.to_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_annual_M-K_results_2025-10-07.csv', index=False, encoding='utf-8')
    # print(annual_results_df.head())


def histogram():
    # read in tgm annual results
    # df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\hgee_active_tgm_hg_table.csv', encoding='utf-8')

    # read in daily results
    df =  pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\tgm_daily_averages_2025-10-01.csv', index_col=0, encoding='utf-8')

    # read in the tgm active table to grab the site and country information
    sites_df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\hgee_active_tgm_hg_table.csv', encoding='utf-8')

    flat_df = df.reset_index().melt(
        id_vars=df.index.name,
        var_name='site',
        value_name='concentration'
    )

    # remove nans from the flat_df
    flat_df = flat_df.dropna(subset=['concentration'])

    # Convert datetime to pandas datetime if possible
    flat_df['datetime'] = pd.to_datetime(flat_df['datetime'], errors='coerce')

    print(flat_df.head())

    # Merge continent info into the flattened dataframe
    df = flat_df.merge(sites_df[["site", "country", "Continent"]], on="site", how="left")

    print (df.columns)

    # Reorder columns
    df = df[["datetime", "site", "country", "Continent", "concentration"]]

    print(df.head())

    # print out any sites with no continent
    missing_continent = df[df['Continent'].isna()]
    print("Sites with no continent:")
    print(missing_continent[['site', 'country']])

    # # plot a histogram of the mean concentrations for each continent
    # for continent in df['continent'].dropna().unique():
    #     continent_df = df[df['continent'] == continent]
    #     plt.figure(figsize=(10, 6))
    
    #     # Fixed bins of width 0.1 from 0 to 4
    #     bins = np.arange(0, 4 + 0.1, 0.1)


    #     # Create histogram with percentage weights
    #     n, bins, patches = plt.hist(
    #         continent_df['mean_concentration'],
    #         bins=bins,
    #         color='skyblue',
    #         edgecolor='black',
    #         weights=np.ones_like(continent_df['mean_concentration']) / len(continent_df) * 100
    #     )

    #     # Label each bar with percentage occurrence
    #     for count, patch in zip(n, patches):
    #         if count > 0:
    #             plt.text(
    #                 patch.get_x() + patch.get_width() / 2,
    #                 count,
    #                 f"{count:.1f}%",
    #                 ha="center",
    #                 va="bottom",
    #                 fontsize=8
    #             )

    #     # ⚙️ Set fixed axes limits
    #     plt.ylim(0, 50)  # Y axis from 0% to 50%
    #     plt.xlim(0, 4)   # X axis from 0 to 4

    #     plt.title(f'TGM Mean Concentration Histogram - {continent}')
    #     plt.xlabel('Mean Concentration (ng/m³)')
    #     plt.ylabel('Percentage Occurrence (%)')
    #     plt.grid(axis='y', alpha=0.75)

    #     out_dir = r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots'
    #     outfile = os.path.join(out_dir, f"tgm_mean_concentration_histogram_{continent}.png")
    #     plt.savefig(outfile)
    #     plt.close()

def table_check():
    df = pd.read_csv(r'\\econm3hwvfsp008.ncr.int.ec.gc.ca\arqp_data\Projects\OnGoing\Mercury\HGEE-Minamata\Results and Plots\wd_seasonal_M-K_results_2025-10-09.csv',encoding='utf-8')

#     cols_to_check = ["MEAN", "MIN", "MAX", "25TH", "75TH"]
# # --- 1️⃣ Check for negative values ---
#     for col in cols_to_check:
#         bad_rows = df[df[col] < 0]
#         if not bad_rows.empty:
#             print(f"\n🚫 Negative values found in '{col}':")
#             print(bad_rows[["site", "variable", col]])
#         else:
#             print(f"✅ No negative values in '{col}'")

    # --- 2️⃣ Check for p vs ANNUAL TREND consistency ---
    # Case 1: P > 0.05 should be 'no trend'
    p_high_bad = df[(df["p"] > 0.05) & (df["trend"] != "no trend")]
    if not p_high_bad.empty:
        print("\n🚫 p > 0.05 but trend not 'no trend':")
        # print(p_high_bad[["site", "season", "variable", "p", "slope", "trend"]])
    else:
        print("✅ All p > 0.05 rows correctly marked as no trend")

    # Case 2: P ≤ 0.05 and slope < 0 should be 'decreasing'
    p_low_dec_bad = df[(df["p"] <= 0.05) & (df["slope"] < 0) & (df["trend"] != "decreasing")]
    if not p_low_dec_bad.empty:
        print("\n🚫 P ≤ 0.05 and slope < 0 but trend not 'decreasing':")
        print(p_low_dec_bad[["site", "season", "variable", "p", "slope", "trend"]])
    else:
        print("✅ All negative significant slopes correctly marked as decreasing")

    # Case 3: P ≤ 0.05 and slope > 0 should be 'increasing'
    p_low_inc_bad = df[(df["p"] <= 0.05) & (df["slope"] > 0) & (df["trend"] != "increasing")]
    if not p_low_inc_bad.empty:
        print("\n🚫 P ≤ 0.05 and slope > 0 but trend not 'increasing':")
        print(p_low_inc_bad[["site", "season", "variable", "p", "slope", "trend"]])
    else:
        print("✅ All positive significant slopes correctly marked as increasing")
    
    required_variables = {"dep_mean", "mm_mean", "pwc"}
    sites_missing_vars = {}

    # for site, group in df.groupby("site", "season"):
    for site, group in df.groupby("site"):
        variables_present = set(group["variable"].unique())
        missing_vars = required_variables - variables_present
        if missing_vars:
            sites_missing_vars[site] = missing_vars

    if sites_missing_vars:
        print("\n🚫 Sites missing required variables:")
        for site, missing in sites_missing_vars.items():
            print(f" - {site}: missing {', '.join(missing)}")
    else:
        print("✅ All sites have dep_mean, mm_mean, and pwc")

# Run the Gantt plotter
# gantt_plotter(sql_engine)

# Run the table pivot function
# table_pivot()

# daily_averaging
# daily_averaging()

# Run the monthly averaging
# monthly_average()

# Run the TGM MK analysis
# tgm_mk_analysis(sql_engine)

# Run the histogram function
# histogram()

# do a table check
table_check()