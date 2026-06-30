import pandas as pd

CLEAN_DATA = "data/processed/clean_stock_data.csv"

df = pd.read_csv(CLEAN_DATA)

df["Date"] = pd.to_datetime(df["Date"])