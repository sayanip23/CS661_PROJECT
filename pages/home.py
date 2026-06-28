import dash
from dash import html
import dash_bootstrap_components as dbc

from components.hero import create_hero
from components.cards import create_stat_card
from components.feature_card import create_feature_card
from components.workflow import create_workflow

dash.register_page(__name__, path="/")

layout = dbc.Container(

    [

        # ============================================================
        # Hero Section
        # ============================================================

        create_hero(),

        html.Br(),

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
                        "50",
                        "bi bi-graph-up-arrow",
                        "success"
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Sectors",
                        "--",
                        "bi bi-building",
                        "primary"
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Years",
                        "--",
                        "bi bi-calendar3",
                        "warning"
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Records",
                        "--",
                        "bi bi-database",
                        "danger"
                    ),
                    md=3
                ),

            ],

            className="mb-5"

        ),

        # ============================================================
        # Available Analytics
        # ============================================================

        html.H3(
            "Available Analysis Modules",
            className="fw-bold mb-4"
        ),

        dbc.Row(

            [

                dbc.Col(

                    create_feature_card(

                        "Correlation Heatmap",

                        "Explore relationships between NIFTY-50 stocks using daily return correlations.",

                        "bi bi-grid-3x3-gap-fill",

                        "/correlation"

                    ),

                    md=4,

                    className="mb-4"

                ),

                dbc.Col(

                    create_feature_card(

                        "Risk vs Return",

                        "Compare expected return and volatility across companies.",

                        "bi bi-bar-chart-fill",

                        "/risk_return"

                    ),

                    md=4,

                    className="mb-4"

                ),

                dbc.Col(

                    create_feature_card(

                        "Market Shock",

                        "Identify abnormal movements and significant market events.",

                        "bi bi-lightning-fill",

                        "/market_shock"

                    ),

                    md=4,

                    className="mb-4"

                ),

            ]

        ),

        dbc.Row(

            [

                dbc.Col(

                    create_feature_card(

                        "Sector Rotation",

                        "Analyze how sectors outperform or underperform over time.",

                        "bi bi-arrow-repeat",

                        "/sector_rotation"

                    ),

                    md=6,

                    className="mb-4"

                ),

                dbc.Col(

                    create_feature_card(

                        "Sector Treemap",

                        "Visualize sector-wise distribution and overall performance.",

                        "bi bi-diagram-3-fill",

                        "/treemap"

                    ),

                    md=6,

                    className="mb-4"

                ),

            ]

        ),

        # ============================================================
        # Workflow
        # ============================================================

        html.H3(
            "Project Workflow",
            className="fw-bold mb-4 mt-3"
        ),

        create_workflow(),

        html.Br(),

        # ============================================================
        # Footer
        # ============================================================

        html.Hr(),

        html.Div(

            [

                html.H5(
                    "CS661 • Visual Analytics Course Project",
                    className="text-center"
                ),

                html.P(
                    "Department of Computer Science and Engineering • IIT Kanpur",
                    className="text-center text-muted"
                )

            ]

        )

    ],

    fluid=True

)