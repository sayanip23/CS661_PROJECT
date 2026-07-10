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
from utils.config import DEFAULT_N_CLUSTERS, DEFAULT_LINKAGE_METHOD, get_corr_colorscale, MODEBAR_CONFIG, ThemeManager

dash.register_page(__name__, path="/correlation")


from utils.database import run_query

# ---------------------------------------------------------------------------
# Load + run the analytics pipeline once at import time.
# We no longer run the heavy pipeline on import. We only fetch the unique 
# companies for the dropdown using a fast SQL query.
# ---------------------------------------------------------------------------
def _get_all_companies():
    query = "SELECT DISTINCT Company FROM clean_stock_data ORDER BY Company"
    return run_query(query)["Company"].tolist()

try:
    ALL_COMPANIES = _get_all_companies()
except Exception:
    ALL_COMPANIES = []



# ---------------------------------------------------------------------------
# create_heatmap()
# ---------------------------------------------------------------------------
def create_heatmap(clustered_matrix, order, theme="dark"):
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
            colorscale=get_corr_colorscale(theme),
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
        template=f"financial_{theme}"
    )

    return fig


# ---------------------------------------------------------------------------
# create_dendrogram()
# ---------------------------------------------------------------------------
def create_dendrogram(cluster_result, theme="dark"):
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
        plot_color = MPL_COLOR_MAP.get(color, color if str(color).startswith("#") else ThemeManager.get_colors(theme)["text_secondary"])
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
        template=f"financial_{theme}"
    )

    return fig


# ---------------------------------------------------------------------------
# create_time_series()
# ---------------------------------------------------------------------------
def create_time_series(df, selected_companies, theme="dark"):
    """
    Multi-line time series of closing prices for the given list of
    company names. Shows a placeholder message if none are selected.
    """
    fig = go.Figure()

    if not selected_companies:
        fig.update_layout(
            height=350,
            margin=dict(l=60, r=20, t=30, b=40),
            template=f"financial_{theme}",
            annotations=[
                dict(
                    text="Drag-select a region on the heatmap above (or use the dropdown) "
                         "to compare closing prices of specific stocks.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=13, color=ThemeManager.get_colors(theme)["text_secondary"]),
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
        template=f"financial_{theme}"
    )

    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout = dbc.Container(
    [
        html.H2("Clustered Correlation Matrix Heatmap", className="fw-bold mt-3"),
        html.Div(id="correlation-smart-narrative"),
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
                        html.Label("Number of Clusters", className="fw-bold mb-2"),
                        html.Div([
                            html.Span("2", className="static-bound-label text-muted fw-bold small me-2"),
                            dcc.Slider(
                                id="n-clusters-slider",
                                min=2,
                                max=10,
                                step=1,
                                value=DEFAULT_N_CLUSTERS,
                                marks={i: {"label": str(i), "style": {"color": "#9499a6", "fontSize": "14px", "fontWeight": "600"}} for i in range(2, 11)},
                                className="slider-track flex-grow-1 mx-3"
                            ),
                            dcc.Input(id="n-clusters-box", type="number", min=2, max=10, step=1, value=DEFAULT_N_CLUSTERS, className="form-control text-center p-0 me-2", style={"width": "55px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "28px", "fontSize": "13px"}),
                            html.Span("10", className="static-bound-label text-muted fw-bold small"),
                        ], className="slider-wrapper", style={"display": "flex", "alignItems": "center"}),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        html.Label("Or pick companies directly", className="fw-bold"),
                        dcc.Dropdown(
                            id={"type": "company-selector", "index": "main"},
                            options=[{"label": c, "value": c} for c in ALL_COMPANIES],
                            value=[],
                            multi=True,
                            placeholder="Select companies to plot...",
                        ),
                    ],
                    md=6,
                ),
            ],
            className="shadow-sm rounded-4 border-0 mb-4 bg-surface p-4",
        ),

        html.Div(
            [
                dcc.Loading(dcc.Graph(id="correlation-dendrogram", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)"),
                dcc.Loading(dcc.Graph(id="correlation-heatmap", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)"),
            ],
            className="card shadow-sm border-0 bg-surface mb-4"
        ),

        html.Hr(),
        html.H4("Closing Price Comparison", className="fw-bold"),
        html.Div(
            [
                dcc.Loading(dcc.Graph(id="correlation-time-series", config=MODEBAR_CONFIG), type="circle", color="var(--accent-primary)")
            ],
            className="card shadow-sm border-0 bg-surface p-3"
        ),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@callback(
    Output("correlation-heatmap", "figure"),
    Output("correlation-dendrogram", "figure"),
    Input("n-clusters-slider", "value"),
    Input("theme-store", "data")
)
def update_clustering(n_clusters, theme):
    """Re-clusters (sklearn) and recolors the dendrogram (scipy) when the
    slider changes. Leaf order stays stable since it comes from the
    linkage matrix, not from the chosen number of flat clusters."""
    import plotly.express as px
    import plotly.graph_objects as go
    
    result = run_correlation_pipeline(n_clusters=n_clusters, linkage_method=DEFAULT_LINKAGE_METHOD)
    
    if "order" not in result["cluster_result"]:
        empty_fig = go.Figure().update_layout(title="No data available", xaxis_visible=False, yaxis_visible=False)
        return empty_fig, empty_fig

    order = result["cluster_result"]["order"]

    heatmap_fig = create_heatmap(result["clustered_matrix"], order, theme)
    dendrogram_fig = create_dendrogram(result["cluster_result"], theme)

    return heatmap_fig, dendrogram_fig

from dash import ALL

@callback(
    Output({"type": "company-selector", "index": ALL}, "value"),
    Output("global-state", "data", allow_duplicate=True),
    Input("correlation-heatmap", "selectedData", allow_optional=True),
    Input("global-state", "data"),
    State({"type": "company-selector", "index": ALL}, "value", allow_optional=True),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def heatmap_brush_to_dropdown(selected_data, global_state, current_value_list, pathname):
    if pathname != "/correlation":
        raise dash.exceptions.PreventUpdate
        
    current_value = current_value_list[0] if current_value_list else []
        
    if not global_state: global_state = {"sectors": [], "companies": []}
    
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "global-state":
        # Merge global companies into current selection
        combined = list(set((current_value or []) + global_state.get("companies", [])))
        return [combined], dash.no_update

    # Otherwise triggered by heatmap selection
    if not selected_data or "points" not in selected_data or not selected_data["points"]:
        return [current_value or []], dash.no_update

    companies = set(current_value or [])
    for point in selected_data["points"]:
        companies.add(point["x"])
        companies.add(point["y"])
        
    updated = list(companies)
    return [updated], global_state

@callback(
    Output("correlation-time-series", "figure"),
    Output("correlation-smart-narrative", "children"),
    Input({"type": "company-selector", "index": ALL}, "value"),
    Input("theme-store", "data")
)
def update_time_series(company_selections, theme):
    from components.narrative import generate_smart_narrative
    
    selected_companies = company_selections[0] if company_selections else []
    
    result = run_correlation_pipeline(
        n_clusters=DEFAULT_N_CLUSTERS, linkage_method=DEFAULT_LINKAGE_METHOD
    )
    
    fig = create_time_series(result["raw_df"], selected_companies, theme)
    
    # Generate Narrative
    subset_df = result["raw_df"]
    if selected_companies:
        subset_df = subset_df[subset_df["Company"].isin(selected_companies)]
    narrative = generate_smart_narrative(subset_df, context="correlation")
    return fig, narrative

dash.clientside_callback(
    "function(val, box) {\n"
    "    const ctx = dash_clientside.callback_context;\n"
    "    if (!ctx.triggered.length) return [val, val];\n"
    "    const trigger = ctx.triggered[0].prop_id;\n"
    "    if (trigger === 'n-clusters-slider.value') {\n"
    "        return [val, dash_clientside.no_update];\n"
    "    } else {\n"
    "        let v = parseInt(box) || 5;\n"
    "        if (v < 2) v = 2;\n"
    "        if (v > 10) v = 10;\n"
    "        return [dash_clientside.no_update, v];\n"
    "    }\n"
    "}",
    Output("n-clusters-box", "value"),
    Output("n-clusters-slider", "value"),
    Input("n-clusters-slider", "value"),
    Input("n-clusters-box", "value")
)

