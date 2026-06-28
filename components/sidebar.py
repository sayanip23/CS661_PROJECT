# =============================================================================
# SIDEBAR
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc

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

            html.Label("Date Range"),

            dcc.Dropdown(
                id="date-filter",
                placeholder="Coming Soon",
                disabled=True,
            ),

            html.Br(),

            html.Label("Sector"),

            dcc.Dropdown(
                id="sector-filter",
                placeholder="Coming Soon",
                disabled=True,
            ),

            html.Br(),

            html.Label("Company"),

            dcc.Dropdown(
                id="company-filter",
                placeholder="Coming Soon",
                disabled=True,
            ),

        ],

        className="sidebar",

    )