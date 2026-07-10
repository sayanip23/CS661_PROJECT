import dash
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc

from components.hero import create_hero
from components.cards import create_stat_card, create_feature_card
from utils.database import run_query

# ============================
# Dashboard Statistics (via DuckDB)
# ============================

stats_query = """
SELECT 
    COUNT(DISTINCT Company) AS num_stocks,
    COUNT(DISTINCT Sector) AS num_sectors,
    COUNT(DISTINCT EXTRACT(YEAR FROM Date)) AS num_years,
    COUNT(*) AS num_records
FROM clean_stock_data
"""
stats_df = run_query(stats_query)

num_stocks = stats_df["num_stocks"].iloc[0]
num_sectors = stats_df["num_sectors"].iloc[0]
num_years = stats_df["num_years"].iloc[0]
num_records = f"{stats_df['num_records'].iloc[0]:,}" 

dash.register_page(__name__, path="/")

layout = dbc.Container(
    [
        # Hero Section
        create_hero(),
        
        # Dashboard Statistics
        dbc.Row([
            dbc.Col(html.H5("DATASET OVERVIEW", className="fw-bold text-muted mb-0", style={"letterSpacing": "1px", "fontSize": "14px"})),
            dbc.Col(
                html.Button([
                    html.I(className="bi bi-download me-2"), "Download Clean Data"
                ], id="btn-download-csv", className="btn btn-sm btn-outline-primary", **{"aria-label": "Download dataset as CSV"}),
                className="text-end"
            )
        ], className="align-items-center mb-3"),
        
        dcc.Download(id="download-dataframe-csv"),
        
        dbc.Row(
            [
                dbc.Col(create_stat_card("Total Stocks", str(num_stocks), "bi bi-bar-chart-fill", "success"), md=3, className="mb-3 mb-md-0"),
                dbc.Col(create_stat_card("Sectors", str(num_sectors), "bi bi-building", "primary"), md=3, className="mb-3 mb-md-0"),
                dbc.Col(create_stat_card("Years Covered", str(num_years), "bi bi-calendar3", "warning"), md=3, className="mb-3 mb-md-0"),
                dbc.Col(create_stat_card("Daily Records", str(num_records), "bi bi-database-fill", "info"), md=3),
            ],
            className="mb-5"
        ),

        # Features Section
        html.H5("ANALYTICAL TOOLS", className="fw-bold mb-3 text-muted", style={"letterSpacing": "1px", "fontSize": "14px"}),
        
        dbc.Row(
            [
                dbc.Col(create_feature_card(
                    "Correlation Heatmap", 
                    "Discover hidden sector couplings and index redundancies using K-Means clustered returns.",
                    "bi bi-grid-3x3-gap-fill",
                    "/correlation"
                ), md=6, lg=3, className="mb-4"),
                
                dbc.Col(create_feature_card(
                    "Risk vs Return", 
                    "Map out optimal Sharpe clusters on a volatility frontier and inspect historical price history.",
                    "bi bi-graph-up-arrow",
                    "/risk_return"
                ), md=6, lg=3, className="mb-4"),
                
                dbc.Col(create_feature_card(
                    "Market Shocks", 
                    "Detect systemic anomalies via Z-Score divergence and analyze intra-day cross-sectional dispersion.",
                    "bi bi-lightning-charge-fill",
                    "/market_shock"
                ), md=6, lg=3, className="mb-4"),
                
                dbc.Col(create_feature_card(
                    "Sector Rotation (RRG)", 
                    "Track institutional momentum via Relative Rotation Graphs to find leading vs lagging sectors.",
                    "bi bi-arrow-repeat",
                    "/sector_rotation"
                ), md=6, lg=3, className="mb-4"),
            ]
        )
    ],
    fluid=True
)


@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    prevent_initial_call=True
)
def download_data(n_clicks):
    if n_clicks:
        df = run_query("SELECT * FROM clean_stock_data")
        return dcc.send_data_frame(df.to_csv, "nifty50_clean.csv", index=False)