"""
utils/analytics/treemap.py

Backend analytics for Sector-Level Growth Attribution (Task 4.5).

Pipeline:
    load_clean_data()
        -> filter_by_date_range()
        -> compute_company_growth()
        -> aggregate_sector_growth()
        -> build_hierarchy_dataframe()
"""

import os

import numpy as np
import pandas as pd


CLEAN_DATA_PATH = "data/processed/clean_stock_data.csv"

# A company needs at least this many trading days inside the selected
# window for its CAGR to be considered reliable (avoids wild CAGR values
# from newly-listed stocks with only a handful of trading days).
MIN_TRADING_DAYS = 30

ROOT_ID = "NIFTY-50"
ROOT_LABEL = "NIFTY-50"


# ---------------------------------------------------------------------------
# Step 1: Load Data
# ---------------------------------------------------------------------------
def load_clean_data(path: str = CLEAN_DATA_PATH) -> pd.DataFrame:
    """
    Reads the cleaned stock dataset produced by utils/preprocessing.py.

    Expects (at minimum) columns: Company, Sector, Date, Close, Volume.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Clean data not found at '{path}'. "
            "Run `python utils/loader.py` then `python utils/preprocessing.py` first."
        )

    df = pd.read_csv(path, parse_dates=["Date"])

    required_cols = {"Company", "Sector", "Date", "Close", "Volume"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"clean_stock_data.csv is missing required columns: {missing}")

    df = df.dropna(subset=["Sector"])
    df = df.sort_values(["Company", "Date"]).reset_index(drop=True)

    return df


def get_year_bounds(df: pd.DataFrame):
    """Returns (min_year, max_year) available in the dataset, for slider bounds."""
    return int(df["Date"].dt.year.min()), int(df["Date"].dt.year.max())


# ---------------------------------------------------------------------------
# Step 2: Restrict to the user-selected window
# ---------------------------------------------------------------------------
def filter_by_date_range(df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Restricts the dataset to [start_date, end_date] (inclusive). Either bound
    may be None to leave that side open.
    """
    out = df
    if start_date is not None:
        out = out[out["Date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        out = out[out["Date"] <= pd.to_datetime(end_date)]
    return out


# ---------------------------------------------------------------------------
# Step 3: Per-company CAGR + Total Volume
# ---------------------------------------------------------------------------
def compute_company_growth(
    df: pd.DataFrame,
    min_trading_days: int = MIN_TRADING_DAYS,
) -> pd.DataFrame:
    """
    For every company, computes:
        - Start/End close price and date within the (already filtered) window
        - CAGR = (End_Close / Start_Close) ** (1 / years) - 1
        - Total traded Volume and Turnover across the window
        - Number of trading days observed

    Companies with fewer than `min_trading_days` observations, or a
    non-positive starting price, are dropped (CAGR would be unreliable
    or undefined).

    Returns
    -------
    pd.DataFrame with one row per company:
        Company, Sector, Start_Date, End_Date, Start_Close, End_Close,
        Years, CAGR, Total_Volume, Total_Turnover, Trading_Days
    """
    has_turnover = "Turnover" in df.columns
    records = []

    for (company, sector), group in df.groupby(["Company", "Sector"]):
        group = group.sort_values("Date")

        if len(group) < min_trading_days:
            continue

        start_row = group.iloc[0]
        end_row = group.iloc[-1]

        start_close = start_row["Close"]
        end_close = end_row["Close"]

        if pd.isna(start_close) or pd.isna(end_close) or start_close <= 0:
            continue

        years = (end_row["Date"] - start_row["Date"]).days / 365.25
        if years <= 0:
            continue

        cagr = (end_close / start_close) ** (1 / years) - 1

        records.append({
            "Company": company,
            "Sector": sector,
            "Start_Date": start_row["Date"],
            "End_Date": end_row["Date"],
            "Start_Close": start_close,
            "End_Close": end_close,
            "Years": years,
            "CAGR": cagr,
            "Total_Volume": group["Volume"].sum(),
            "Total_Turnover": group["Turnover"].sum() if has_turnover else np.nan,
            "Trading_Days": len(group),
        })

    result = pd.DataFrame.from_records(records)

    if result.empty:
        raise ValueError(
            "No companies had enough trading days in the selected window "
            "to compute a reliable CAGR. Try widening the date range."
        )

    return result


# ---------------------------------------------------------------------------
# Step 4: Sector-Level Aggregation
# ---------------------------------------------------------------------------
def aggregate_sector_growth(company_growth: pd.DataFrame) -> pd.DataFrame:
    """
    Rolls the per-company table up to one row per Sector:
        - Total_Volume / Total_Turnover: summed across constituent companies
        - CAGR: volume-weighted average of constituent CAGRs (a heavily-traded
          stock's growth moves the sector figure more than a thinly-traded
          one -- a simple stand-in for a market-cap-weighted sector index,
          since the dataset has no shares-outstanding/market-cap field).
        - Num_Companies: constituent count, shown on hover.

    Returns
    -------
    pd.DataFrame with columns: Sector, Total_Volume, Total_Turnover, CAGR, Num_Companies
    """
    def weighted_cagr(g):
        weights = g["Total_Volume"]
        if weights.sum() == 0:
            return g["CAGR"].mean()
        return np.average(g["CAGR"], weights=weights)

    sector_df = (
        company_growth.groupby("Sector")
        .apply(lambda g: pd.Series({
            "Total_Volume": g["Total_Volume"].sum(),
            "Total_Turnover": g["Total_Turnover"].sum(),
            "CAGR": weighted_cagr(g),
            "Num_Companies": len(g),
        }))
        .reset_index()
    )

    return sector_df


# ---------------------------------------------------------------------------
# Step 5: Build the Treemap/Sunburst hierarchy
# ---------------------------------------------------------------------------
def build_hierarchy_dataframe(
    company_growth: pd.DataFrame,
    sector_growth: pd.DataFrame,
    size_metric: str = "Total_Volume",
) -> pd.DataFrame:
    """
    Builds a flat ids/parents/values table that Plotly's go.Treemap and
    go.Sunburst both consume directly, with three levels:

        NIFTY-50 (root) -> Sector -> Company

    `size_metric` controls what determines segment area/arc size
    ('Total_Volume' or 'Total_Turnover'); CAGR always drives color.

    Returns
    -------
    pd.DataFrame with columns: id, parent, label, value, cagr, level, hover_extra
    """
    rows = []

    root_value = sector_growth[size_metric].sum()
    root_cagr = (
        np.average(sector_growth["CAGR"], weights=sector_growth[size_metric])
        if sector_growth[size_metric].sum() > 0
        else sector_growth["CAGR"].mean()
    )

    rows.append({
        "id": ROOT_ID,
        "parent": "",
        "label": ROOT_LABEL,
        "value": root_value,
        "cagr": root_cagr,
        "level": "root",
        "hover_extra": f"{sector_growth.shape[0]} sectors",
    })

    for _, srow in sector_growth.iterrows():
        rows.append({
            "id": srow["Sector"],
            "parent": ROOT_ID,
            "label": srow["Sector"],
            "value": srow[size_metric],
            "cagr": srow["CAGR"],
            "level": "sector",
            "hover_extra": f"{int(srow['Num_Companies'])} companies",
        })

    for _, crow in company_growth.iterrows():
        rows.append({
            "id": f"{crow['Sector']}/{crow['Company']}",
            "parent": crow["Sector"],
            "label": crow["Company"],
            "value": crow[size_metric],
            "cagr": crow["CAGR"],
            "level": "company",
            "hover_extra": f"{crow['Trading_Days']} trading days",
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Convenience: run the full pipeline in one call
# ---------------------------------------------------------------------------
def run_treemap_pipeline(
    path: str = CLEAN_DATA_PATH,
    start_date=None,
    end_date=None,
    size_metric: str = "Total_Volume",
    min_trading_days: int = MIN_TRADING_DAYS,
):
    """
    Runs steps 1-5 end to end. Used by pages/treemap.py.

    Returns
    -------
    dict with keys:
        'company_growth' : per-company CAGR/volume table
        'sector_growth'  : per-sector aggregated table
        'hierarchy'      : flat ids/parents/values table for the chart
        'year_bounds'    : (min_year, max_year) of the full dataset
    """
    df = load_clean_data(path)
    year_bounds = get_year_bounds(df)

    windowed = filter_by_date_range(df, start_date, end_date)
    company_growth = compute_company_growth(windowed, min_trading_days=min_trading_days)
    sector_growth = aggregate_sector_growth(company_growth)
    hierarchy = build_hierarchy_dataframe(company_growth, sector_growth, size_metric=size_metric)

    return {
        "company_growth": company_growth,
        "sector_growth": sector_growth,
        "hierarchy": hierarchy,
        "year_bounds": year_bounds,
    }


if __name__ == "__main__":
    # Quick smoke test: python utils/analytics/treemap.py
    result = run_treemap_pipeline()
    print("Year bounds:", result["year_bounds"])
    print("Companies:", len(result["company_growth"]))
    print("Sectors:", len(result["sector_growth"]))
    print(result["sector_growth"].sort_values("CAGR", ascending=False).to_string(index=False))