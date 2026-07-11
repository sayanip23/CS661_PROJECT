"""
utils/analytics/shared.py

Shared analytical utility functions used across multiple analytics pipelines.
Centralizes common computations to eliminate code duplication.
"""

import pandas as pd
import functools
import copy

def safe_lru_cache(maxsize=32):
    """
    LRU cache that safely returns shallow copies of pandas DataFrames and dicts 
    to prevent accidental mutations while preserving extreme performance.
    """
    def decorator(func):
        cached_func = functools.lru_cache(maxsize=maxsize)(func)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = cached_func(*args, **kwargs)
            if isinstance(result, tuple):
                return tuple(
                    item.copy(deep=False) if isinstance(item, pd.DataFrame) else (item.copy() if hasattr(item, "copy") else copy.deepcopy(item))
                    for item in result
                )
            if isinstance(result, pd.DataFrame):
                return result.copy(deep=False)
            if hasattr(result, "copy"):
                return result.copy()
            return copy.deepcopy(result)
        return wrapper
    return decorator


def compute_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes daily percentage returns per company as a decimal fraction.

    Formula: Return_t = (Close_t - Close_(t-1)) / Close_(t-1)

    The first trading day of each company will have NaN (no prior close),
    which is expected and handled downstream.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain 'Company' and 'Close' columns, sorted by
        [Company, Date].

    Returns
    -------
    pd.DataFrame
        Original dataframe with an added 'Daily_Return' column.
    """
    df = df.copy()
    df["Daily_Return"] = df.groupby("Company")["Close"].pct_change()
    return df
