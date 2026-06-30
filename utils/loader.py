import os
import pandas as pd

#Function 1
def load_all_data(raw_data_path):
    """
    Reads all company CSV files from raw_data_path,
    merges them into a single DataFrame,
    and returns the master DataFrame.
    """
    files = os.listdir(raw_data_path)

    all_data = []

    for file in files:
        if not file.endswith(".csv"):
            continue

        if file in ["stock_metadata.csv", "NIFTY50_all.csv"]:
            continue

        file_path = os.path.join(raw_data_path, file)

        df = pd.read_csv(file_path)

        company_name = file.replace(".csv", "")

        # Handle filename and metadata mismatch
        if company_name == "MM":
         company_name = "M&M"

        # Warn if the CSV has no data
        if df.empty:
          print(f"Warning: {company_name}.csv contains no data.")

        df["Company"] = company_name

        df["Symbol"] = company_name

        all_data.append(df)

    
    master_df = pd.concat(all_data, ignore_index=True)

    return master_df

#Function 2
def merge_metadata(master_df, metadata_path):
    """
    Merges sector information into the master dataframe.
    """

    metadata = pd.read_csv(metadata_path)

    metadata = metadata[["Symbol", "Industry"]]

    metadata.rename(
    columns={"Industry": "Sector"},
    inplace=True
    )

    master_df = pd.merge(
    master_df,
    metadata,
    on="Symbol",
    how="left"
    )

    column_mapping = {
        "Prev Close": "Prev_Close",
        "Deliverable Volume": "Deliverable_Volume",
        "%Deliverble": "Percent_Deliverable"
    }

    master_df.rename(columns=column_mapping, inplace=True)

    return master_df

#Function 3
def sort_data(master_df) :
    """
    Sorting data by Company and Date.
    """
    master_df = master_df.sort_values(
        by=["Company", "Date"]
    )

    master_df.reset_index(drop=True, inplace=True)

    return master_df

#Function 4
def save_processed_data(master_df, output_path):
    """
    Saves the processed dataframe to a CSV file.
    """
    # Create the folder if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    master_df.to_csv(output_path, index=False)

#Function 5
def reorder_columns(master_df):
    column_order = [
        "Company",
        "Sector",
        "Date",
        "Symbol",
        "Series",
        "Open",
        "High",
        "Low",
        "Close",
        "Last",
        "Prev_Close",
        "VWAP",
        "Volume",
        "Turnover",
        "Trades",
        "Deliverable_Volume",
        "Percent_Deliverable",
    ]

    return master_df[column_order]

#Function 6
def get_dataset_summary(master_df):
    """
    Returns a summary of the dataset.
    """

    summary = {
        "Rows": len(master_df),
        "Columns": len(master_df.columns),
        "Companies": master_df["Company"].nunique(),
        "Sectors": master_df["Sector"].nunique(),
        "Start Date": master_df["Date"].min(),
        "End Date": master_df["Date"].max()
    }

    return summary
# ------------------------------------------------
# ------------------------------------------------

if __name__ == "__main__":

    master_df = load_all_data("data/raw")

    master_df = merge_metadata(
        master_df,
        "data/raw/stock_metadata.csv"
    )

    master_df = sort_data(master_df)

    master_df = reorder_columns(master_df)

    save_processed_data(
        master_df,
        "data/processed/master_stock_data.csv"
    )

    summary = get_dataset_summary(master_df)

    print("\nDataset Summary\n")

    for key, value in summary.items():
        print(f"{key}: {value}")

    