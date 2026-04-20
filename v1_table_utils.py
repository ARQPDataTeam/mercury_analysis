import pandas as pd
import numpy as np
from sqlalchemy import text
import logging

# -----------------------------
# Logger setup (adjust as needed)
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def retrieve_v0_table_data(engine: "sqlalchemy.engine.Engine") -> pd.DataFrame:
    """Retrieve the v0 table data."""
    try:
        v0_df = pd.read_sql(
            "SELECT samplename, kitid, samplerid, sampleid, sampletype, hg FROM mpn__tgm_v0",
            engine
        )
        logger.info("V0 table data retrieved successfully")
        return v0_df
    except Exception as e:
        logger.error(f"Error retrieving V0 table: {str(e)}")
        raise

def retrieve_v1_table_kitids(engine: "sqlalchemy.engine.Engine") -> pd.DataFrame:
    """Retrieve existing kitids from v1 table."""
    try:
        v1_kitids = pd.read_sql("SELECT kitid FROM mpn__tgm_v1", engine)
        logger.info("V1 table kitids retrieved successfully")
        return v1_kitids
    except Exception as e:
        logger.error(f"Error retrieving V1 kitids: {str(e)}")
        raise

def retrieve_tracking_info(engine: "sqlalchemy.engine.Engine") -> pd.DataFrame:
    """Retrieve passive sampling tracking information."""
    try:
        tracking_df = pd.read_sql(
            """
            SELECT kitid, sample_start, sample_end, altsiteid
            FROM dcp_passive_sample_tracking
            """,
            engine
        )
        tracking_df["sample_start"] = pd.to_datetime(tracking_df["sample_start"], utc=True, errors="coerce")
        tracking_df["sample_end"] = pd.to_datetime(tracking_df["sample_end"], utc=True, errors="coerce")

        # rename the sample_start and sample_end columns to start_dt and end_dt
        tracking_df = tracking_df.rename(columns={
            "sample_start": "start_dt",
            "sample_end": "end_dt",
        })
        
        logger.info("Tracking data retrieved successfully")
        return tracking_df
    except Exception as e:
        logger.error(f"Error retrieving tracking info: {str(e)}")
        raise

def met_data_load(engine: "sqlalchemy.engine.Engine", altsiteid: str) -> pd.DataFrame:
    """Load meteorological data for a given site."""
    try:
        sql = text("""
            SELECT datetime, temperature, wind_speed
            FROM wmo_met_v0
            WHERE altsiteid = :altsiteid
        """)
        met_df = pd.read_sql(sql, engine, params={"altsiteid": altsiteid})
        met_df["datetime"] = pd.to_datetime(met_df["datetime"], utc=True, errors="coerce")
        logger.info(f"Met data loaded for altsiteid {altsiteid}, {len(met_df)} records")
        return met_df
    except Exception as e:
        logger.error(f"Error loading met data for altsiteid {altsiteid}: {str(e)}")
        raise

def calculate_sample_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate sampler sums, blank sums, average, and blank-corrected masses."""
    try:
        df = df.copy()
        df["part"] = df["samplename"].str.extract(r"_([SB][12])$", expand=False)

        # Sampler sums
        sampler_sums = (
            df[df["sampletype"] == "sample"]
            .groupby(["kitid", "samplerid"], as_index=False)["hg"]
            .sum()
            .rename(columns={"hg": "sampler_sum"})
        )

        # smp_mass_1 and smp_mass_2
        sampler_wide = (
            sampler_sums.sort_values(["kitid", "samplerid"])
            .assign(sampler_num=lambda x: x.groupby("kitid").cumcount() + 1)
            .pivot(index="kitid", columns="sampler_num", values="sampler_sum")
            .rename(columns={1: "smp_mass_1", 2: "smp_mass_2"})
            .reset_index()
        )

        # Blank sum
        blank_sum = (
            df[df["sampletype"] == "blank"]
            .groupby("kitid", as_index=False)["hg"]
            .sum()
            .rename(columns={"hg": "blank_mass"})
        )

        # Combine
        result = (
            sampler_wide.merge(blank_sum, on="kitid", how="left")
            .assign(
                smp_mass_avg=lambda x: x[["smp_mass_1", "smp_mass_2"]].mean(axis=1),
                blank_corr_mass=lambda x: x["smp_mass_avg"] - x["blank_mass"]
            )
            .loc[:, ["kitid", "smp1_mass", "smp2_mass", "smp_mass_avg", "blank_mass", "blank_corr_mass"]]
            .sort_values("kitid")
            .reset_index(drop=True)
        )
        logger.info(f"Sample averages calculated for {len(result)} kitids")
        return result
    except Exception as e:
        logger.error(f"Error calculating sample averages: {str(e)}")
        raise

# -----------------------------
# MAIN V1 TABLE FUNCTION
# -----------------------------

def v1_table_upload(engine: "sqlalchemy.engine.Engine") -> pd.DataFrame:
    """
    Process v0 data, calculate sample averages, merge tracking info,
    and prepare v1 table for upload.
    Returns the fully prepared v1 dataframe.
    """
    try:
        v0_df = retrieve_v0_table_data(engine)
        v1_kitids = retrieve_v1_table_kitids(engine)
        tracking_df = retrieve_tracking_info(engine)
    except Exception:
        logger.error("Aborting v1 table upload due to data retrieval error.")
        raise

    # Remove duplicates
    v0_df = v0_df[~v0_df["kitid"].isin(v1_kitids["kitid"])]
    logger.info(f"{len(v0_df)} kitids remain after removing duplicates from v1 table")

    # Calculate sample averages
    sample_averages = calculate_sample_averages(v0_df)

    # Prepare blank v1 dataframe with all columns
    v1_columns = [
        'kitid', 'altsiteid', 'start_dt', 'end_dt', 'duration',
        'smp_mass_1', 'smp_mass_2', 'smp_mass_avg', 'blank_mass', 'blank_corr_mass',
        'conc', 'blank_corr_conc', 'tempav', 'tempa_std', 'ws_smean', 'ws_std', 'conc_adj'
    ]
    v1_df = pd.DataFrame(columns=v1_columns)
    v1_df['kitid'] = v0_df['kitid'].unique()

    # Merge sample averages
    v1_df = v1_df.merge(sample_averages, on='kitid', how='left')

    # Merge tracking info
    v1_df = v1_df.merge(tracking_df, on='kitid', how='left')

    # Calculate duration in days
    v1_df['duration'] = (v1_df['end_dt'] - v1_df['start_dt']).dt.total_seconds() / (24 * 3600)

    # Concentration calculations
    v1_df['conc'] = v1_df['smp_mass_avg'] / v1_df['duration'] * 0.1354
    v1_df['blank_corr_conc'] = v1_df['blank_corr_mass'] / v1_df['duration'] * 0.1354

    logger.info("V1 table prepared successfully")
    return v1_df