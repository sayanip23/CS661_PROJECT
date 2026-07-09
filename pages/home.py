import dash
from dash import html
import dash_bootstrap_components as dbc

from components.hero import create_hero
from components.cards import create_stat_card
from components.feature_card import create_feature_card
from components.workflow import create_workflow
from utils.database import run_query

# ============================
# Dashboard Statistics (via DuckDB)
# ============================

# Fetch all overview stats in a single, ultra-fast SQL query
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
# Add comma formatting so millions of records are readable (e.g., "1,234,567")
num_records = f"{stats_df['num_records'].iloc[0]:,}" 

dash.register_page(__name__, path="/")

layout = dbc.Container(

    [

        # ============================================================
        # Hero Section
        # ============================================================

        create_hero(),

        

        # ============================================================
        # Dashboard Statistics
        # ============================================================

        html.H3(
            "Dashboard Overview",
            className="fw-bold mb-4"
        ),

        dbc.Row(

            [

                dbc.Col(
                    create_stat_card(
                        "Stocks",
                        str(num_stocks),
                        "bi bi-graph-up-arrow",
                        "success"
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Sectors",
                        str(num_sectors),
                        "bi bi-building",
                        "primary"
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Years",
                        str(num_years),
                        "bi bi-calendar3",
                        "warning"
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Records",
                        str(num_records),
                        "bi bi-database",
                        "danger"
                    ),
                    md=3
                ),

            ],

            className="mb-3"

        ),

        dbc.Alert(
            [
                html.I(className="bi bi-info-circle-fill me-2"),
                html.B("Dataset Note: "),
                "Historical trading data for ",
                html.B("Infratel"),
                " was unavailable in the collected dataset. "
                "Therefore, all visualizations and analyses are based on ",
                html.B("49 companies"),
                " instead of the complete NIFTY-50."
            ],
          color="light",
          className="shadow-sm border-start border-4 border-primary mt-2 mb-4",
        )

    ],

    fluid=True

)