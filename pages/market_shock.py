import dash
from dash import html, dcc, Input, Output, callback, State
import plotly.express as px
from utils.analytics.market_shock import load_and_compute_base_metrics, apply_threshold_and_aggregate, extract_cross_section

dash.register_page(__name__, path="/market_shock", name="Market Shocks")

# Load the base dataset and compute rolling statistics and Z-scores at application startup
BASE_DATA = load_and_compute_base_metrics()


# Define the layout of the Market Shocks page
layout = html.Div([
    
    # Z-score threshold slider
    html.Div([
        html.Label("Anomaly Threshold (Z-Score):", className="fw-bold me-3 mb-0", style={'white-space': 'nowrap'}),
        html.Div([
            dcc.Slider(
                id='z-threshold-slider',
                min=1.5, max=5.0, step=0.5, value=3.0, 
                marks={i/10: str(i/10) for i in range(15, 55, 5)},
                tooltip={"placement": "top", "always_visible": True},
                updatemode="mouseup"
            )
        ], style={'width': '100%', 'padding-top': '5px', 'padding-bottom': '5px'}) 
    ], className="d-flex align-items-center mb-4 p-3 card shadow-sm"),
    
    # Timeline Heatmap of Market Shocks
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
    
    # Beeswarm Plot for Cross-Sectional Dispersion
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


# Instantly re-aggregate the data and update the timeline heatmap when the Z-score threshold is changed
@callback(
    Output("timeline-heatmap", "figure"),
    Input("z-threshold-slider", "value"),
    State("timeline-heatmap", "relayoutData"),
    State("timeline-heatmap", "figure")
)
def update_timeline(z_threshold, relayout_data, current_fig):
    
    # Re-aggregate the data based on the new Z-score threshold
    pipeline_data = apply_threshold_and_aggregate(BASE_DATA.copy(), z_threshold=z_threshold)
    market_shocks = pipeline_data["market_shocks"]
    
    # Rebuild the timeline heatmap for the new threshold
    fig_timeline = px.bar(
        market_shocks,
        x="Date", y=["Crash_Severity", "Rally_Severity"], 
        title="Systemic Market Volatility",
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

    # Check if the user just explicitly manually zoomed by dragging a box
    if relayout_data and "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
        zoom_range = [relayout_data["xaxis.range[0]"], relayout_data["xaxis.range[1]"]]
        
    # Check if the user just explicitly clicked "Reset Axes" or "Max"
    elif relayout_data and ("xaxis.autorange" in relayout_data or "autorange" in relayout_data):
        zoom_range = None # Force autoscale
        
    # If no explicit zooming, check if the current figure already has a zoom range set
    elif current_fig and "layout" in current_fig and "xaxis" in current_fig["layout"] and "range" in current_fig["layout"]["xaxis"]:
        zoom_range = current_fig["layout"]["xaxis"]["range"]

    # Apply the final decided state
    if zoom_range:
        fig_timeline.update_xaxes(range=zoom_range)
    else:
        fig_timeline.update_xaxes(autorange=True)
    
    return fig_timeline

# Update the Beeswarm plot to show cross-sectional dispersion for the selected date and Z-score threshold
@callback(
    Output("beeswarm-plot", "figure"),
    Output("beeswarm-title", "children"),
    Input("timeline-heatmap", "clickData"),
    Input("z-threshold-slider", "value")
)
def update_beeswarm_dispersion(clickData, z_threshold):
    
    if not clickData:
        empty_fig = px.scatter(title="Waiting for selection...")
        empty_fig.update_layout(template="plotly_white", xaxis_visible=False, yaxis_visible=False)
        return empty_fig, "Select a date spike on the timeline above to view stock dispersion."

    target_date = clickData["points"][0]["x"]
    
    # Fetch data based on current threshold
    pipeline_data = apply_threshold_and_aggregate(BASE_DATA.copy(), z_threshold=z_threshold)
    cross_section = extract_cross_section(pipeline_data["company_anomalies"], target_date)

    # Build Beeswarm Plot for the selected date and threshold
    fig_beeswarm = px.strip(
        cross_section,
        x="Sector", y="Z_Score", color="Sector",
        hover_name="Company",
        hover_data={"Z_Score": ":.2f", "Close": True, "Sector": False},
        stripmode="overlay"
    )

    # Add Dynamic Boundary Lines
    fig_beeswarm.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
    fig_beeswarm.add_hline(y=z_threshold, line_dash="dash", line_color="red", annotation_text=f"+{z_threshold}σ")
    fig_beeswarm.add_hline(y=-z_threshold, line_dash="dash", line_color="red", annotation_text=f"-{z_threshold}σ")
    
    fig_beeswarm.update_layout(
        template="plotly_white",
        showlegend=False, 
        yaxis_title="Volatility (Z-Score)",
        transition_duration=100
    )

    # Return figure and dynamic title
    clean_date = target_date.split('T')[0]
    return fig_beeswarm, f"Sector Dispersion on {clean_date}"