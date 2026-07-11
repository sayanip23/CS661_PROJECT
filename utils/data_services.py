import functools
import pandas as pd
from utils.database import run_query

@functools.lru_cache(maxsize=1)
def get_all_companies() -> list:
    """Cached retrieval of all unique companies."""
    query = "SELECT DISTINCT Company FROM clean_stock_data ORDER BY Company"
    df = run_query(query)
    if df.empty:
        return []
    return df["Company"].tolist()

@functools.lru_cache(maxsize=1)
def get_all_sectors() -> list:
    """Cached retrieval of all unique sectors."""
    query = "SELECT DISTINCT Sector FROM clean_stock_data ORDER BY Sector"
    df = run_query(query)
    if df.empty:
        return []
    return df["Sector"].tolist()

def get_historical_prices(companies: list, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Retrieves closing prices for a list of companies, optionally filtered by date."""
    if not companies:
        return pd.DataFrame()
        
    placeholders = ", ".join(["?"] * len(companies))
    query = f"SELECT Date, Company, Close FROM clean_stock_data WHERE Company IN ({placeholders})"
    params = list(companies)
    
    if start_date and end_date:
        query += " AND Date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
        
    query += " ORDER BY Date"
    return run_query(query, params=tuple(params))
