"""
pages/correlation.py

Task 4.1 — Clustered Correlation Matrix Heatmap with Dendrograms.

Layout:
    - Top:    Dendrogram (column order matches the heatmap below it)
    - Middle: Plotly heatmap of clustered stock-return correlations
              (blue = negative, white = zero, red = positive)
    - Controls: number-of-clusters slider, company dropdown
    - Bottom: Multi-line time series of closing prices for whichever
              stocks are selected (via box-select/"brushing" on the
              heatmap, or via the dropdown)
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from scipy.cluster.hierarchy import dendrogram as scipy_dendrogram

from utils.analytics.correlation import run_correlation_pipeline

dash.register_page(__name__, path="/correlation")


# ---------------------------------------------------------------------------
# Load + run the analytics pipeline once at import time.
# The underlying dataset is static, so there's no need to recompute the
# full correlation/clustering pipeline on every callback.
# ---------------------------------------------------------------------------
PIPELINE = run_correlation_pipeline(n_clusters=5, linkage_method="average")

RAW_DF = PIPELINE["raw_df"]
ALL_COMPANIES = sorted(RAW_DF["Company"].unique())

DEFAULT_N_CLUSTERS = 5
DEFAULT_LINKAGE = "average"

# Diverging colorscale: blue (negative) -> white (zero) -> red (positive)
CORR_COLORSCALE = [
    [0.0, "rgb(33,102,172)"],
    [0.25, "rgb(103,169,207)"],
    [0.5, "rgb(247,247,247)"],
    [0.75, "rgb(239,138,98)"],
    [1.0, "rgb(178,24,43)"],
]


# ---------------------------------------------------------------------------
# create_heatmap()
# ---------------------------------------------------------------------------
def create_heatmap(clustered_matrix, order):
    """
    Builds the Plotly heatmap of the (dendrogram-reordered) correlation
    matrix. Stocks x stocks, colored blue (negative) -> white (zero) ->
    red (positive).
    """
    z = clustered_matrix.values

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=order,
            y=order,
            colorscale=CORR_COLORSCALE,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorbar=dict(title="Correlation", thickness=15),
            hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.2f}<extra></extra>",
        )
    )

    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=order,
        tickangle=90,
        tickfont=dict(size=9),
    )
    fig.update_yaxes(
        type="category",
        categoryorder="array",
        categoryarray=order,
        autorange="reversed",
        tickfont=dict(size=9),
    )

    fig.update_layout(
        dragmode="select",
        margin=dict(l=140, r=20, t=10, b=140),
        height=650,
    )

    return fig


# ---------------------------------------------------------------------------
# create_dendrogram()
# ---------------------------------------------------------------------------
def create_dendrogram(cluster_result):
    """
    Builds a Plotly line-segment dendrogram from the scipy linkage matrix,
    using the same leaf order as the heatmap so the two stay visually
    aligned (marginal dendrogram on top of the heatmap).
    """
    linkage_matrix = cluster_result["linkage_matrix"]
    companies = cluster_result["companies"]

    dendro = scipy_dendrogram(
        linkage_matrix,
        labels=companies,
        no_plot=True,
        color_threshold=0.7 * max(linkage_matrix[:, 2]),
    )

    fig = go.Figure()

    # scipy returns matplotlib-style short codes ('C0', 'C1', ...) which are
    # not valid Plotly/CSS colors -> map them to actual hex values.
    MPL_COLOR_MAP = {
        "C0": "#1f77b4", "C1": "#ff7f0e", "C2": "#2ca02c", "C3": "#d62728",
        "C4": "#9467bd", "C5": "#8c564b", "C6": "#e377c2", "C7": "#7f7f7f",
        "C8": "#bcbd22", "C9": "#17becf",
        "b": "#1f77b4", "g": "#2ca02c", "r": "#d62728", "c": "#17becf",
        "m": "#9467bd", "y": "#bcbd22", "k": "#333333",
    }

    # scipy places leaves at x = 5, 15, 25, ... -> rescale to 0, 1, 2, ...
    # so it lines up with the heatmap's categorical x positions.
    for icoord, dcoord, color in zip(dendro["icoord"], dendro["dcoord"], dendro["color_list"]):
        x = [(v / 10.0) - 0.5 for v in icoord]
        plot_color = MPL_COLOR_MAP.get(color, color if str(color).startswith("#") else "#333333")
        fig.add_trace(
            go.Scatter(
                x=x,
                y=dcoord,
                mode="lines",
                line=dict(color=plot_color, width=1.5),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    n = len(dendro["ivl"])
    fig.update_xaxes(
        range=[-0.5, n - 0.5],
        showticklabels=False,
        showgrid=False,
        zeroline=False,
    )
    fig.update_yaxes(
        title="Distance (1 - correlation)",
        showgrid=False,
        zeroline=False,
    )

    fig.update_layout(
        margin=dict(l=140, r=20, t=20, b=0),
        height=220,
        showlegend=False,
    )

    return fig


# ---------------------------------------------------------------------------
# create_time_series()
# ---------------------------------------------------------------------------
def create_time_series(df, selected_companies):
    """
    Multi-line time series of closing prices for the given list of
    company names. Shows a placeholder message if none are selected.
    """
    fig = go.Figure()

    if not selected_companies:
        fig.update_layout(
            height=350,
            margin=dict(l=60, r=20, t=30, b=40),
            annotations=[
                dict(
                    text="Drag-select a region on the heatmap above (or use the dropdown) "
                         "to compare closing prices of specific stocks.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=13, color="gray"),
                )
            ],
        )
        return fig

    subset = df[df["Company"].isin(selected_companies)]

    for company, group in subset.groupby("Company"):
        fig.add_trace(
            go.Scatter(
                x=group["Date"],
                y=group["Close"],
                mode="lines",
                name=company,
            )
        )

    fig.update_layout(
        height=350,
        margin=dict(l=60, r=20, t=30, b=40),
        xaxis_title="Date",
        yaxis_title="Closing Price",
        legend=dict(orientation="h", y=1.02, x=0),
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout = dbc.Container(
    [
        html.H2("Clustered Correlation Matrix Heatmap", className="fw-bold mt-3"),
        html.P(
            "Hierarchical clustering groups stocks with similar daily-return behavior, "
            "avoiding the 'hairball' of a force-directed graph. Drag-select a block of "
            "cells on the heatmap (or use the dropdown) to compare closing prices below.",
            className="text-muted",
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Number of Clusters", className="fw-bold"),
                        dcc.Slider(
                            id="n-clusters-slider",
                            min=2,
                            max=10,
                            step=1,
                            value=DEFAULT_N_CLUSTERS,
                            marks={i: str(i) for i in range(2, 11)},
                        ),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        html.Label("Or pick companies directly", className="fw-bold"),
                        dcc.Dropdown(
                            id="company-selector",
                            options=[{"label": c, "value": c} for c in ALL_COMPANIES],
                            value=[],
                            multi=True,
                            placeholder="Select companies to plot...",
                        ),
                    ],
                    md=6,
                ),
            ],
            className="mb-3",
        ),

        dcc.Loading(
            dcc.Graph(id="correlation-dendrogram", config={"displayModeBar": False}),
        ),
        dcc.Loading(
            dcc.Graph(id="correlation-heatmap", config={"displayModeBar": True}),
        ),

        html.Hr(),
        html.H4("Closing Price Comparison", className="fw-bold"),
        dcc.Loading(
            dcc.Graph(id="correlation-time-series"),
        ),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# register_callbacks()
# ---------------------------------------------------------------------------
def register_callbacks():

    @callback(
        Output("correlation-heatmap", "figure"),
        Output("correlation-dendrogram", "figure"),
        Input("n-clusters-slider", "value"),
    )
    def update_clustering(n_clusters):
        """Re-clusters (sklearn) and recolors the dendrogram (scipy) when the
        slider changes. Leaf order stays stable since it comes from the
        linkage matrix, not from the chosen number of flat clusters."""
        result = run_correlation_pipeline(n_clusters=n_clusters, linkage_method=DEFAULT_LINKAGE)
        order = result["cluster_result"]["order"]

        heatmap_fig = create_heatmap(result["clustered_matrix"], order)
        dendrogram_fig = create_dendrogram(result["cluster_result"])

        return heatmap_fig, dendrogram_fig

    @callback(
        Output("company-selector", "value"),
        Input("correlation-heatmap", "selectedData"),
        State("company-selector", "value"),
        prevent_initial_call=True,
    )
    def heatmap_brush_to_dropdown(selected_data, current_value):
        """Box-selecting (brushing) a block of cells on the heatmap pushes
        the involved company names into the dropdown, which in turn drives
        the time-series chart below."""
        if not selected_data or "points" not in selected_data or not selected_data["points"]:
            return current_value or []

        companies = set()
        for point in selected_data["points"]:
            companies.add(point["x"])
            companies.add(point["y"])

        return sorted(companies)

    @callback(
        Output("correlation-time-series", "figure"),
        Input("company-selector", "value"),
    )
    def update_time_series(selected_companies):
        return create_time_series(RAW_DF, selected_companies or [])


register_callbacks()
