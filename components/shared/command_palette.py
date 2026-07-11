import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
import json

def create_command_palette():
    """
    Returns the Command Palette modal triggered by Ctrl+K.
    """
    
    commands = [
        {"label": html.Div([html.I(className="bi bi-house me-3"), "Go to Home Dashboard"]), "value": "/"},
        {"label": html.Div([html.I(className="bi bi-graph-up me-3"), "Go to Risk vs Return"]), "value": "/risk-return"},
        {"label": html.Div([html.I(className="bi bi-lightning-charge me-3"), "Go to Market Shock"]), "value": "/market-shock"},
        {"label": html.Div([html.I(className="bi bi-arrow-repeat me-3"), "Go to Sector Rotation"]), "value": "/sector-rotation"},
        {"label": html.Div([html.I(className="bi bi-diagram-3 me-3"), "Go to Correlation Network"]), "value": "/correlation"},
        {"label": html.Div([html.I(className="bi bi-grid-3x3-gap me-3"), "Go to Treemap Analytics"]), "value": "/treemap"},
        {"label": html.Div([html.I(className="bi bi-moon me-3"), "Toggle Theme"]), "value": "CMD_THEME"},
        {"label": html.Div([html.I(className="bi bi-star me-3"), "Open Watchlist"]), "value": "CMD_WATCHLIST"},
        {"label": html.Div([html.I(className="bi bi-projector me-3"), "Toggle Presentation Mode"]), "value": "CMD_PRESENTATION"},
    ]
    
    return html.Div([
        # Hidden button triggered by shortcuts.js
        html.Button(id="cmd-palette-toggle", style={"display": "none"}),
        
        dbc.Modal([
            dbc.ModalBody([
                html.Div([
                    html.I(className="bi bi-search text-muted me-3 fs-5"),
                    dcc.Dropdown(
                        id="cmd-palette-input",
                        options=commands,
                        placeholder="Search commands or navigate... (e.g. 'Theme', 'Home')",
                        className="cmd-palette-dropdown flex-grow-1",
                        clearable=False,
                    )
                ], className="d-flex align-items-center bg-surface px-3 py-2 rounded shadow-sm border")
            ], className="p-0 border-0 bg-transparent")
        ],
        id="cmd-palette-modal",
        is_open=False,
        centered=True,
        size="lg",
        backdropClassName="cmd-palette-backdrop",
        contentClassName="bg-transparent border-0"
        ),
        
        # State for Presentation Mode
        dcc.Store(id="presentation-mode-state", data=False, storage_type="local")
    ])

@callback(
    Output("cmd-palette-modal", "is_open"),
    Input("cmd-palette-toggle", "n_clicks"),
    State("cmd-palette-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(n_clicks, is_open):
    return not is_open

# Handle Command Execution
@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("theme-toggle-btn", "n_clicks", allow_duplicate=True),
    Output("watchlist-drawer-toggle", "n_clicks", allow_duplicate=True),
    Output("presentation-mode-state", "data", allow_duplicate=True),
    Output("cmd-palette-modal", "is_open", allow_duplicate=True),
    Output("cmd-palette-input", "value"),
    Input("cmd-palette-input", "value"),
    State("presentation-mode-state", "data"),
    prevent_initial_call=True
)
def execute_command(value, is_presentation):
    if not value:
        return no_update, no_update, no_update, no_update, no_update, no_update
        
    url = no_update
    theme = no_update
    watchlist = no_update
    presentation = no_update
    
    if value.startswith("/"):
        url = value
    elif value == "CMD_THEME":
        theme = 1 # trigger clientside callback
    elif value == "CMD_WATCHLIST":
        watchlist = 1
    elif value == "CMD_PRESENTATION":
        presentation = not is_presentation
        
    # Close modal and clear input
    return url, theme, watchlist, presentation, False, None

# Clientside callback to inject Presentation Mode CSS class into body
dash.clientside_callback(
    """
    function(is_presentation) {
        if (is_presentation) {
            document.body.classList.add("presentation-mode");
            return {"message": "Presentation Mode Enabled. Press Esc to exit.", "type": "success", "icon": "bi-projector", "duration": 4000};
        } else {
            document.body.classList.remove("presentation-mode");
            return {"message": "Presentation Mode Disabled", "type": "info", "icon": "bi-info-circle", "duration": 2000};
        }
    }
    """,
    Output("notification-bus", "data", allow_duplicate=True),
    Input("presentation-mode-state", "data"),
    prevent_initial_call=True
)
