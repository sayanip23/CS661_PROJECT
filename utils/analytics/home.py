import pandas as pd
from utils.analytics.shared import safe_lru_cache
from utils.analytics.treemap import run_treemap_pipeline
from utils.database import run_query

@safe_lru_cache(maxsize=1)
def compute_executive_metrics() -> dict:
    """
    Computes all necessary metrics for the Executive Dashboard.
    Uses the treemap pipeline for core calculations to maximize reuse and caching.
    """
    # Fetch global static statistics
    stats_query = """
    SELECT 
        COUNT(DISTINCT Company) AS num_stocks,
        COUNT(DISTINCT Sector) AS num_sectors,
        COUNT(DISTINCT EXTRACT(YEAR FROM Date)) AS num_years,
        COUNT(*) AS num_records
    FROM clean_stock_data
    """
    stats_df = run_query(stats_query)
    num_stocks = stats_df["num_stocks"].iloc[0] if not stats_df.empty else 0
    num_sectors = stats_df["num_sectors"].iloc[0] if not stats_df.empty else 0
    num_years = stats_df["num_years"].iloc[0] if not stats_df.empty else 0
    num_records = stats_df["num_records"].iloc[0] if not stats_df.empty else 0

    # Retrieve processed performance metrics from the existing treemap pipeline
    # We use a broad time range for the home page (2021-2022 for the snapshot, but we can do the last 2 years of the dataset)
    # The dataset ends in 2022. We'll use 2021-2022 as the 'recent' snapshot.
    res = run_treemap_pipeline("2021-01-01", "2022-12-31", size_metric="Total_Volume", group_by="Sector")
    
    comp_df = res["company_growth"]
    sector_df = res["sector_growth"]
    raw_df = res["raw_data"]

    if comp_df.empty or sector_df.empty:
        return _empty_metrics(num_stocks, num_sectors, num_years, num_records)

    # 1. Market Health Score
    advancing = len(comp_df[comp_df["CAGR"] > 0])
    declining = len(comp_df[comp_df["CAGR"] <= 0])
    total = advancing + declining
    breadth_ratio = advancing / total if total > 0 else 0

    sector_advancing = len(sector_df[sector_df["CAGR"] > 0])
    sector_total = len(sector_df)
    sector_ratio = sector_advancing / sector_total if sector_total > 0 else 0

    market_volatility = comp_df["Volatility"].mean()
    # Normalize volatility roughly: 0.1 is great, 0.4+ is bad
    vol_score = max(0, min(100, (0.4 - market_volatility) / 0.3 * 100))

    # Health Score Calculation: 40% Breadth, 40% Sector Participation, 20% Volatility
    health_score = int(breadth_ratio * 40 + sector_ratio * 40 + (vol_score / 100) * 20)
    
    if health_score >= 80:
        health_status = "Excellent"
    elif health_score >= 60:
        health_status = "Healthy"
    elif health_score >= 40:
        health_status = "Neutral"
    elif health_score >= 20:
        health_status = "Weak"
    else:
        health_status = "Critical"

    # Market Direction
    if health_score >= 60:
        direction = "Bullish"
    elif health_score <= 40:
        direction = "Bearish"
    else:
        direction = "Neutral"

    # Averages
    avg_return = comp_df["CAGR"].mean()
    avg_vol = market_volatility
    avg_sharpe = comp_df["Sharpe_Ratio"].mean()
    
    # Top/Bottom Performers
    best_sector = sector_df.loc[sector_df["CAGR"].idxmax()]
    worst_sector = sector_df.loc[sector_df["CAGR"].idxmin()]
    
    highest_cagr_comp = comp_df.loc[comp_df["CAGR"].idxmax()]
    lowest_cagr_comp = comp_df.loc[comp_df["CAGR"].idxmin()]

    # Movers Lists
    top_companies = comp_df.nlargest(5, "CAGR")[["Company", "CAGR"]].to_dict('records')
    bottom_companies = comp_df.nsmallest(5, "CAGR")[["Company", "CAGR"]].to_dict('records')
    top_sectors = sector_df.nlargest(5, "CAGR")[["Sector", "CAGR"]].to_dict('records')
    bottom_sectors = sector_df.nsmallest(5, "CAGR")[["Sector", "CAGR"]].to_dict('records')

    # Key Insight
    top_sharpe_sector = sector_df.loc[sector_df["CAGR"] / sector_df["Volatility"].replace(0, 0.001) > 0]
    if not top_sharpe_sector.empty:
        best_sharpe = sector_df.loc[(sector_df["CAGR"] / sector_df["Volatility"].replace(0, 0.001)).idxmax()]
        insight = f"{best_sharpe['Sector']} currently demonstrates the strongest risk-adjusted returns."
    else:
        insight = f"{best_sector['Sector']} currently has the highest growth rate."

    # Market Summary
    summary = (
        f"{best_sector['Sector']} continues to outperform the broader market. "
        f"Conversely, {worst_sector['Sector']} is underperforming. "
        f"Overall market volatility remains {'high' if avg_vol > 0.25 else 'moderate' if avg_vol > 0.15 else 'low'}."
    )

    # Mini Trend Data (Aggregated Daily Close)
    market_trend = raw_df.groupby("Date")["Close"].mean().reset_index()

    return {
        "num_stocks": num_stocks,
        "num_sectors": num_sectors,
        "num_years": num_years,
        "num_records": num_records,
        "health_score": health_score,
        "health_status": health_status,
        "direction": direction,
        "avg_return": avg_return,
        "avg_vol": avg_vol,
        "avg_sharpe": avg_sharpe,
        "best_sector": best_sector["Sector"],
        "worst_sector": worst_sector["Sector"],
        "highest_cagr": highest_cagr_comp["CAGR"],
        "lowest_cagr": lowest_cagr_comp["CAGR"],
        "highest_cagr_name": highest_cagr_comp["Company"],
        "lowest_cagr_name": lowest_cagr_comp["Company"],
        "top_companies": top_companies,
        "bottom_companies": bottom_companies,
        "top_sectors": top_sectors,
        "bottom_sectors": bottom_sectors,
        "insight": insight,
        "summary": summary,
        "market_trend": market_trend,
        "breadth": {"advancing": advancing, "declining": declining},
        "last_updated": "2022-12-31" # Since our dataset ends here
    }

def _empty_metrics(num_stocks, num_sectors, num_years, num_records):
    return {
        "num_stocks": num_stocks,
        "num_sectors": num_sectors,
        "num_years": num_years,
        "num_records": num_records,
        "health_score": 50,
        "health_status": "Neutral",
        "direction": "Neutral",
        "avg_return": 0,
        "avg_vol": 0,
        "avg_sharpe": 0,
        "best_sector": "N/A",
        "worst_sector": "N/A",
        "highest_cagr": 0,
        "lowest_cagr": 0,
        "highest_cagr_name": "N/A",
        "lowest_cagr_name": "N/A",
        "top_companies": [],
        "bottom_companies": [],
        "top_sectors": [],
        "bottom_sectors": [],
        "insight": "No data available.",
        "summary": "No data available.",
        "market_trend": pd.DataFrame(),
        "breadth": {"advancing": 0, "declining": 0},
        "last_updated": "N/A"
    }
