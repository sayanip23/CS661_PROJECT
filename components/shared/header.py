import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
from utils.data_services import get_all_companies, get_all_sectors
from utils.config import ThemeManager

def create_global_header():
    """Returns the persistent top bar for the dashboard, including Global Search."""
    companies = get_all_companies()
    sectors = get_all_sectors()


    return html.Div([
        # Hamburger Toggle
        html.Button(
            html.I(className="bi bi-list fs-4"), 
            id="sidebar-toggle", 
            className="toggle-btn me-3 text-muted",
            **{"aria-label": "Toggle Sidebar"}
        ),
        # Branding
        html.Div([
            html.I(className="bi bi-pie-chart-fill text-primary fs-4 me-2"),
            html.H5("CS661", className="mb-0 fw-bold me-2"),
            html.Span("|", className="text-muted mx-2"),
            html.Span("Quantitative Analytics", className="text-muted small fw-bold text-uppercase", style={"letterSpacing": "1px"})
        ], className="d-flex align-items-center flex-grow-1"),
        
        

        
        html.Div(className="flex-grow-1"), # Spacer to push actions right
        
        # Action Buttons



        # Theme Toggle
        html.Button(
            html.I(className="bi bi-moon-fill fs-5", id="theme-toggle-icon"), 
            id="theme-toggle-btn", 
            className="btn btn-sm btn-link text-muted border-0 text-decoration-none shadow-none",
            **{"aria-label": "Toggle Theme"}
        )
    ], className="top-bar d-flex align-items-center px-4 shadow-sm bg-surface position-fixed w-100", style={"height": "60px", "zIndex": "1040", "top": "0", "left": "0"})


