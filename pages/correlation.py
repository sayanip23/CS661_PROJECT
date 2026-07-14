"""
pages/correlation.py

Task 4.1 — Clustered Correlation Matrix Heatmap with Dendrograms.

Layout:
    - Top:    Dendrogram (column order matches the heatmap below it)
    - Middle: Plotly heatmap of clustered stock-return correlations
              (blue = negative, white = zero, red = positive)
    - Controls: company dropdown
    - Bottom: Multi-line time series of closing prices for whichever
              stocks are selected (via box-select/"brushing" on the
              heatmap, or via the dropdown)
"""

from collections import Counter

import dash
from dash import html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from scipy.cluster.hierarchy import dendrogram as scipy_dendrogram, fcluster

from utils.analytics.correlation import run_correlation_pipeline, load_clean_data

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

# Colorblind-safe qualitative palette (ColorBrewer Dark2, extended with two
# more distinct hues) for tagging genuinely distinct correlation clusters in
# the dendrogram. Links that don't belong to any single multi-stock cluster
# (singleton stocks, or the backbone connecting separate clusters together)
# get this neutral gray instead.
DENDROGRAM_NEUTRAL_COLOR = "#B0B7C3"
DENDROGRAM_PALETTE = [
    "#1b9e77", "#d95f02", "#7570b3", "#e7298a",
    "#66a61e", "#e6ab02", "#a6761d", "#666666",
    "#08519c", "#54278f",
]

# Diverging colorscale: blue (negative) -> white (zero) -> red (positive)
CORR_COLORSCALE = [
    [0.0, "rgb(33,102,172)"],
    [0.25, "rgb(103,169,207)"],
    [0.5, "rgb(247,247,247)"],
    [0.75, "rgb(239,138,98)"],
    [1.0, "rgb(178,24,43)"],
]


# ---------------------------------------------------------------------------
# _empty_message_figure()
# ---------------------------------------------------------------------------
def _empty_message_figure(text):
    fig = go.Figure()
    fig.update_layout(
        height=400,
        annotations=[dict(
            text=text, xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#6c757d"),
        )],
    )
    return fig


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
            colorbar=dict(title="Correlation", thickness=15, x=1.02, len=0.85),
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
        margin=dict(l=140, r=80, t=10, b=40),
        height=650,
    )

    return fig


# ---------------------------------------------------------------------------
# _build_cluster_link_color_func()
# ---------------------------------------------------------------------------
def _build_cluster_link_color_func(linkage_matrix, threshold):
    """
    Colors each dendrogram link by which single, genuine correlation cluster
    (computed via `fcluster` at this same cut height) all of its descendant
    leaves belong to.

    This intentionally bypasses scipy's own automatic color-tag cycling:
    scipy only has ~10 built-in tag names ('C0'..'C9'), and once there are
    more distinct clusters below the cut than that, it silently reuses a tag
    -- making two completely unrelated stock clusters render as the exact
    same color. Computing membership ourselves guarantees a 1-to-1 mapping
    between real clusters and colors, however many there are.
    """
    n_leaves = linkage_matrix.shape[0] + 1
    flat = fcluster(linkage_matrix, t=threshold, criterion="distance")

    # Cluster-id set covered by each node's descendant leaves (leaves first,
    # then internal merge nodes in linkage-matrix order).
    node_clusters = {i: {int(flat[i])} for i in range(n_leaves)}
    for i, (a, b, _dist, _cnt) in enumerate(linkage_matrix):
        node_clusters[n_leaves + i] = node_clusters[int(a)] | node_clusters[int(b)]

    sizes = Counter(flat)
    real_cluster_ids = sorted(cid for cid, sz in sizes.items() if sz > 1)
    color_for_cluster = {
        cid: DENDROGRAM_PALETTE[idx % len(DENDROGRAM_PALETTE)]
        for idx, cid in enumerate(real_cluster_ids)
    }

    def link_color_func(node_id):
        clusters_below = node_clusters[node_id]
        if len(clusters_below) == 1:
            only_cluster = next(iter(clusters_below))
            if only_cluster in color_for_cluster:
                return color_for_cluster[only_cluster]
        return DENDROGRAM_NEUTRAL_COLOR

    return link_color_func


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

    threshold = 0.7 * max(linkage_matrix[:, 2])
    link_color_func = _build_cluster_link_color_func(linkage_matrix, threshold)

    dendro = scipy_dendrogram(
        linkage_matrix,
        labels=companies,
        no_plot=True,
        link_color_func=link_color_func,
    )

    fig = go.Figure()

    # scipy places leaves at x = 5, 15, 25, ... -> rescale to 0, 1, 2, ...
    # so it lines up with the heatmap's categorical x positions. color_list
    # entries are already final hex colors here (from link_color_func above),
    # not matplotlib-style codes, so no translation step is needed.
    for icoord, dcoord, color in zip(dendro["icoord"], dendro["dcoord"], dendro["color_list"]):
        x = [(v / 10.0) - 0.5 for v in icoord]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=dcoord,
                mode="lines",
                line=dict(color=color, width=2.5),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    n = len(dendro["ivl"])
    fig.update_xaxes(
        range=[-0.5, n - 0.5],
        tickmode="array",
        tickvals=list(range(n)),
        ticktext=dendro["ivl"],      # company names
        tickangle=90,
        tickfont=dict(size=10),
        showgrid=False,
        zeroline=False,
    )
    fig.update_yaxes(
        title="Correlation Distance (1 − r)",
        showgrid=False,
        zeroline=False,
    )

    fig.update_layout(
      title={
        "text": "Hierarchical Clustering of Stocks",
        "x": 0.5,
        "xanchor": "center"
      },
      margin=dict(l=170, r=40, t=60, b=170),
      height=500,
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
                        html.Label("Pick companies to compare", className="fw-bold"),
                        dcc.Dropdown(
                            id="company-selector",
                            options=[{"label": c, "value": c} for c in ALL_COMPANIES],
                            value=[],
                            multi=True,
                            placeholder="Select companies to plot...",
                        ),
                    ],
                    md=12,
                ),
            ],
            className="mb-3",
        ),

        # ============================================================
# Hierarchical Clustering (Dendrogram)
# ============================================================

dbc.Card(

    dbc.CardBody([

        html.H4(
            "Hierarchical Clustering of Stocks",
            className="fw-bold mb-3"
        ),

        html.P(
            "Stocks that merge at lower heights exhibit more similar daily-return behaviour.",
            className="text-muted"
        ),

        dcc.Loading(
            dcc.Graph(
                id="correlation-dendrogram",
                config={"displayModeBar": False}
            )
        )

    ]),

    className="shadow-sm mb-4"

),

# ============================================================
# Clustered Correlation Heatmap
# ============================================================

dbc.Card(

    dbc.CardBody([

        html.H4(
            "Clustered Correlation Matrix",
            className="fw-bold mb-3"
        ),

        dcc.Loading(
            dcc.Graph(
                id="correlation-heatmap",
                config={"displayModeBar": True}
            )
        )

    ]),

    className="shadow-sm mb-4"

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
        Input("start-date-filter", "value"),
        Input("end-date-filter", "value"),
        Input("sector-filter", "value"),
    )
    def update_clustering(start_date, end_date, sector):
        """Re-clusters (sklearn) and recolors the dendrogram (scipy) when the
        sidebar's Date/Sector filters change. Leaf order stays stable since it
        comes from the linkage matrix, not from the fixed cluster count.
        (The Company filter isn't applied here -- correlating a single stock
        against itself is meaningless.)"""
        try:
            result = run_correlation_pipeline(
                n_clusters=DEFAULT_N_CLUSTERS, linkage_method=DEFAULT_LINKAGE,
                start_date=start_date, end_date=end_date, sector=sector,
            )
        except ValueError as e:
            empty = _empty_message_figure(str(e))
            return empty, empty

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
        Input("start-date-filter", "value"),
        Input("end-date-filter", "value"),
    )
    def update_time_series(selected_companies, start_date, end_date):
        if not selected_companies:
            return create_time_series(RAW_DF, [])
        df = load_clean_data(start_date=start_date, end_date=end_date)
        return create_time_series(df, selected_companies)


register_callbacks()
