import os
import numpy as np
import pandas as pd

DATA_PATH = "data/processed/clean_stock_data.csv"
WINDOW_SIZE = 20

# Loads the dataset and computes rolling statistics and Z-Scores
def load_and_compute_base_metrics(path: str = DATA_PATH, window: int = WINDOW_SIZE) -> pd.DataFrame:

    if not os.path.exists(path):
        raise FileNotFoundError(f"Data not found at '{path}'.")

    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.dropna(subset=["Sector", "Close"])
    
    # Sort by Company and Date to ensure rolling calculations are correct
    df = df.sort_values(["Company", "Date"]).reset_index(drop=True)

    # Rolling Mean & Std. Deviation Calculation
    df["Rolling_Mean"] = df.groupby("Company")["Close"].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    df["Rolling_Std"] = df.groupby("Company")["Close"].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )
    
    # Base Z-Score Calculation
    df["Z_Score"] = (df["Close"] - df["Rolling_Mean"]) / df["Rolling_Std"].replace(0, np.nan)
    
    return df

# Applies the user-defined Z-score threshold to identify market shocks and aggregates the results.
def apply_threshold_and_aggregate(df: pd.DataFrame, z_threshold: float) -> dict:

    # Calculates crash and rally flags based on the Z-score threshold
    df["Is_Crash"] = (df["Z_Score"] < -z_threshold).astype(int)
    df["Is_Rally"] = (df["Z_Score"] > z_threshold).astype(int)
    
    # Isolate the Z-scores for anomalous days to calculate averages
    df["Crash_Z"] = df["Z_Score"].where(df["Is_Crash"] == 1)
    df["Rally_Z"] = df["Z_Score"].where(df["Is_Rally"] == 1)
    
    # Aggregate by Date to compute total crashes, rallies, and average Z-scores for each day
    market_df = df.groupby("Date").agg(
        Total_Crashes=("Is_Crash", "sum"),
        Total_Rallies=("Is_Rally", "sum"),
        Crash_Z_Avg=("Crash_Z", "mean"),
        Rally_Z_Avg=("Rally_Z", "mean")
    ).reset_index()

    # Fill NaNs for calm days where no shocks occurred
    market_df["Crash_Z_Avg"] = market_df["Crash_Z_Avg"].fillna(0)
    market_df["Rally_Z_Avg"] = market_df["Rally_Z_Avg"].fillna(0)
    
    # Calculate severity scores by multiplying the number of shocks by their average Z-score
    market_df["Crash_Severity"] = market_df["Total_Crashes"] * market_df["Crash_Z_Avg"]
    market_df["Rally_Severity"] = market_df["Total_Rallies"] * market_df["Rally_Z_Avg"]
    
    # Drop temporary columns from the main dataframe to preserve memory
    df = df.drop(columns=["Crash_Z", "Rally_Z"])
    
    return {
        "company_anomalies": df, 
        "market_shocks": market_df.sort_values("Date").reset_index(drop=True)
    }

# Extracts all company data for a specific day to plot the cross-sectional dispersion
def extract_cross_section(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    target_dt = pd.to_datetime(target_date)
    cross_section = df[df["Date"] == target_dt].copy()
    
    return cross_section.dropna(subset=["Z_Score"])