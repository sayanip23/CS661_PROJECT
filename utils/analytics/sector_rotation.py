import pandas as pd
import numpy as np
from utils.database import run_query
from utils.logger import get_logger
from utils.logger import get_logger
from utils.analytics.shared import safe_lru_cache
from utils.analytics.global_state import get_global_data

logger = get_logger(__name__)

def _get_market_data(target_year: int) -> pd.DataFrame:
    """Fetches weekly downsampled data for the target year and 6 months prior."""
    start_date = f"{target_year - 1}-07-01"
    end_date = f"{target_year}-12-31"

    df = get_global_data()
    if df.empty:
        return pd.DataFrame()
        
    mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
    filtered = df.loc[mask].copy()
    
    # Weekly aggregation
    filtered['WeekDate'] = filtered['Date'].dt.to_period('W').dt.start_time
    weekly_data = filtered.groupby(['Sector', 'WeekDate'])['Close'].mean().reset_index()
    weekly_data.rename(columns={'Close': 'WeeklyClose'}, inplace=True)
    
    benchmark = weekly_data.groupby('WeekDate')['WeeklyClose'].mean().reset_index()
    benchmark.rename(columns={'WeeklyClose': 'MarketClose'}, inplace=True)
    
    final_df = pd.merge(weekly_data, benchmark, on='WeekDate')
    final_df['RS'] = final_df['WeeklyClose'] / final_df['MarketClose']
    
    return final_df.sort_values(['Sector', 'WeekDate'])

@safe_lru_cache(maxsize=32)
def prepare_sector_rrg(target_year: int) -> pd.DataFrame:
    """Calculates JdK RS-Ratio and RS-Momentum aggregated by Sector."""
    try:
        df = _get_market_data(target_year)
        if df.empty:
            return df

        # RS-Ratio = (RS / 14-Week Average of RS) * 100
        df['RS_14_MA'] = df.groupby('Sector')['RS'].transform(lambda x: x.rolling(14).mean())
        df['RS_Ratio'] = (df['RS'] / df['RS_14_MA']) * 100

        # RS-Momentum = (RS-Ratio / 14-Week Average of RS-Ratio) * 100
        df['Ratio_14_MA'] = df.groupby('Sector')['RS_Ratio'].transform(lambda x: x.rolling(14).mean())
        df['RS_Momentum'] = (df['RS_Ratio'] / df['Ratio_14_MA']) * 100

        # Filter out the "burn-in" period
        df = df[df['WeekDate'].dt.year == target_year].copy()
        
        df['RS_Ratio'] = np.clip(df['RS_Ratio'], 85, 115)
        df['RS_Momentum'] = np.clip(df['RS_Momentum'], 85, 115)
        
        df['Frame'] = df['WeekDate'].dt.strftime('%d-%b-%Y')
        df = df.sort_values(['WeekDate', 'Sector'])
        
        # Calculate Velocity (distance moved from previous week)
        df['Prev_RS_Ratio'] = df.groupby('Sector')['RS_Ratio'].shift(1)
        df['Prev_RS_Mom'] = df.groupby('Sector')['RS_Momentum'].shift(1)
        df['Velocity'] = np.sqrt(
            (df['RS_Ratio'] - df['Prev_RS_Ratio'])**2 + 
            (df['RS_Momentum'] - df['Prev_RS_Mom'])**2
        ).fillna(0)
        
        # Quadrant Assignment
        conditions = [
            (df['RS_Ratio'] > 100) & (df['RS_Momentum'] > 100),
            (df['RS_Ratio'] > 100) & (df['RS_Momentum'] <= 100),
            (df['RS_Ratio'] <= 100) & (df['RS_Momentum'] <= 100),
            (df['RS_Ratio'] <= 100) & (df['RS_Momentum'] > 100)
        ]
        choices = ['Leading', 'Weakening', 'Lagging', 'Improving']
        df['Quadrant'] = np.select(conditions, choices, default='Unknown')
        
        return df
    except Exception as e:
        logger.error(f"Failed to prepare RRG features: {e}")
        return pd.DataFrame()


@safe_lru_cache(maxsize=32)
def detect_market_regime(target_year: int) -> dict:
    """Classifies the overall market regime for the target year."""
    df = _get_market_data(target_year)
    if df.empty:
        return {"regime": "Unknown", "score": 0.0, "desc": "No data available."}
        
    market_df = df.drop_duplicates(subset=['WeekDate'])[['WeekDate', 'MarketClose']].sort_values('WeekDate')
    
    # Calculate 13-week (approx 3 months) and 26-week (approx 6 months) moving averages
    market_df['MA13'] = market_df['MarketClose'].rolling(13).mean()
    market_df['MA26'] = market_df['MarketClose'].rolling(26).mean()
    
    current_data = market_df[market_df['WeekDate'].dt.year == target_year]
    if current_data.empty:
        return {"regime": "Unknown", "score": 0.0, "desc": "Insufficient data."}
        
    last_row = current_data.iloc[-1]
    close = last_row['MarketClose']
    ma13 = last_row['MA13']
    ma26 = last_row['MA26']
    
    if pd.isna(ma13) or pd.isna(ma26):
        return {"regime": "Transitioning", "score": 50.0, "desc": "Insufficient historical depth for MA."}
        
    if close > ma13 and ma13 > ma26:
        return {"regime": "Expansion", "score": 90.0, "desc": "Market is in a strong uptrend with short-term MA above long-term MA."}
    elif close < ma13 and ma13 > ma26:
        return {"regime": "Peak / Weakening", "score": 75.0, "desc": "Market momentum is slowing. Price has broken below short-term MA."}
    elif close < ma13 and ma13 < ma26:
        return {"regime": "Contraction", "score": 20.0, "desc": "Market is in a strong downtrend with short-term MA below long-term MA."}
    elif close > ma13 and ma13 < ma26:
        return {"regime": "Recovery / Bottoming", "score": 45.0, "desc": "Market is attempting a recovery. Price has broken above short-term MA."}
        
    return {"regime": "Consolidation", "score": 50.0, "desc": "Market is moving sideways without clear trend alignment."}


def calculate_sector_leadership(rrg_df: pd.DataFrame) -> dict:
    """Analyzes the most recent frame of the RRG to identify leaders."""
    if rrg_df.empty:
        return {}
        
    latest_date = rrg_df['WeekDate'].max()
    current_df = rrg_df[rrg_df['WeekDate'] == latest_date].copy()
    
    # Distance from origin (100, 100)
    current_df['Power'] = np.sqrt((current_df['RS_Ratio'] - 100)**2 + (current_df['RS_Momentum'] - 100)**2)
    
    leaders = current_df[current_df['Quadrant'] == 'Leading'].sort_values('Power', ascending=False)
    improving = current_df[current_df['Quadrant'] == 'Improving'].sort_values('Power', ascending=False)
    lagging = current_df[current_df['Quadrant'] == 'Lagging'].sort_values('Power', ascending=False)
    
    fastest = current_df.sort_values('Velocity', ascending=False)
    
    return {
        "Leader": leaders.iloc[0]['Sector'] if not leaders.empty else "None",
        "Emerging": improving.iloc[0]['Sector'] if not improving.empty else "None",
        "Lagging": lagging.iloc[0]['Sector'] if not lagging.empty else "None",
        "Fastest": fastest.iloc[0]['Sector'] if not fastest.empty else "None",
        "current_data": current_df
    }


def predict_future_rotation(rrg_df: pd.DataFrame) -> pd.DataFrame:
    """Estimates the next position using simple vector projection."""
    if rrg_df.empty:
        return pd.DataFrame()
        
    # Get last 2 weeks
    dates = sorted(rrg_df['WeekDate'].unique())
    if len(dates) < 2:
        return pd.DataFrame()
        
    last_2_dates = dates[-2:]
    recent = rrg_df[rrg_df['WeekDate'].isin(last_2_dates)].copy()
    
    projections = []
    for sector, group in recent.groupby('Sector'):
        if len(group) == 2:
            group = group.sort_values('WeekDate')
            dx = group['RS_Ratio'].iloc[1] - group['RS_Ratio'].iloc[0]
            dy = group['RS_Momentum'].iloc[1] - group['RS_Momentum'].iloc[0]
            
            proj_x = group['RS_Ratio'].iloc[1] + dx
            proj_y = group['RS_Momentum'].iloc[1] + dy
            
            projections.append({
                "Sector": sector,
                "Proj_RS_Ratio": np.clip(proj_x, 85, 115),
                "Proj_RS_Momentum": np.clip(proj_y, 85, 115)
            })
            
    return pd.DataFrame(projections)


@safe_lru_cache(maxsize=32)
def calculate_sector_relationships(target_year: int) -> pd.DataFrame:
    """Builds a correlation matrix of sector momentum to use as network edges."""
    df = prepare_sector_rrg(target_year)
    if df.empty:
        return pd.DataFrame()
        
    pivot = df.pivot(index='WeekDate', columns='Sector', values='RS_Momentum')
    corr = pivot.corr().fillna(0)
    
    # Flatten to edges
    edges = []
    sectors = corr.columns
    for i in range(len(sectors)):
        for j in range(i + 1, len(sectors)):
            val = corr.iloc[i, j]
            if abs(val) > 0.3: # Minimum threshold
                edges.append({
                    "source": sectors[i],
                    "target": sectors[j],
                    "weight": val
                })
                
    return pd.DataFrame(edges).sort_values(by="weight", key=abs, ascending=False)