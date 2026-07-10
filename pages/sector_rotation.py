"""
pages/sector_rotation.py

Dash layout and interactive callbacks for the Relative Rotation Graph (RRG).
Displays relative sector strength and momentum over time with click-to-drilldown capabilities
using cleanly separated, synchronized stacked subplots.
"""

import io

import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.analytics.sector_rotation import run_sector_rotation_pipeline

dash.register_page(__name__, path="/sector_rotation")

# Initialize pipeline once at application startup
PIPELINE = run_sector_rotation_pipeline(weighting="return", freq="W")
RS_DF = PIPELINE["rs_df"]
ANIM_DF = PIPELINE["anim_df"]
SECTORS = PIPELINE["sectors"]

QUADRANT_COLORS = {
    "Leading": "#1D9E75",
    "Weakening": "#BA7517",
    "Lagging": "#E24B4A",
    "Improving": "#378ADD",
}

TIME_WINDOWS = {
    "1M": 4,
    "3M": 13,
    "6M": 26,
    "1Y": 52,
    "All": None,
}


def create_rrg_plot(anim_df, window="1Y"):
    n_periods = TIME_WINDOWS.get(window)
    df = anim_df.copy()

    if n_periods is not None:
        recent_periods = sorted(df["Period"].unique())[-n_periods:]
        df = df[df["Period"].isin(recent_periods)]
    else:
        # "All" spans ~20 years of weekly frames (1000+), which is extremely slow
        # to build server-side and to render client-side. Collapse to monthly frames
        # so the full history animation stays responsive.
        df["Period"] = df["Period"].dt.to_period("M").dt.start_time
        df = (
            df.groupby(["Sector", "Period"], as_index=False)
            .agg(
                RS_Ratio=("RS_Ratio", "last"),
                RS_Momentum=("RS_Momentum", "last"),
                Quadrant=("Quadrant", "last"),
            )
        )
        df["PeriodStr"] = df["Period"].dt.strftime("%Y-%m")

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=600,
            annotations=[dict(
                text="Insufficient historical data for this window.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="#6c757d")
            )]
        )
        return fig

    # Dynamic padding to ensure edge points and annotations remain visible
    x_pad = max(df["RS_Ratio"].std() * 1.5, 3)
    y_pad = max(df["RS_Momentum"].std() * 1.5, 3)
    x_range = [df["RS_Ratio"].min() - x_pad, df["RS_Ratio"].max() + x_pad]
    y_range = [df["RS_Momentum"].min() - y_pad, df["RS_Momentum"].max() + y_pad]

    fig = px.scatter(
        df,
        x="RS_Ratio",
        y="RS_Momentum",
        color="Sector",
        animation_frame="PeriodStr",
        animation_group="Sector",
        hover_name="Sector",
        range_x=x_range,
        range_y=y_range,
    )

    fig.update_traces(
        marker=dict(size=16, opacity=0.85, line=dict(width=1.5, color="white")),
        selector=dict(mode="markers")
    )

    # Quadrant dividing lines
    fig.add_hline(y=0, line_dash="dash", line_color="#adb5bd", line_width=1)
    fig.add_vline(x=100, line_dash="dash", line_color="#adb5bd", line_width=1)

    # Corner annotations for RRG quadrants using xshift/yshift (Fixes the pad error!)
    corners = [
        ("Leading", x_range[1], y_range[1], "right", "top"),
        ("Weakening", x_range[1], y_range[0], "right", "bottom"),
        ("Lagging", x_range[0], y_range[0], "left", "bottom"),
        ("Improving", x_range[0], y_range[1], "left", "top"),
    ]
    for label, x, y, x_anchor, y_anchor in corners:
        x_shift = -15 if x_anchor == "right" else 15
        y_shift = -15 if y_anchor == "top" else 15
        
        fig.add_annotation(
            x=x, y=y, text=label, showarrow=False,
            font=dict(color=QUADRANT_COLORS[label], size=14, family="Arial, sans-serif"),
            xanchor=x_anchor, yanchor=y_anchor,
            xshift=x_shift, yshift=y_shift,
            opacity=0.4
        )

    fig.update_layout(
        height=650,
        margin=dict(l=50, r=200, t=30, b=100),
        xaxis_title="RS Ratio (100 = Market Benchmark)",
        yaxis_title="RS Momentum",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            title=dict(text="Sectors"),
            bordercolor="#e9ecef",
            borderwidth=1
        ),
        hoverlabel=dict(bgcolor="white", font_size=13)
    )

    # Smooth animation pacing and prevent control overlap
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 200
        fig.layout.updatemenus[0].pad = {"r": 10, "t": 50}
        
    if fig.layout.sliders:
        fig.layout.sliders[0].pad = {"r": 10, "t": 50}

    return fig


def create_sector_history_chart(rs_df, sector):
    if not sector:
        fig = go.Figure()
        fig.update_layout(
            height=450,
            annotations=[dict(
                text="Click any sector dot above to load historical performance.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="#6c757d")
            )],
            plot_bgcolor="#f8f9fa"
        )
        return fig

    sub = rs_df[rs_df["Sector"] == sector].dropna(subset=["RS_Ratio", "RS_Momentum"])

    # Create vertically stacked subplots with shared X-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("RS Ratio (Trend Strength vs Market)", "RS Momentum (Rate of Acceleration)")
    )

    # Trace 1: RS Ratio (Top Plot)
    fig.add_trace(
        go.Scatter(
            x=sub["Date"], y=sub["RS_Ratio"], 
            name="RS Ratio", line=dict(color="#0d6efd", width=2),
            showlegend=False
        ),
        row=1, col=1
    )
    # Benchmark line at 100
    fig.add_hline(y=100, line_dash="dash", line_color="#adb5bd", line_width=1.5, row=1, col=1)

    # Trace 2: RS Momentum (Bottom Plot)
    fig.add_trace(
        go.Scatter(
            x=sub["Date"], y=sub["RS_Momentum"], 
            name="RS Momentum", line=dict(color="#fd7e14", width=1.5),
            showlegend=False
        ),
        row=2, col=1
    )
    # Zero-momentum pivot line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="#adb5bd", line_width=1.5, row=2, col=1)

    fig.update_layout(
        height=480,
        title=dict(text=f"{sector} \u2014 Relative Strength Decomposition", font_size=16),
        margin=dict(l=60, r=40, t=60, b=40),
        plot_bgcolor="white",
        hovermode="x unified"
    )

    # Configure axes formatting and grid lines
    fig.update_yaxes(title_text="Ratio", gridcolor="#e9ecef", row=1, col=1)
    fig.update_yaxes(title_text="Momentum", gridcolor="#e9ecef", row=2, col=1)
    fig.update_xaxes(gridcolor="#e9ecef", row=1, col=1)
    fig.update_xaxes(title_text="Date", gridcolor="#e9ecef", row=2, col=1)

    return fig


layout = dbc.Container(
    [
        dcc.Store(id="sector-rotation-rsdf-store", data=RS_DF.to_json(date_format="iso", orient="split")),

        dbc.Row([
            dbc.Col([
                html.H2("Sector Rotation Analysis", className="fw-bold mt-4"),
                html.P(
                    "Relative Rotation Graphs evaluate sector strength against the broader market. "
                    "The X-axis measures trend strength (RS Ratio), while the Y-axis measures directional "
                    "velocity (RS Momentum). Click any sector dot to inspect its historical drill-down.",
                    className="text-muted mb-4",
                ),
            ])
        ]),

        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Time Horizon", className="fw-semibold me-3"),
                        dcc.RadioItems(
                            id="rrg-time-window",
                            options=[{"label": f"  {k}", "value": k} for k in TIME_WINDOWS],
                            value="1Y",
                            inline=True,
                            inputClassName="me-1 ms-3",
                            labelClassName="me-2 cursor-pointer",
                        ),
                    ], className="d-flex align-items-center mb-3")
                ]),
                dcc.Loading(
                    dcc.Graph(id="rrg-plot", figure=create_rrg_plot(ANIM_DF, window="1Y"), clear_on_unhover=True),
                    type="circle", color="#0d6efd"
                ),
            ])
        ], className="shadow-sm mb-4 border-0"),

        dbc.Card([
            dbc.CardBody([
                html.H5("Sector Deep Dive", className="fw-bold mb-3"),
                dcc.Loading(
                    dcc.Graph(id="rrg-sector-history", figure=create_sector_history_chart(RS_DF, None)),
                    type="circle", color="#0d6efd"
                ),
            ])
        ], className="shadow-sm mb-5 border-0"),
    ],
    fluid=True,
    className="px-4"
)


def register_callbacks():
    @callback(
        Output("rrg-plot", "figure"),
        Output("sector-rotation-rsdf-store", "data"),
        Input("rrg-time-window", "value"),
        Input("start-date-filter", "value"),
        Input("end-date-filter", "value"),
    )
    def update_time_window(window, start_date, end_date):
        """Recomputes the RRG pipeline when the zoom window or the sidebar's
        Date filter changes. (Sector/Company filters aren't applied here --
        the RRG's whole purpose is comparing sectors against each other and
        the market, so narrowing to one sector or company would remove the
        comparison.)"""
        pipeline = run_sector_rotation_pipeline(
            weighting="return", freq="W", start_date=start_date, end_date=end_date
        )
        rs_df = pipeline["rs_df"]
        anim_df = pipeline["anim_df"]
        rs_df_json = rs_df.to_json(date_format="iso", orient="split")
        return create_rrg_plot(anim_df, window=window), rs_df_json

    @callback(
        Output("rrg-sector-history", "figure"),
        Input("rrg-plot", "clickData"),
        Input("sector-rotation-rsdf-store", "data"),
    )
    def update_sector_history(click_data, rs_df_json):
        rs_df = pd.read_json(io.StringIO(rs_df_json), orient="split")
        rs_df["Date"] = pd.to_datetime(rs_df["Date"])

        if not click_data or not click_data.get("points"):
            return create_sector_history_chart(rs_df, None)

        sector = click_data["points"][0].get("hovertext")
        return create_sector_history_chart(rs_df, sector)


register_callbacks()