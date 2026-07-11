import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
from components.sidebar import create_sidebar

import plotly.io as pio
from utils.config import get_plotly_template

# Register custom financial themes
pio.templates["financial_dark"] = pio.templates["plotly_dark"]
pio.templates["financial_dark"].layout.update(get_plotly_template("dark"))

pio.templates["financial_light"] = pio.templates["plotly_white"]
pio.templates["financial_light"].layout.update(get_plotly_template("light"))

pio.templates.default = "financial_dark"

# ==========================================
# Initialize Dash App
# ==========================================
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        dbc.icons.BOOTSTRAP
    ],
    suppress_callback_exceptions=True
)

# ==========================================
# Master Layout with Sliding State
# ==========================================
# ==========================================
# Master Layout with Top Bar & Mini-Sidebar
# ==========================================

from components.shared.header import create_global_header
from components.shared.global_drawers import create_global_drawers
from components.shared.navigation import create_global_breadcrumbs
from components.shared.notifications import create_global_notifications
from components.shared.command_palette import create_command_palette
from components.shared.export_center import create_export_center

# ==========================================
# Master Layout with Top Bar & Mini-Sidebar
# ==========================================


app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="sidebar-state", data=True, storage_type="local"),
    # Global state initialized empty
    dcc.Store(id="global-state", data={"sectors": [], "companies": []}, storage_type="local"),
    # Event Bus for cross-page communication
    dcc.Store(id="event-bus", data={"type": None, "payload": None}, storage_type="memory"),
    # Theme state initialized to dark
    dcc.Store(id="theme-store", data="dark", storage_type="local"),
    
    # Global Intelligence State

    dcc.Store(id="comparison-state", data=[], storage_type="local"),
    
    # Notification State
    dcc.Store(id="notification-bus", data=None, storage_type="memory"),
    
    # Inject Global Components
    create_global_header(),
    create_global_drawers(),
    create_global_notifications(),
    create_command_palette(),
    create_export_center(),
    
    # Inject Sidebar (Now positioned below Top Bar via CSS)
    html.Div(create_sidebar(), id="sidebar", className="sidebar", role="navigation"),
    
    # Inject Main Content wrapped in a global Error Boundary
    html.Main([
        # Breadcrumbs Navigation
        create_global_breadcrumbs(),
        
        # Page Content
        dcc.Loading(
            dash.page_container,
            type="circle",
            color="var(--accent-primary)"
        )
    ],
    id="page-content", 
    className="content", 
    role="main"
    )
])

# ==========================================
# Sliding Animation Callback
# ==========================================
@app.callback(
    Output("sidebar", "className"),
    Output("page-content", "className"),
    Output("sidebar-state", "data"),
    Input("sidebar-toggle", "n_clicks"),
    State("sidebar-state", "data"),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, is_open):
    if is_open:
        # If open -> Close it and expand content
        return "sidebar collapsed", "content expanded", False
    else:
        return "sidebar", "content", True






# ==========================================
# Theme Toggle Clientside Callback
# ==========================================
dash.clientside_callback(
    """
    function(n_clicks, current_theme) {
        let new_theme = current_theme;
        
        // If triggered by button click, toggle theme
        if (dash_clientside.callback_context.triggered.length > 0) {
            new_theme = current_theme === 'dark' ? 'light' : 'dark';
        }
        
        // Apply theme to body
        document.documentElement.setAttribute('data-theme', new_theme);
        document.body.setAttribute('data-theme', new_theme);
        
        // Apply theme to Bootstrap 5
        document.documentElement.setAttribute('data-bs-theme', new_theme);
        
        // Update AG Grid themes
        document.querySelectorAll('.ag-theme-alpine, .ag-theme-alpine-dark').forEach(el => {
            el.classList.remove('ag-theme-alpine', 'ag-theme-alpine-dark');
            el.classList.add(new_theme === 'dark' ? 'ag-theme-alpine-dark' : 'ag-theme-alpine');
        });
        
        // Update icon class
        const icon_class = new_theme === 'dark' ? 'bi bi-moon-fill fs-5' : 'bi bi-sun-fill fs-5 text-warning';
        
        return [new_theme, icon_class];
    }
    """,
    Output("theme-store", "data"),
    Output("theme-toggle-icon", "className"),
    Input("theme-toggle-btn", "n_clicks"),
    State("theme-store", "data")
)


if __name__ == "__main__":
    app.run(debug=True, port=8050)        # New Dash 2.0+ syntax
