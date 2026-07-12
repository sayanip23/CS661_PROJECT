# =============================================================================
# SIDEBAR
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from utils.database import run_query

df = run_query("""
SELECT
    Company,
    Sector,
    Date
FROM clean_stock_data
""")

df["Date"] = pd.to_datetime(df["Date"])

date_options = [
    {
        "label": d.strftime("%d-%b-%Y"),
        "value": d.strftime("%Y-%m-%d")
    }
    for d in sorted(df["Date"].unique())
]

sector_options = [
    {
        "label": s,
        "value": s
    }
    for s in sorted(df["Sector"].dropna().unique())
]

company_options = [
    {
        "label": c,
        "value": c
    }
    for c in sorted(df["Company"].dropna().unique())
]

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

                    html.P(
                        "Visual Analytics",
                        className="sidebar-subtitle"
                    ),

                ],

                className="sidebar-header",

            ),

            html.Hr(),

            html.H5("Navigation"),

            dbc.Nav(

                [

                    dbc.NavLink(

                        [

                            html.I(className=icon),

                            html.Span(name, className="ms-2"),

                        ],

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
               value=df["Date"].min().strftime("%Y-%m-%d"),
               clearable=False,
               searchable=True,
          ),

          html.Br(),

          html.Label("End Date"),

          dcc.Dropdown(
             id="end-date-filter",
             options=date_options,
             value=df["Date"].max().strftime("%Y-%m-%d"),
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