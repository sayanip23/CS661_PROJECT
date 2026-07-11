# utils/analytics/risk_return.py

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from utils.database import run_query
<<<<<<< HEAD
from utils.logger import get_logger
from utils.analytics.shared import compute_daily_returns, safe_lru_cache

logger = get_logger(__name__)
=======
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474

from utils.analytics.global_state import get_global_data

<<<<<<< HEAD
def load_data() -> pd.DataFrame:
    """Fetches clean data from the global in-memory dataset."""
    df = get_global_data()
=======


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

>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
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
    
    # Risk Classification mapping based on Annual Volatility
    def classify_risk(vol):
        if vol < 0.15: return "Defensive"
        elif vol < 0.25: return "Balanced"
        elif vol < 0.40: return "Growth"
        else: return "Aggressive"
        
    feature_matrix["Risk_Class"] = feature_matrix["Annual_Volatility"].apply(classify_risk)

    return feature_matrix

def compute_covariance_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Computes the annualized covariance matrix from daily returns."""
    # Pivot so columns are companies and rows are dates
    pivot_df = df.pivot(index="Date", columns="Company", values="Daily_Return")
    return pivot_df.cov() * 252

def get_portfolio_performance(weights, returns, cov_matrix, risk_free_rate=0.05):
    """Calculates expected return, volatility, and sharpe ratio for a portfolio."""
    p_ret = np.sum(returns * weights)
    p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    p_sharpe = (p_ret - risk_free_rate) / p_vol
    return p_ret, p_vol, p_sharpe

def calculate_efficient_frontier(returns, cov_matrix, num_portfolios=15):
    """Calculates the Efficient Frontier using scipy.optimize."""
    num_assets = len(returns)
    if num_assets < 2:
        return pd.DataFrame()
        
    # We want to find the min variance for a range of target returns
    min_ret = returns.min()
    max_ret = returns.max()
    target_returns = np.linspace(min_ret, max_ret, num_portfolios)
    
    frontier = []
    
    # Initial guess (equal weight)
    init_guess = np.ones(num_assets) / num_assets
    bounds = tuple((0.0, 1.0) for asset in range(num_assets))
    
    for t_ret in target_returns:
        # Constraints: 1. Weights sum to 1, 2. Return equals target return
        constraints = (
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w: np.sum(returns * w) - t_ret}
        )
        
        # Minimize volatility (variance)
        result = minimize(
            lambda w: np.dot(w.T, np.dot(cov_matrix, w)), 
            init_guess, 
            method='SLSQP', 
            bounds=bounds, 
            constraints=constraints
        )
        
        if result.success:
            vol = np.sqrt(result.fun)
            frontier.append({"Annual_Return": t_ret, "Annual_Volatility": vol})
            
    return pd.DataFrame(frontier)

def calculate_tangency_portfolio(returns, cov_matrix, risk_free_rate=0.05):
    """Finds the portfolio that maximizes the Sharpe Ratio."""
    num_assets = len(returns)
    if num_assets < 2:
        return None
        
    init_guess = np.ones(num_assets) / num_assets
    bounds = tuple((0.0, 1.0) for asset in range(num_assets))
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    
    # We minimize the negative Sharpe Ratio
    def neg_sharpe(w):
        p_ret = np.sum(returns * w)
        p_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        return -(p_ret - risk_free_rate) / p_vol
        
    result = minimize(neg_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if result.success:
        weights = result.x
        p_ret, p_vol, p_sharpe = get_portfolio_performance(weights, returns, cov_matrix, risk_free_rate)
        return {
            "Weights": weights,
            "Annual_Return": p_ret,
            "Annual_Volatility": p_vol,
            "Sharpe_Ratio": p_sharpe
        }
    return None


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


<<<<<<< HEAD
@safe_lru_cache(maxsize=1)
def prepare_plot_data():
=======
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
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
    """
    Orchestrator: runs the full pipeline using DuckDB and returns
    (raw_df_with_returns, feature_matrix_with_clusters, cov_matrix, efficient_frontier, tangency_portfolio)
    """
<<<<<<< HEAD
    try:
        df = load_data()
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None
            
        feature_matrix = prepare_features(df)
        X = scale_features(feature_matrix)
        feature_matrix["Cluster"] = perform_kmeans(X).astype(str)
        
        # MPT Calculations
        cov_matrix = compute_covariance_matrix(df)
        
        # Ensure ordering of returns matches covariance matrix columns
        companies = cov_matrix.columns
        returns_aligned = feature_matrix.set_index("Company").loc[companies]["Annual_Return"].values
        
        frontier_df = calculate_efficient_frontier(returns_aligned, cov_matrix)
        tangency = calculate_tangency_portfolio(returns_aligned, cov_matrix)
        
        if tangency:
            tangency["Companies"] = companies.tolist()

        return df, feature_matrix, cov_matrix, frontier_df, tangency
    except Exception as e:
        logger.error(f"Risk-Return pipeline failed: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None
=======
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
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
