import pandas as pd
import numpy as np
from utils.database import run_query
from utils.logger import get_logger
from utils.analytics.shared import safe_lru_cache

logger = get_logger(__name__)

@safe_lru_cache(maxsize=32)
def load_rrg_data(target_year: int) -> pd.DataFrame:
    """
    Fetches weekly downsampled data and calculates Relative Strength (RS).
    We fetch an extra 20 weeks before the target year to "burn in" the rolling averages.
    """
    start_date = f"{target_year - 1}-08-01" # 5 months prior for rolling window
    end_date = f"{target_year}-12-31"

    # DuckDB Query: Downsample to Weekly & Calculate Market Benchmark dynamically
    query = """
        WITH weekly_data AS (
            SELECT 
                Company, 
                Sector, 
                DATE_TRUNC('week', Date) AS WeekDate, 
                AVG(Close) AS WeeklyClose
            FROM clean_stock_data
            WHERE Date >= ? AND Date <= ?
              AND Close IS NOT NULL
            GROUP BY Company, Sector, DATE_TRUNC('week', Date)
        ),
        benchmark AS (
            SELECT 
                WeekDate, 
                AVG(WeeklyClose) AS MarketClose
            FROM weekly_data
            GROUP BY WeekDate
        )
        SELECT 
            w.Company, 
            w.Sector, 
            w.WeekDate, 
            w.WeeklyClose,
            b.MarketClose,
            (w.WeeklyClose / b.MarketClose) AS RS
        FROM weekly_data w
        JOIN benchmark b ON w.WeekDate = b.WeekDate
        ORDER BY w.Company, w.WeekDate
    """
    df = run_query(query, params=(start_date, end_date))
    df['WeekDate'] = pd.to_datetime(df['WeekDate'])
    return df

@safe_lru_cache(maxsize=32)
def prepare_rrg_features(target_year: int) -> pd.DataFrame:
    """Calculates JdK RS-Ratio and RS-Momentum."""
    try:
        df = load_rrg_data(target_year)
        if df.empty:
            return df

        # Standard RRG Math (14-Week Rolling Averages)
        # RS-Ratio = (RS / 14-Week Average of RS) * 100
        df['RS_14_MA'] = df.groupby('Company')['RS'].transform(lambda x: x.rolling(14).mean())
        df['RS_Ratio'] = (df['RS'] / df['RS_14_MA']) * 100

        # RS-Momentum = (RS-Ratio / 14-Week Average of RS-Ratio) * 100
        df['Ratio_14_MA'] = df.groupby('Company')['RS_Ratio'].transform(lambda x: x.rolling(14).mean())
        df['RS_Momentum'] = (df['RS_Ratio'] / df['Ratio_14_MA']) * 100

        # Filter out the "burn-in" period and keep only the requested year
        df = df[df['WeekDate'].dt.year == target_year].copy()
        
        # Clip extreme outliers so the Plotly axes don't jump wildly
        df['RS_Ratio'] = np.clip(df['RS_Ratio'], 85, 115)
        df['RS_Momentum'] = np.clip(df['RS_Momentum'], 85, 115)
        
        # Format dates as strings for Plotly animation frames
        df['Frame'] = df['WeekDate'].dt.strftime('%d-%b-%Y')
        
        # Sort carefully so Plotly doesn't glitch between frames
        df = df.sort_values(['Frame', 'Company'])
        
        return df
    except Exception as e:
        logger.error(f"Failed to prepare RRG features: {e}")
        return pd.DataFrame()