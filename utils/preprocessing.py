import os
import pandas as pd



INPUT_FILE = "data/processed/master_stock_data.csv"
OUTPUT_FILE = "data/processed/clean_stock_data.csv"
REPORT_FILE = "docs/data_quality_report.md"

os.makedirs("data/processed", exist_ok=True)
os.makedirs("docs", exist_ok=True)



# Function 1
# Load Dataset
def load_dataset():

    print("="*60)
    print("LOADING DATASET")
    print("="*60)

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows    : {df.shape[0]}")
    print(f"Columns : {df.shape[1]}")

    return df





# Function 2
# Dataset Information
def dataset_info(df):

    print("\nDATASET INFORMATION")

    print(df.dtypes)

    print("\nFirst 5 rows")

    print(df.head())



# Function 3
# Missing Values
def check_missing_values(df):

    print("\nChecking Missing Values...")

    missing = df.isnull().sum()

    report = pd.DataFrame({

        "Column": missing.index,
        "Missing Values": missing.values,
        "Percentage": (missing.values/len(df)*100).round(2)

    })

    print(report)

    return report




# Function 4
# Convert Data Types
def convert_datatypes(df):

    print("\nConverting Data Types...")

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    float_cols = [
        "Open",
        "High",
        "Low",
        "Close",
        "Last",
        "Prev_Close",
        "VWAP",
        "Turnover",
        "Trades",
        "Deliverable_Volume",
        "Percent_Deliverable"
    ]

    for col in float_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df["Volume"] = pd.to_numeric(
        df["Volume"],
        errors="coerce"
    )
    df["Trades"] = df["Trades"].fillna("NaN")
    return df




# Function 5
# Sort
def sort_dataset(df):

    print("\nSorting Dataset...")

    return df.sort_values(
        ["Company","Date"]
    ).reset_index(drop=True)




# Function 6
# Duplicate Rows
def remove_duplicates(df):

    duplicate_rows = df.duplicated().sum()

    print(f"\nDuplicate Rows : {duplicate_rows}")

    df = df.drop_duplicates()

    return df, duplicate_rows



# Function 7
# Validation
def validate_dataset(df):

    print("\nValidating Dataset...")

    invalid = pd.Series(False,index=df.index)

    critical = [
        "Company",
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    invalid |= df[critical].isnull().any(axis=1)

    invalid |= df["Open"]<=0
    invalid |= df["High"]<=0
    invalid |= df["Low"]<=0
    invalid |= df["Close"]<=0

    invalid |= df["Volume"]<0

    invalid |= df["High"]<df["Low"]

    removed = invalid.sum()

    df = df[~invalid]

    print(f"Invalid Rows Removed : {removed}")

    return df.reset_index(drop=True), removed




# Function 8
# Trading Days

# Put all three checks together.

def verify_trading_data(df):

    print("\nVerifying Trading Data...")

    # -------------------------------------------------
    # 1. Chronological Order Check
    # -------------------------------------------------

    chronological_errors = []

    for company, group in df.groupby("Company"):

        if not group["Date"].is_monotonic_increasing:
            chronological_errors.append(company)

    if len(chronological_errors) == 0:
        print("✓ All companies are in chronological order.")
    else:
        print(f"{len(chronological_errors)} companies have date ordering issues.")

    # -------------------------------------------------
    # 2. Duplicate Trading Dates
    # -------------------------------------------------

    duplicate_dates = df[df.duplicated(
        subset=["Company", "Date"],
        keep=False
    )]

    if duplicate_dates.empty:
        print("✓ No duplicate trading dates found.")
    else:
        print(f"Duplicate trading date rows: {len(duplicate_dates)}")

    # -------------------------------------------------
    # 3. Trading Day Gap Analysis
    # -------------------------------------------------

    gap_report = []

    for company, group in df.groupby("Company"):

        group = group.sort_values("Date")

        gaps = group["Date"].diff().dt.days

        max_gap = gaps.max()

        if pd.notna(max_gap):

            idx = gaps.idxmax()

            gap_report.append({
                "Company": company,
                "Maximum Gap (Days)": int(max_gap),
                "Gap Ends On": group.loc[idx, "Date"].date()
            })

    gap_df = pd.DataFrame(gap_report)

    print("\nTop 10 Largest Trading Gaps")

    print(
        gap_df.sort_values(
            "Maximum Gap (Days)",
            ascending=False
        ).head(10)
    )

    return duplicate_dates, chronological_errors, gap_df


# Function 9
# Outliers
def detect_outliers(df):

    print("\nDetecting Outliers...")

    outlier_report = {}

    columns_to_check = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Turnover"
    ]

    for col in columns_to_check:

        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)

        IQR = Q3 - Q1

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        outliers = ((df[col] < lower) | (df[col] > upper)).sum()

        outlier_report[col] = outliers

    print("\nOutlier Summary")
    print("-" * 30)

    for col, count in outlier_report.items():
        print(f"{col:<12}: {count}")

    return outlier_report



# Function 10
# Save Dataset
def save_dataset(df):

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"\nDataset saved to {OUTPUT_FILE}")
    
    
    
    

# Function 11
# Generate Report


def generate_report(
    df,
    missing_report,
    duplicate_rows,
    invalid_rows,
    outlier_report,
    duplicate_dates,
    chronological_errors,
    gap_df
):

    with open(REPORT_FILE,"w") as f:

        f.write("# Data Quality Report\n\n")

        f.write("## Dataset Summary\n")

        f.write(f"Rows : {len(df)}\n")
        f.write(f"Columns : {len(df.columns)}\n")
        f.write(f"Companies : {df.Company.nunique()}\n")
        f.write(f"Sectors : {df.Sector.nunique()}\n")
        f.write(
            f"Date Range : {df.Date.min().date()} to {df.Date.max().date()}\n\n"
        )

        f.write("## Missing Values\n\n")
        f.write(missing_report.to_string(index=False))
        f.write("\n\n")

        f.write(f"Duplicate Rows Removed : {duplicate_rows}\n\n")

        f.write(f"Invalid Rows Removed : {invalid_rows}\n\n")

        f.write("## Outliers\n")

        for col,count in outlier_report.items():

            f.write(f"{col} : {count}\n")

        f.write("\n")

        f.write("## Largest Trading Gaps\n\n")
        
        f.write(f"Duplicate Trading Dates : {len(duplicate_dates)}\n")
        f.write(f"Chronological Errors : {len(chronological_errors)}\n\n")

        f.write(
            gap_df
            .sort_values("Maximum Gap (Days)",ascending=False)
            .head(10)
            .to_string(index=False)
        )

    print("\nReport Generated Successfully")
    
    
    

# Main Function
def main():

    df = load_dataset()

    dataset_info(df)

    missing = check_missing_values(df)

    df = convert_datatypes(df)

    df = sort_dataset(df)

    df, duplicates = remove_duplicates(df)

    df, invalid = validate_dataset(df)

    duplicate_dates, chronological_errors, gap_df = verify_trading_data(df)

    outliers = detect_outliers(df)

    save_dataset(df)

    generate_report(
        df,
        missing,
        duplicates,
        invalid,
        outliers,
        duplicate_dates,
        chronological_errors,
        gap_df
    )

if __name__=="__main__":
    main()



















