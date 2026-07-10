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


def label_clusters(feature_matrix: pd.DataFrame) -> dict:
    """
    Maps the numeric cluster ids produced by KMeans to human-readable risk/
    return archetypes (e.g. "High Risk, High Return"). Cluster ids from KMeans
    are arbitrary and can be reassigned every time the filters change the
    input data, so labels are derived from each cluster's actual mean return
    and volatility *relative to the other clusters currently in view*, rather
    than hardcoded against a fixed id.

    Returns: {cluster_id (str): label (str)}
    """
    stats = feature_matrix.groupby("Cluster").agg(
        mean_return=("Annual_Return", "mean"),
        mean_vol=("Annual_Volatility", "mean"),
    )

    # rank=1 -> lowest, rank=n -> highest
    vol_rank = stats["mean_vol"].rank(method="first")
    ret_rank = stats["mean_return"].rank(method="first")
    n = len(stats)

    labels = {}
    for cluster_id in stats.index:
        v, r = vol_rank[cluster_id], ret_rank[cluster_id]

        if v == vol_rank.min():
            labels[cluster_id] = "Defensive / Low Volatility"
        elif v == vol_rank.max():
            labels[cluster_id] = (
                "High Risk, High Return" if r == ret_rank.max() else "High Risk, Low Return"
            )
        else:
            labels[cluster_id] = (
                "Moderate Risk, Steady Return" if r > n / 2 else "Low Risk, Low Return"
            )

    return labels


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
def compute_benchmark_cumulative_return(start_date=None, end_date=None):
    """
    Equal-weighted average cumulative return across all companies,
    used as a Nifty-50-wide benchmark line on the price chart.
    """
    df = load_data(start_date=start_date, end_date=end_date)
    df = compute_daily_returns(df)
    daily_avg = df.groupby("Date")["Daily_Return"].mean().reset_index()
    daily_avg["Cumulative_Return"] = (1 + daily_avg["Daily_Return"].fillna(0)).cumprod() - 1
    return daily_avg[["Date", "Cumulative_Return"]]