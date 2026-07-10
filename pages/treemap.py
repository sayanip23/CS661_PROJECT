import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.analytics.treemap import run_treemap_pipeline, get_node_trend_data, compute_rolling_performance, compute_risk_contribution, compute_market_breadth
from utils.config import get_quant_colorscale, MODEBAR_CONFIG, ThemeManager
import numpy as np

dash.register_page(__name__, path="/treemap")

def get_ticker(company_name):
    if not company_name: return ""
    word = company_name.split()[0]
    return "".join(c for c in word if c.isalnum()).upper()

def create_growth_figure(hierarchy_df, size_metric, color_metric, start_year, end_year, uirevision, is_fullscreen=False, theme="dark"):
    if hierarchy_df.empty:
        return go.Figure()

    color_data = hierarchy_df[color_metric]
    
    # Adaptive Labels and Smart Text Colors
    text_labels = []
    text_colors = []
    max_c = color_data.max()
    
    for _, row in hierarchy_df.iterrows():
        weight = row['market_weight']
        company = row['label']
        c_val = row[color_metric]
        
        # Adaptive Label Configuration
        t1, t2, t3 = (0.005, 0.002, 0.0005) if is_fullscreen else (0.01, 0.005, 0.001)
        
        if weight >= t1:
            metric_str = f"{c_val:+.1%}" if color_metric == "cagr" else f"{c_val:.2f}"
            text_labels.append(f"{company}<br>{metric_str}")
        elif weight >= t2:
            text_labels.append(company)
        elif weight >= t3:
            text_labels.append(get_ticker(company))
        else:
            text_labels.append("")
            
        # Smart Text Color
        if max_c > 0 and c_val > (0.6 * max_c):
            text_colors.append("black")
        else:
            text_colors.append("white")
            
    metric_title = "CAGR" if color_metric == "cagr" else "Sharpe (Risk-Adj)"
    
    # Custom Legend
    min_val, max_val = color_data.min(), color_data.max()
    tick_vals = [min_val, 0, max_val]
    if color_metric == "cagr":
        tick_text = [f"Negative ↓ ({min_val:.1%})", "Neutral", f"Positive ↑ ({max_val:.1%})"]
    else:
        tick_text = [f"Poor ({min_val:.2f})", "Average", f"Excellent ({max_val:.2f})"]

    quant_colorscale = get_quant_colorscale(theme)
    colors = ThemeManager.get_colors(theme)
    
    marker = dict(
        colors=color_data,
        colorscale=quant_colorscale,
        cmid=0.0,
        colorbar=dict(
            title=metric_title, thickness=12, len=0.7,
            tickmode="array", tickvals=tick_vals, ticktext=tick_text
        ),
        line=dict(width=1, color=colors["bg_surface"]),
    )
    
    # Customdata mapping
    customdata = list(zip(
        hierarchy_df["cagr"], hierarchy_df["sharpe"], hierarchy_df["volume"], 
        hierarchy_df["turnover"], hierarchy_df["market_weight"], hierarchy_df["rank"],
        hierarchy_df["sector"], hierarchy_df.get("volatility", [0]*len(hierarchy_df)), 
        hierarchy_df.get("max_drawdown", [0]*len(hierarchy_df)),
        [start_year]*len(hierarchy_df), [end_year]*len(hierarchy_df),
        hierarchy_df.get("sector_weight", [0]*len(hierarchy_df)), 
        hierarchy_df.get("hover_cagr", [""]*len(hierarchy_df)), 
        hierarchy_df.get("hover_sharpe", [""]*len(hierarchy_df)), 
        hierarchy_df.get("diff_market_cagr", [""]*len(hierarchy_df)), 
        hierarchy_df.get("diff_market_sharpe", [""]*len(hierarchy_df)),
        hierarchy_df.get("diff_sector_cagr", [""]*len(hierarchy_df)), 
        hierarchy_df.get("diff_sector_sharpe", [""]*len(hierarchy_df)),
        hierarchy_df.get("sector_avg_cagr", [""]*len(hierarchy_df)), 
        hierarchy_df.get("sector_avg_sharpe", [""]*len(hierarchy_df))
    ))
    
    if color_metric == "cagr":
        current_metric = "CAGR"
        hover_val = "%{customdata[12]}"
        sector_avg_val = "%{customdata[18]}"
        diff_sec_val = "%{customdata[16]}"
        diff_mkt_val = "%{customdata[14]}"
    else:
        current_metric = "Sharpe Ratio"
        hover_val = "%{customdata[13]}"
        sector_avg_val = "%{customdata[19]}"
        diff_sec_val = "%{customdata[17]}"
        diff_mkt_val = "%{customdata[15]}"

    hover_template = (
        "<b>%{label}</b> (%{customdata[6]})<br>"
        "-----------------------------------------<br>"
        "<b>Current Metric:</b> " + current_metric + "<br>"
        "<b>Value:</b> " + hover_val + "<br>"
        "<b>Sector Avg:</b> " + sector_avg_val + "<br>"
        "<b>Diff vs Sector:</b> " + diff_sec_val + "<br>"
        "<b>Alpha vs Market:</b> " + diff_mkt_val + "<br>"
        "-----------------------------------------<br>"
        "<b>Volume:</b> %{customdata[2]:,.0f}<br>"
        "<b>Turnover:</b> ₹%{customdata[3]:,.0f}<br>"
        "<b>Sector Contrib:</b> %{customdata[11]:.2%}<br>"
        "<b>Market Contrib:</b> %{customdata[4]:.2%}<br>"
        "<b>Market Rank:</b> #%{customdata[5]:.0f}<br>"
        "<b>Period:</b> %{customdata[9]} - %{customdata[10]}<br>"
        "<i>Click to drill down</i><extra></extra>"
    )

    
    base_font = 22 if is_fullscreen else 14
    pathbar_font = 28 if is_fullscreen else 14
    hover_font = 18 if is_fullscreen else 13

    fig = go.Figure(go.Treemap(
        ids=hierarchy_df["id"], labels=hierarchy_df["label"], parents=hierarchy_df["parent"],
        values=hierarchy_df["value"],
        customdata=customdata,
        text=text_labels,
        textinfo="text",
        hovertemplate=hover_template,
        marker=marker,
        tiling=dict(packing="squarify", pad=2),
        pathbar=dict(visible=True, textfont=dict(family="JetBrains Mono, monospace", size=pathbar_font)),
        textfont=dict(family="JetBrains Mono, monospace", color=text_colors, size=base_font),
    ))
    fig.update_layout(
        template=f"financial_{theme}",
        margin=dict(l=0, r=0, t=35 if is_fullscreen else 25, b=0),
        paper_bgcolor="rgba(0,0,0,0)" if is_fullscreen else colors["bg_surface"], 
        plot_bgcolor="rgba(0,0,0,0)" if is_fullscreen else colors["bg_surface"],
        uirevision=uirevision,
        hoverlabel=dict(font_size=hover_font)
    )
    return fig

fullscreen_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle([
                html.I(className="bi bi-arrows-fullscreen me-2"), 
                "Focus Mode: Cross-Sectional Market Map"
            ], className="fw-bold font-mono text-primary"), 
            close_button=True, 
            className="border-0 pb-0"
        ),
        dbc.ModalBody(
            dcc.Loading(dcc.Graph(id="growth-treemap-chart-fullscreen", config=MODEBAR_CONFIG, style={"height": "calc(100vh - 80px)", "width": "100%"}),
                        type="circle", color="var(--accent-primary)"),
            className="p-1"
        )
    ],
    id="fullscreen-modal",
    fullscreen=True,
    is_open=False,
    keyboard=True,
    backdrop=True,
    style={"backdropFilter": "blur(4px)"}
)

filter_drawer = dbc.Offcanvas(
    id="filter-drawer",
    title="Dashboard Filters",
    is_open=False,
    placement="end",
    style={"width": "350px", "backdropFilter": "blur(4px)"},
    children=[
        html.Div([
            html.H6("General", className="text-uppercase text-muted small fw-bold mb-3 border-bottom border-secondary border-opacity-25 pb-1"),
            
            html.Div("Group By", className="fw-bold text-muted small mb-1"),
            dcc.Dropdown(
                id="group-by-toggle",
                options=[
                    {"label": "Sector", "value": "Sector"},
                    {"label": "Risk Profile", "value": "Risk Profile"},
                    {"label": "Return Profile", "value": "Return Profile"},
                    {"label": "Liquidity Profile", "value": "Liquidity Profile"},
                    {"label": "Correlation Cluster (ML)", "value": "Correlation Cluster"}
                ],
                value="Sector", clearable=False,
                className="small mb-3 font-mono shadow-sm",
                style={"color": "black"}
            ),
            
            html.Div("Year Range", className="fw-bold text-muted small mb-1"),
            html.Div([
                html.Span("2000", className="static-bound-label text-muted fw-bold small me-2"),
                dcc.Input(id="year-range-min-box", type="number", min=2000, max=2022, step=1, value=2000, className="form-control text-center p-0", style={"width": "45px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "24px", "fontSize": "12px"}),
                dcc.RangeSlider(
                    id="year-range-slider", min=2000, max=2022, step=1, 
                    value=[2000, 2022],
                    marks=None, tooltip={"placement": "bottom", "always_visible": False},
                    className="slider-track flex-grow-1 mx-2"
                ),
                dcc.Input(id="year-range-max-box", type="number", min=2000, max=2022, step=1, value=2022, className="form-control text-center p-0", style={"width": "45px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "24px", "fontSize": "12px"}),
                html.Span("2022", className="static-bound-label text-muted fw-bold small ms-2"),
            ], className="d-flex align-items-center mb-4"),
            
            html.H6("Metrics", className="text-uppercase text-muted small fw-bold mb-3 border-bottom border-secondary border-opacity-25 pb-1 mt-4"),
            
            html.Div("Color Metric", className="fw-bold text-muted small mb-1"),
            dbc.RadioItems(
                id="color-metric-toggle",
                options=[{"label": "Growth", "value": "cagr"},
                         {"label": "Sharpe", "value": "sharpe"}],
                value="cagr", inline=True, className="mb-3 btn-group w-100", 
                inputClassName="btn-check", 
                labelClassName="btn btn-outline-primary btn-sm transition-all py-1"
            ),
            
            html.Div("Size Metric", className="fw-bold text-muted small mb-1"),
            dbc.RadioItems(
                id="size-metric-toggle",
                options=[{"label": "Volume", "value": "Total_Volume"},
                         {"label": "Turnover", "value": "Total_Turnover"}],
                value="Total_Volume", inline=True, className="mb-4 btn-group w-100", 
                inputClassName="btn-check", 
                labelClassName="btn btn-outline-primary btn-sm transition-all py-1"
            ),
        ], className="d-flex flex-column h-100"),
        
        # Bottom sticky actions
        html.Div([
            dbc.Button("Reset Defaults", id="reset-filters-btn", color="link", className="text-muted text-decoration-none flex-grow-1 me-2 btn-sm"),
            dbc.Button("Apply Filters", id="apply-filters-btn", color="primary", className="fw-bold px-4 btn-sm shadow-sm"),
        ], className="d-flex border-top border-secondary border-opacity-25 pt-3 mt-auto", style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
    ]
)

layout = dbc.Container([
    dcc.Store(id="treemap-active-node", data="NIFTY-50"),
    dcc.Store(id="filter-state", data={"group_by": "Sector", "color_metric": "cagr", "size_metric": "Total_Volume", "year_range": [2000, 2022]}),
    fullscreen_modal,
    filter_drawer,
    
    # Title & Toolbar Row
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Cross-Sectional Market Map", className="fw-bold mb-0 text-primary font-mono", style={"display": "inline-block"}),
                html.Div([
                    # Active Filter Summary
                    html.Div(id="active-filter-summary", className="d-none d-lg-flex align-items-center me-3 text-muted small font-mono"),
                    
                    dbc.Button(
                        [html.I(className="bi bi-funnel-fill me-1"), "Filters"], 
                        id="open-filters-btn", color="primary", outline=True, className="ms-2 shadow-sm transition-all btn-sm fw-bold", 
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-arrow-counterclockwise me-1"), "Reset Market"], 
                        id="reset-treemap-btn", color="secondary", outline=True, className="ms-2 shadow-sm transition-all btn-sm fw-bold border-0", 
                    ),
                ], className="d-flex align-items-center")
            ], className="d-flex align-items-center justify-content-between p-2 mb-2 card shadow-sm border-0 bg-surface")
        ], md=12),
    ]),

    # Analytical Summary Cards
    dbc.Row(id="analytical-summary-cards", className="mb-2 g-2"),

    # Treemap
    dbc.Row([
        dbc.Col(
            html.Div([
                dcc.Loading(dcc.Graph(id="market-breadth-chart", config=MODEBAR_CONFIG, style={"height": "40px"}),
                            type="dot", color="var(--accent-primary)"),
                html.Div([
                    html.Div(id="breadcrumb-trail", className="text-muted small mb-1 font-mono text-center flex-grow-1"),
                    dbc.Button(html.I(className="bi bi-arrows-fullscreen"), id="expand-treemap-btn", color="link", className="text-muted p-0 text-decoration-none shadow-none", style={"position": "absolute", "right": "15px", "top": "10px"}, title="Open Full Screen")
                ], style={"position": "relative"}),
                dcc.Loading(dcc.Graph(id="growth-treemap-chart", config=MODEBAR_CONFIG, style={"height": "calc(100vh - 350px)", "minHeight": "400px"}),
                            type="circle", color="var(--accent-primary)")
            ], className="card shadow-sm border-0 bg-surface p-1 mb-3"), 
            md=12
        ),
    ]),
    
    # Growth Trend Detail
    dbc.Row([
        dbc.Col(html.Div(id="pane-detail-content", className="w-100"), md=12)
    ])
], fluid=True, className="py-2")

@callback(
    Output("growth-treemap-chart", "figure"),
    Output("growth-treemap-chart-fullscreen", "figure"),
    Input("filter-state", "data"),
    Input("reset-treemap-btn", "n_clicks"),
    Input("theme-store", "data")
)
def update_treemap_figure(filter_state, reset_clicks, theme):
    color_metric = filter_state["color_metric"]
    size_metric = filter_state["size_metric"]
    start_year, end_year = filter_state["year_range"]
    group_by = filter_state["group_by"]
    
    res = run_treemap_pipeline(f"{start_year}-01-01", f"{end_year}-12-31", size_metric, group_by)
    
    if res["hierarchy"].empty:
        empty_fig = go.Figure().update_layout(title="No data available", xaxis_visible=False, yaxis_visible=False)
        return empty_fig, empty_fig
        
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    uirevision = f"reset_{reset_clicks}" if "reset-treemap-btn" in trigger else f"{color_metric}_{size_metric}_{start_year}_{end_year}"
    
    fig_norm = create_growth_figure(res["hierarchy"], size_metric, color_metric, start_year, end_year, uirevision, is_fullscreen=False, theme=theme)
    fig_full = create_growth_figure(res["hierarchy"], size_metric, color_metric, start_year, end_year, uirevision, is_fullscreen=True, theme=theme)
    return fig_norm, fig_full

dash.clientside_callback(
    "function(val, min_box, max_box) {\n"
    "    const ctx = dash_clientside.callback_context;\n"
    "    if (!ctx.triggered.length) return [val[0], val[1], val];\n"
    "    const trigger = ctx.triggered[0].prop_id;\n"
    "    if (trigger === 'year-range-slider.value') {\n"
    "        return [val[0], val[1], dash_clientside.no_update];\n"
    "    } else {\n"
    "        let new_min = parseInt(min_box) || 2000;\n"
    "        let new_max = parseInt(max_box) || 2022;\n"
    "        if (new_min < 2000) new_min = 2000;\n"
    "        if (new_max > 2022) new_max = 2022;\n"
    "        if (new_min > new_max) new_min = new_max;\n"
    "        return [dash_clientside.no_update, dash_clientside.no_update, [new_min, new_max]];\n"
    "    }\n"
    "}",
    Output("year-range-min-box", "value"),
    Output("year-range-max-box", "value"),
    Output("year-range-slider", "value"),
    Input("year-range-slider", "value"),
    Input("year-range-min-box", "value"),
    Input("year-range-max-box", "value")
)

dash.clientside_callback(
    "function(n_clicks) { return [null, null]; }",
    Output("growth-treemap-chart", "clickData"),
    Output("growth-treemap-chart-fullscreen", "clickData"),
    Input("reset-treemap-btn", "n_clicks"),
    prevent_initial_call=True
)

@callback(
    Output("fullscreen-modal", "is_open"),
    Input("expand-treemap-btn", "n_clicks"),
    State("fullscreen-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("treemap-active-node", "data"),
    Input("growth-treemap-chart", "clickData"),
    Input("growth-treemap-chart-fullscreen", "clickData"),
    Input("reset-treemap-btn", "n_clicks"),
    State("treemap-active-node", "data")
)
def update_active_node(click_data_norm, click_data_full, reset_clicks, current_node):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "NIFTY-50"
    trigger = ctx.triggered[0]["prop_id"]
    
    if "reset-treemap-btn" in trigger:
        return "NIFTY-50"
        
    click_data = click_data_full if "fullscreen" in trigger else click_data_norm
        
    if click_data and "points" in click_data:
        clicked_id = click_data["points"][0].get("id", "NIFTY-50")
        
        # If user clicked the node they are already on, it means zoom out
        if clicked_id == current_node:
            if "/" in current_node:
                return current_node.split("/")[0] # Go to sector
            else:
                return "NIFTY-50" # Go to market
        return clicked_id
        
    return current_node

def create_scatter_fig(comp_df, node_id, group_by, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    if comp_df.empty: return go.Figure().update_layout(title="No data", template=f"financial_{theme}", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig = go.Figure()
    
    # Filter for active group if needed
    plot_df = comp_df
    if node_id != "NIFTY-50" and "/" not in node_id:
        if group_by in plot_df.columns:
            plot_df = plot_df[plot_df[group_by] == node_id]
        else:
            plot_df = plot_df[plot_df["Sector"] == node_id]
            
    fig.add_trace(go.Scatter(
        x=plot_df["Volatility"], y=plot_df["CAGR"],
        mode="markers+text", text=plot_df["Company"],
        marker=dict(size=plot_df["Total_Volume"]/plot_df["Total_Volume"].max()*40 + 5, 
                    color=plot_df["CAGR"], 
                    colorscale=get_quant_colorscale(theme), 
                    cmid=0, showscale=True,
                    opacity=0.9,
                    line=dict(width=1.5, color=colors["bg_surface"])),
        textposition="top center", hovertemplate="%{text}<br>Vol: %{x:.1%}<br>CAGR: %{y:.1%}<extra></extra>"
    ))
    fig.update_layout(title="Cross-Sectional Risk vs Return", template=f"financial_{theme}", margin=dict(l=0,r=0,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Annualized Volatility", yaxis_title="CAGR")
    return fig

def create_rolling_fig(raw_df, node_id, comp_df, group_by, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    roll_df = compute_rolling_performance(raw_df, node_id, comp_df, group_by)
    if roll_df.empty: return go.Figure().update_layout(title="No data", template=f"financial_{theme}", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=roll_df["Date"], y=roll_df["Market_Rolling_Return"], name="Market (NIFTY-50)", line=dict(color=colors["text_secondary"], width=2)))
    if "Node_Rolling_Return" in roll_df.columns:
        fig.add_trace(go.Scatter(x=roll_df["Date"], y=roll_df["Node_Rolling_Return"], name=node_id, line=dict(color=colors["success"], width=2)))
    fig.update_layout(title="60-Day Rolling Return", template=f"financial_{theme}", margin=dict(l=0,r=0,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified")
    return fig

def create_risk_fig(raw_df, node_id, comp_df, group_by, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    risk_df = compute_risk_contribution(raw_df, node_id, comp_df, group_by)
    if risk_df.empty: return go.Figure().update_layout(title="Not enough assets for risk decomp", template=f"financial_{theme}", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=risk_df["Company"], y=risk_df["PCR"], name="Risk Contribution (PCR)", marker_color=colors["danger"]))
    fig.add_trace(go.Bar(x=risk_df["Company"], y=risk_df["Weight"], name="Capital Weight", marker_color=colors["info"]))
    fig.update_layout(title="Marginal Contribution to Risk", barmode="group", template=f"financial_{theme}", margin=dict(l=0,r=0,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_distribution_fig(raw_df, node_id, comp_df, group_by, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    if raw_df.empty: return go.Figure().update_layout(title="No data", template=f"financial_{theme}", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    if node_id == "NIFTY-50" or not node_id:
        comps = comp_df["Company"].unique()
    elif "/" in node_id:
        comps = [node_id.split("/")[1]]
    else:
        if group_by in comp_df.columns:
            comps = comp_df[comp_df[group_by] == node_id]["Company"].unique()
        else:
            comps = comp_df[comp_df["Sector"] == node_id]["Company"].unique()
            
    plot_df = raw_df[raw_df["Company"].isin(comps)]
    if plot_df.empty: return go.Figure().update_layout(title="No data", template=f"financial_{theme}", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    # Generate background color with alpha manually
    success_rgb = "16, 185, 129" if theme == "light" else "33, 206, 153"
    
    fig = go.Figure()
    fig.add_trace(go.Violin(
        y=plot_df["Daily_Return"],
        name=node_id,
        box_visible=True,
        meanline_visible=True,
        fillcolor=f"rgba({success_rgb}, 0.4)",
        line_color=colors["success"]
    ))
    fig.update_layout(
        title=f"Return Distribution: {node_id}",
        template=f"financial_{theme}",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=40, b=20),
        yaxis_title="Daily Return"
    )
    return fig

@callback(
    Output("analytical-summary-cards", "children"),
    Output("pane-detail-content", "children"),
    Output("breadcrumb-trail", "children"),
    Input("treemap-active-node", "data"),
    Input("filter-state", "data"),
    Input("theme-store", "data")
)
def update_dashboard_state(node_id, filter_state, theme):
    colors = ThemeManager.get_colors(theme)
    color_metric = filter_state["color_metric"]
    size_metric = filter_state["size_metric"]
    year_range = filter_state["year_range"]
    group_by = filter_state["group_by"]
    
    if not year_range:
        year_range = [2000, 2022]
        
    start_year, end_year = year_range
    
    # Fast O(1) cache hits
    res = run_treemap_pipeline(f"{start_year}-01-01", f"{end_year}-12-31", size_metric, group_by)
    
    if res["hierarchy"].empty or res["raw_data"].empty:
        return [], html.Div(), go.Figure().update_layout(title="No data", xaxis_visible=False, yaxis_visible=False), ""
        
    comp_df = res["company_growth"]
    sector_df = res["sector_growth"]
    
    market_df, node_trend = get_node_trend_data(res["raw_data"], node_id, comp_df, group_by)
    
    # ---------------------------
    # STATE IDENTIFICATION
    # ---------------------------
    if node_id == "NIFTY-50":
        # MARKET STATE
        pdf = market_df
        title_text = "NIFTY-50 Equal-Weight Average"
        subtitle_text = "Overall Market Trend"
        line_color = "#2962ff"
        fill_color = "rgba(41, 98, 255, 0.1)"
        
        stat_cagr = comp_df['CAGR'].mean()
        stat_sharpe = comp_df['Sharpe_Ratio'].mean()
        stat_vol = comp_df['Volatility'].mean()
        stat_dd = comp_df['Max_Drawdown'].mean()
        stat_volume = comp_df['Total_Volume'].sum()
        stat_weight = 1.0
        
        largest_sector = sector_df.loc[sector_df[size_metric].idxmax()]['Sector']
        if color_metric == "cagr":
            top_growth = comp_df.loc[comp_df['CAGR'].idxmax()]
            low_growth = comp_df.loc[comp_df['CAGR'].idxmin()]
            best_perf = f"{top_growth['Company']} ({top_growth['CAGR']:+.1%})"
            worst_perf = f"{low_growth['Company']} ({low_growth['CAGR']:+.1%})"
        else:
            top_sharpe = comp_df.loc[comp_df['Sharpe_Ratio'].idxmax()]
            low_sharpe = comp_df.loc[comp_df['Sharpe_Ratio'].idxmin()]
            safest_sector = sector_df.loc[sector_df['Volatility'].idxmin()]['Sector']
            best_perf = f"{top_sharpe['Company']} ({top_sharpe['Sharpe_Ratio']:.2f})"
            worst_perf = f"{low_sharpe['Company']} ({low_sharpe['Sharpe_Ratio']:.2f})"
            
        kpi_title_1 = "Best Performer"
        kpi_title_2 = "Worst Performer"
        kpi_title_3 = "Largest Sector"
        kpi_val_3 = largest_sector
            
    elif "/" not in node_id:
        # SECTOR STATE
        pdf = node_trend
        title_text = f"{node_id} Sector Average"
        subtitle_text = "Sector Trend"
        line_color = "#2962ff"
        fill_color = "rgba(41, 98, 255, 0.1)"
        
        s_row = sector_df[sector_df['Sector'] == node_id]
        if not s_row.empty:
            s_row = s_row.iloc[0]
            stat_cagr = s_row['CAGR']
            stat_sharpe = s_row['CAGR'] / s_row['Volatility'] if s_row['Volatility'] > 0 else 0
            stat_vol = s_row['Volatility']
            stat_dd = s_row['Max_Drawdown']
            stat_volume = s_row['Total_Volume']
            stat_weight = s_row['Market_Weight']
        else:
            stat_cagr = stat_sharpe = stat_vol = stat_dd = stat_volume = stat_weight = 0
            
        if group_by in comp_df.columns:
            sector_comps = comp_df[comp_df[group_by] == node_id]
        else:
            sector_comps = comp_df[comp_df['Sector'] == node_id]
            
        if not sector_comps.empty:
            largest_comp = sector_comps.loc[sector_comps[size_metric].idxmax()]['Company']
            if color_metric == "cagr":
                top_growth = sector_comps.loc[sector_comps['CAGR'].idxmax()]
                low_growth = sector_comps.loc[sector_comps['CAGR'].idxmin()]
                best_perf = f"{top_growth['Company']} ({top_growth['CAGR']:+.1%})"
                worst_perf = f"{low_growth['Company']} ({low_growth['CAGR']:+.1%})"
            else:
                top_sharpe = sector_comps.loc[sector_comps['Sharpe_Ratio'].idxmax()]
                low_sharpe = sector_comps.loc[sector_comps['Sharpe_Ratio'].idxmin()]
                best_perf = f"{top_sharpe['Company']} ({top_sharpe['Sharpe_Ratio']:.2f})"
                worst_perf = f"{low_sharpe['Company']} ({low_sharpe['Sharpe_Ratio']:.2f})"
        else:
            best_perf = worst_perf = largest_comp = "N/A"
            
        kpi_title_1 = "Sector Leader"
        kpi_title_2 = "Sector Laggard"
        kpi_title_3 = "Largest Asset"
        kpi_val_3 = largest_comp
            
    else:
        # COMPANY STATE
        sector_name, company_name = node_id.split("/", 1)
        pdf = node_trend
        title_text = company_name
        subtitle_text = sector_name
        line_color = "#21ce99"
        fill_color = "rgba(33, 206, 153, 0.1)"
        
        c_row = comp_df[comp_df['Company'] == company_name]
        if not c_row.empty:
            c_row = c_row.iloc[0]
            stat_cagr = c_row['CAGR']
            stat_sharpe = c_row['Sharpe_Ratio']
            stat_vol = c_row['Volatility']
            stat_dd = c_row['Max_Drawdown']
            stat_volume = c_row['Total_Volume']
            stat_weight = c_row['Market_Weight']
        else:
            stat_cagr = stat_sharpe = stat_vol = stat_dd = stat_volume = stat_weight = 0
            
        # Contextual comparison for the company
        s_row = sector_df[sector_df['Sector'] == sector_name]
        s_cagr = s_row.iloc[0]['CAGR'] if not s_row.empty else 0
        diff = stat_cagr - s_cagr
        diff_str = f"outperformed its sector average by {diff:+.1%}" if diff > 0 else f"underperformed its sector average by {diff:+.1%}"
        
        best_perf = f"{stat_cagr:+.1%}"
        worst_perf = f"{stat_vol:.1%}"
        kpi_title_1 = "Company CAGR"
        kpi_title_2 = "Company Volatility"
        kpi_title_3 = "Sector"
        kpi_val_3 = sector_name

    current_metric = "Raw Growth (CAGR)" if color_metric == "cagr" else "Risk-Adjusted (Sharpe)"

    # ---------------------------
    # KPI CARDS BUILDER
    # ---------------------------
    cards = [
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div(kpi_title_1, className="text-muted small fw-bold text-uppercase mb-1", style={"fontSize": "11px"}), 
                html.Div([
                    html.I(className="bi bi-arrow-up-right-circle-fill text-success me-2 fs-6"),
                    html.Span(best_perf, className="fw-bold text-success font-mono fs-6")
                ], className="d-flex align-items-center")
            ], className="p-2"), className="shadow-sm border-0 bg-surface h-100 transition-all"), 
            lg=3, md=6, className="mb-3 mb-lg-0"
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div(kpi_title_2, className="text-muted small fw-bold text-uppercase mb-1", style={"fontSize": "11px"}), 
                html.Div([
                    html.I(className="bi bi-arrow-down-right-circle-fill text-danger me-2 fs-6"),
                    html.Span(worst_perf, className="fw-bold text-danger font-mono fs-6")
                ], className="d-flex align-items-center")
            ], className="p-2"), className="shadow-sm border-0 bg-surface h-100 transition-all"), 
            lg=3, md=6, className="mb-3 mb-lg-0"
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div(kpi_title_3, className="text-muted small fw-bold text-uppercase mb-1", style={"fontSize": "11px"}), 
                html.Div([
                    html.I(className="bi bi-pie-chart-fill text-info me-2 fs-6"),
                    html.Span(kpi_val_3, className="fw-bold text-info font-mono fs-6 text-truncate")
                ], className="d-flex align-items-center")
            ], className="p-2"), className="shadow-sm border-0 bg-surface h-100 transition-all"), 
            lg=3, md=6, className="mb-3 mb-lg-0"
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div("Active Metric", className="text-muted small fw-bold text-uppercase mb-1", style={"fontSize": "11px"}), 
                html.Div([
                    html.I(className="bi bi-bar-chart-fill text-primary me-2 fs-6"),
                    html.Span(current_metric, className="fw-bold text-primary font-mono fs-6")
                ], className="d-flex align-items-center")
            ], className="p-2"), className="shadow-sm border-0 bg-surface h-100 transition-all"), 
            lg=3, md=6, className="mb-3 mb-lg-0"
        )
    ]
    summary_cards = dbc.Row(cards, className="w-100 m-0")

    # ---------------------------
    # TEAR SHEET BUILDER
    # ---------------------------
    spark_fig = go.Figure()
    
    # Benchmark Overlay
    spark_fig.add_trace(go.Scatter(
        x=market_df["Date"], y=market_df["Close"] / market_df["Close"].iloc[0] * 100, 
        mode="lines", name="NIFTY-50 (Base 100)",
        line=dict(color=colors["text_secondary"], width=1.5, dash="dot"),
    ))
    
    # Selected Asset
    if not pdf.empty:
        spark_fig.add_trace(go.Scatter(
            x=pdf["Date"], y=pdf["Close"] / pdf["Close"].iloc[0] * 100, 
            mode="lines", name=title_text + " (Base 100)",
            line=dict(color=line_color, width=2.5), fill='tozeroy', fillcolor=fill_color
        ))

    spark_fig.update_layout(
        margin=dict(l=0,r=0,t=20,b=20), height=300, 
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor=colors["grid"]),
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template=f"financial_{theme}"
    )

    stats_row = dbc.Row([
        dbc.Col([html.Div("CAGR", className="text-muted small"), html.Div(f"{stat_cagr:+.2%}", className="fw-bold font-mono text-primary")], width=2),
        dbc.Col([html.Div("Sharpe", className="text-muted small"), html.Div(f"{stat_sharpe:.2f}", className="fw-bold font-mono text-primary")], width=2),
        dbc.Col([html.Div("Volatility", className="text-muted small"), html.Div(f"{stat_vol:.1%}", className="fw-bold font-mono text-primary")], width=2),
        dbc.Col([html.Div("Max Drawdown", className="text-muted small"), html.Div(f"{stat_dd:+.1%}", className="fw-bold font-mono text-primary")], width=2),
        dbc.Col([html.Div("Market Weight", className="text-muted small"), html.Div(f"{stat_weight:.2%}", className="fw-bold font-mono text-primary")], width=2),
        dbc.Col([html.Div("Total Volume", className="text-muted small"), html.Div(f"{stat_volume:,.0f}", className="fw-bold font-mono text-primary")], width=2),
    ], className="mb-3 py-2 border-top border-bottom border-secondary border-opacity-25")

    # ---------------------------
    # ATTRIBUTION WATERFALL
    # ---------------------------
    waterfall_fig = go.Figure()
    
    if node_id == "NIFTY-50":
        # Group Contribution
        x_vals = []
        y_vals = []
        text_vals = []
        for _, row in sector_df.iterrows():
            g_name = row['Sector']
            g_cagr = row['CAGR']
            g_weight = row['Market_Weight']
            contrib = g_cagr * g_weight
            x_vals.append(g_name)
            y_vals.append(contrib)
            text_vals.append(f"{contrib:+.2%}")
            
        waterfall_fig.add_trace(go.Waterfall(
            name = "Attribution", orientation = "v",
            measure = ["relative"] * len(x_vals) + ["total"],
            x = x_vals + ["Market Total"],
            textposition = "outside",
            text = text_vals + [f"{sum(y_vals):+.2%}"],
            y = y_vals + [sum(y_vals)],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        waterfall_fig.update_layout(title=f"{group_by} Contribution to Market Return", showlegend=False, template=f"financial_{theme}", margin=dict(l=0,r=0,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
    elif "/" not in node_id:
        # Company Contribution to Group
        sector_comps = comp_df[comp_df.get(group_by, comp_df['Sector']) == node_id]
        if not sector_comps.empty:
            x_vals = []
            y_vals = []
            text_vals = []
            group_size = sector_comps[size_metric].sum()
            for _, row in sector_comps.iterrows():
                c_name = row['Company']
                c_cagr = row['CAGR']
                c_weight = row[size_metric] / group_size if group_size > 0 else 0
                contrib = c_cagr * c_weight
                x_vals.append(c_name)
                y_vals.append(contrib)
                text_vals.append(f"{contrib:+.2%}")
                
            waterfall_fig.add_trace(go.Waterfall(
                name = "Attribution", orientation = "v",
                measure = ["relative"] * len(x_vals) + ["total"],
                x = x_vals + ["Group Total"],
                textposition = "outside",
                text = text_vals + [f"{sum(y_vals):+.2%}"],
                y = y_vals + [sum(y_vals)],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            waterfall_fig.update_layout(title=f"Asset Contribution to {node_id} Return", showlegend=False, template=f"financial_{theme}", margin=dict(l=0,r=0,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    else:
        # Company selected
        waterfall_fig.update_layout(title="Attribution not available at asset level", template=f"financial_{theme}", margin=dict(l=0,r=0,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_visible=False, yaxis_visible=False)

    tabs = dbc.Tabs([
        dbc.Tab(dcc.Graph(figure=spark_fig, config=MODEBAR_CONFIG), label="Trend Analysis", tab_id="tab-trend", tab_style={"cursor": "pointer"}),
        dbc.Tab(dcc.Graph(figure=waterfall_fig, config=MODEBAR_CONFIG), label="Performance Attribution", tab_id="tab-attr", tab_style={"cursor": "pointer"}),
        dbc.Tab(dcc.Graph(figure=create_scatter_fig(comp_df, node_id, group_by, theme), config=MODEBAR_CONFIG), label="Risk vs Return", tab_id="tab-scatter", tab_style={"cursor": "pointer"}),
        dbc.Tab(dcc.Graph(figure=create_rolling_fig(res["raw_data"], node_id, comp_df, group_by, theme), config=MODEBAR_CONFIG), label="Rolling Trend", tab_id="tab-rolling", tab_style={"cursor": "pointer"}),
        dbc.Tab(dcc.Graph(figure=create_risk_fig(res["raw_data"], node_id, comp_df, group_by, theme), config=MODEBAR_CONFIG), label="Risk Decomposition", tab_id="tab-risk", tab_style={"cursor": "pointer"}),
        dbc.Tab(dcc.Graph(figure=create_distribution_fig(res["raw_data"], node_id, comp_df, group_by, theme), config=MODEBAR_CONFIG), label="Return Distribution", tab_id="tab-dist", tab_style={"cursor": "pointer"})
    ], id="tear-sheet-tabs", active_tab="tab-trend", className="mt-3")
    content = html.Div([
        html.H4(title_text, className="fw-bold text-primary mb-0 font-mono"),
        html.Span(subtitle_text, className="text-muted small text-uppercase fw-bold"),
        stats_row,
        tabs
    ], className="card shadow-sm border-0 bg-surface w-100 p-4 transition-all")
    
    # Generate Breadcrumbs
    if node_id == "NIFTY-50" or not node_id:
        breadcrumbs = html.Div([
            html.Span("NIFTY-50 Market", className="fw-bold text-primary"),
            html.Span(" • Click a block to drill down", className="text-muted small ms-2")
        ], className="font-mono")
    elif "/" in node_id:
        group, comp = node_id.split("/", 1)
        breadcrumbs = html.Div([
            html.Span("NIFTY-50 Market", className="text-muted"),
            html.I(className="bi bi-chevron-right mx-2 text-muted small"),
            html.Span(group, className="text-muted"),
            html.I(className="bi bi-chevron-right mx-2 text-muted small"),
            html.Span(comp, className="fw-bold text-primary")
        ], className="font-mono")
    else:
        breadcrumbs = html.Div([
            html.Span("NIFTY-50 Market", className="text-muted"),
            html.I(className="bi bi-chevron-right mx-2 text-muted small"),
            html.Span(node_id, className="fw-bold text-primary"),
            html.Span(" • Click a block to drill down", className="text-muted small ms-2")
        ], className="font-mono")
    
    return summary_cards, content, breadcrumbs

@callback(
    Output("market-breadth-chart", "figure"),
    Input("filter-state", "data"),
    Input("theme-store", "data")
)
def update_market_breadth(filter_state, theme):
    year_range = filter_state["year_range"]
    if not year_range:
        year_range = [2000, 2022]
        
    start_year, end_year = year_range
    
    from utils.analytics.treemap import load_clean_data, compute_market_breadth
    raw_df = load_clean_data(f"{start_year}-01-01", f"{end_year}-12-31")
    
    breadth_df = compute_market_breadth(raw_df, window=60)
    breadth_fig = go.Figure()
    if not breadth_df.empty:
        latest = breadth_df.iloc[-1]
        adv, dec, ratio = latest["Advancing"], latest["Declining"], latest["Breadth"]
        ad_text = f"Breadth: {ratio:.0%} | Advancing: {int(adv)} | Declining: {int(dec)}"
        
        breadth_fig.add_trace(go.Scatter(
            x=breadth_df["Date"], y=breadth_df["Breadth"], fill='tozeroy',
            line=dict(color="#21ce99", width=1), fillcolor="rgba(33, 206, 153, 0.2)",
            hovertemplate="Date: %{x}<br>Breadth: %{y:.1%}<br>Adv: %{customdata[0]}<br>Dec: %{customdata[1]}<extra></extra>",
            customdata=breadth_df[["Advancing", "Declining"]].values
        ))
        breadth_fig.add_annotation(
            text=ad_text, x=1, y=1, xref="paper", yref="paper", 
            showarrow=False, font=dict(family="JetBrains Mono", size=10, color=ThemeManager.get_colors(theme)["text_primary"]),
            xanchor="right", yanchor="top"
        )
    breadth_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), height=40, showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True),
        template=f"financial_{theme}"
    )
    return breadth_fig

# ---------------------------
# FILTER STATE MANAGEMENT
# ---------------------------
@callback(
    Output("filter-drawer", "is_open"),
    Input("open-filters-btn", "n_clicks"),
    Input("apply-filters-btn", "n_clicks"),
    State("filter-drawer", "is_open"),
    prevent_initial_call=True
)
def toggle_filter_drawer(open_clicks, apply_clicks, is_open):
    if open_clicks or apply_clicks:
        return not is_open
    return is_open

@callback(
    Output("filter-state", "data", allow_duplicate=True),
    Output("group-by-toggle", "value", allow_duplicate=True),
    Output("color-metric-toggle", "value", allow_duplicate=True),
    Output("size-metric-toggle", "value", allow_duplicate=True),
    Output("year-range-slider", "value", allow_duplicate=True),
    Input("apply-filters-btn", "n_clicks"),
    Input("reset-filters-btn", "n_clicks"),
    State("group-by-toggle", "value"),
    State("color-metric-toggle", "value"),
    State("size-metric-toggle", "value"),
    State("year-range-slider", "value"),
    prevent_initial_call=True
)
def update_filter_state(apply_clicks, reset_clicks, group_by, color_metric, size_metric, year_range):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"]
    
    if "reset-filters-btn" in trigger:
        # Reset defaults but DO NOT update the applied state yet
        return dash.no_update, "Sector", "cagr", "Total_Volume", [2000, 2022]
        
    if "apply-filters-btn" in trigger:
        # Save draft inputs to application state
        new_state = {
            "group_by": group_by,
            "color_metric": color_metric,
            "size_metric": size_metric,
            "year_range": year_range
        }
        return new_state, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@callback(
    Output("active-filter-summary", "children"),
    Output("active-filter-summary", "className"),
    Input("filter-state", "data")
)
def update_active_filter_summary(filter_state):
    if not filter_state:
        return "No Active Filters", "d-none d-lg-flex align-items-center me-3 text-muted small font-mono"
        
    summary = []
    if filter_state.get("group_by"):
        summary.append(html.Span(f"Group: {filter_state['group_by']}", className="badge bg-secondary me-2"))
    if filter_state.get("color_metric"):
        val = "Growth" if filter_state["color_metric"] == "cagr" else "Sharpe"
        summary.append(html.Span(f"Color: {val}", className="badge bg-secondary me-2"))
    if filter_state.get("size_metric"):
        val = "Volume" if filter_state["size_metric"] == "Total_Volume" else "Turnover"
        summary.append(html.Span(f"Size: {val}", className="badge bg-secondary me-2"))
    if filter_state.get("year_range"):
        yr = filter_state["year_range"]
        summary.append(html.Span(f"Years: {yr[0]}-{yr[1]}", className="badge bg-secondary me-2"))
        
    return summary, "d-none d-lg-flex align-items-center me-3 text-muted small font-mono"