import dash
from dash import State, html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
import plotly.express as px
from utils.analytics.sector_rotation import prepare_rrg_features
from utils.config import get_rrg_quadrants, MODEBAR_CONFIG, ThemeManager

dash.register_page(__name__, path="/sector_rotation")

# Generate standard years based on dataset (e.g., 2010 to 2021)
YEAR_OPTIONS = [{"label": str(y), "value": y} for y in range(2010, 2022)]

layout = dbc.Container([
    # Title Row
    dbc.Row([
        dbc.Col([
            html.H2("Relative Rotation Graphs (RRG)", className="fw-bold mb-2"),
            html.P(
                "Institutional momentum tracking. X-Axis: Relative Strength (Trend). Y-Axis: Relative Momentum (Velocity). "
                "Data is downsampled to weekly intervals for high-performance animation.",
                className="text-muted mb-0"
            )
        ], md=12),
    ], className="mb-3"),

    # Controls Row — Responsive, No Overlap
    html.Div([
        html.Div([
            html.Div([
                html.Label("Playback Speed:", className="fw-bold small mb-2 text-primary"),
                dbc.RadioItems(
                    id="rrg-speed-selector",
                    options=[
                        {"label": "0.25x", "value": 0.25},
                        {"label": "0.5x", "value": 0.5},
                        {"label": "1x", "value": 1.0},
                        {"label": "1.5x", "value": 1.5},
                        {"label": "2x", "value": 2.0},
                        {"label": "4x", "value": 4.0},
                    ],
                    value=1.0, inline=True, className="btn-group", 
                    inputClassName="btn-check", 
                    labelClassName="btn btn-outline-primary btn-sm"
                )
            ], className="me-4"),
            html.Div([
                html.Label("Select Year:", className="fw-bold small mb-2 text-primary"),
                dcc.Dropdown(
                    id="rrg-year-selector",
                    options=YEAR_OPTIONS,
                    value=2021,
                    clearable=False,
                    className="text-dark",
                    style={"minWidth": "120px"}
                )
            ]),
        ], style={"display": "flex", "flexWrap": "wrap", "alignItems": "flex-end", "gap": "16px"}),
    ], className="card shadow-sm border-0 bg-surface p-4 mb-4"),

    # Chart
    dbc.Row([
        dbc.Col([
            html.Div(
                dcc.Loading(dcc.Graph(id="rrg-animated-chart", style={"height": "75vh"},
                                      config=MODEBAR_CONFIG),
                            type="circle", color="var(--accent-primary)"),
                className="card shadow-sm border-0 bg-surface p-2"
            )
        ], width=12)
    ])
], fluid=True, className="py-4")

@callback(
    Output("rrg-animated-chart", "figure"),
    Input("rrg-year-selector", "value", allow_optional=True),
    Input("rrg-speed-selector", "value", allow_optional=True),
    Input("global-state", "data"),
    Input("theme-store", "data"),
    State("url", "pathname")
)
def update_rrg_chart(selected_year, playback_speed, global_state, theme, pathname):
    import dash
    if pathname != "/sector-rotation" and pathname != "/sector_rotation":
        raise dash.exceptions.PreventUpdate
        
    from utils.config import ANIMATION_CONFIG
    df = prepare_rrg_features(selected_year)
    
    if global_state and global_state.get("sectors"):
        df = df[df["Sector"].isin(global_state["sectors"])]
        
    if df.empty:
        import plotly.graph_objects as go
        empty_fig = go.Figure().update_layout(title="No data available", xaxis_visible=False, yaxis_visible=False, template=f"financial_{theme}")
        return empty_fig

    colors = ThemeManager.get_colors(theme)

    # Base Animated Scatter
    fig = px.scatter(
        df, x="RS_Ratio", y="RS_Momentum", 
        animation_frame="Frame", animation_group="Company",
        color="Sector", hover_name="Company",
        text="Company", # Shows ticker next to the dot
        range_x=[88, 112], range_y=[88, 112], # Fixed RRG Boundaries
    )

    # Institutional Styling & Quadrants
    fig.update_traces(
        textposition='top center', 
        textfont=dict(family="JetBrains Mono, monospace", size=10, color=colors["text_secondary"]),
        marker=dict(size=12, line=dict(width=1, color=colors["bg_surface"]))
    )



    # Add the RRG Crosshairs (Centered exactly at 100)
    fig.add_hline(y=100, line_width=2.0, line_color=colors["crosshair"], opacity=1.0)
    fig.add_vline(x=100, line_width=2.0, line_color=colors["crosshair"], opacity=1.0)

    # Annotate the 4 Quadrants
    annotations = get_rrg_quadrants(theme)
    for ann in annotations:
        fig.add_annotation(
            x=ann['x'], y=ann['y'], text=ann['text'], showarrow=False, opacity=0.8, font=ann['font']
        )

    # Final Quant Aesthetic Tweaks
    fig.update_layout(
        template=f"financial_{theme}",
        xaxis=dict(title="JdK RS-Ratio (Trend)", showgrid=False, zeroline=False),
        yaxis=dict(title="JdK RS-Momentum (Velocity)", showgrid=False, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    if len(fig.layout.updatemenus) > 0:
        base_duration = ANIMATION_CONFIG["frame"]["duration"]
        base_transition = ANIMATION_CONFIG["transition"]["duration"]
        
        adjusted_duration = int(base_duration / playback_speed)
        adjusted_transition = int(base_transition / playback_speed)
        
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = adjusted_duration
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = adjusted_transition

    return fig