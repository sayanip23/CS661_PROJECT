import pandas as pd
from utils.database import run_query

DEFAULT_WINDOW = 20

def _get_zscore_cte(window: int = DEFAULT_WINDOW, sector: str = None, company: str = None):
    """
    Returns the Common Table Expression (CTE) string required to compute
    rolling statistics and Z-Scores directly from the persistent database table,
    plus the bind params for its placeholders.

    Sector/company filters are applied to the source rows before the rolling
    window is computed. Since the window partitions by Company, narrowing to
    fewer companies doesn't disturb any single company's own rolling stats.
    """
    conditions = ["Sector IS NOT NULL", "Close IS NOT NULL"]
    params = []
    if sector is not None:
        conditions.append("Sector = ?")
        params.append(sector)
    if company is not None:
        conditions.append("Company = ?")
        params.append(company)
    where_clause = " AND ".join(conditions)

    cte = f"""
    WITH rolling_stats AS (
        SELECT
            Date::DATE AS Date,
            Company,
            Sector,
            Close,
            AVG(Close) OVER w AS Rolling_Mean,
            STDDEV_SAMP(Close) OVER w AS Rolling_Std
        FROM clean_stock_data
        WHERE {where_clause}
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
    return cte, params


# Queries for Market Shocks
def get_market_shocks(
    z_threshold: float,
    window: int = DEFAULT_WINDOW,
    sector: str = None,
    company: str = None,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:

    cte, params = _get_zscore_cte(window, sector=sector, company=company)

    date_conditions = []
    if start_date is not None:
        date_conditions.append("Date >= CAST(? AS DATE)")
    if end_date is not None:
        date_conditions.append("Date <= CAST(? AS DATE)")
    # Date range is applied here, after the rolling window is computed, so
    # the rolling average/std at the start of the range still reflects the
    # full lookback history rather than being truncated at the boundary.
    date_where = f"WHERE {' AND '.join(date_conditions)}" if date_conditions else ""

    query = f"""
    {cte}
    SELECT
        Date,
        SUM(CASE WHEN Z_Score < -? THEN 1 ELSE 0 END) AS Total_Crashes,
        SUM(CASE WHEN Z_Score > ? THEN 1 ELSE 0 END) AS Total_Rallies,
        COALESCE(AVG(CASE WHEN Z_Score < -? THEN Z_Score END), 0) AS Crash_Z_Avg,
        COALESCE(AVG(CASE WHEN Z_Score > ? THEN Z_Score END), 0) AS Rally_Z_Avg
    FROM cached_z_scores
    {date_where}
    GROUP BY Date
    ORDER BY Date;
    """

    params = params + [z_threshold, z_threshold, z_threshold, z_threshold]
    if start_date is not None:
        params.append(start_date)
    if end_date is not None:
        params.append(end_date)

    # Execute query using the repo's central database utility
    market_df = run_query(query, tuple(params))

    # Calculate Final Severity
    market_df["Crash_Severity"] = market_df["Total_Crashes"] * market_df["Crash_Z_Avg"]
    market_df["Rally_Severity"] = market_df["Total_Rallies"] * market_df["Rally_Z_Avg"]

    return market_df


# Queries for Cross-Section Data
def get_cross_section(
    target_date: str,
    window: int = DEFAULT_WINDOW,
    sector: str = None,
    company: str = None,
) -> pd.DataFrame:
    """Fetches exactly one day of company data for the dispersion plot."""
    clean_date = target_date.split('T')[0]
    cte, params = _get_zscore_cte(window, sector=sector, company=company)

    query = f"""
    {cte}
    SELECT Company, Sector, Close, Z_Score
    FROM cached_z_scores
    WHERE Date = ?
    """

    params = params + [clean_date]
    return run_query(query, tuple(params))
