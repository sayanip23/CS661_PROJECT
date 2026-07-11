from dash import html
import dash_bootstrap_components as dbc
<<<<<<< HEAD
=======
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
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474

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
            html.Div("ANALYTICS", className="text-muted small fw-bold mb-3 ms-2 nav-text", style={"letterSpacing": "1px"}),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [
                            html.I(className=f"{icon} fs-5"),
                            # Added 'nav-text' class so CSS can hide this span on collapse
                            html.Span(name, className="ms-3 nav-text"), 
                        ],
                        href=path,
                        active="exact",
                        className="nav-link-custom d-flex align-items-center mb-1",
                    )
                    for name, path, icon in PAGES
                ],
                vertical=True,
                pills=True,
            ),
        ]
    )