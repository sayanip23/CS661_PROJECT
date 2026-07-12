"""
pages/treemap.py

Task 4.5 — Sector-Level Growth Attribution.

Single-screen layout:
    - Compact toolbar: title, filters popover, fullscreen toggle, period label
    - Thin KPI chip strip
    - Treemap/Sunburst (left) + detail chart (right), both fill 100% of the
      remaining viewport height. Hovering a pane grows it, shrinks the other.
"""

import dash
from dash import html, dcc, Input, Output, State, callback, clientside_callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from utils.analytics.treemap import (
    run_treemap_pipeline,
    load_clean_data,
    filter_by_date_range,
    ROOT_ID,
)

dash.register_page(__name__, path="/treemap")

PIPELINE = run_treemap_pipeline()
MIN_YEAR, MAX_YEAR = PIPELINE["year_bounds"]
YEAR_MARKS = {MIN_YEAR: str(MIN_YEAR), MAX_YEAR: str(MAX_YEAR)}

GROWTH_COLORSCALE = "Viridis"  # colorblind-safe: monotonic luminance


# ---------------------------------------------------------------------------
# create_growth_figure()
# ---------------------------------------------------------------------------
def create_growth_figure(hierarchy_df: pd.DataFrame, chart_type: str, size_metric: str) -> go.Figure:
    cagr = hierarchy_df["cagr"]
    customdata = list(zip(cagr, hierarchy_df["hover_extra"]))
    metric_label = size_metric.replace("_", " ")

    lo, hi = cagr.min(), cagr.max()
    span = (hi - lo) or 1.0
    text_colors = ["white" if (v - lo) / span < 0.6 else "black" for v in cagr]

    marker = dict(
        colors=cagr,
        colorscale=GROWTH_COLORSCALE,
        colorbar=dict(title="CAGR", tickformat=".0%", thickness=10, len=0.75),
        line=dict(width=1, color="white"),
    )

    common = dict(
        ids=hierarchy_df["id"],
        labels=hierarchy_df["label"],
        parents=hierarchy_df["parent"],
        values=hierarchy_df["value"],
        branchvalues="total",
        customdata=customdata,
        texttemplate="%{label}<br>%{customdata[0]:+.0%}",
        textfont=dict(color=text_colors),
        hovertemplate=(
            "<b>%{label}</b><br>CAGR %{customdata[0]:+.1%} · "
            f"{metric_label} " + "%{value:,.0f}<extra></extra>"
        ),
        marker=marker,
    )

    if chart_type == "sunburst":
        fig = go.Figure(go.Sunburst(**common, maxdepth=3, insidetextorientation="radial"))
    else:
        fig = go.Figure(go.Treemap(
            **common, maxdepth=3, root=dict(color="#eeeeee"),
            tiling=dict(packing="squarify"),
        ))

    fig.update_layout(margin=dict(l=4, r=4, t=4, b=4), autosize=True)
    return fig


# ---------------------------------------------------------------------------
# create_sector_bar_figure()
# ---------------------------------------------------------------------------
def create_sector_bar_figure(sector_name: str, company_growth: pd.DataFrame) -> go.Figure:
    subset = company_growth[company_growth["Sector"] == sector_name].sort_values("CAGR")

    fig = go.Figure(go.Bar(
        x=subset["CAGR"],
        y=subset["Company"],
        orientation="h",
        marker=dict(color=subset["CAGR"], colorscale=GROWTH_COLORSCALE),
        text=[f"{v:+.0%}" for v in subset["CAGR"]],
        textposition="outside",
        hovertemplate="%{y} · %{x:+.1%}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_tickformat=".0%",
        margin=dict(l=110, r=30, t=10, b=20),
        autosize=True,
    )
    return fig


def create_all_sector_comparison_figure(company_growth: pd.DataFrame) -> go.Figure:
    sector_growth = (
        company_growth.groupby("Sector", as_index=False)
        .agg(CAGR=("CAGR", "mean"), Num_Companies=("Company", "nunique"))
        .sort_values("CAGR")
    )

    fig = go.Figure(go.Bar(
        x=sector_growth["CAGR"],
        y=sector_growth["Sector"],
        orientation="h",
        marker=dict(color=sector_growth["CAGR"], colorscale=GROWTH_COLORSCALE),
        text=[f"{v:+.0%}" for v in sector_growth["CAGR"]],
        textposition="outside",
        customdata=sector_growth[["Num_Companies"]],
        hovertemplate="%{y} · %{x:+.1%}<br>%{customdata[0]} companies<extra></extra>",
    ))
    fig.update_layout(
        xaxis_tickformat=".0%",
        margin=dict(l=110, r=30, t=10, b=20),
        autosize=True,
    )
    return fig


# ---------------------------------------------------------------------------
# create_company_price_figure()
# ---------------------------------------------------------------------------
def create_company_price_figure(company_name: str, price_df: pd.DataFrame, cagr: float) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=price_df["Date"], y=price_df["Close"], mode="lines",
        line=dict(color="#443983"),
    ))
    fig.update_layout(margin=dict(l=50, r=20, t=10, b=20), autosize=True)
    return fig


def _kpi_chip(icon, label, value, variant):
    return html.Span(
        [
            html.I(className=f"bi {icon} me-1"),
            html.Span(f"{label} ", className="growth-chip-label"),
            html.B(value),
        ],
        className=f"growth-kpi-chip bg-{variant}-subtle text-{variant}-emphasis border border-{variant}-subtle",
    )


def build_kpi_strip(company_growth: pd.DataFrame, sector_growth: pd.DataFrame):
    top_gainer = company_growth.loc[company_growth["CAGR"].idxmax()]
    top_loser = company_growth.loc[company_growth["CAGR"].idxmin()]
    top_sector = sector_growth.loc[sector_growth["CAGR"].idxmax()]

    return html.Div(
        [
            _kpi_chip("bi-rocket-takeoff-fill", "Best", top_gainer["Company"], "success"),
            _kpi_chip("bi-graph-down-arrow", "Worst", top_loser["Company"], "danger"),
            _kpi_chip("bi-award-fill", "Top sector", top_sector["Sector"], "primary"),
        ],
        className="growth-kpi-bar",
    )


def serialize_company_growth(company_growth: pd.DataFrame) -> list:
    out = company_growth.copy()
    out["Start_Date"] = out["Start_Date"].dt.strftime("%Y-%m-%d")
    out["End_Date"] = out["End_Date"].dt.strftime("%Y-%m-%d")
    return out.to_dict("records")


def _pane(pane_id, title, graph_id, figure):
    return html.Div(
        [
            html.Div(title, className="growth-pane-title", id=f"{pane_id}-title"),
            html.Div(
                dcc.Loading(dcc.Graph(
                    id=graph_id, figure=figure,
                    style={"height": "100%", "width": "100%"},
                    config={"displayModeBar": False, "responsive": True},
                )),
                className="growth-pane-body",
            ),
        ],
        className="growth-pane", id=pane_id,
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
default_sector = PIPELINE["sector_growth"].loc[PIPELINE["sector_growth"]["CAGR"].idxmax(), "Sector"]

controls_popover = html.Div(
    [
        dbc.Button(
            [html.I(className="bi bi-sliders me-1"), "Filters"],
            id="growth-controls-btn", color="light", size="sm",
            className="growth-toolbar-btn border",
        ),
        dbc.Popover(
            dbc.PopoverBody(
                [
                    html.Div("Chart", className="growth-control-label"),
                    dbc.RadioItems(
                        id="chart-type-toggle",
                        options=[{"label": "Treemap", "value": "treemap"},
                                 {"label": "Sunburst", "value": "sunburst"}],
                        value="treemap", inline=True,
                        inputClassName="btn-check", labelClassName="btn btn-outline-primary btn-sm",
                        labelCheckedClassName="active", className="btn-group mb-2",
                    ),
                    html.Div("Size by", className="growth-control-label"),
                    dbc.RadioItems(
                        id="size-metric-toggle",
                        options=[{"label": "Volume", "value": "Total_Volume"},
                                 {"label": "Turnover", "value": "Total_Turnover"}],
                        value="Total_Volume", inline=True,
                        inputClassName="btn-check", labelClassName="btn btn-outline-primary btn-sm",
                        labelCheckedClassName="active", className="btn-group mb-2",
                    ),
                    html.Div("Period", className="growth-control-label"),
                    dcc.RangeSlider(
                        id="year-range-slider", min=MIN_YEAR, max=MAX_YEAR, step=1,
                        value=[MIN_YEAR, MAX_YEAR], marks=YEAR_MARKS,
                        tooltip={"placement": "bottom"},
                    ),
                ],
                className="growth-popover-body",
            ),
            id="growth-controls-popover", target="growth-controls-btn",
            trigger="legacy", placement="bottom-end",
        ),
    ],
    className="d-inline-block",
)

toolbar = dbc.Row(
    [
        dbc.Col(
            [
                html.Span("Sector Growth Attribution", className="growth-toolbar-title"),
                html.Span("NIFTY-50 · CAGR & Volume", className="growth-toolbar-subtitle"),
            ],
            width="auto",
        ),
        dbc.Col(controls_popover, width="auto"),
        dbc.Col(
            dbc.Button(html.I(className="bi bi-arrows-fullscreen"), id="growth-fullscreen-btn",
                       color="light", size="sm", className="growth-toolbar-btn border"),
            width="auto",
        ),
        dbc.Col(html.Div(id="year-range-label", className="growth-period-label"), className="text-end"),
    ],
    align="center", justify="between", className="growth-toolbar g-2",
)

layout = dbc.Container(
    [
        dcc.Store(id="growth-data-store", data=serialize_company_growth(PIPELINE["company_growth"])),

        html.Div(
            [
                toolbar,
                html.Div(id="kpi-strip-container", children=build_kpi_strip(
                    PIPELINE["company_growth"], PIPELINE["sector_growth"]
                )),
                html.Div(
                    [
                        _pane(
                            "pane-treemap", "Sectors → companies", "growth-treemap-chart",
                            create_growth_figure(PIPELINE["hierarchy"], "treemap", "Total_Volume"),
                        ),
                        _pane(
                            "pane-detail", "All sector comparison", "growth-detail-graph",
                            create_all_sector_comparison_figure(PIPELINE["company_growth"]),
                        ),
                    ],
                    className="growth-split",
                ),
            ],
            id="growth-fullscreen-target",
            className="growth-fullscreen-target",
        ),
    ],
    fluid=True,
)


# ---------------------------------------------------------------------------
# register_callbacks()
# ---------------------------------------------------------------------------
def register_callbacks():

    @callback(
        Output("growth-treemap-chart", "figure"),
        Output("growth-data-store", "data"),
        Output("kpi-strip-container", "children"),
        Output("year-range-label", "children"),
        Input("chart-type-toggle", "value"),
        Input("size-metric-toggle", "value"),
        Input("year-range-slider", "value"),
        Input("sector-filter", "value"),
        Input("company-filter", "value"),
    )
    def update_growth_chart(chart_type, size_metric, year_range, sector, company):
        # Sector/Company come from the sidebar; the Date filter is skipped
        # here since this page already has its own year-range control above.
        start_year, end_year = year_range
        try:
            result = run_treemap_pipeline(
                start_date=f"{start_year}-01-01", end_date=f"{end_year}-12-31", size_metric=size_metric,
                sector=sector, company=company,
            )
        except ValueError:
            # Too few trading days for this Sector/Company + year-range combo
            # to compute a reliable CAGR -- keep showing the last valid chart.
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        fig = create_growth_figure(result["hierarchy"], chart_type, size_metric)
        kpi_strip = build_kpi_strip(result["company_growth"], result["sector_growth"])
        return fig, serialize_company_growth(result["company_growth"]), kpi_strip, f"{start_year}–{end_year}"

    @callback(
        Output("growth-detail-graph", "figure"),
        Output("pane-detail-title", "children"),
        Input("growth-treemap-chart", "clickData"),
        State("growth-data-store", "data"),
        State("year-range-slider", "value"),
        prevent_initial_call=True,
    )
    def update_detail_panel(click_data, stored_data, year_range):
        company_growth = pd.DataFrame(stored_data)

        if not click_data:
            return create_all_sector_comparison_figure(company_growth), "All sector comparison"

        node_id = click_data["points"][0].get("id", "")
        if node_id in ("", ROOT_ID):
            return create_all_sector_comparison_figure(company_growth), "All sector comparison"

        if "/" in node_id:
            _, company_name = node_id.split("/", 1)
            start_year, end_year = year_range
            raw = load_clean_data()
            windowed = filter_by_date_range(raw, f"{start_year}-01-01", f"{end_year}-12-31")
            price_df = windowed[windowed["Company"] == company_name].sort_values("Date")
            row = company_growth[company_growth["Company"] == company_name].iloc[0]

            fig = create_company_price_figure(company_name, price_df, float(row["CAGR"]))
            title = f"{company_name} · {float(row['CAGR']):+.1%} CAGR"
        else:
            fig = create_sector_bar_figure(node_id, company_growth)
            title = f"{node_id} companies"

        return fig, title

    clientside_callback(
        """
        function(n_clicks) {
            const el = document.getElementById('growth-fullscreen-target');
            if (!document.fullscreenElement) {
                el.requestFullscreen().catch(() => {});
            } else {
                document.exitFullscreen();
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("growth-fullscreen-btn", "n_clicks"),
        Input("growth-fullscreen-btn", "n_clicks"),
        prevent_initial_call=True,
    )


register_callbacks()
