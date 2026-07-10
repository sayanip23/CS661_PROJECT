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

# 1. The New Top Bar Component
top_bar = html.Div([
    # Hamburger Toggle
    html.Button(
        html.I(className="bi bi-list fs-4"), 
        id="sidebar-toggle", 
        className="toggle-btn me-3",
        **{"aria-label": "Toggle Sidebar", "aria-expanded": "true"}
    ),
    # Branding
    html.I(className="bi bi-pie-chart-fill text-primary fs-4 me-2"),
    html.H4("CS661 IIT KANPUR", className="top-bar-title mb-0"),
    html.H6("| Quantitative Analytics", className="top-bar-subtitle mb-0 ms-2 text-muted"),
    
    # Global Filter Summary Area
    html.Div(id="global-filter-summary", className="ms-auto d-flex align-items-center"),
    
    # Theme Toggle
    html.Button(
        html.I(className="bi bi-moon-fill fs-5", id="theme-toggle-icon"), 
        id="theme-toggle-btn", 
        className="btn btn-sm btn-link text-muted ms-3 border-0 text-decoration-none shadow-none",
        **{"aria-label": "Toggle Theme"}
    )
], className="top-bar")


app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="sidebar-state", data=True, storage_type="local"),
    # Global state initialized empty
    dcc.Store(id="global-state", data={"sectors": [], "companies": []}, storage_type="local"),
    # Theme state initialized to dark
    dcc.Store(id="theme-store", data="dark", storage_type="local"),
    
    # Inject Top Bar
    top_bar,
    
    # Inject Sidebar (Now positioned below Top Bar via CSS)
    html.Div(create_sidebar(), id="sidebar", className="sidebar", role="navigation"),
    
    # Inject Main Content wrapped in a global Error Boundary
    html.Main(
        dcc.Loading(
            dash.page_container,
            type="circle",
            color="var(--accent-primary)"
        ), 
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
# Global Filter State Rendering
# ==========================================
@app.callback(
    Output("global-filter-summary", "children"),
    Input("global-state", "data")
)
def render_global_filter(data):
    if not data:
        return ""
    
    sectors = data.get("sectors", [])
    companies = data.get("companies", [])
    
    badges = []
    for s in sectors:
        badges.append(html.Span([s, html.I(className="bi bi-x ms-1")], className="badge bg-primary me-2 px-2 py-1", style={"cursor": "pointer"}))
    for c in companies:
        badges.append(html.Span([c, html.I(className="bi bi-x ms-1")], className="badge bg-secondary me-2 px-2 py-1", style={"cursor": "pointer"}))
        
    if badges:
        badges.append(
            html.Button(
                "Clear All", 
                id="clear-global-filter", 
                className="btn btn-sm btn-outline-danger ms-2 px-2 py-1",
                **{"aria-label": "Clear all global filters"}
            )
        )
        return html.Div([
            html.Span("Active Filters:", className="text-muted small me-2"),
            *badges
        ], className="d-flex align-items-center")
    
    return html.Div(className="text-muted small", children="No active filters")


@app.callback(
    Output("global-state", "data"),
    Input("clear-global-filter", "n_clicks"),
    prevent_initial_call=True
)
def clear_global_filters(n_clicks):
    return {"sectors": [], "companies": []}


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