# utils/analytics/risk_return.py

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from utils.database import run_query
from utils.logger import get_logger
from utils.analytics.shared import compute_daily_returns, safe_lru_cache

logger = get_logger(__name__)


def load_data() -> pd.DataFrame:
    """Fetches clean data from DuckDB for risk-return profiling."""
    query = """
        SELECT Company, Sector, Date, Close
        FROM clean_stock_data
        WHERE Close IS NOT NULL
        ORDER BY Company, Date
    """
    df = run_query(query)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def compute_annual_return(df: pd.DataFrame) -> pd.Series:
    return df.groupby("Company")["Daily_Return"].mean() * 252


def compute_volatility(df: pd.DataFrame) -> pd.Series:
    return df.groupby("Company")["Daily_Return"].std() * np.sqrt(252)


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    annual_return = compute_annual_return(df)
    annual_volatility = compute_volatility(df)

    feature_matrix = pd.DataFrame({
        "Company": annual_return.index,
        "Annual_Return": annual_return.values,
        "Annual_Volatility": annual_volatility.values,
    })

    RISK_FREE_RATE = 0.05
    feature_matrix["Sharpe_Ratio"] = (feature_matrix["Annual_Return"] - RISK_FREE_RATE) / feature_matrix["Annual_Volatility"]

    sector = df.groupby("Company")["Sector"].first()
    feature_matrix["Sector"] = feature_matrix["Company"].map(sector)

    return feature_matrix


def scale_features(feature_matrix: pd.DataFrame) -> np.ndarray:
    scaler = StandardScaler()
    return scaler.fit_transform(
        feature_matrix[["Annual_Return", "Annual_Volatility"]]
    )


def perform_kmeans(X: np.ndarray, n_clusters: int = 4) -> np.ndarray:
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    return kmeans.fit_predict(X)


@safe_lru_cache(maxsize=1)
def prepare_plot_data():
    """
    Orchestrator: runs the full pipeline using DuckDB and returns
    (raw_df_with_returns, feature_matrix_with_clusters)
    """
    try:
        df = load_data()  # <-- Removed the 'path' argument here
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        df = compute_daily_returns(df)

        feature_matrix = prepare_features(df)
        X = scale_features(feature_matrix)
        feature_matrix["Cluster"] = perform_kmeans(X).astype(str)

        return df, feature_matrix
    except Exception as e:
        logger.error(f"Risk-Return pipeline failed: {e}")
        return pd.DataFrame(), pd.DataFrame()