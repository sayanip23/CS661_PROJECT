import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# =============================================================================
# DASH APP
# =============================================================================

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP
    ],
)

app.title = "NIFTY-50 Visual Analytics"

# =============================================================================
# NAVIGATION
# =============================================================================

PAGES = [
    ("Home", "/", "bi bi-house-fill"),
    ("Correlation Heatmap", "/correlation", "bi bi-grid-3x3-gap-fill"),
    ("Risk vs Return", "/risk_return", "bi bi-bar-chart-fill"),
    ("Market Shock", "/market_shock", "bi bi-lightning-fill"),
    ("Sector Rotation", "/sector_rotation", "bi bi-arrow-repeat"),
    ("Treemap", "/treemap", "bi bi-diagram-3-fill"),
]

# =============================================================================
# SIDEBAR
# =============================================================================

sidebar = html.Div(

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

# =============================================================================
# NAVBAR
# =============================================================================

navbar = dbc.Navbar(

    dbc.Container(

        [

            dbc.NavbarBrand(

                "NIFTY-50 Visual Analytics",

                className="navbar-title",

            ),

            html.Div(

                "CS661 • IIT Kanpur",

                className="navbar-subtitle",

            ),

        ],

        fluid=True,

    ),

    color="dark",

    dark=True,

    fixed="top",

    className="navbar-custom",

)

# =============================================================================
# MAIN CONTENT
# =============================================================================

content = html.Div(

    dash.page_container,

    className="content",

)

# =============================================================================
# APP LAYOUT
# =============================================================================

app.layout = html.Div(

    [

        navbar,

        sidebar,

        content,

    ]

)

# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True)