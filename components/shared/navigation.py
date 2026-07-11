import dash
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc

def create_global_breadcrumbs():
    """Returns a breadcrumb container positioned at the top of the main content."""
    return html.Div(id="global-breadcrumbs-container", className="mb-4")

@callback(
    Output("global-breadcrumbs-container", "children"),
    Input("url", "pathname")
)
def update_breadcrumbs(pathname):
    if not pathname or pathname == "/":
        return html.Nav(
            html.Ol([
                html.Li("Home", className="breadcrumb-item active text-primary fw-bold")
            ], className="breadcrumb bg-transparent p-0 m-0 fs-6 text-uppercase", style={"letterSpacing": "1px"}),
            **{"aria-label": "breadcrumb"}
        )
        
    # Standardize path to name
    path_map = {
        "/correlation": "Correlation Heatmap",
        "/risk_return": "Risk vs Return",
        "/market_shock": "Market Shock",
        "/sector_rotation": "Sector Rotation",
        "/treemap": "Treemap Analytics"
    }
    
    current_page = path_map.get(pathname, pathname.replace("/", " ").strip().title())
    
    return html.Nav(
        html.Ol([
            html.Li(dcc.Link("Home", href="/", className="text-decoration-none text-muted"), className="breadcrumb-item"),
            html.Li(current_page, className="breadcrumb-item active text-primary fw-bold")
        ], className="breadcrumb bg-transparent p-0 m-0 fs-6 text-uppercase", style={"letterSpacing": "1px"}),
        **{"aria-label": "breadcrumb"}
    )
