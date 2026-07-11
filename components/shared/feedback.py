from dash import html
import dash_bootstrap_components as dbc

def create_loading_spinner(component, type="circle", color="var(--accent-primary)"):
    """Generic loading spinner wrapper."""
    from dash import dcc
    return dcc.Loading(
        component,
        type=type,
        color=color
    )

def create_error_state(message):
    """Generic error message display."""
    return html.Div(
        [
            html.I(className="bi bi-exclamation-triangle-fill text-danger mb-2", style={"fontSize": "2rem"}),
            html.H5("Error Loading Data", className="text-danger fw-bold"),
            html.P(message, className="text-muted small")
        ],
        className="d-flex flex-column align-items-center justify-content-center h-100 p-5 text-center"
    )

def create_empty_state(message, icon="bi-inbox"):
    """Generic empty state display."""
    return html.Div(
        [
            html.I(className=f"{icon} text-muted mb-2", style={"fontSize": "2rem"}),
            html.P(message, className="text-muted small fw-bold")
        ],
        className="d-flex flex-column align-items-center justify-content-center h-100 p-5 text-center"
    )
