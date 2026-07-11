import dash
from dash import State, html, dcc, Output, Input, callback, no_update, ALL
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.analytics.correlation import (
    run_correlation_pipeline, generate_network_data, generate_sankey_data,
    calculate_diversification, calculate_time_varying_correlation
)
from utils.config import DEFAULT_N_CLUSTERS, DEFAULT_LINKAGE_METHOD, get_corr_colorscale, MODEBAR_CONFIG, ThemeManager
from utils.visuals import apply_shared_layout, create_empty_figure
from components.cards import create_stat_card
from components.narrative import generate_smart_narrative
from scipy.cluster.hierarchy import dendrogram as scipy_dendrogram

dash.register_page(__name__, path="/correlation", name="Correlation Analysis")

# Fetch companies for dropdown
def _get_all_companies():
    from utils.data_services import get_all_companies
    return get_all_companies()
try:
    ALL_COMPANIES = _get_all_companies()
except Exception:
    ALL_COMPANIES = []


# ---------------------------------------------------------------------------
# View Builders (Original Matrix & Dendrogram logic preserved)
# ---------------------------------------------------------------------------
def create_heatmap(clustered_matrix, order, theme="dark"):
    z = clustered_matrix.values
    fig = go.Figure(data=go.Heatmap(
        z=z, x=order, y=order, colorscale=get_corr_colorscale(theme),
        zmin=-1, zmax=1, zmid=0, colorbar=dict(title="Correlation", thickness=15),
        hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>"
    ))
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=order, tickangle=90, tickfont=dict(size=9))
    fig.update_yaxes(type="category", categoryorder="array", categoryarray=order, autorange="reversed", tickfont=dict(size=9))
    fig = apply_shared_layout(fig, theme=theme, dragmode="select", margin=dict(l=140, r=20, t=10, b=140), height=650)
    return fig

def create_dendrogram(cluster_result, theme="dark"):
    linkage_matrix = cluster_result["linkage_matrix"]
    companies = cluster_result["companies"]
    dendro = scipy_dendrogram(linkage_matrix, labels=companies, no_plot=True, color_threshold=0.7 * max(linkage_matrix[:, 2]))
    fig = go.Figure()
    
    MPL_COLOR_MAP = {
        "C0": "#1f77b4", "C1": "#ff7f0e", "C2": "#2ca02c", "C3": "#d62728",
        "C4": "#9467bd", "C5": "#8c564b", "C6": "#e377c2", "C7": "#7f7f7f",
        "C8": "#bcbd22", "C9": "#17becf", "b": "#1f77b4", "g": "#2ca02c", 
        "r": "#d62728", "c": "#17becf", "m": "#9467bd", "y": "#bcbd22", "k": "#333333"
    }

    colors = ThemeManager.get_colors(theme)
    for icoord, dcoord, color in zip(dendro["icoord"], dendro["dcoord"], dendro["color_list"]):
        x = [(v / 10.0) - 0.5 for v in icoord]
        plot_color = MPL_COLOR_MAP.get(color, color if str(color).startswith("#") else colors["text_secondary"])
        fig.add_trace(go.Scatter(x=x, y=dcoord, mode="lines", line=dict(color=plot_color, width=1.5), hoverinfo="skip", showlegend=False))

    n = len(dendro["ivl"])
    fig.update_xaxes(range=[-0.5, n - 0.5], showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(title="Distance (1 - corr)", showgrid=False, zeroline=False)
    fig = apply_shared_layout(fig, theme=theme, margin=dict(l=140, r=20, t=20, b=0), height=220, showlegend=False)
    return fig

def create_network_graph(corr_matrix, comp_to_sec, threshold, theme):
    edges = generate_network_data(corr_matrix, threshold)
    if edges.empty:
        return create_empty_figure("No connections above threshold.", theme)
        
    colors = ThemeManager.get_colors(theme)
    nodes = list(set(edges['source']).union(set(edges['target'])))
    
    # Circular layout
    n_nodes = len(nodes)
    angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
    node_x = np.cos(angles)
    node_y = np.sin(angles)
    pos = {node: (x, y) for node, x, y in zip(nodes, node_x, node_y)}
    
    fig = go.Figure()
    for _, row in edges.iterrows():
        x0, y0 = pos[row['source']]
        x1, y1 = pos[row['target']]
        w = row['weight']
        color = colors['success'] if w > 0 else colors['danger']
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines', line=dict(width=abs(w)*3, color=color),
            opacity=0.4, hoverinfo='none', showlegend=False
        ))
        
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes],
        mode='markers+text', text=nodes, textposition="top center",
        marker=dict(size=12, color=colors['info'], line=dict(width=1, color=colors['bg_surface'])),
        textfont=dict(color=colors['text_primary'], size=9)
    ))
    
    fig = apply_shared_layout(fig, theme=theme, height=650)
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
    return fig

def create_sankey_graph(corr_matrix, comp_to_sec, theme):
    nodes, sources, targets, values, edges = generate_sankey_data(corr_matrix, comp_to_sec)
    if not nodes:
        return create_empty_figure("Insufficient data for Sankey.", theme)
        
    colors = ThemeManager.get_colors(theme)
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color=colors.get('text_secondary', '#444'), width=0.5), label=nodes, color=colors['info']),
        link=dict(source=sources, target=targets, value=values, color=colors['bg_surface']) # Using muted background for links
    )])
    fig = apply_shared_layout(fig, theme=theme, height=650)
    return fig

def create_time_varying_chart(raw_df, companies, theme):
    if len(companies) < 2:
        return create_empty_figure("Select at least 2 companies to view rolling correlation.", theme)
        
    colors = ThemeManager.get_colors(theme)
    fig = go.Figure()
    
    # Calculate for the first pair as an example
    c1, c2 = companies[0], companies[1]
    roll_df = calculate_time_varying_correlation(raw_df, c1, c2)
    
    if not roll_df.empty:
        fig.add_trace(go.Scatter(
            x=roll_df['Date'], y=roll_df['Rolling_Correlation'],
            mode='lines', name=f"{c1} vs {c2}", line=dict(color=colors.get('primary', '#0d6efd'), width=2)
        ))
        
    fig = apply_shared_layout(fig, theme=theme, height=350, yaxis_title="60-Day Rolling Corr")
    fig.update_yaxes(range=[-1.1, 1.1])
    return fig

# ---------------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------------
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Correlation & Market Network", className="fw-bold mb-1 text-primary"),
            html.P("Institutional intelligence workspace. Discover hidden communities, dependencies, and correlation regimes.", className="text-muted mb-3")
        ], md=8),
        dbc.Col([
            html.Div(id="corr-regime-badge-container", className="d-flex justify-content-end align-items-center h-100")
        ], md=4)
    ]),
    
    html.Div(id="corr-playbook-narrative", className="mb-4"),
    
    dbc.Row([
        # Controls Panel
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Analytical Controls", className="fw-bold text-primary"),
                dbc.CardBody([
                    html.Label("Asset Selection", className="small fw-bold text-muted"),
                    dcc.Dropdown(
                        id={"type": "company-selector", "index": "corr-main"},
                        options=[{"label": c, "value": c} for c in ALL_COMPANIES],
                        value=[], multi=True, placeholder="Select companies...",
                        className="mb-4"
                    ),
                    html.Label("Matrix Clusters", className="small fw-bold text-muted"),
                    dcc.Slider(
                        id="corr-n-clusters", min=2, max=10, step=1, value=DEFAULT_N_CLUSTERS, 
                        marks={i: {"label": str(i), "style": {"color": "#9499a6"}} for i in range(2, 11, 2)},
                        className="mb-4"
                    ),
                    html.Label("Network Edge Threshold", className="small fw-bold text-muted"),
                    dcc.Slider(
                        id="corr-network-threshold", min=0.3, max=0.9, step=0.1, value=0.6, 
                        marks={round(v, 1): {"label": str(round(v, 1)), "style": {"color": "#9499a6"}} for v in [0.3, 0.5, 0.7, 0.9]},
                        className="mb-4"
                    ),
                ])
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=3, md=12, className="mb-4"),
        
        # Primary Visualization Canvas
        dbc.Col([
            dbc.Tabs([
                dbc.Tab([
                    dcc.Loading(dcc.Graph(id="corr-dendrogram", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)"),
                    dcc.Loading(dcc.Graph(id="corr-heatmap", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)")
                ], label="Matrix & Heatmap", tab_id="tab-matrix", label_style={"fontWeight": "bold"}),
                
                dbc.Tab([
                    dcc.Loading(dcc.Graph(id="corr-network", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)")
                ], label="Market Network Graph", tab_id="tab-network", label_style={"fontWeight": "bold"}),
                
                dbc.Tab([
                    dcc.Loading(dcc.Graph(id="corr-sankey", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)")
                ], label="Sector Influence Flow (Sankey)", tab_id="tab-sankey", label_style={"fontWeight": "bold"})
                
            ], id="corr-tabs", active_tab="tab-matrix", className="mt-2")
        ], lg=9, md=12, className="mb-4")
    ]),
    
    # Secondary Analytics
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Diversification Analyzer", className="fw-bold text-primary"),
                dbc.CardBody(id="corr-diversification-panel", className="p-3")
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=4, md=12, className="mb-4"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Time-Varying Rolling Correlation (60-Day)", className="fw-bold text-primary"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="corr-time-varying", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)")
                ], className="p-0")
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=8, md=12, className="mb-4")
    ]),
    
    # Rankings Table
    dbc.Row([
        dbc.Col([
            html.H6("CORRELATION RANKINGS", className="text-muted text-uppercase fw-bold mb-3 mt-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
            dbc.Card([
                dbc.CardBody(
                    dag.AgGrid(id="corr-rankings-table", dashGridOptions={"pagination": True, "paginationPageSize": 10, "domLayout": "autoHeight"}),
                    className="p-0"
                )
            ], className="shadow-sm border-0 bg-surface overflow-hidden")
        ], width=12)
    ])
    
], fluid=True, className="py-4 px-4")


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@callback(
    Output("corr-dendrogram", "figure"),
    Output("corr-heatmap", "figure"),
    Output("corr-network", "figure"),
    Output("corr-sankey", "figure"),
    Output("corr-time-varying", "figure"),
    Output("corr-regime-badge-container", "children"),
    Output("corr-playbook-narrative", "children"),
    Output("corr-diversification-panel", "children"),
    Output("corr-rankings-table", "rowData"),
    Output("corr-rankings-table", "columnDefs"),
    Output("corr-rankings-table", "className"),
    Input("corr-n-clusters", "value"),
    Input("corr-network-threshold", "value"),
    Input({"type": "company-selector", "index": "corr-main"}, "value"),
    Input("theme-store", "data")
)
def update_workspace(n_clusters, threshold, selected_companies, theme):
    result = run_correlation_pipeline(n_clusters=n_clusters, linkage_method=DEFAULT_LINKAGE_METHOD)
    
    if "order" not in result.get("cluster_result", {}):
        empty = create_empty_figure("No Data", theme)
        return empty, empty, empty, empty, empty, html.Div(), html.Div(), html.Div(), [], [], ""
        
    colors = ThemeManager.get_colors(theme)
    
    # 1. Regime
    reg = result.get("regime", {})
    r_color = "success" if reg.get("regime") == "Diversified" else "danger" if reg.get("regime") == "Highly Correlated" else "warning"
    badge = html.Div([
        html.Span("CORRELATION REGIME", className="text-muted small fw-bold me-2"),
        dbc.Badge(f"{reg.get('regime')} ({reg.get('score')}%)", color=r_color, className="fs-6 px-3 py-2")
    ])
    
    # 2. Diversification
    div = calculate_diversification(result["corr_matrix"], selected_companies)
    div_panel = dbc.Row([
        dbc.Col(create_stat_card("Independence Score", f"{div['score']}/100", "bi-shield-check", "info"), width=12, className="mb-3"),
        dbc.Col(html.P(div['desc'], className="text-muted small fw-bold text-center"), width=12)
    ])
    
    # 3. Playbook
    playbook_narrative = dbc.Alert([
        html.I(className="bi bi-lightbulb-fill text-warning me-2"),
        html.Span(f"{reg.get('desc')} Selecting multiple companies enables the Diversification Analyzer and the Time-Varying rolling correlation explorer.", className="small fw-bold text-muted")
    ], color="secondary", className="border-0 shadow-sm py-2 px-3 bg-surface bg-opacity-50")
    
    # 4. Visuals
    fig_dendro = create_dendrogram(result["cluster_result"], theme)
    fig_heat = create_heatmap(result["clustered_matrix"], result["cluster_result"]["order"], theme)
    fig_net = create_network_graph(result["corr_matrix"], result["comp_to_sec"], threshold, theme)
    fig_sankey = create_sankey_graph(result["corr_matrix"], result["comp_to_sec"], theme)
    fig_time = create_time_varying_chart(result["raw_df"], selected_companies or [], theme)
    
    # 5. Rankings Table
    rank_df = result.get("rankings", pd.DataFrame())
    if not rank_df.empty:
        rank_df["Correlation"] = rank_df["Correlation"].apply(lambda x: f"{float(x):.3f}")
        
        cell_style_logic = {
            "styleConditions": [
                {"condition": "params.data.Type === 'Strong Positive'", "style": {"color": colors["success"], "fontWeight": "bold"}},
                {"condition": "params.data.Type === 'Strong Negative'", "style": {"color": colors["danger"], "fontWeight": "bold"}}
            ],
            "defaultStyle": {"backgroundColor": "transparent", "color": colors["text_primary"]}
        }
        columns = [{"field": i, "cellStyle": cell_style_logic, "headerName": i, "sortable": True} for i in rank_df.columns]
        data = rank_df.to_dict("records")
    else:
        columns, data = [], []

    return fig_dendro, fig_heat, fig_net, fig_sankey, fig_time, badge, playbook_narrative, div_panel, data, columns, "ag-theme-alpine-dark" if theme == "dark" else "ag-theme-alpine"


# Sync heatmap brush / global context
@callback(
    Output({"type": "company-selector", "index": "corr-main"}, "value"),
    Output("global-state", "data", allow_duplicate=True),
    Input("corr-heatmap", "selectedData"),
    Input("global-state", "data"),
    State({"type": "company-selector", "index": "corr-main"}, "value"),
    prevent_initial_call=True,
)
def sync_dropdown(selected_data, global_state, current_value):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    curr = set(current_value or [])
    if not global_state: global_state = {"sectors": [], "companies": []}
    
    if trigger == "global-state":
        return list(curr.union(set(global_state.get("companies", [])))), no_update
        
    if selected_data and "points" in selected_data:
        for point in selected_data["points"]:
            curr.add(point["x"])
            curr.add(point["y"])
        return list(curr), global_state
        
    return list(curr), no_update
