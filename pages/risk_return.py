import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from utils.analytics.risk_return import (
    prepare_plot_data,
    load_company_prices,
    load_data,
    compute_benchmark_cumulative_return,
    label_clusters,
)

dash.register_page(__name__, path="/risk_return", name="Risk vs Return")

# Load data once when the page loads
_, feature_matrix = prepare_plot_data()

# Colors for each cluster
CLUSTER_COLORS = {
    "0": "#4C72B0",
    "1": "#C44E52",
    "2": "#55A868",
    "3": "#8172B2",
}


# Creating scatter plot
def create_scatter_plot(feature_matrix, highlighted_company=None):
    cluster_labels = label_clusters(feature_matrix)
    colors = feature_matrix["Cluster"].map(CLUSTER_COLORS)

    # Dim all other points if one is selected
    if highlighted_company is not None:
        opacity = feature_matrix["Company"].apply(
            lambda c: 1.0 if c == highlighted_company else 0.25
        )
        line_widths = feature_matrix["Company"].apply(
            lambda c: 2.5 if c == highlighted_company else 0.8
        )
    else:
        opacity = 0.9
        line_widths = 0.8

    # Mean lines for the quadrants
    mean_return = feature_matrix["Annual_Return"].mean()
    mean_vol = feature_matrix["Annual_Volatility"].mean()

    # Data for hover text
    hover_df = feature_matrix[["Company", "Sector", "Cluster"]].copy()
    hover_df["Cluster_Label"] = feature_matrix["Cluster"].map(cluster_labels)

    fig = go.Figure(
        go.Scatter(
            x=feature_matrix["Annual_Volatility"],
            y=feature_matrix["Annual_Return"],
            mode="markers",
            marker=dict(
                size=16,
                color=colors,
                opacity=opacity,
                line=dict(width=line_widths, color="rgba(0,0,0,0.5)"),
            ),
            customdata=hover_df[["Company", "Sector", "Cluster_Label"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sector: %{customdata[1]}<br>"
                "Return: %{y:.2%}<br>"
                "Volatility: %{x:.2%}<br>"
                "Profile: %{customdata[2]}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    # Add dummy traces just for the legend
    for cluster_id in sorted(cluster_labels.keys(), key=lambda c: int(c)):
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=CLUSTER_COLORS.get(cluster_id, "#999999")),
            name=cluster_labels[cluster_id],
            showlegend=True,
        ))

    # Quadrant lines
    fig.add_vline(x=mean_vol, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)
    fig.add_hline(y=mean_return, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)

    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=90),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="white",
        legend=dict(
            title="Risk Profile",
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        font=dict(family="Inter, sans-serif", size=13),
        xaxis_title="Annual Volatility (Risk)",
        yaxis_title="Annual Return",
        clickmode="event",
        uirevision="constant",
    )
    fig.update_xaxes(gridcolor="#e0e0e0", tickformat=".0%", zeroline=False)
    fig.update_yaxes(gridcolor="#e0e0e0", tickformat=".0%", zeroline=False)
    return fig


# Creating the price/return chart on the bottom
def create_price_chart(company_df, company, benchmark_df=None):
    fig = go.Figure()

    # Line for the selected company
    if company_df is not None and not company_df.empty:
        company_df = company_df.copy()
        if "Daily_Return" not in company_df.columns:
            company_df["Daily_Return"] = company_df["Close"].pct_change()

        company_df["Cumulative_Return"] = (
            (1 + company_df["Daily_Return"].fillna(0)).cumprod() - 1
        )
        # what 100 rs invested on day 1 would be worth now
        company_df["Indexed_Value"] = 100 * (1 + company_df["Cumulative_Return"])

        fig.add_trace(go.Scatter(
            x=company_df["Date"], y=company_df["Cumulative_Return"],
            mode="lines", name=company,
            line=dict(color="#55A868", width=2),
            customdata=company_df["Indexed_Value"],
            hovertemplate=(
                f"<b>{company}</b><br>Date: %{{x|%b %d, %Y}}<br>"
                "Return: %{y:.2%}<br>"
                "Value of ₹100 invested: ₹%{customdata:.2f}<extra></extra>"
            ),
        ))

        # label showing the final return at the end of the line
        final_ret = company_df["Cumulative_Return"].iloc[-1]
        final_val = company_df["Indexed_Value"].iloc[-1]
        fig.add_annotation(
            x=company_df["Date"].iloc[-1], y=final_ret,
            text=f"{company}: {final_ret:+.1%}  (₹{final_val:,.0f})",
            showarrow=True, arrowhead=2, ax=-60, ay=-25,
            font=dict(color="#3d7a4d", size=12),
            bgcolor="rgba(255,255,255,0.85)",
        )

    # Benchmark line (Nifty 50 average)
    if benchmark_df is not None and not benchmark_df.empty:
        benchmark_df = benchmark_df.copy()
        benchmark_df["Indexed_Value"] = 100 * (1 + benchmark_df["Cumulative_Return"])

        fig.add_trace(go.Scatter(
            x=benchmark_df["Date"], y=benchmark_df["Cumulative_Return"],
            mode="lines", name="Nifty 50 Average",
            line=dict(color="#999999", width=2, dash="dash"),
            customdata=benchmark_df["Indexed_Value"],
            hovertemplate=(
                "<b>Nifty 50 Average</b><br>Date: %{x|%b %d, %Y}<br>"
                "Return: %{y:.2%}<br>"
                "Value of ₹100 invested: ₹%{customdata:.2f}<extra></extra>"
            ),
        ))

        final_ret_b = benchmark_df["Cumulative_Return"].iloc[-1]
        final_val_b = benchmark_df["Indexed_Value"].iloc[-1]
        fig.add_annotation(
            x=benchmark_df["Date"].iloc[-1], y=final_ret_b,
            text=f"Nifty 50: {final_ret_b:+.1%}  (₹{final_val_b:,.0f})",
            showarrow=True, arrowhead=2, ax=-60, ay=25,
            font=dict(color="#777777", size=12),
            bgcolor="rgba(255,255,255,0.85)",
        )

    title = f"{company} vs Nifty 50 — Cumulative Return" if company else "Nifty 50 Average — Cumulative Return"

    fig.update_layout(
        title=title,
        yaxis_tickformat=".0%",
        yaxis_title="Cumulative Return (hover for ₹ value of ₹100 invested)",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=40, r=20, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
    )
    fig.update_xaxes(gridcolor="#eee")
    fig.update_yaxes(gridcolor="#eee")
    return fig


# Page layout
layout = dbc.Container([
    html.H2(
        "Risk Return Analysis",
        className="mt-3 mb-1",
        style={"fontWeight": "700", "color": "#1a1a2e"}
    ),

    html.P(
        "Explore how Nifty 50 companies balance risk and return — and see how each stacks up against the market.",
        className="mb-4",
        style={
            "fontSize": "0.95rem",
            "color": "#5a5a6e",
            "maxWidth": "720px"
        }
    ),

    # Stores for keeping track of selected/highlighted company
    dcc.Store(id="selected-company-store", data=None),
    dcc.Store(id="highlight-company-store", data=None),

    # Reset button
    dbc.Row([
        dbc.Col(
            dbc.Button(
                "↺ Reset View",
                id="reset-risk-return-btn",
                color="secondary",
                outline=True,
                size="sm",
            ),
            width="auto",
        ),
    ], className="mb-3"),

    # Scatter plot card
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.Span("Cluster Scatter Plot", className="fw-bold")
                ),

                dbc.CardBody(
                    dcc.Graph(
                        id="risk-return-scatter",
                        figure=create_scatter_plot(feature_matrix, None),
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": [
                                "select2d",
                                "lasso2d",
                            ],
                        },
                        style={"height": "600px"},
                    )
                ),
            ], className="shadow-sm"),
            width=12,
        ),
    ], className="g-3 mb-4"),

    # Cumulative return chart card
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    id="price-chart-title",
                    className="fw-bold"
                ),

                dbc.CardBody(
                    dcc.Graph(
                        id="risk-return-price-chart",
                        config={"displayModeBar": False},
                        style={"height": "500px"},
                    )
                ),
            ], className="shadow-sm"),
            width=12,
        ),
    ], className="g-3"),

], fluid=True, className="px-4 py-3")


# Updates which company is selected (for the bottom chart)
@callback(
    Output("selected-company-store", "data"),
    Input("risk-return-scatter", "clickData"),
    Input("company-filter", "value"),
    Input("sector-filter", "value"),
    Input("start-date-filter", "value"),
    Input("end-date-filter", "value"),
    Input("reset-risk-return-btn", "n_clicks"),
    State("selected-company-store", "data"),
)
def update_selected_company(
    click_data,
    company_filter,
    sector,
    start_date,
    end_date,
    reset_clicks,
    current_company,
):
    trigger = ctx.triggered_id

    # Reset button pressed
    if trigger == "reset-risk-return-btn":
        return None

    # Company picked from the filter dropdown
    if trigger == "company-filter":
        return company_filter or None

    # Company clicked on the scatter plot
    if trigger == "risk-return-scatter":
        if click_data is None:
            return dash.no_update
        return click_data["points"][0]["customdata"][0]

    # Other filters changed, check if current company still valid
    if trigger in ("sector-filter", "start-date-filter", "end-date-filter"):
        if current_company is None:
            return dash.no_update

        available = load_data(
            start_date=start_date, end_date=end_date, sector=sector, company=company_filter
        )["Company"].unique()

        if current_company in available:
            return dash.no_update
        return None

    return dash.no_update


# Updates which company is highlighted on the scatter plot
@callback(
    Output("highlight-company-store", "data"),
    Input("risk-return-scatter", "clickData"),
    Input("risk-return-scatter", "relayoutData"),
    Input("reset-risk-return-btn", "n_clicks"),
    prevent_initial_call=True,
)
def update_highlight(click_data, relayout_data, reset_clicks):
    trigger = ctx.triggered_id

    if trigger == "reset-risk-return-btn":
        return None

    if trigger == "risk-return-scatter":
        if click_data:
            return click_data["points"][0]["customdata"][0]

    # Double click resets the zoom, use that to also clear highlight
    if trigger == "risk-return-scatter.relayoutData":
        if relayout_data and (
            "xaxis.autorange" in relayout_data or
            "yaxis.autorange" in relayout_data
        ):
            return None

    return dash.no_update


# Redraws the scatter plot whenever filters or highlight changes
@callback(
    Output("risk-return-scatter", "figure"),
    Input("highlight-company-store", "data"),
    Input("start-date-filter", "value"),
    Input("end-date-filter", "value"),
    Input("sector-filter", "value"),
    Input("company-filter", "value"),
)
def update_scatter_highlight(highlighted_company, start_date, end_date, sector, company_filter):
    try:
        _, fm = prepare_plot_data(
            start_date=start_date, end_date=end_date, sector=sector, company=company_filter
        )
    except ValueError:
        return dash.no_update
    return create_scatter_plot(fm, highlighted_company)


# Redraws the bottom price chart whenever the selected company changes
@callback(
    Output("risk-return-price-chart", "figure"),
    Output("price-chart-title", "children"),
    Input("selected-company-store", "data"),
    Input("start-date-filter", "value"),
    Input("end-date-filter", "value"),
)
def update_price_chart(company, start_date, end_date):
    # No company selected yet, just show the market average
    if not company:
        benchmark_df = compute_benchmark_cumulative_return(
            start_date=start_date, end_date=end_date
        )
        fig = create_price_chart(None, None, benchmark_df)
        return fig, "Nifty 50 Average — click a point or pick a company to compare"

    company_df = load_company_prices(company, start_date=start_date, end_date=end_date)

    # Align benchmark to start from the same date as the company data
    benchmark_df = None
    if not company_df.empty:
        aligned_start = company_df["Date"].min()
        benchmark_df = compute_benchmark_cumulative_return(
            start_date=aligned_start, end_date=end_date
        )

    fig = create_price_chart(company_df, company, benchmark_df)
    return fig, f"Historical Price — {company}"