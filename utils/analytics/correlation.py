"""
utils/analytics/correlation.py

Backend analytics for the Clustered Correlation Matrix, Market Network, 
Sankey Flows, and Diversification Intelligence.
"""

import numpy as np
import pandas as pd
from utils.database import run_query
from utils.logger import get_logger
from utils.analytics.shared import compute_daily_returns, safe_lru_cache
from utils.analytics.global_state import get_global_data, get_global_company_sector_map

logger = get_logger(__name__)
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, dendrogram as scipy_dendrogram
from scipy.spatial.distance import squareform

MIN_OVERLAP_PERIODS = 60

# ---------------------------------------------------------------------------
# Core Data Pipeline
# ---------------------------------------------------------------------------
def load_clean_data() -> pd.DataFrame:
    """Loads the cleaned stock dataset from the global in-memory dataset."""
    return get_global_data()

def get_company_sector_map(df: pd.DataFrame = None) -> dict:
    """Extracts a mapping of Company to Sector."""
    return get_global_company_sector_map()

def create_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """Pivots the long-format dataframe into Date x Company matrix of returns."""
    return df.pivot_table(index="Date", columns="Company", values="Daily_Return")

def compute_correlation_matrix(pivot_df: pd.DataFrame, min_periods: int = MIN_OVERLAP_PERIODS) -> pd.DataFrame:
    """Computes the pairwise Pearson correlation matrix of daily returns."""
    corr_matrix = pivot_df.corr(min_periods=min_periods)
    corr_matrix = corr_matrix.dropna(axis=0, how="all").dropna(axis=1, how="all")
    corr_matrix = corr_matrix.fillna(0.0)
    return corr_matrix

# ---------------------------------------------------------------------------
# Original Heatmap Clustering
# ---------------------------------------------------------------------------
def perform_agglomerative_clustering(corr_matrix: pd.DataFrame, n_clusters: int = 5, linkage_method: str = "average"):
    companies = corr_matrix.columns.tolist()
    distance_matrix = 1 - corr_matrix.values
    distance_matrix = np.clip(distance_matrix, 0, 2)
    distance_matrix = (distance_matrix + distance_matrix.T) / 2
    np.fill_diagonal(distance_matrix, 0)
    condensed_distance = squareform(distance_matrix, checks=False)

    sk_model = AgglomerativeClustering(n_clusters=n_clusters, metric="precomputed", linkage=linkage_method)
    labels = sk_model.fit_predict(distance_matrix)

    linkage_matrix = linkage(condensed_distance, method=linkage_method)
    dendro = scipy_dendrogram(linkage_matrix, labels=companies, no_plot=True)
    leaf_order = dendro["ivl"]

    return {
        "labels": labels,
        "linkage_matrix": linkage_matrix,
        "order": leaf_order,
        "companies": companies,
        "distance_matrix": distance_matrix,
    }

def get_clustered_matrix(corr_matrix: pd.DataFrame, cluster_result: dict) -> pd.DataFrame:
    order = cluster_result["order"]
    return corr_matrix.loc[order, order]

# ---------------------------------------------------------------------------
# Group 6 Enhancements: Intelligence & Networks
# ---------------------------------------------------------------------------
def detect_correlation_regime(corr_matrix: pd.DataFrame) -> dict:
    """Identifies the current market correlation regime."""
    if corr_matrix.empty:
        return {"regime": "Unknown", "score": 0.0, "desc": "No data available."}
        
    # Exclude diagonal (1.0s)
    mask = np.ones(corr_matrix.shape, dtype=bool)
    np.fill_diagonal(mask, 0)
    
    mean_abs_corr = np.abs(corr_matrix.values[mask]).mean()
    
    if mean_abs_corr > 0.5:
        return {"regime": "Highly Correlated", "score": round(mean_abs_corr * 100, 1), "desc": "Market moves as a monolith. Systemic macro factors are dominating."}
    elif mean_abs_corr > 0.3:
        return {"regime": "Transitional", "score": round(mean_abs_corr * 100, 1), "desc": "Market shows moderate clustering with some independent sectors."}
    else:
        return {"regime": "Diversified", "score": round(mean_abs_corr * 100, 1), "desc": "Low systemic correlation. Alpha is driven by stock-specific fundamentals."}

def calculate_diversification(corr_matrix: pd.DataFrame, selected_companies: list) -> dict:
    """Calculates diversification metrics for a selected subset."""
    if not selected_companies or corr_matrix.empty:
        return {"score": 0, "desc": "Select companies to analyze diversification."}
        
    valid_companies = [c for c in selected_companies if c in corr_matrix.columns]
    if len(valid_companies) < 2:
        return {"score": 0, "desc": "Need at least 2 valid companies."}
        
    sub_matrix = corr_matrix.loc[valid_companies, valid_companies]
    mask = np.ones(sub_matrix.shape, dtype=bool)
    np.fill_diagonal(mask, 0)
    
    mean_corr = sub_matrix.values[mask].mean()
    # Score 0-100: lower correlation = higher diversification score
    # e.g., mean_corr of 0 = 100 score, 1 = 0 score.
    score = max(0, min(100, (1 - mean_corr) * 100))
    
    desc = "Excellent Diversification" if score > 75 else "Moderate Diversification" if score > 40 else "Poor Diversification (Highly Concentrated)"
    
    return {"score": round(score, 1), "desc": desc, "mean_corr": round(mean_corr, 2)}

def generate_network_data(corr_matrix: pd.DataFrame, threshold: float = 0.6) -> pd.DataFrame:
    """Extracts edges that exceed the absolute threshold."""
    if corr_matrix.empty:
        return pd.DataFrame()
        
    # Use upper triangle only to avoid duplicate edges
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Rename axes to avoid "cannot insert Company, already exists" during reset_index
    upper_tri.index.name = 'source'
    upper_tri.columns.name = 'target'
    
    # Stack to long format
    edges = upper_tri.stack().reset_index()
    edges.columns = ['source', 'target', 'weight']
    
    # Filter by threshold
    edges = edges[edges['weight'].abs() >= threshold].copy()
    return edges.sort_values(by="weight", key=abs, ascending=False)

def generate_correlation_rankings(corr_matrix: pd.DataFrame) -> pd.DataFrame:
    """Finds top pairs (positive/negative) and most independent companies."""
    if corr_matrix.empty:
        return pd.DataFrame()
        
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    upper_tri.index.name = 'Company_A'
    upper_tri.columns.name = 'Company_B'
    edges = upper_tri.stack().reset_index()
    edges.columns = ['Company A', 'Company B', 'Correlation']
    
    # Strongest Positive
    pos = edges.sort_values(by="Correlation", ascending=False).head(20).copy()
    pos['Type'] = 'Strong Positive'
    
    # Strongest Negative
    neg = edges.sort_values(by="Correlation", ascending=True).head(20).copy()
    neg['Type'] = 'Strong Negative'
    
    return pd.concat([pos, neg], ignore_index=True)

def generate_sankey_data(corr_matrix: pd.DataFrame, company_sector_map: dict) -> tuple:
    """Calculates Sector-to-Sector influence flow (sum of absolute correlations)."""
    if corr_matrix.empty or not company_sector_map:
        return [], [], []
        
    # Build Sector x Sector correlation matrix
    sectors = list(set(company_sector_map.values()))
    
    # Simple approach: average correlation between companies in Sector A vs companies in Sector B
    edges = []
    for i in range(len(sectors)):
        for j in range(i + 1, len(sectors)):
            s1 = sectors[i]
            s2 = sectors[j]
            comps1 = [c for c, s in company_sector_map.items() if s == s1 and c in corr_matrix.columns]
            comps2 = [c for c, s in company_sector_map.items() if s == s2 and c in corr_matrix.columns]
            
            if comps1 and comps2:
                sub = corr_matrix.loc[comps1, comps2]
                val = sub.mean().mean() # average correlation
                if abs(val) > 0.1: # threshold to reduce noise
                    edges.append({
                        "source": s1,
                        "target": s2,
                        "value": abs(val),
                        "actual": val
                    })
                    
    # Format for Plotly Sankey
    nodes = list(set([e['source'] for e in edges] + [e['target'] for e in edges]))
    node_indices = {n: i for i, n in enumerate(nodes)}
    
    sources = [node_indices[e['source']] for e in edges]
    targets = [node_indices[e['target']] for e in edges]
    values = [e['value'] for e in edges]
    
    return nodes, sources, targets, values, edges

def calculate_time_varying_correlation(df: pd.DataFrame, comp1: str, comp2: str, window: int = 60) -> pd.DataFrame:
    """Calculates rolling correlation between two companies over time."""
    pivot = create_pivot_table(df)
    if comp1 not in pivot.columns or comp2 not in pivot.columns:
        return pd.DataFrame()
        
    s1 = pivot[comp1]
    s2 = pivot[comp2]
    
    rolling_corr = s1.rolling(window=window).corr(s2)
    res = rolling_corr.dropna().reset_index()
    res.columns = ['Date', 'Rolling_Correlation']
    return res


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------
@safe_lru_cache(maxsize=32)
def run_correlation_pipeline(n_clusters: int = 4, linkage_method: str = "average") -> dict:
    if n_clusters is None: n_clusters = 4
    try:
        df = load_clean_data()
        comp_to_sec = get_company_sector_map()
        
        pivot = create_pivot_table(df)
        corr_matrix = compute_correlation_matrix(pivot)
        
        cluster_result = perform_agglomerative_clustering(corr_matrix, n_clusters=n_clusters, linkage_method=linkage_method)
        clustered_matrix = get_clustered_matrix(corr_matrix, cluster_result)
        
        regime = detect_correlation_regime(corr_matrix)
        rankings = generate_correlation_rankings(corr_matrix)

        return {
            "raw_df": df,
            "comp_to_sec": comp_to_sec,
            "pivot": pivot,
            "corr_matrix": corr_matrix,
            "cluster_result": cluster_result,
            "clustered_matrix": clustered_matrix,
            "regime": regime,
            "rankings": rankings
        }
    except Exception as e:
        logger.error(f"Correlation pipeline failed: {e}")
        return {
            "raw_df": pd.DataFrame(),
            "comp_to_sec": {},
            "pivot": pd.DataFrame(),
            "corr_matrix": pd.DataFrame(),
            "cluster_result": {"dendrogram": {}, "labels": [], "n_clusters": n_clusters},
            "clustered_matrix": pd.DataFrame(),
            "regime": {"regime": "Error", "score": 0},
            "rankings": pd.DataFrame()
        }
