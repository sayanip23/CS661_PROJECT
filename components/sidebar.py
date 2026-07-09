# =============================================================================
# SIDEBAR
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from utils.database import run_query

# 1. Fetch ONLY the unique values needed for the sidebar using DuckDB
dates_df = run_query("SELECT DISTINCT Date FROM clean_stock_data ORDER BY Date")
dates_df["Date"] = pd.to_datetime(dates_df["Date"])

sectors_df = run_query("SELECT DISTINCT Sector FROM clean_stock_data WHERE Sector IS NOT NULL ORDER BY Sector")
companies_df = run_query("SELECT DISTINCT Company FROM clean_stock_data WHERE Company IS NOT NULL ORDER BY Company")

# 2. Build the dropdown options
date_options = [
    {"label": d.strftime("%d-%b-%Y"), "value": d.strftime("%Y-%m-%d")}
    for d in dates_df["Date"]
]

sector_options = [{"label": s, "value": s} for s in sectors_df["Sector"]]
company_options = [{"label": c, "value": c} for c in companies_df["Company"]]

# Default Date Variables
min_date = dates_df["Date"].min().strftime("%Y-%m-%d")
max_date = dates_df["Date"].max().strftime("%Y-%m-%d")

PAGES = [
    ("Home", "/", "bi bi-house-fill"),
    ("Correlation Heatmap", "/correlation", "bi bi-grid-3x3-gap-fill"),
    ("Risk vs Return", "/risk_return", "bi bi-bar-chart-fill"),
    ("Market Shock", "/market_shock", "bi bi-lightning-fill"),
    ("Sector Rotation", "/sector_rotation", "bi bi-arrow-repeat"),
    ("Treemap", "/treemap", "bi bi-diagram-3-fill"),
]

def create_sidebar():
    return html.Div(
        [
            html.Div(
                [
                    html.H2("NIFTY-50", className="sidebar-title"),
                    html.P("Visual Analytics", className="sidebar-subtitle"),
                ],
                className="sidebar-header",
            ),
            html.Hr(),
            html.H5("Navigation"),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className=icon), html.Span(name, className="ms-2")],
                        href=path,
                        active="exact",
                        className="nav-link-custom",
                    )
                    for name, path, icon in PAGES
                ],
                vertical=True,
                pills=True,
            ),
            html.Hr(),
            html.H5("Filters"),
            html.Label("Start Date"),
            dcc.Dropdown(
               id="start-date-filter",
               options=date_options,
               value=min_date,  # <-- Now uses the fast variable
               clearable=False,
               searchable=True,
            ),
            html.Br(),
            html.Label("End Date"),
            dcc.Dropdown(
               id="end-date-filter",
               options=date_options,
               value=max_date,  # <-- Now uses the fast variable
               clearable=False,
               searchable=True,
            ),
            html.Br(),
            html.Label("Sector"),
            dcc.Dropdown(
                id="sector-filter",
                options=sector_options,
                placeholder="Select sector",
                searchable=True,
                clearable=True,
            ),
            html.Br(),
            html.Label("Company"),
            dcc.Dropdown(
                id="company-filter",
                options=company_options,
                placeholder="Select company",
                searchable=True,
                clearable=True,
            ),
        ],
        className="sidebar",
    )