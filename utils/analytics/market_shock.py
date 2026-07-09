import pandas as pd
from utils.database import run_query

DEFAULT_WINDOW = 20

def _get_zscore_cte(window: int = DEFAULT_WINDOW) -> str:
    """
    Returns the Common Table Expression (CTE) string required to compute 
    rolling statistics and Z-Scores directly from the persistent database table.
    """
    return f"""
    WITH rolling_stats AS (
        SELECT 
            Date::DATE AS Date,
            Company,
            Sector,
            Close,
            AVG(Close) OVER w AS Rolling_Mean,
            STDDEV_SAMP(Close) OVER w AS Rolling_Std
        FROM clean_stock_data
        WHERE Sector IS NOT NULL AND Close IS NOT NULL
        WINDOW w AS (PARTITION BY Company ORDER BY Date ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW)
    ),
    cached_z_scores AS (
        SELECT 
            Date,
            Company,
            Sector,
            Close,
            (Close - Rolling_Mean) / NULLIF(Rolling_Std, 0) AS Z_Score
        FROM rolling_stats
        WHERE Rolling_Std IS NOT NULL
    )
    """


# Queries for Market Shocks
def get_market_shocks(z_threshold: float, window: int = DEFAULT_WINDOW) -> pd.DataFrame:

    cte = _get_zscore_cte(window)
    
    query = f"""
    {cte}
    SELECT 
        Date,
        SUM(CASE WHEN Z_Score < -{z_threshold} THEN 1 ELSE 0 END) AS Total_Crashes,
        SUM(CASE WHEN Z_Score > {z_threshold} THEN 1 ELSE 0 END) AS Total_Rallies,
        COALESCE(AVG(CASE WHEN Z_Score < -{z_threshold} THEN Z_Score END), 0) AS Crash_Z_Avg,
        COALESCE(AVG(CASE WHEN Z_Score > {z_threshold} THEN Z_Score END), 0) AS Rally_Z_Avg
    FROM cached_z_scores
    GROUP BY Date
    ORDER BY Date;
    """
    
    # Execute query using the repo's central database utility
    market_df = run_query(query)
    
    # Calculate Final Severity
    market_df["Crash_Severity"] = market_df["Total_Crashes"] * market_df["Crash_Z_Avg"]
    market_df["Rally_Severity"] = market_df["Total_Rallies"] * market_df["Rally_Z_Avg"]
    
    return market_df


# Queries for Cross-Section Data
def get_cross_section(target_date: str, window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """Fetches exactly one day of company data for the dispersion plot."""
    clean_date = target_date.split('T')[0]
    cte = _get_zscore_cte(window)
    
    query = f"""
    {cte}
    SELECT Company, Sector, Close, Z_Score
    FROM cached_z_scores
    WHERE Date = '{clean_date}'
    """
    
    return run_query(query)