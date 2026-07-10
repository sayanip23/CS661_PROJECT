"""
utils/analytics/correlation.py

Backend analytics for the Clustered Correlation Matrix Heatmap with
Dendrograms visualization (Task 4.1).

Pipeline:
    load_clean_data()
        -> compute_daily_returns()   [from utils.analytics.shared]
        -> create_pivot_table()
        -> compute_correlation_matrix()
        -> perform_agglomerative_clustering()
        -> get_clustered_matrix()
"""

import numpy as np
import pandas as pd
from utils.database import run_query
from utils.logger import get_logger
from utils.analytics.shared import compute_daily_returns, safe_lru_cache

logger = get_logger(__name__)
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, dendrogram as scipy_dendrogram
from scipy.spatial.distance import squareform


# Minimum number of overlapping trading days required for a correlation
# pair to be considered reliable (stocks have different listing dates).
MIN_OVERLAP_PERIODS = 60


# ---------------------------------------------------------------------------
# Step 1: Load Data
# ---------------------------------------------------------------------------
@safe_lru_cache(maxsize=1)
def load_clean_data() -> pd.DataFrame:
    """
    Loads the cleaned stock dataset from DuckDB.

    Returns
    -------
    pd.DataFrame
        Sorted by Company and Date.
    """

    query = """
        SELECT
            Company,
            Date,
            Close
        FROM clean_stock_data
        ORDER BY Company, Date
    """

    df = run_query(query)

    df["Date"] = pd.to_datetime(df["Date"])

    return df


# ---------------------------------------------------------------------------
# Step 3: Pivot Table
# ---------------------------------------------------------------------------
def create_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivots the long-format dataframe into a wide Date x Company matrix
    of daily returns, ready for correlation.

    Returns
    -------
    pd.DataFrame
        Index: Date, Columns: Company, Values: Daily_Return
    """
    pivot = df.pivot_table(
        index="Date",
        columns="Company",
        values="Daily_Return",
    )

    return pivot


# ---------------------------------------------------------------------------
# Step 4: Correlation Matrix
# ---------------------------------------------------------------------------
def compute_correlation_matrix(
    pivot_df: pd.DataFrame,
    min_periods: int = MIN_OVERLAP_PERIODS,
) -> pd.DataFrame:
    """
    Computes the pairwise Pearson correlation matrix of daily returns.

    Uses pandas' pairwise-complete-observations correlation (NaNs from
    differing IPO/listing dates are excluded per-pair rather than
    dropping entire rows/companies).

    Parameters
    ----------
    min_periods : int
        Minimum number of overlapping (non-NaN) days required for a pair
        to get a correlation value; pairs with fewer overlapping days
        will be NaN.

    Returns
    -------
    pd.DataFrame
        Square Company x Company correlation matrix.
    """
    corr_matrix = pivot_df.corr(min_periods=min_periods)

    # Drop any company that ended up with no valid correlations at all
    # (e.g. too little overlapping history with every other stock).
    corr_matrix = corr_matrix.dropna(axis=0, how="all").dropna(axis=1, how="all")

    # Any remaining sparse NaNs (insufficient overlap for a specific pair)
    # are filled with 0 so clustering/distance math doesn't break.
    corr_matrix = corr_matrix.fillna(0.0)

    return corr_matrix


# ---------------------------------------------------------------------------
# Step 5: Agglomerative Clustering
# ---------------------------------------------------------------------------
def perform_agglomerative_clustering(
    corr_matrix: pd.DataFrame,
    n_clusters: int = 5,
    linkage_method: str = "average",
):
    """
    Performs hierarchical (agglomerative) clustering on stocks using
    1 - correlation as the distance metric (highly correlated stocks
    are "closer together").

    Uses both:
      - sklearn.cluster.AgglomerativeClustering -> cluster labels
      - scipy.cluster.hierarchy.linkage          -> linkage matrix for dendrogram

    Parameters
    ----------
    n_clusters : int
        Number of flat clusters to cut the dendrogram into.
    linkage_method : str
        Linkage criterion passed to both sklearn and scipy ('average',
        'complete', 'single', 'ward'). Note: 'ward' requires euclidean
        distances, so for correlation-distance use 'average' or 'complete'.

    Returns
    -------
    dict with keys:
        'labels'          : np.ndarray of cluster id per company (sklearn order == corr_matrix.columns order)
        'linkage_matrix'  : scipy linkage matrix (for dendrogram)
        'order'           : list of company names in dendrogram leaf order
        'companies'       : list of company names, same order as corr_matrix
        'distance_matrix' : the full 1 - corr distance matrix used
    """
    companies = corr_matrix.columns.tolist()

    # Distance = 1 - correlation, clipped to avoid tiny negative floats
    distance_matrix = 1 - corr_matrix.values
    distance_matrix = np.clip(distance_matrix, 0, 2)

    # Force exact symmetry & zero diagonal (guards against floating point drift)
    distance_matrix = (distance_matrix + distance_matrix.T) / 2
    np.fill_diagonal(distance_matrix, 0)

    condensed_distance = squareform(distance_matrix, checks=False)

    # --- scikit-learn: cluster labels ---
    sk_model = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="precomputed",
        linkage=linkage_method,
    )
    labels = sk_model.fit_predict(distance_matrix)

    # --- scipy: linkage matrix for the dendrogram visualization ---
    linkage_matrix = linkage(condensed_distance, method=linkage_method)

    dendro = scipy_dendrogram(linkage_matrix, labels=companies, no_plot=True)
    leaf_order = dendro["ivl"]  # company names in dendrogram leaf order

    return {
        "labels": labels,
        "linkage_matrix": linkage_matrix,
        "order": leaf_order,
        "companies": companies,
        "distance_matrix": distance_matrix,
    }


# ---------------------------------------------------------------------------
# Step 6: Reordered (clustered) Matrix
# ---------------------------------------------------------------------------
def get_clustered_matrix(
    corr_matrix: pd.DataFrame,
    cluster_result: dict,
) -> pd.DataFrame:
    """
    Reorders the correlation matrix's rows & columns according to the
    dendrogram leaf order, so visually correlated blocks of stocks sit
    next to each other in the heatmap (removes the "hairball" effect).

    Returns
    -------
    pd.DataFrame
        Correlation matrix reordered/reindexed by dendrogram leaf order.
    """
    order = cluster_result["order"]
    return corr_matrix.loc[order, order]


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------
@safe_lru_cache(maxsize=32)
def run_correlation_pipeline(
    n_clusters: int = 4, linkage_method: str = "average"
) -> dict:
    if n_clusters is None:
        n_clusters = 4
    """
    Runs steps 1-6 end to end. Used by pages/correlation.py.

    Returns
    -------
    dict with keys:
        'raw_df'           : cleaned input dataframe (with Daily_Return added)
        'pivot'             : Date x Company daily-return pivot table
        'corr_matrix'       : Company x Company correlation matrix (original order)
        'cluster_result'    : output of perform_agglomerative_clustering()
        'clustered_matrix'  : correlation matrix reordered by dendrogram leaves
    """
    try:
        df = load_clean_data()
        df = compute_daily_returns(df)
        pivot = create_pivot_table(df)
        corr_matrix = compute_correlation_matrix(pivot)
        cluster_result = perform_agglomerative_clustering(
            corr_matrix, n_clusters=n_clusters, linkage_method=linkage_method
        )
        clustered_matrix = get_clustered_matrix(corr_matrix, cluster_result)

        return {
            "raw_df": df,
            "pivot": pivot,
            "corr_matrix": corr_matrix,
            "cluster_result": cluster_result,
            "clustered_matrix": clustered_matrix,
        }
    except Exception as e:
        logger.error(f"Correlation pipeline failed: {e}")
        return {
            "raw_df": pd.DataFrame(),
            "pivot": pd.DataFrame(),
            "corr_matrix": pd.DataFrame(),
            "cluster_result": {"dendrogram": {}, "labels": [], "n_clusters": n_clusters},
            "clustered_matrix": pd.DataFrame(),
        }


if __name__ == "__main__":
    # Quick smoke test: python utils/analytics/correlation.py
    result = run_correlation_pipeline()
    print("Pivot shape:", result["pivot"].shape)
    print("Correlation matrix shape:", result["corr_matrix"].shape)
    print("Clustered matrix shape:", result["clustered_matrix"].shape)
    print("Number of clusters found:", len(set(result["cluster_result"]["labels"])))
    print("First 5 companies in dendrogram order:", result["cluster_result"]["order"][:5])
