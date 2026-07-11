import dash
from dash import State, html, dcc, Output, Input, callback, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.analytics.sector_rotation import prepare_sector_rrg, detect_market_regime, calculate_sector_leadership, predict_future_rotation, calculate_sector_relationships
from utils.config import get_rrg_quadrants, MODEBAR_CONFIG, ThemeManager
from utils.visuals import apply_shared_layout, create_empty_figure
from components.cards import create_stat_card

dash.register_page(__name__, path="/sector_rotation", name="Sector Rotation")

YEAR_OPTIONS = [{"label": str(y), "value": y} for y in range(2010, 2022)]

def create_network_graph(corr_df, theme):
    if corr_df.empty:
        return create_empty_figure("No network data", theme=theme)
        
    colors = ThemeManager.get_colors(theme)
    
    # Extract unique nodes
    nodes = list(set(corr_df['source']).union(set(corr_df['target'])))
    
    # Circular layout for simplicity
    n_nodes = len(nodes)
    angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
    node_x = np.cos(angles)
    node_y = np.sin(angles)
    
    pos = {node: (x, y) for node, x, y in zip(nodes, node_x, node_y)}
    
    edge_traces = []
    for _, row in corr_df.iterrows():
        x0, y0 = pos[row['source']]
        x1, y1 = pos[row['target']]
        weight = row['weight']
        
        # Color based on positive/negative correlation
        line_color = colors['success'] if weight > 0 else colors['danger']
        
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(width=abs(weight) * 5, color=line_color),
            opacity=0.6,
            hoverinfo='none',
            showlegend=False
        ))
        
    node_trace = go.Scatter(
        x=[pos[n][0] for n in nodes],
        y=[pos[n][1] for n in nodes],
        mode='markers+text',
        text=nodes,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            size=25,
            color=colors['info'],
            line=dict(width=2, color=colors['bg_surface'])
        ),
        textfont=dict(color=colors['text_primary'], size=10, family="JetBrains Mono")
    )
    
    fig = go.Figure(data=edge_traces + [node_trace])
    fig = apply_shared_layout(fig, theme=theme, margin=dict(l=20, r=20, t=20, b=20))
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
    
    return fig


layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Sector Rotation & Market Regime", className="fw-bold mb-1 text-primary"),
            html.P("Institutional intelligence workspace. Analyze sector leadership, momentum, and historical transition paths.", className="text-muted mb-3")
        ], md=8),
        dbc.Col([
            html.Div(id="regime-badge-container", className="d-flex justify-content-end align-items-center h-100")
        ], md=4)
    ]),
    
    html.Div(id="rotation-playbook-narrative", className="mb-4"),
    
    dbc.Row([
        # Controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Intelligence Controls", className="fw-bold text-primary"),
                dbc.CardBody([
                    html.Label("Target Year", className="small fw-bold text-muted"),
                    dcc.Dropdown(
                        id="rrg-year-selector",
                        options=YEAR_OPTIONS,
                        value=2021,
                        clearable=False,
                        className="mb-4"
                    ),
                    html.Label("Playback Speed", className="small fw-bold text-muted"),
                    dbc.RadioItems(
                        id="rrg-speed-selector",
                        options=[
                            {"label": "0.5x", "value": 0.5},
                            {"label": "1.0x", "value": 1.0},
                            {"label": "2.0x", "value": 2.0},
                        ],
                        value=1.0, inline=True, className="btn-group w-100 mb-4", 
                        inputClassName="btn-check", 
                        labelClassName="btn btn-outline-primary btn-sm"
                    ),
                    html.Hr(className="my-4"),
                    html.Label("Advanced Analytics", className="small fw-bold text-muted mb-2 d-block"),
                    dbc.Checklist(
                        id="rrg-options-toggle",
                        options=[
                            {"label": "Show Full Rotation Trajectories", "value": "paths"},
                            {"label": "Show Rotation Projections", "value": "projections"}
                        ],
                        value=["paths"],
                        switch=True,
                        className="mb-0"
                    )
                ])
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=3, md=12, className="mb-4"),
        
        # Main RRG Chart
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Loading(
                        dcc.Graph(id="rrg-animated-chart", style={"height": "500px"}, config=MODEBAR_CONFIG),
                        type="circle", color="var(--accent-primary)"
                    )
                ], className="p-2")
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=9, md=12, className="mb-4")
    ]),
    
    # Leadership & Network
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Leadership Intelligence", className="fw-bold text-primary"),
                dbc.CardBody(id="leadership-kpi-panel", className="p-3")
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=6, md=12, className="mb-4"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Sector Relationship Network (Correlation)", className="fw-bold text-primary"),
                dbc.CardBody([
                    dcc.Loading(
                        dcc.Graph(id="sector-network-chart", style={"height": "300px"}, config=MODEBAR_CONFIG),
                        type="circle", color="var(--accent-primary)"
                    )
                ], className="p-2")
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=6, md=12, className="mb-4")
    ]),
    
    # Rankings Table
    dbc.Row([
        dbc.Col([
            html.H6("RELATIVE ROTATION RANKINGS", className="text-muted text-uppercase fw-bold mb-3 mt-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
            dbc.Card([
                dbc.CardBody(
                    dag.AgGrid(
                        id="rotation-rankings-table",
                        dashGridOptions={"pagination": True, "paginationPageSize": 12, "domLayout": "autoHeight"},
                    ),
                    className="p-0"
                )
            ], className="shadow-sm border-0 bg-surface overflow-hidden")
        ], width=12)
    ])
    
], fluid=True, className="py-4 px-4")


@callback(
    Output("rrg-animated-chart", "figure"),
    Output("sector-network-chart", "figure"),
    Output("regime-badge-container", "children"),
    Output("rotation-playbook-narrative", "children"),
    Output("leadership-kpi-panel", "children"),
    Output("rotation-rankings-table", "rowData"),
    Output("rotation-rankings-table", "columnDefs"),
    Output("rotation-rankings-table", "className"),
    Input("rrg-year-selector", "value"),
    Input("rrg-speed-selector", "value"),
    Input("rrg-options-toggle", "value"),
    Input("theme-store", "data")
)
def update_workspace(target_year, playback_speed, options, theme):
    df = prepare_sector_rrg(target_year)
    
    if df.empty:
        return create_empty_figure("No Data", theme), create_empty_figure("No Data", theme), html.Div(), html.Div(), html.Div(), [], [], ""
        
    colors = ThemeManager.get_colors(theme)
    show_paths = "paths" in options
    show_proj = "projections" in options
    
    # 1. Market Regime
    regime_data = detect_market_regime(target_year)
    regime_colors = {
        "Expansion": "success",
        "Peak / Weakening": "warning",
        "Contraction": "danger",
        "Recovery / Bottoming": "info",
        "Consolidation": "secondary",
        "Unknown": "secondary"
    }
    r_color = regime_colors.get(regime_data["regime"], "secondary")
    
    regime_badge = html.Div([
        html.Span("MARKET REGIME", className="text-muted small fw-bold me-2"),
        dbc.Badge(f"{regime_data['regime']} ({regime_data['score']}%)", color=r_color, className="fs-6 px-3 py-2")
    ])
    
    # 2. Leadership & Narrative
    leadership = calculate_sector_leadership(df)
    
    playbook_text = (
        f"The overall market environment is classified as {regime_data['regime']}. "
        f"{regime_data['desc']} "
        f"Currently, {leadership.get('Leader', 'No sector')} is leading the rotation, while {leadership.get('Emerging', 'no sector')} is showing strong emerging momentum. "
        f"Conversely, {leadership.get('Lagging', 'no sector')} is lagging significantly behind the benchmark."
    )
    playbook_narrative = dbc.Alert([
        html.I(className="bi bi-lightbulb-fill text-warning me-2"),
        html.Span(playbook_text, className="small fw-bold text-muted")
    ], color="secondary", className="border-0 shadow-sm py-2 px-3 bg-surface bg-opacity-50")
    
    kpis = dbc.Row([
        dbc.Col(create_stat_card("Current Leader", leadership.get("Leader", "-"), "bi-trophy", "success"), width=6, className="mb-3"),
        dbc.Col(create_stat_card("Emerging Leader", leadership.get("Emerging", "-"), "bi-rocket", "info"), width=6, className="mb-3"),
        dbc.Col(create_stat_card("Weakest Sector", leadership.get("Lagging", "-"), "bi-graph-down", "danger"), width=6, className="mb-3"),
        dbc.Col(create_stat_card("Highest Velocity", leadership.get("Fastest", "-"), "bi-speedometer2", "warning"), width=6, className="mb-3"),
    ])
    
    # 3. Main RRG Chart
    fig = px.scatter(
        df, x="RS_Ratio", y="RS_Momentum", 
        animation_frame="Frame", animation_group="Sector",
        color="Sector", hover_name="Sector", text="Sector",
        range_x=[85, 115], range_y=[85, 115]
    )
    
    fig.update_traces(
        textposition='top center', 
        textfont=dict(family="JetBrains Mono, monospace", size=11, color=colors["text_primary"]),
        marker=dict(size=14, line=dict(width=2, color=colors["bg_surface"]))
    )
    
    # Add Trails (Full Path lines in background)
    if show_paths:
        for sector, grp in df.groupby("Sector"):
            fig.add_trace(go.Scatter(
                x=grp["RS_Ratio"], y=grp["RS_Momentum"],
                mode="lines",
                line=dict(color=colors["text_secondary"], width=1),
                opacity=0.3,
                showlegend=False,
                hoverinfo="skip"
            ))
            
    # Add Projections
    if show_proj:
        proj_df = predict_future_rotation(df)
        if not proj_df.empty:
            current = leadership.get("current_data", pd.DataFrame())
            if not current.empty:
                for _, p_row in proj_df.iterrows():
                    sec = p_row["Sector"]
                    curr_row = current[current["Sector"] == sec]
                    if not curr_row.empty:
                        fig.add_trace(go.Scatter(
                            x=[curr_row["RS_Ratio"].iloc[0], p_row["Proj_RS_Ratio"]],
                            y=[curr_row["RS_Momentum"].iloc[0], p_row["Proj_RS_Momentum"]],
                            mode="lines+markers",
                            line=dict(color=colors["info"], width=2, dash="dot"),
                            marker=dict(symbol="arrow-up", size=8),
                            showlegend=False,
                            hoverinfo="skip"
                        ))
            
    fig.add_hline(y=100, line_width=2.0, line_color=colors["crosshair"], opacity=1.0)
    fig.add_vline(x=100, line_width=2.0, line_color=colors["crosshair"], opacity=1.0)

    for ann in get_rrg_quadrants(theme):
        fig.add_annotation(x=ann['x'], y=ann['y'], text=ann['text'], showarrow=False, opacity=0.8, font=ann['font'])

    fig = apply_shared_layout(
        fig, theme=theme,
        xaxis=dict(title="JdK RS-Ratio (Trend)", showgrid=False, zeroline=False),
        yaxis=dict(title="JdK RS-Momentum (Velocity)", showgrid=False, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Fix Plotly Animation frames if we added custom traces (Plotly animations sometimes overwrite custom traces, 
    # but since the background trails are added to the figure directly, they persist if they aren't part of frames)
    # Adjust speed
    if len(fig.layout.updatemenus) > 0:
        base_dur = 400
        base_trans = 250
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = int(base_dur / playback_speed)
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = int(base_trans / playback_speed)
        
    # 4. Network Graph
    corr_df = calculate_sector_relationships(target_year)
    fig_network = create_network_graph(corr_df, theme)
    
    # 5. Rankings Table
    if not leadership.get("current_data").empty:
        curr = leadership["current_data"].copy()
        curr["Power"] = curr["Power"].apply(lambda x: f"{x:.2f}")
        curr["Velocity"] = curr["Velocity"].apply(lambda x: f"{x:.2f}")
        curr["RS_Ratio"] = curr["RS_Ratio"].apply(lambda x: f"{x:.2f}")
        curr["RS_Momentum"] = curr["RS_Momentum"].apply(lambda x: f"{x:.2f}")
        
        display_df = curr[["Sector", "Quadrant", "RS_Ratio", "RS_Momentum", "Velocity", "Power"]].sort_values("Power", ascending=False)
        
        # Build coldefs with cellStyle logic for conditional formatting
        cell_style_logic = {
            "styleConditions": [
                {"condition": "params.data.Quadrant === 'Leading'", "style": {"color": colors["success"], "fontWeight": "bold"}},
                {"condition": "params.data.Quadrant === 'Lagging'", "style": {"color": colors["danger"]}},
                {"condition": "params.data.Quadrant === 'Improving'", "style": {"color": colors["info"]}},
                {"condition": "params.data.Quadrant === 'Weakening'", "style": {"color": colors["warning"]}}
            ],
            "defaultStyle": {"backgroundColor": "transparent", "color": colors["text_primary"]}
        }
        
        columns = [{"field": i, "cellStyle": cell_style_logic, "headerName": i, "sortable": True} for i in display_df.columns]
        data = display_df.to_dict("records")
    else:
        columns, data = [], []

    # Inject base grid styles using HTML container/dash properties if needed, but styling via columnDefs works well
    # AgGrid doesn't use style_header/style_cell natively in this manner, but we can set them as default column properties or themes.
    
    return fig, fig_network, regime_badge, playbook_narrative, kpis, data, columns, "ag-theme-alpine-dark" if theme == "dark" else "ag-theme-alpine"

# Sync table to active context
@callback(
    Output("event-bus", "data", allow_duplicate=True),
    Input("rotation-rankings-table", "cellClicked"),
    State("rotation-rankings-table", "rowData"),
    prevent_initial_call=True
)
def sync_context(cell_clicked, row_data):
    if cell_clicked and row_data:
        row_idx = cell_clicked.get("rowIndex")
        if row_idx is not None and row_idx < len(row_data):
            sector = row_data[row_idx].get("Sector")
            if sector:
                return {"type": "OPEN_COMPANY_DRAWER", "payload": f"Sector:{sector}"}
    return no_update