import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from utils.database import run_query




def load_data(start_date=None, end_date=None, sector=None, company=None) -> pd.DataFrame:
    """
    Loads the cleaned stock dataset from DuckDB, optionally restricted to a
    date range, a single sector, and/or a single company.
    """

    conditions = []
    params = []
    if start_date is not None:
        conditions.append("Date >= CAST(? AS DATE)")
        params.append(start_date)
    if end_date is not None:
        conditions.append("Date <= CAST(? AS DATE)")
        params.append(end_date)
    if sector is not None:
        conditions.append("Sector = ?")
        params.append(sector)
    if company is not None:
        conditions.append("Company = ?")
        params.append(company)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            Company,
            Sector,
            Date,
            Close
        FROM clean_stock_data
        {where_clause}
        ORDER BY Company, Date
    """

    df = run_query(query, tuple(params) if params else None)

    df["Date"] = pd.to_datetime(df["Date"])

    return df


def compute_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Daily_Return"] = df.groupby("Company")["Close"].pct_change()
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

    sector = df.groupby("Company")["Sector"].first()
    feature_matrix["Sector"] = feature_matrix["Company"].map(sector)

    return feature_matrix


def scale_features(feature_matrix: pd.DataFrame) -> np.ndarray:
    scaler = StandardScaler()
    return scaler.fit_transform(
        feature_matrix[["Annual_Return", "Annual_Volatility"]]
    )


def perform_kmeans(X: np.ndarray, n_clusters: int = 4) -> np.ndarray:
    # A sector/company filter can leave fewer companies than n_clusters.
    n_clusters = max(1, min(n_clusters, X.shape[0]))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    return kmeans.fit_predict(X)


def prepare_plot_data(start_date=None, end_date=None, sector=None, company=None):
    """
    Orchestrator: runs the full pipeline and returns
    (raw_df_with_returns, feature_matrix_with_clusters)
    """
    df = load_data(start_date=start_date, end_date=end_date, sector=sector, company=company)
    if df.empty:
        raise ValueError(
            "No data for the selected Date/Sector/Company filter combination "
            "(the Sector and Company filters may not match)."
        )
    df = compute_daily_returns(df)

    feature_matrix = prepare_features(df)
    X = scale_features(feature_matrix)
    feature_matrix["Cluster"] = perform_kmeans(X).astype(str)

    return df, feature_matrix


def load_company_prices(company: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Lightweight, targeted load for the price-chart panel: just the daily
    closes (+ daily return) for one company, without recomputing the
    clustering pipeline.
    """
    df = load_data(start_date=start_date, end_date=end_date, company=company)
    return compute_daily_returns(df)