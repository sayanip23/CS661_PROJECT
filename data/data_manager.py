# data/data_manager.py

import pandas as pd
from utils.database import run_query

def get_all_clean_data() -> pd.DataFrame:
    """
    Fetches the entire clean dataset from DuckDB.
    Use this sparingly; prefer specific SQL queries for analytics components.
    """
    query = "SELECT * FROM clean_stock_data"
    df = run_query(query)
    df["Date"] = pd.to_datetime(df["Date"])
    return df