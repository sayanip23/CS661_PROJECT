import numpy as np
import pandas as pd
from utils.database import run_query
from utils.logger import get_logger
from utils.analytics.shared import safe_lru_cache, compute_daily_returns
from utils.analytics.global_state import get_global_data

logger = get_logger(__name__)

SCENARIO_LIBRARY = {
    "mild_correction": {
        "label": "Mild Correction (-5%)",
        "shock_mag": -0.05, "shock_days": 10, "recovery_days": 30, "target_sector": "All", "multiplier": 1.0
    },
    "standard_correction": {
        "label": "Standard Correction (-10%)",
        "shock_mag": -0.10, "shock_days": 15, "recovery_days": 60, "target_sector": "All", "multiplier": 1.0
    },
    "bear_market": {
        "label": "Bear Market (-20%)",
        "shock_mag": -0.20, "shock_days": 40, "recovery_days": 150, "target_sector": "All", "multiplier": 1.0
    },
    "financial_crisis": {
        "label": "Financial Crisis",
        "shock_mag": -0.30, "shock_days": 90, "recovery_days": 365, "target_sector": "FINANCIAL SERVICES", "multiplier": 1.5
    },
    "tech_selloff": {
        "label": "Technology Selloff",
        "shock_mag": -0.15, "shock_days": 20, "recovery_days": 90, "target_sector": "INFORMATION TECHNOLOGY", "multiplier": 2.0
    }
}

def calculate_historical_betas():
    """Calculates Beta for all companies relative to an equal-weighted market index."""
    df = get_global_data()
    if df.empty:
        return pd.DataFrame()
    
    # Calculate Equal-Weighted Market Return
    market_returns = df.groupby("Date")["Daily_Return"].mean().rename("Market_Return")
    df = df.join(market_returns, on="Date")
    
    # Calculate Beta = Cov(Asset, Market) / Var(Market)
    market_var = market_returns.var()
    
    betas = {}
    sectors = {}
    
    for company, group in df.groupby("Company"):
        cov = group["Daily_Return"].cov(group["Market_Return"])
        beta = cov / market_var if market_var > 0 else 1.0
        betas[company] = beta
        sectors[company] = group["Sector"].iloc[0]
        
    beta_df = pd.DataFrame({
        "Company": list(betas.keys()),
        "Sector": list(sectors.values()),
        "Beta": list(betas.values())
    })
    
    # Clamp extreme betas to avoid absurd simulations
    beta_df["Beta"] = beta_df["Beta"].clip(lower=0.1, upper=3.0)
    
    return beta_df


@safe_lru_cache(maxsize=32)
def run_scenario_simulation(shock_mag, shock_days, recovery_days, target_sector="All", multiplier=1.0):
    """
    Generates a forward-looking simulation of a market shock.
    Returns:
    - timeline_df: DataFrame with (Day, Company, Sector, Value)
    - summary_df: DataFrame with Resilience scoring per company
    """
    beta_df = calculate_historical_betas()
    if beta_df.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    total_days = shock_days + recovery_days
    days = np.arange(total_days + 1)
    
    # Generate Baseline Market Path
    market_path = np.ones(total_days + 1)
    
    # Shock Phase: Linear drop
    if shock_days > 0:
        drop_step = shock_mag / shock_days
        for d in range(1, shock_days + 1):
            market_path[d] = 1.0 + (drop_step * d)
            
    # Recovery Phase: Logistic recovery (S-Curve)
    if recovery_days > 0:
        bottom_val = 1.0 + shock_mag
        for d in range(1, recovery_days + 1):
            # Logistic curve from 0 to 1 over recovery_days
            # midpoint at recovery_days/2
            x = (d - (recovery_days / 2)) / (recovery_days / 6) # Spread it out
            logistic_val = 1 / (1 + np.exp(-x))
            market_path[shock_days + d] = bottom_val + (np.abs(shock_mag) * logistic_val)
            
    # Simulate for each company
    records = []
    summary = []
    
    for _, row in beta_df.iterrows():
        company = row["Company"]
        sector = row["Sector"]
        beta = row["Beta"]
        
        # Apply specific sector stress multiplier
        eff_beta = beta
        if target_sector != "All" and sector == target_sector:
            eff_beta *= multiplier
            
        company_path = 1.0 + eff_beta * (market_path - 1.0)
        
        # Calculate Resilience Metrics
        max_drawdown = company_path.min() - 1.0
        
        # Find days to recover (first day it hits >= 0.99)
        recovery_day = -1
        for d in range(shock_days, total_days + 1):
            if company_path[d] >= 0.99:
                recovery_day = d - shock_days
                break
                
        # Resilience Score (0-100): Lower drawdown = better, faster recovery = better
        drawdown_score = np.clip(1.0 - (abs(max_drawdown) / 0.5), 0, 1) # Normalizing max 50% drop
        rec_score = 1.0 if recovery_day != -1 else 0.0
        if recovery_day > 0:
            rec_score = np.clip(1.0 - (recovery_day / recovery_days), 0, 1)
            
        resilience_score = (drawdown_score * 0.7 + rec_score * 0.3) * 100
        
        summary.append({
            "Company": company,
            "Sector": sector,
            "Max_Drawdown": max_drawdown,
            "Recovery_Days": recovery_day,
            "Resilience_Score": resilience_score
        })
        
        for d in days:
            records.append({
                "Day": d,
                "Company": company,
                "Sector": sector,
                "Value": company_path[d]
            })
            
    timeline_df = pd.DataFrame(records)
    summary_df = pd.DataFrame(summary)
    
    # Calculate Sector aggregates for timeline
    sector_timeline = timeline_df.groupby(["Day", "Sector"])["Value"].mean().reset_index()
    sector_timeline["Company"] = sector_timeline["Sector"] + " (Avg)"
    
    # Market Baseline timeline
    market_timeline = pd.DataFrame({
        "Day": days,
        "Company": "Market Baseline",
        "Sector": "Market",
        "Value": market_path
    })
    
    # Combine for UI efficiency
    full_timeline = pd.concat([timeline_df, sector_timeline, market_timeline], ignore_index=True)
    
    return full_timeline, summary_df