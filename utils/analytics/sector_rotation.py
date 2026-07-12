"""
utils/analytics/sector_rotation.py

Backend analytics pipeline for the Relative Rotation Graph (RRG).
Calculates rebased sector indices, Relative Strength (RS), RS-Ratio, and RS-Momentum
directly from the DuckDB database.
"""

import pandas as pd
from utils.database import run_query

RS_RATIO_WINDOW = 14
RS_MOMENTUM_WINDOW = 10
RESAMPLE_FREQ = "W"


def load_data(start_date=None, end_date=None) -> pd.DataFrame:
    """Fetches clean stock data from DuckDB and ensures proper datetime typing.

    Note: only date-range filtering is supported here (not sector/company).
    The RRG is inherently a sector-vs-sector-vs-market comparison, so
    narrowing the company/sector universe would remove the very comparison
    the page exists to show.
    """
    conditions = []
    params = []
    if start_date is not None:
        conditions.append("Date >= CAST(? AS DATE)")
        params.append(start_date)
    if end_date is not None:
        conditions.append("Date <= CAST(? AS DATE)")
        params.append(end_date)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT Company, Sector, Date, Close
        FROM clean_stock_data
        {where_clause}
        ORDER BY Sector, Company, Date;
    """
    try:
        df = run_query(query, tuple(params) if params else None)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch stock data from DuckDB: {e}")

    df["Date"] = pd.to_datetime(df["Date"])

    required = {"Company", "Sector", "Date", "Close"}
    if missing := required - set(df.columns):
        raise ValueError(f"Database table is missing columns: {missing}")

    return df


def create_sector_index(df: pd.DataFrame, weighting: str = "return") -> pd.DataFrame:
    """
    Collapses individual company stock prices into a daily index per sector.
    
    We default to 'return' weighting to rebase every stock to 100 on day one.
    This prevents expensive stocks (priced in the thousands) from overshadowing
    cheaper stocks in the sector average.
    """
    if weighting == "equal":
        sector_df = df.groupby(["Sector", "Date"], as_index=False)["Close"].mean()
        return sector_df.rename(columns={"Close": "SectorIndex"})

    if weighting == "return":
        tmp = df.copy()
        # Fast vectorized rebasing to 100 using the first available closing price
        first_closes = tmp.groupby("Company")["Close"].transform("first")
        tmp["Norm"] = (tmp["Close"] / first_closes) * 100

        sector_df = tmp.groupby(["Sector", "Date"], as_index=False)["Norm"].mean()
        return sector_df.rename(columns={"Norm": "SectorIndex"})

    raise ValueError("Weighting must be either 'equal' or 'return'.")


def create_market_index(df: pd.DataFrame, weighting: str = "return") -> pd.DataFrame:
    """
    Builds a custom market benchmark using the entire stock universe in our database.
    This prevents date-alignment bugs that happen when importing external CSV benchmarks.
    """
    if weighting == "equal":
        market_df = df.groupby("Date", as_index=False)["Close"].mean()
        return market_df.rename(columns={"Close": "MarketIndex"})

    if weighting == "return":
        tmp = df.copy()
        first_closes = tmp.groupby("Company")["Close"].transform("first")
        tmp["Norm"] = (tmp["Close"] / first_closes) * 100

        market_df = tmp.groupby("Date", as_index=False)["Norm"].mean()
        return market_df.rename(columns={"Norm": "MarketIndex"})

    raise ValueError("Weighting must be either 'equal' or 'return'.")


def compute_relative_strength(sector_df: pd.DataFrame, market_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates raw Relative Strength (RS = Sector / Market * 100).
    Both series are rebased to 100 at their common starting date so they scale cleanly.
    """
    sector_df = sector_df.copy()
    market_df = market_df.copy()

    sector_start = sector_df.groupby("Sector")["SectorIndex"].transform("first")
    sector_df["SectorIndex"] = (sector_df["SectorIndex"] / sector_start) * 100

    market_start = market_df["MarketIndex"].iloc[0]
    market_df["MarketIndex"] = (market_df["MarketIndex"] / market_start) * 100

    merged = sector_df.merge(market_df, on="Date", how="inner")
    merged["RS"] = (merged["SectorIndex"] / merged["MarketIndex"]) * 100
    return merged


def compute_rs_ratio(df: pd.DataFrame, window: int = RS_RATIO_WINDOW) -> pd.DataFrame:
    """
    Normalizes raw RS against its own rolling simple moving average.
    This forces all sectors to oscillate around a center baseline of 100.
    """
    df = df.copy()
    rolling_ma = df.groupby("Sector")["RS"].transform(
        lambda s: s.rolling(window, min_periods=window).mean()
    )
    df["RS_Ratio"] = 100 * (df["RS"] / rolling_ma)
    return df


def compute_rs_momentum(df: pd.DataFrame, window: int = RS_MOMENTUM_WINDOW) -> pd.DataFrame:
    """
    Measures the velocity (rate of change) of the RS-Ratio over time.
    A value above 0 means relative performance is accelerating; below 0 means it's fading.
    """
    df = df.copy()
    shifted_ratio = df.groupby("Sector")["RS_Ratio"].shift(window)
    df["RS_Momentum"] = ((df["RS_Ratio"] / shifted_ratio) - 1) * 100
    return df


def classify_quadrants(df: pd.DataFrame) -> pd.DataFrame:
    """Assigns each sector to an RRG quadrant based on the 100/0 intersection."""
    df = df.copy()

    high_rs = df["RS_Ratio"] >= 100
    high_mom = df["RS_Momentum"] >= 0

    df["Quadrant"] = "Improving"
    df.loc[high_rs & high_mom, "Quadrant"] = "Leading"
    df.loc[high_rs & ~high_mom, "Quadrant"] = "Weakening"
    df.loc[~high_rs & ~high_mom, "Quadrant"] = "Lagging"

    # Mask early warm-up periods where moving averages haven't populated yet
    not_warmed_up = df["RS_Ratio"].isna() | df["RS_Momentum"].isna()
    df.loc[not_warmed_up, "Quadrant"] = None

    return df


def prepare_animation_data(df: pd.DataFrame, freq: str = RESAMPLE_FREQ) -> pd.DataFrame:
    """
    Resamples daily metrics to weekly/monthly intervals.
    Plotly animations struggle with thousands of daily frames, so taking the last 
    trading day of each week keeps the UI fast and responsive.
    """
    df = df.dropna(subset=["RS_Ratio", "RS_Momentum"]).copy()
    df["Period"] = df["Date"].dt.to_period(freq).dt.start_time

    anim = (
        df.groupby(["Sector", "Period"], as_index=False)
        .agg(
            RS_Ratio=("RS_Ratio", "last"),
            RS_Momentum=("RS_Momentum", "last"),
            Quadrant=("Quadrant", "last"),
        )
        .sort_values(["Sector", "Period"])
    )
    anim["PeriodStr"] = anim["Period"].dt.strftime("%Y-%m-%d")
    return anim


def run_sector_rotation_pipeline(
    weighting: str = "return", freq: str = RESAMPLE_FREQ, start_date=None, end_date=None
) -> dict:
    """Executes the full RRG data pipeline and returns datasets for the Dash UI."""
    df = load_data(start_date=start_date, end_date=end_date)
    sector_df = create_sector_index(df, weighting=weighting)
    market_df = create_market_index(df, weighting=weighting)

    rs_df = compute_relative_strength(sector_df, market_df)
    rs_df = compute_rs_ratio(rs_df)
    rs_df = compute_rs_momentum(rs_df)
    rs_df = classify_quadrants(rs_df)
    anim_df = prepare_animation_data(rs_df, freq=freq)

    return {
        "raw_df": df,
        "sector_df": sector_df,
        "market_df": market_df,
        "rs_df": rs_df,
        "anim_df": anim_df,
        "sectors": sorted(rs_df["Sector"].unique()),
    }


if __name__ == "__main__":
    # Quick verification script for terminal testing
    print("Running sector rotation pipeline...")
    pipeline = run_sector_rotation_pipeline()
    print(f"Success! Processed {len(pipeline['sectors'])} sectors.")
    print("\nRecent animation data sample:")
    print(pipeline["anim_df"].tail(10))