# NIFTY-50 Visual Analytics Dashboard

A multi-page Dash application for visual analytics on NIFTY-50 stock market data, with a reproducible data processing pipeline and DuckDB-backed querying.

## Project Overview

This repository contains:

- **Data engineering scripts** to combine raw stock CSV files, merge metadata, validate quality, and generate cleaned outputs.
- **A DuckDB data layer** for fast analytical queries from dashboard pages.
- **A multi-page dashboard** built with Dash + Plotly for market analytics visualizations.

The codebase is organized around one end-to-end flow:

1. Build `master_stock_data.csv` from raw files (`utils/loader.py`)
2. Clean/validate and produce `clean_stock_data.csv` + `stocks.duckdb` (`utils/preprocessing.py`)
3. Serve interactive analytics via Dash pages (`app.py`, `pages/*.py`)

## Repository Structure

```text
.
├── app.py                         # Dash app entry point (multi-page layout)
├── requirements.txt               # Python dependencies
├── generate_correlation_figures.py
├── assets/                        # CSS/static assets for Dash
├── callbacks/                     # Placeholder callback modules (currently empty)
├── components/                    # Reusable UI components (navbar, sidebar, cards, etc.)
├── data/
│   └── raw/                       # Raw input CSV files
├── docs/
│   └── data_quality_report.md     # Generated quality report from preprocessing
├── pages/                         # Individual dashboard pages
│   ├── home.py
│   ├── correlation.py
│   ├── risk_return.py
│   ├── market_shock.py
│   ├── sector_rotation.py
│   └── treemap.py
└── utils/
    ├── loader.py                  # Raw data consolidation + metadata merge
    ├── preprocessing.py           # Cleaning, validation, outlier checks, DuckDB export
    ├── database.py                # DuckDB initialization + query helpers
    ├── constants.py               # currently empty
    ├── metrics.py                 # currently empty
    └── analytics/                 # analytics helpers (package directory)
```

## Key Features (Implemented)

Based on the current code and file structure, the project includes these implemented modules/pages:

- **Correlation Analysis** (`pages/correlation.py`)
- **Risk vs Return Analysis** (`pages/risk_return.py`)
- **Market Shock Analysis** (`pages/market_shock.py`)
- **Sector Rotation Analysis** (`pages/sector_rotation.py`)
- **Treemap-based Market View** (`pages/treemap.py`)
- **Landing/Home page** (`pages/home.py`)

> Note: The previous README referenced a few generic/promotional items (e.g., badges/theme claims/docs links) that are not consistently represented in this repository. This README reflects only what is present in code/files.

## Technology Stack

### Application

- Python 3
- Dash (`dash==2.18.2`)
- Dash Bootstrap Components (`dash-bootstrap-components==1.6.0`)
- Plotly (`plotly==5.24.1`)

### Data and Analytics

- Pandas (`pandas==2.2.3`)
- NumPy (`numpy==2.2.1`)
- SciPy (`scipy==1.14.1`)
- Scikit-learn (`scikit-learn==1.6.0`)
- DuckDB (`duckdb==1.3.2`)

## Data Pipeline

### 1) Raw Data Consolidation (`utils/loader.py`)

- Reads per-company CSV files from `data/raw/`
- Skips non-data files like `stock_metadata.csv` and `NIFTY50_all.csv`
- Adds `Company` and `Symbol` columns
- Merges sector metadata from `stock_metadata.csv`
- Normalizes/selects column names and order
- Saves `data/processed/master_stock_data.csv`

### 2) Data Cleaning & Validation (`utils/preprocessing.py`)

- Loads `master_stock_data.csv`
- Converts date and numeric datatypes safely (`errors="coerce"`)
- Removes duplicate rows
- Validates critical columns and price/volume constraints
- Performs trading-series checks:
  - chronological order per company
  - duplicate (Company, Date) checks
  - gap analysis between trading dates
- Detects outliers with IQR-based thresholds
- Saves:
  - `data/processed/clean_stock_data.csv`
  - `data/processed/stocks.duckdb` (table: `clean_stock_data`)
- Generates `docs/data_quality_report.md`

### 3) DuckDB Runtime Access (`utils/database.py`)

- Ensures DB/table exists at import time (`init_db()`)
- Auto-creates `clean_stock_data` table from CSV if missing
- Exposes:
  - `get_connection()` (read-only)
  - `run_query(query, params=None)` → Pandas DataFrame

## Dashboard Architecture

- `app.py` initializes Dash with `use_pages=True`
- Layout includes reusable navbar + sidebar components
- Individual analytical views live under `pages/`
- Shared UI fragments are in `components/`

## Setup and Run

### 1. Clone

```bash
git clone https://github.com/sayanip23/CS661_PROJECT.git
cd CS661_PROJECT
```

### 2. Create virtual environment

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare processed data (recommended)

Run these scripts in sequence:

```bash
python utils/loader.py
python utils/preprocessing.py
```

This creates:

- `data/processed/master_stock_data.csv`
- `data/processed/clean_stock_data.csv`
- `data/processed/stocks.duckdb`
- `docs/data_quality_report.md`

### 5. Launch dashboard

```bash
python app.py
```

Then open: `http://127.0.0.1:8050`

## Current Repository Notes

- `callbacks/filters.py`, `callbacks/interaction.py`, `callbacks/state.py` are currently empty placeholders.
- `utils/constants.py` and `utils/metrics.py` are currently empty.
- The data quality report currently indicates **49 companies** (not 50) in the prepared dataset.

## License

No license file is currently present in the repository root. If you want, add a `LICENSE` file and reference it here.
