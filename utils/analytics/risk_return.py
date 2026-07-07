import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DATA_PATH = "data/processed/clean_stock_data.csv"


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Company", "Date"])
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
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    return kmeans.fit_predict(X)


def prepare_plot_data(path: str = DATA_PATH):
    """
    Orchestrator: runs the full pipeline and returns
    (raw_df_with_returns, feature_matrix_with_clusters)
    """
    df = load_data(path)
    df = compute_daily_returns(df)

    feature_matrix = prepare_features(df)
    X = scale_features(feature_matrix)
    feature_matrix["Cluster"] = perform_kmeans(X).astype(str)

    return df, feature_matrix