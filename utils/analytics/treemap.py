import pandas as pd
import numpy as np
from utils.database import run_query
from utils.logger import get_logger
from utils.logger import get_logger
from utils.analytics.shared import compute_daily_returns, safe_lru_cache
from utils.analytics.global_state import get_global_data

logger = get_logger(__name__)

@safe_lru_cache(maxsize=32)
def load_clean_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetches clean data from the global dataset for the specific date window."""
    df = get_global_data()
    if df.empty:
        return df
        
    mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
    return df.loc[mask]

def compute_growth_metrics(df: pd.DataFrame, size_metric: str, group_by: str = "Sector") -> tuple:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    actual_size_col = 'Volume' if 'Volume' in size_metric else 'Turnover'
    market_total_size = df[actual_size_col].sum()

    stats = []
    for (company, sector), group in df.groupby(['Company', 'Sector']):
        start_price, end_price = group['Close'].iloc[0], group['Close'].iloc[-1]
        days = (group['Date'].iloc[-1] - group['Date'].iloc[0]).days
        
        cagr = ((end_price / start_price) ** (365.25 / days)) - 1 if days > 0 else 0
        volatility = group['Daily_Return'].std() * np.sqrt(252)
        sharpe = (cagr / volatility) if volatility > 0 else 0
        
        total_size = group[actual_size_col].sum()
        total_volume = group['Volume'].sum()
        total_turnover = group.get('Turnover', group['Volume']).sum()
        market_weight = total_size / market_total_size if market_total_size > 0 else 0
        
        stats.append({
            'Company': company, 'Sector': sector,
            'CAGR': cagr, 'Volatility': volatility, 'Sharpe_Ratio': np.clip(sharpe, -3, 3),
            'Market_Weight': market_weight, 
            'Total_Volume': total_volume, 'Total_Turnover': total_turnover,
            size_metric: total_size,
            'Trading_Days': len(group),
            'Max_Drawdown': (group['Close'] / group['Close'].cummax() - 1).min()
        })
        
    company_growth = pd.DataFrame(stats)
    company_growth['Market_Rank'] = company_growth['Market_Weight'].rank(ascending=False, method='min')
    
    # Generate Categorical Profiles for Multi-Layer Hierarchy
    def safe_qcut(series, q, labels):
        try:
            return pd.qcut(series, q=q, labels=labels, duplicates='drop')
        except Exception:
            return labels[len(labels)//2]
            
    company_growth['Risk Profile'] = safe_qcut(company_growth['Volatility'], 3, ["Low Risk", "Medium Risk", "High Risk"])
    company_growth['Return Profile'] = safe_qcut(company_growth['CAGR'], 3, ["Laggard", "Average", "Leader"])
    company_growth['Liquidity Profile'] = safe_qcut(company_growth['Total_Turnover'], 3, ["Low Liquidity", "Medium Liquidity", "High Liquidity"])
    
    if group_by == "Correlation Cluster":
        try:
            from sklearn.cluster import KMeans
            # Pivot to get daily returns per company
            ret_matrix = df.pivot(index='Date', columns='Company', values='Daily_Return').fillna(0)
            # Use correlation distance as features
            corr_matrix = ret_matrix.corr().fillna(0)
            
            kmeans = KMeans(n_clusters=min(5, len(corr_matrix.columns)), random_state=42, n_init=10)
            clusters = kmeans.fit_predict(corr_matrix)
            
            cluster_map = {comp: f"Cluster {c+1}" for comp, c in zip(corr_matrix.columns, clusters)}
            company_growth['Correlation Cluster'] = company_growth['Company'].map(cluster_map)
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            company_growth['Correlation Cluster'] = "Unclustered"

    if group_by not in company_growth.columns:
        group_by = "Sector"
        
    sector_growth = company_growth.groupby(group_by).agg({
        'Total_Volume': 'sum', 'Total_Turnover': 'sum', size_metric: 'sum', 
        'CAGR': 'mean', 'Volatility': 'mean', 'Market_Weight': 'sum', 'Max_Drawdown': 'mean'
    }).reset_index()
    sector_growth = sector_growth.rename(columns={group_by: 'Sector'}) # Keep the column name 'Sector' internally for compatibility with frontend mapping
    sector_growth['Market_Rank'] = sector_growth['Market_Weight'].rank(ascending=False, method='min')
    
    return company_growth, sector_growth

def format_html_metric(val, is_pct=True, diff=False):
    if pd.isna(val) or val is None:
        return "<span style='color:#9499a6'>N/A</span>"
    color = "#21ce99" if val > 0 else ("#f62d2d" if val < 0 else "#9499a6")
    sign = "+" if diff and val > 0 else ""
    formatted_val = f"{sign}{val:.2%}" if is_pct else f"{sign}{val:.2f}"
    return f"<span style='color:{color}'>{formatted_val}</span>"

def build_hierarchy_dataframe(company_growth: pd.DataFrame, sector_growth: pd.DataFrame, size_metric: str, group_by: str = "Sector") -> pd.DataFrame:
    if company_growth.empty:
        return pd.DataFrame()
        
    rows = []
    market_avg_cagr = company_growth['CAGR'].mean()
    market_avg_sharpe = company_growth['Sharpe_Ratio'].mean()
    market_total_size = company_growth[size_metric].sum()
    market_total_vol = company_growth['Total_Volume'].sum()
    market_total_turn = company_growth['Total_Turnover'].sum()
    market_volatility = company_growth['Volatility'].mean()
    market_max_dd = company_growth['Max_Drawdown'].mean()
    
    # Floor value to ensure visibility of tiny rectangles (0.25% of market total)
    min_visible_size = market_total_size * 0.0025
    
    # Root Node
    rows.append({
        "id": "NIFTY-50", "parent": "", "label": "NIFTY-50", "value": 0,
        "cagr": market_avg_cagr, "sharpe": market_avg_sharpe, "level": "root", 
        "volume": market_total_vol, "turnover": market_total_turn, 
        "market_weight": 1.0, "sector_weight": 1.0, "rank": 1, "sector": "Market", "company": "NIFTY-50",
        "volatility": market_volatility, "max_drawdown": market_max_dd,
        "hover_cagr": format_html_metric(market_avg_cagr, True, True),
        "hover_sharpe": format_html_metric(market_avg_sharpe, False, False),
        "diff_market_cagr": format_html_metric(0, True, True),
        "diff_market_sharpe": format_html_metric(0, False, True),
        "diff_sector_cagr": format_html_metric(0, True, True),
        "diff_sector_sharpe": format_html_metric(0, False, True),
        "sector_avg_cagr": format_html_metric(market_avg_cagr, True, False),
        "sector_avg_sharpe": format_html_metric(market_avg_sharpe, False, False)
    })

    # Sector/Group Nodes
    for _, srow in sector_growth.iterrows():
        s_cagr = srow["CAGR"]
        s_sharpe = srow["CAGR"] / srow["Volatility"] if srow["Volatility"]>0 else 0
        g_name = str(srow["Sector"])
        
        rows.append({
            "id": g_name, "parent": "NIFTY-50", "label": g_name, 
            "value": 0,
            "cagr": s_cagr, "sharpe": s_sharpe,
            "level": "sector", "volume": srow["Total_Volume"], "turnover": srow["Total_Turnover"],
            "market_weight": srow["Market_Weight"], "sector_weight": 1.0, "rank": srow["Market_Rank"],
            "sector": g_name, "company": "",
            "volatility": srow["Volatility"], "max_drawdown": srow["Max_Drawdown"],
            "hover_cagr": format_html_metric(s_cagr, True, True),
            "hover_sharpe": format_html_metric(s_sharpe, False, False),
            "diff_market_cagr": format_html_metric(s_cagr - market_avg_cagr, True, True),
            "diff_market_sharpe": format_html_metric(s_sharpe - market_avg_sharpe, False, True),
            "diff_sector_cagr": format_html_metric(0, True, True),
            "diff_sector_sharpe": format_html_metric(0, False, True),
            "sector_avg_cagr": format_html_metric(s_cagr, True, False),
            "sector_avg_sharpe": format_html_metric(s_sharpe, False, False)
        })

    # Company Nodes
    for _, crow in company_growth.iterrows():
        if crow[size_metric] <= 0:
            continue
            
        c_cagr = crow["CAGR"]
        c_sharpe = crow["Sharpe_Ratio"]
        g_name = str(crow.get(group_by, crow["Sector"]))
        
        # Get sector/group averages
        srow = sector_growth[sector_growth["Sector"] == g_name].iloc[0]
        s_cagr = srow["CAGR"]
        s_sharpe = srow["CAGR"] / srow["Volatility"] if srow["Volatility"]>0 else 0
        sector_total = srow[size_metric]
        sector_weight = crow[size_metric] / sector_total if sector_total > 0 else 0
            
        rows.append({
            "id": f"{g_name}/{crow['Company']}", "parent": g_name, "label": crow["Company"],
            "value": max(crow[size_metric], min_visible_size),
            "cagr": c_cagr, "sharpe": c_sharpe,
            "level": "company", "volume": crow["Total_Volume"], "turnover": crow["Total_Turnover"],
            "market_weight": crow["Market_Weight"], "sector_weight": sector_weight, "rank": crow["Market_Rank"],
            "sector": g_name, "company": crow["Company"],
            "volatility": crow["Volatility"], "max_drawdown": crow["Max_Drawdown"],
            "hover_cagr": format_html_metric(c_cagr, True, True),
            "hover_sharpe": format_html_metric(c_sharpe, False, False),
            "diff_market_cagr": format_html_metric(c_cagr - market_avg_cagr, True, True),
            "diff_market_sharpe": format_html_metric(c_sharpe - market_avg_sharpe, False, True),
            "diff_sector_cagr": format_html_metric(c_cagr - s_cagr, True, True),
            "diff_sector_sharpe": format_html_metric(c_sharpe - s_sharpe, False, True),
            "sector_avg_cagr": format_html_metric(s_cagr, True, False),
            "sector_avg_sharpe": format_html_metric(s_sharpe, False, False)
        })

    return pd.DataFrame(rows)

@safe_lru_cache(maxsize=32)
def run_treemap_pipeline(start_date: str, end_date: str, size_metric: str = "Total_Volume", group_by: str = "Sector") -> dict:
    try:
        df = load_clean_data(start_date, end_date)
        company_growth, sector_growth = compute_growth_metrics(df, size_metric, group_by)
        hierarchy = build_hierarchy_dataframe(company_growth, sector_growth, size_metric, group_by)
        
        return {
            "hierarchy": hierarchy,
            "company_growth": company_growth,
            "sector_growth": sector_growth,
            "raw_data": df
        }
    except Exception as e:
        logger.error(f"Treemap pipeline failed: {e}")
        return {
            "hierarchy": pd.DataFrame(),
            "company_growth": pd.DataFrame(),
            "sector_growth": pd.DataFrame(),
            "raw_data": pd.DataFrame()
        }

def get_node_trend_data(df: pd.DataFrame, node_id: str, company_growth: pd.DataFrame = None, group_by: str = "Sector") -> tuple:
    """Computes trend data on-the-fly for the active node and market."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    market_trend = df.groupby("Date")["Close"].mean().reset_index()
    
    if node_id == "NIFTY-50" or not node_id:
        node_trend = pd.DataFrame()
    elif "/" in node_id:
        # Company
        group, company = node_id.split("/", 1)
        node_trend = df[df["Company"] == company].sort_values("Date").copy()
    else:
        # Group
        if company_growth is not None and not company_growth.empty and group_by in company_growth.columns and group_by != "Sector":
            companies_in_group = company_growth[company_growth[group_by] == node_id]['Company'].tolist()
            node_trend = df[df["Company"].isin(companies_in_group)].groupby("Date")["Close"].mean().reset_index()
        else:
            node_trend = df[df["Sector"] == node_id].groupby("Date")["Close"].mean().reset_index()
        
    return market_trend, node_trend

def compute_rolling_performance(df: pd.DataFrame, node_id: str, company_growth: pd.DataFrame = None, group_by: str = "Sector", window: int = 60) -> pd.DataFrame:
    """Computes 60-day rolling return for the active node vs Market."""
    if df.empty:
        return pd.DataFrame()
        
    
    # 1. Market Rolling
    market_daily = df.groupby("Date")["Daily_Return"].mean().reset_index()
    market_daily["Market_Rolling_Return"] = market_daily["Daily_Return"].rolling(window).apply(lambda x: (np.prod(1 + x) - 1), raw=True)
    
    # 2. Node Rolling
    if node_id == "NIFTY-50" or not node_id:
        return market_daily.dropna()
        
    if "/" in node_id:
        group, company = node_id.split("/", 1)
        node_df = df[df["Company"] == company].sort_values("Date")
        node_daily = node_df[["Date", "Daily_Return"]].copy()
    else:
        if company_growth is not None and not company_growth.empty and group_by in company_growth.columns and group_by != "Sector":
            comps = company_growth[company_growth[group_by] == node_id]['Company'].tolist()
            node_daily = df[df["Company"].isin(comps)].groupby("Date")["Daily_Return"].mean().reset_index()
        else:
            node_daily = df[df["Sector"] == node_id].groupby("Date")["Daily_Return"].mean().reset_index()
            
    node_daily["Node_Rolling_Return"] = node_daily["Daily_Return"].rolling(window).apply(lambda x: (np.prod(1 + x) - 1), raw=True)
    
    merged = pd.merge(market_daily[["Date", "Market_Rolling_Return"]], node_daily[["Date", "Node_Rolling_Return"]], on="Date", how="inner")
    return merged.dropna()

def compute_risk_contribution(df: pd.DataFrame, node_id: str, company_growth: pd.DataFrame = None, group_by: str = "Sector") -> pd.DataFrame:
    """Computes Marginal Contribution to Risk (MCR) for the assets in the node."""
    if df.empty:
        return pd.DataFrame()
        
    
    # Determine which companies are in the portfolio
    if node_id == "NIFTY-50" or not node_id:
        comps = company_growth.nlargest(10, 'Total_Volume')['Company'].tolist() if company_growth is not None else df["Company"].unique()[:10]
    elif "/" in node_id:
        return pd.DataFrame() # Cannot decompose a single asset
    else:
        if company_growth is not None and not company_growth.empty and group_by in company_growth.columns and group_by != "Sector":
            comps = company_growth[company_growth[group_by] == node_id]['Company'].tolist()
        else:
            comps = df[df["Sector"] == node_id]["Company"].unique().tolist()
            
    if len(comps) <= 1:
        return pd.DataFrame()
        
    pivot_df = df[df["Company"].isin(comps)].pivot(index="Date", columns="Company", values="Daily_Return").fillna(0)
    cov_matrix = pivot_df.cov() * 252
    
    weights = np.array([1/len(comps)] * len(comps))
    
    portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
    if portfolio_var <= 0: return pd.DataFrame()
    portfolio_vol = np.sqrt(portfolio_var)
    
    mcr = np.dot(cov_matrix, weights) / portfolio_vol
    pcr = (weights * mcr) / portfolio_vol
    
    risk_df = pd.DataFrame({
        "Company": pivot_df.columns,
        "Weight": weights,
        "MCR": mcr,
        "PCR": pcr
    }).sort_values("PCR", ascending=False)
    
    return risk_df

def compute_market_breadth(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Computes % of stocks with positive rolling return."""
    if df.empty:
        return pd.DataFrame()
        
    pivot_df = df.pivot(index="Date", columns="Company", values="Daily_Return").fillna(0)
    
    rolling_returns = pivot_df.rolling(window).apply(lambda x: (np.prod(1 + x) - 1), raw=True)
    positive_count = (rolling_returns > 0).sum(axis=1)
    negative_count = (rolling_returns < 0).sum(axis=1)
    total_count = rolling_returns.notna().sum(axis=1)
    
    breadth = pd.DataFrame({
        "Date": pivot_df.index,
        "Breadth": positive_count / total_count,
        "Advancing": positive_count,
        "Declining": negative_count,
        "Total": total_count
    })
    return breadth.dropna()