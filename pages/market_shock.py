import dash
from dash import html, dcc, Input, Output, callback, State
import plotly.express as px
import plotly.graph_objects as go
from utils.analytics.market_shock import get_market_shocks, get_cross_section
from utils.config import MODEBAR_CONFIG, ThemeManager

dash.register_page(__name__, path="/market_shock", name="Market Shocks")


layout = html.Div([
    html.H2("Market Shock & Systemic Anomaly Detection", className="fw-bold mb-1"),
    html.P("Identify extreme market events and observe how different stocks disperse during a crisis.",
           className="text-muted mb-4"),
    
    # --- CONTROL PANEL ---
    html.Div([
        html.Div([
            # Z-Score Slider
            html.Div([
                html.Label("Anomaly Threshold (Z-Score)", className="fw-bold mb-2 text-primary"),
                html.Div([
                    html.Span("1.5", className="static-bound-label text-muted fw-bold small me-2"),
                    dcc.Slider(
                        id='z-threshold-slider',
                        min=1.5, max=5.0, step=0.5, value=3.0, 
                        marks={i/10: {"label": str(i/10),
                                      "style": {"color": "#9499a6", "fontSize": "13px",
                                                "fontWeight": "600"}} for i in range(15, 55, 5)},
                        updatemode="mouseup",
                        className="slider-track flex-grow-1 mx-3"
                    ),
                    dcc.Input(id="z-threshold-box", type="number", min=1.5, max=5.0, step=0.5, value=3.0, className="form-control text-center p-0 me-2", style={"width": "55px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "28px", "fontSize": "13px"}),
                    html.Span("5.0", className="static-bound-label text-muted fw-bold small"),
                ], className="slider-wrapper", style={"display": "flex", "alignItems": "center"})
            ], className="col-12 col-md-6 mb-4 mb-md-0 pe-md-4"),
            
            # Rolling Window Slider
            html.Div([
                html.Label("Rolling Window (Days)", className="fw-bold mb-2 text-primary"),
                html.Div([
                    html.Span("10", className="static-bound-label text-muted fw-bold small me-2"),
                    dcc.Slider(
                        id='rolling-window-slider',
                        min=10, max=60, step=10, value=20, 
                        marks={i: {"label": f"{i}d",
                                   "style": {"color": "#9499a6", "fontSize": "13px",
                                             "fontWeight": "600"}} for i in range(10, 70, 10)},
                        updatemode="mouseup",
                        className="slider-track flex-grow-1 mx-3"
                    ),
                    dcc.Input(id="rolling-window-box", type="number", min=10, max=60, step=10, value=20, className="form-control text-center p-0 me-2", style={"width": "55px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "28px", "fontSize": "13px"}),
                    html.Span("60", className="static-bound-label text-muted fw-bold small"),
                ], className="slider-wrapper", style={"display": "flex", "alignItems": "center"})
            ], className="col-12 col-md-6 mb-4 ps-md-4")
        ], className="row")
    ], className="card shadow-sm border-0 bg-surface mb-4 p-4"),
    
    # --- MACRO VIEW: Diverging Timeline ---
    html.Div([
        dcc.Loading(
            dcc.Graph(
                id="timeline-heatmap", 
                style={"height": "450px"},
                config=MODEBAR_CONFIG
            ),
            type="circle", color="var(--accent-primary)"
        )
    ], className="card shadow-sm border-0 bg-surface mb-4 p-3"),
    
    # --- MICRO VIEW: Beeswarm Dispersion ---
    html.Div([
        html.Div(id="shock-smart-narrative"),
        html.H4(
            id="beeswarm-title", 
            children="Hover over a date spike on the timeline above to view stock dispersion.",
            className="text-center text-muted mb-3"
        ),
        dcc.Loading(
            dcc.Graph(
                id="beeswarm-plot", 
                style={"height": "500px"},
                config=MODEBAR_CONFIG
            ),
            type="circle", color="var(--accent-primary)"
        )
    ], className="card shadow-sm border-0 bg-surface p-3")
], className="container-fluid py-3")



@callback(
    Output("timeline-heatmap", "figure"),
    Input("z-threshold-slider", "value"),
    Input("rolling-window-slider", "value"),
    State("timeline-heatmap", "relayoutData"),
    State("timeline-heatmap", "figure"),
    Input("theme-store", "data"),
    State("url", "pathname")
)
def update_timeline(z_threshold, rolling_window, relayout_data, current_fig, theme, pathname):
    if pathname != "/market-shocks" and pathname != "/market_shock":
        raise dash.exceptions.PreventUpdate
    
    market_shocks = get_market_shocks(z_threshold, window=rolling_window)
    
    if market_shocks.empty:
        empty_fig = go.Figure().update_layout(title="No market shocks detected",
                                              xaxis_visible=False, yaxis_visible=False, template=f"financial_{theme}")
        return empty_fig

    colors = ThemeManager.get_colors(theme)

    # Plot the timeline bar chart with updated data
    fig_timeline = px.bar(
        market_shocks,
        x="Date", y=["Crash_Severity", "Rally_Severity"], 
        title="Systemic Market Volatility",
        labels={"value": "Severity Score", "variable": "Shock Type"},
        color_discrete_map={"Crash_Severity": colors["danger"], "Rally_Severity": colors["success"]}
    )

    newnames = {'Crash_Severity': 'Market Crash', 'Rally_Severity': 'Market Rally'}
    fig_timeline.for_each_trace(lambda t: t.update(name = newnames.get(t.name, t.name)))

    fig_timeline.update_layout(
        clickmode='event+select', 
        barmode='relative', 
        yaxis_title="Severity Score",
        margin=dict(l=40, r=20, t=60, b=50),
        transition_duration=100,
        template=f"financial_{theme}"
    )
    fig_timeline.update_traces(marker_line_width=0)
    fig_timeline.update_yaxes(fixedrange=True)

    fig_timeline.update_xaxes(
        rangeslider_visible=False, 
        rangeselector=dict(
            y=1.05,
            x=1.0,
            xanchor="right",
            yanchor="bottom",
            bgcolor=colors["bg_surface"],
            activecolor=colors["info"],
            font=dict(color=colors["text_primary"]),
            buttons=list([
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(count=5, label="5y", step="year", stepmode="backward"),
                dict(count=10, label="10y", step="year", stepmode="backward"),
                dict(step="all", label="Max")
            ])
        )
    )
    
    # Preserve Zoom State
    zoom_range = None
    if relayout_data and "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
        zoom_range = [relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]]
    elif relayout_data and ("xaxis.autorange" in relayout_data or "autorange" in relayout_data):
        zoom_range = None 
    elif current_fig and "layout" in current_fig and "xaxis" in current_fig["layout"] and "range" in current_fig["layout"]["xaxis"]:
        zoom_range = current_fig["layout"]["xaxis"]["range"]

    if zoom_range:
        fig_timeline.update_xaxes(range=zoom_range)
    else:
        fig_timeline.update_xaxes(autorange=True)
    
    return fig_timeline


@callback(
    Output("beeswarm-plot", "figure"),
    Output("beeswarm-title", "children"),
    Output("shock-smart-narrative", "children"),
    Input("timeline-heatmap", "hoverData", allow_optional=True),
    Input("timeline-heatmap", "clickData", allow_optional=True),
    Input("z-threshold-slider", "value"),
    Input("rolling-window-slider", "value"),
    Input("global-state", "data"),
    Input("theme-store", "data"),
    State("url", "pathname")
)
def update_beeswarm_dispersion(hoverData, clickData, z_threshold, rolling_window, global_state, theme, pathname):
    if pathname != "/market-shocks" and pathname != "/market_shock":
        raise dash.exceptions.PreventUpdate
        
    from components.narrative import generate_smart_narrative
    
    # Prefer hover, fallback to click
    interaction_data = hoverData or clickData
    
    if not interaction_data:
        empty_fig = go.Figure().update_layout(
            xaxis_visible=False, yaxis_visible=False,
            template=f"financial_{theme}",
            annotations=[dict(text="Hover over a date spike on the timeline to view stock dispersion.",
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                              font=dict(size=14, color=ThemeManager.get_colors(theme)["text_secondary"]))]
        )
        return empty_fig, "Hover over a date spike on the timeline above to view stock dispersion.", html.Div()

    target_date = interaction_data["points"][0]["x"]
    
    # Query the Database for Cross-Section Data on the selected date
    cross_section = get_cross_section(target_date, window=rolling_window)

    if global_state and global_state.get("sectors"):
        cross_section = cross_section[cross_section["Sector"].isin(global_state["sectors"])]

    if cross_section.empty:
        empty_fig = go.Figure().update_layout(title="No data available",
                                              xaxis_visible=False, yaxis_visible=False, template=f"financial_{theme}")
        return empty_fig, "No data available for the selected date and filters.", html.Div()

    colors = ThemeManager.get_colors(theme)

    # Plot the Beeswarm Dispersion
    fig_beeswarm = px.strip(
        cross_section,
        x="Sector", y="Z_Score", color="Sector",
        hover_name="Company",
        hover_data={"Z_Score": ":.2f", "Close": True, "Sector": False},
        stripmode="overlay"
    )

    fig_beeswarm.add_hline(y=0, line_dash="solid", line_color=colors["crosshair"], opacity=0.8)
    fig_beeswarm.add_hline(y=z_threshold, line_dash="dash", line_color=colors["danger"], annotation_text=f"+{z_threshold}σ")
    fig_beeswarm.add_hline(y=-z_threshold, line_dash="dash", line_color=colors["danger"], annotation_text=f"-{z_threshold}σ")
    
    fig_beeswarm.update_layout(
        showlegend=False, 
        yaxis_title="Volatility (Z-Score)",
        transition_duration=100,
        template=f"financial_{theme}"
    )
    
    fig_beeswarm.update_yaxes(fixedrange=True)

    clean_date = target_date.split('T')[0]
    
    narrative = html.Div(f"Cross-sectional shock variance on {clean_date}", className="text-muted small")
    if not cross_section.empty:
        max_shock = cross_section.loc[cross_section['Z_Score'].abs().idxmax()]
        narrative = html.Div([
            html.I(className="bi bi-magic text-danger me-2"),
            html.Span(f"On {clean_date}, ", className="text-muted small"),
            html.B(max_shock['Company'], className="text-danger small"), 
            html.Span(f" exhibited maximum anomaly with a Z-Score of {max_shock['Z_Score']:+.2f}σ.", className="text-muted small")
        ], className="p-2 border border-danger border-opacity-25 rounded bg-danger bg-opacity-10 mb-2 mt-0")
        
    return fig_beeswarm, f"Sector Dispersion on {clean_date}", narrative

dash.clientside_callback(
    "function(val, box) {\n"
    "    const ctx = dash_clientside.callback_context;\n"
    "    if (!ctx.triggered.length) return [val, val];\n"
    "    const trigger = ctx.triggered[0].prop_id;\n"
    "    if (trigger === 'z-threshold-slider.value') {\n"
    "        return [val, dash_clientside.no_update];\n"
    "    } else {\n"
    "        let v = parseFloat(box) || 3.0;\n"
    "        if (v < 1.5) v = 1.5;\n"
    "        if (v > 5.0) v = 5.0;\n"
    "        return [dash_clientside.no_update, v];\n"
    "    }\n"
    "}",
    Output("z-threshold-box", "value"),
    Output("z-threshold-slider", "value"),
    Input("z-threshold-slider", "value"),
    Input("z-threshold-box", "value")
)

dash.clientside_callback(
    "function(val, box) {\n"
    "    const ctx = dash_clientside.callback_context;\n"
    "    if (!ctx.triggered.length) return [val, val];\n"
    "    const trigger = ctx.triggered[0].prop_id;\n"
    "    if (trigger === 'rolling-window-slider.value') {\n"
    "        return [val, dash_clientside.no_update];\n"
    "    } else {\n"
    "        let v = parseInt(box) || 20;\n"
    "        if (v < 10) v = 10;\n"
    "        if (v > 60) v = 60;\n"
    "        return [dash_clientside.no_update, v];\n"
    "    }\n"
    "}",
    Output("rolling-window-box", "value"),
    Output("rolling-window-slider", "value"),
    Input("rolling-window-slider", "value"),
    Input("rolling-window-box", "value")
)

