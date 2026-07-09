import dash
from dash import html, dcc, Input, Output, callback, State
import plotly.express as px
from utils.analytics.market_shock import get_market_shocks, get_cross_section

dash.register_page(__name__, path="/market_shock", name="Market Shocks")


layout = html.Div([
    html.H2("Market Shock & Systemic Anomaly Detection"),
    html.P("Identify extreme market events and observe how different stocks disperse during a crisis."),
    
    # --- CONTROL PANEL ---
    html.Div([
        html.Div([
            # Z-Score Threshold Slider
            html.Div([
                html.Label("Anomaly Threshold (Z-Score):", className="fw-bold mb-2", style={'white-space': 'nowrap'}),
                dcc.Slider(
                    id='z-threshold-slider',
                    min=1.5, max=5.0, step=0.5, value=3.0, 
                    marks={i/10: str(i/10) for i in range(15, 55, 5)},
                    tooltip={"placement": "top", "always_visible": True},
                    updatemode="mouseup"
                )
            ], className="col-12 col-md-6 mb-3 mb-md-0"), # Responsive columns
            
            # Rolling Window Slider
            html.Div([
                html.Label("Rolling Window (Days):", className="fw-bold mb-2", style={'white-space': 'nowrap'}),
                dcc.Slider(
                    id='rolling-window-slider',
                    min=10, max=60, step=10, value=20, 
                    marks={i: f"{i}d" for i in range(10, 70, 10)},
                    tooltip={"placement": "top", "always_visible": True},
                    updatemode="mouseup"
                )
            ], className="col-12 col-md-6")
        ], className="row")
    ], className="card shadow-sm mb-4 p-3"),
    
    # --- MACRO VIEW: Diverging Timeline ---
    html.Div([
        dcc.Loading(
            dcc.Graph(
                id="timeline-heatmap", 
                style={"height": "450px"},
                config={"displayModeBar": True, "responsive": True}
            ),
            type="default"
        )
    ], className="card shadow-sm mb-4 p-3"),
    
    # --- MICRO VIEW: Beeswarm Dispersion ---
    html.Div([
        html.H4(
            id="beeswarm-title", 
            children="Select a date spike on the timeline above to view stock dispersion.",
            className="text-center text-muted mb-3"
        ),
        dcc.Loading(
            dcc.Graph(
                id="beeswarm-plot", 
                style={"height": "500px"},
                config={"displayModeBar": False, "responsive": True}
            ),
            type="default" 
        )
    ], className="card shadow-sm p-3")
], className="container-fluid py-3")



@callback(
    Output("timeline-heatmap", "figure"),
    Input("z-threshold-slider", "value"),
    Input("rolling-window-slider", "value"),
    Input("start-date-filter", "value"),
    Input("end-date-filter", "value"),
    Input("sector-filter", "value"),
    Input("company-filter", "value"),
    State("timeline-heatmap", "relayoutData"),
    State("timeline-heatmap", "figure")
)
def update_timeline(z_threshold, rolling_window, start_date, end_date, sector, company, relayout_data, current_fig):

    # Query the Database for Market Shocks based on the current slider values
    market_shocks = get_market_shocks(
        z_threshold, window=rolling_window,
        sector=sector, company=company, start_date=start_date, end_date=end_date,
    )
    
    # Plot the timeline bar chart with updated data
    fig_timeline = px.bar(
        market_shocks,
        x="Date", y=["Crash_Severity", "Rally_Severity"], 
        title=f"Systemic Market Volatility",
        labels={"value": "Severity Score", "variable": "Shock Type"},
        color_discrete_map={"Crash_Severity": "#EF553B", "Rally_Severity": "#00CC96"},
        template="plotly_white"
    )

    newnames = {'Crash_Severity': 'Market Crash', 'Rally_Severity': 'Market Rally'}
    fig_timeline.for_each_trace(lambda t: t.update(name = newnames.get(t.name, t.name)))

    fig_timeline.update_layout(
        clickmode='event+select', 
        barmode='relative', 
        yaxis_title="Severity Score",
        margin=dict(b=50),
        transition_duration=100
    )
    fig_timeline.update_traces(marker_line_width=0)
    fig_timeline.update_yaxes(fixedrange=True)

    fig_timeline.update_xaxes(
        rangeslider_visible=False, 
        rangeselector=dict(
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
    Input("timeline-heatmap", "clickData"),
    Input("z-threshold-slider", "value"),
    Input("rolling-window-slider", "value"),
    Input("sector-filter", "value"),
    Input("company-filter", "value"),
)
def update_beeswarm_dispersion(clickData, z_threshold, rolling_window, sector, company):
    if not clickData:
        empty_fig = px.scatter(title="Waiting for selection...")
        empty_fig.update_layout(template="plotly_white", xaxis_visible=False, yaxis_visible=False)
        return empty_fig, "Select a date spike on the timeline above to view stock dispersion."

    target_date = clickData["points"][0]["x"]

    # Query the Database for Cross-Section Data on the selected date
    cross_section = get_cross_section(target_date, window=rolling_window, sector=sector, company=company)

    # Plot the Beeswarm Dispersion
    fig_beeswarm = px.strip(
        cross_section,
        x="Sector", y="Z_Score", color="Sector",
        hover_name="Company",
        hover_data={"Z_Score": ":.2f", "Close": True, "Sector": False},
        stripmode="overlay"
    )

    fig_beeswarm.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
    fig_beeswarm.add_hline(y=z_threshold, line_dash="dash", line_color="red", annotation_text=f"+{z_threshold}σ")
    fig_beeswarm.add_hline(y=-z_threshold, line_dash="dash", line_color="red", annotation_text=f"-{z_threshold}σ")
    
    fig_beeswarm.update_layout(
        template="plotly_white",
        showlegend=False, 
        yaxis_title="Volatility (Z-Score)",
        transition_duration=100
    )
    
    fig_beeswarm.update_yaxes(fixedrange=True)

    clean_date = target_date.split('T')[0]
    return fig_beeswarm, f"Sector Dispersion on {clean_date}"