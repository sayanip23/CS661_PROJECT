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

<<<<<<< HEAD
    df = get_global_data()
    if df.empty:
        return pd.DataFrame()
        
    mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
    filtered = df.loc[mask].copy()
=======
def load_data(start_date=None, end_date=None) -> pd.DataFrame:
    """Fetches clean stock data from DuckDB and ensures proper datetime typing.

    Note: only date-range filtering is supported here (not sector/company).
    The RRG is inherently a sector-vs-sector-vs-market comparison, so
    narrowing the company/sector universe would remove the very comparison
    the page exists to show.
    """
    conditions = []
    params = []
    if start_date is not None:
        conditions.append("Date >= CAST(? AS DATE)")
        params.append(start_date)
    if end_date is not None:
        conditions.append("Date <= CAST(? AS DATE)")
        params.append(end_date)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT Company, Sector, Date, Close
        FROM clean_stock_data
        {where_clause}
        ORDER BY Sector, Company, Date;
    """
    try:
        df = run_query(query, tuple(params) if params else None)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch stock data from DuckDB: {e}")

    df["Date"] = pd.to_datetime(df["Date"])

    required = {"Company", "Sector", "Date", "Close"}
    if missing := required - set(df.columns):
        raise ValueError(f"Database table is missing columns: {missing}")

    return df


def create_sector_index(df: pd.DataFrame, weighting: str = "return") -> pd.DataFrame:
    """
    Collapses individual company stock prices into a daily index per sector.
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
    
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


<<<<<<< HEAD
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
    
=======
def compute_relative_strength(sector_df: pd.DataFrame, market_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates raw Relative Strength (RS = Sector / Market * 100).
    Both series are rebased to 100 at their common starting date so they scale cleanly.
    """
    sector_df = sector_df.copy()
    market_df = market_df.copy()

    sector_start = sector_df.groupby("Sector")["SectorIndex"].transform("first")
    sector_df["SectorIndex"] = (sector_df["SectorIndex"] / sector_start) * 100

    market_start = market_df["MarketIndex"].iloc[0]
    market_df["MarketIndex"] = (market_df["MarketIndex"] / market_start) * 100

    merged = sector_df.merge(market_df, on="Date", how="inner")
    merged["RS"] = (merged["SectorIndex"] / merged["MarketIndex"]) * 100
    return merged


def compute_rs_ratio(df: pd.DataFrame, window: int = RS_RATIO_WINDOW) -> pd.DataFrame:
    """
    Normalizes raw RS against its own rolling simple moving average.
    This forces all sectors to oscillate around a center baseline of 100.
    """
    df = df.copy()
    rolling_ma = df.groupby("Sector")["RS"].transform(
        lambda s: s.rolling(window, min_periods=window).mean()
    )
    df["RS_Ratio"] = 100 * (df["RS"] / rolling_ma)
    return df


def compute_rs_momentum(df: pd.DataFrame, window: int = RS_MOMENTUM_WINDOW) -> pd.DataFrame:
    """
    Measures the velocity (rate of change) of the RS-Ratio over time.
    A value above 0 means relative performance is accelerating; below 0 means it's fading.
    """
    df = df.copy()
    shifted_ratio = df.groupby("Sector")["RS_Ratio"].shift(window)
    df["RS_Momentum"] = ((df["RS_Ratio"] / shifted_ratio) - 1) * 100
    return df


def classify_quadrants(df: pd.DataFrame) -> pd.DataFrame:
    """Assigns each sector to an RRG quadrant based on the 100/0 intersection."""
    df = df.copy()

    high_rs = df["RS_Ratio"] >= 100
    high_mom = df["RS_Momentum"] >= 0

    df["Quadrant"] = "Improving"
    df.loc[high_rs & high_mom, "Quadrant"] = "Leading"
    df.loc[high_rs & ~high_mom, "Quadrant"] = "Weakening"
    df.loc[~high_rs & ~high_mom, "Quadrant"] = "Lagging"

    # Mask early warm-up periods where moving averages haven't populated yet
    not_warmed_up = df["RS_Ratio"].isna() | df["RS_Momentum"].isna()
    df.loc[not_warmed_up, "Quadrant"] = None

    return df


def prepare_animation_data(df: pd.DataFrame, freq: str = RESAMPLE_FREQ) -> pd.DataFrame:
    """
    Resamples daily metrics to weekly/monthly intervals.
    Plotly animations struggle with thousands of daily frames, so taking the last 
    trading day of each week keeps the UI fast and responsive.
    """
    df = df.dropna(subset=["RS_Ratio", "RS_Momentum"]).copy()
    df["Period"] = df["Date"].dt.to_period(freq).dt.start_time

    anim = (
        df.groupby(["Sector", "Period"], as_index=False)
        .agg(
            RS_Ratio=("RS_Ratio", "last"),
            RS_Momentum=("RS_Momentum", "last"),
            Quadrant=("Quadrant", "last"),
        )
        .sort_values(["Sector", "Period"])
    )
    anim["PeriodStr"] = anim["Period"].dt.strftime("%Y-%m-%d")
    return anim


def run_sector_rotation_pipeline(
    weighting: str = "return", freq: str = RESAMPLE_FREQ, start_date=None, end_date=None
) -> dict:
    """Executes the full RRG data pipeline and returns datasets for the Dash UI."""
    df = load_data(start_date=start_date, end_date=end_date)
    sector_df = create_sector_index(df, weighting=weighting)
    market_df = create_market_index(df, weighting=weighting)

    rs_df = compute_relative_strength(sector_df, market_df)
    rs_df = compute_rs_ratio(rs_df)
    rs_df = compute_rs_momentum(rs_df)
    rs_df = classify_quadrants(rs_df)
    anim_df = prepare_animation_data(rs_df, freq=freq)

>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
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