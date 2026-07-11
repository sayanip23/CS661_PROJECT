from dash import html
import dash_bootstrap_components as dbc

def create_empty_state(title, message, icon="bi-inbox", height="300px"):
    """
    Returns a standardized empty state component to use throughout the dashboard.
    
    Args:
        title (str): The main title (e.g. "No Data Found")
        message (str): The subtext message.
        icon (str): A bootstrap icon class (e.g. "bi-inbox", "bi-search")
        height (str): The minimum height of the container.
    """
    return html.Div(
        [
            html.I(className=f"bi {icon} text-muted mb-3 d-block", style={"fontSize": "48px"}),
            html.H6(title, className="fw-bold text-muted"),
            html.P(message, className="small text-muted")
        ],
        className="d-flex flex-column justify-content-center align-items-center text-center p-4",
        style={"minHeight": height, "width": "100%"}
    )
