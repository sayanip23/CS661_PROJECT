from dash import html
import dash_bootstrap_components as dbc

def create_offcanvas_drawer(id_prefix, title, content, placement="end", width="350px"):
    """
    Generic offcanvas drawer used for filters, details, or settings.
    
    Args:
        id_prefix: Used to generate the IDs (e.g. `f"{id_prefix}-drawer"`)
        title: Title of the drawer
        content: The Dash components to render inside
        placement: "start", "end", "top", "bottom"
        width: CSS width
    """
    return dbc.Offcanvas(
        id=f"{id_prefix}-drawer",
        title=title,
        is_open=False,
        placement=placement,
        style={"width": width, "backdropFilter": "blur(4px)"},
        children=content
    )

def create_drawer_footer(apply_id, reset_id):
    """Generic sticky footer for a drawer containing Apply and Reset buttons."""
    return html.Div([
        dbc.Button("Reset Defaults", id=reset_id, color="link", className="text-muted text-decoration-none flex-grow-1 me-2 btn-sm"),
        dbc.Button("Apply Filters", id=apply_id, color="primary", className="fw-bold px-4 btn-sm shadow-sm"),
    ], className="d-flex border-top border-secondary border-opacity-25 pt-3 mt-auto", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
