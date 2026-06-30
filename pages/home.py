import dash
from dash import html
import dash_bootstrap_components as dbc

from components.hero import create_hero
from components.cards import create_stat_card
from components.feature_card import create_feature_card
from components.workflow import create_workflow
from data.data_manager import df

# ============================
# Dashboard Statistics
# ============================

num_stocks = df["Company"].nunique()

num_sectors = df["Sector"].nunique()

num_years = df["Date"].dt.year.nunique()

num_records = len(df)

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