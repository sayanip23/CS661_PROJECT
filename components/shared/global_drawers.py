import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
from components.shared.drawer import create_offcanvas_drawer
from components.shared.empty_state import create_empty_state
from components.cards import create_stat_card
from utils.analytics.home import compute_executive_metrics
from utils.config import ThemeManager

def create_global_drawers():
    """Returns the container for all global offcanvas drawers."""
    
    # 1. Company Details Drawer
    details_drawer = dbc.Offcanvas(
        id="global-details-drawer",
        title="Context Details",
        is_open=False,
        placement="end",
        style={"width": "400px", "backdropFilter": "blur(4px)"},
        className="bg-surface border-start border-secondary border-opacity-25 shadow",
        children=[
            html.Div(id="global-details-content", className="mt-2")
        ]
    )
    return html.Div([details_drawer, dcc.Store(id="drawer-current-entity", data=None)])

# ------------------------------------------------------------------------------
# Details Logic
# ------------------------------------------------------------------------------

@callback(
    Output("global-details-drawer", "is_open"),
    Output("drawer-current-entity", "data"),
    Input("event-bus", "data"),
    State("global-details-drawer", "is_open"),
    prevent_initial_call=True
)
def toggle_details_drawer(event_data, is_open):
    if not event_data or event_data.get("type") != "OPEN_COMPANY_DRAWER":
        return no_update, no_update
        
    payload = event_data.get("payload")
    if not payload:
        return no_update, no_update
        
    return True, {"value": payload}

@callback(
    Output("global-details-content", "children"),
    Input("drawer-current-entity", "data"),
    Input("theme-store", "data")
)
def render_details(current_entity, theme):
    if not current_entity or not current_entity.get("value"):
        return ""
        
    context_type, name = current_entity["value"].split(":", 1)
    
    # Re-use existing metrics pipeline to grab data efficiently
    metrics = compute_executive_metrics() 
    # metrics is cached and extremely fast
    
    if context_type == "Company":
        # Extract company from top/bottom movers just as a quick hack
        # Normally we'd pass raw_df or company_growth down, but since compute_executive_metrics() 
        # doesn't export company_growth directly, we'll need to fetch it.
        # Actually, let's fetch it via run_treemap_pipeline for a proper lookup
        from utils.analytics.treemap import run_treemap_pipeline
        res = run_treemap_pipeline("2021-01-01", "2022-12-31")
        df = res["company_growth"]
        comp = df[df["Company"] == name]
        
        if comp.empty:
            return html.Div("Company data not found in current window.", className="text-muted p-3")
            
        c = comp.iloc[0]
        
        return html.Div([
            html.H5([html.I(className="bi bi-building me-2 text-primary"), html.Span(name, className="text-body")], className="fw-bold mb-1"),
            html.Span(c["Sector"], className="badge bg-primary bg-opacity-25 text-primary mb-3"),
            html.H6("COMPANY INTELLIGENCE", className="text-muted text-uppercase fw-bold mb-3", style={"letterSpacing": "1px", "fontSize": "11px"}),
            dbc.Row([
                dbc.Col(create_stat_card("CAGR", f"{c['CAGR']:.2%}", "bi-graph-up-arrow", "success"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Volatility", f"{c['Volatility']:.1%}", "bi-activity", "warning"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Sharpe", f"{c['Sharpe_Ratio']:.2f}", "bi-lightning-charge", "info"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Max Drawdown", f"{c['Max_Drawdown']:.1%}", "bi-graph-down-arrow", "danger"), width=6, className="mb-3"),
            ]),
            
            html.H6("MARKET WEIGHT", className="text-muted text-uppercase fw-bold mb-2 mt-4", style={"letterSpacing": "1px", "fontSize": "11px"}),
            html.P(f"This company constitutes {c['Market_Weight']:.2%} of the NIFTY-50 total volume.", className="small text-muted")
        ])
    else:
        # Sector
        from utils.analytics.treemap import run_treemap_pipeline
        res = run_treemap_pipeline("2021-01-01", "2022-12-31")
        df = res["sector_growth"]
        sec = df[df["Sector"] == name]
        
        if sec.empty:
            return html.Div("Sector data not found.", className="text-muted p-3")
            
        s = sec.iloc[0]

        return html.Div([
            html.H5([html.I(className="bi bi-diagram-3 me-2 text-primary"), html.Span(name, className="text-body")], className="fw-bold mb-3"),
            html.H6("SECTOR INTELLIGENCE", className="text-muted text-uppercase fw-bold mb-3", style={"letterSpacing": "1px", "fontSize": "11px"}),
            dbc.Row([
                dbc.Col(create_stat_card("Average CAGR", f"{s['CAGR']:.2%}", "bi-graph-up-arrow", "success"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Average Vol", f"{s['Volatility']:.1%}", "bi-activity", "warning"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Total Weight", f"{s['Market_Weight']:.1%}", "bi-pie-chart-fill", "primary"), width=12, className="mb-3"),
            ])
        ])
