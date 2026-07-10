import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from utils.analytics.risk_return import prepare_plot_data

dash.register_page(__name__, path="/risk_return", name="Risk vs Return")

df, feature_matrix = prepare_plot_data()

DEFAULT_COMPANY = feature_matrix.iloc[0]["Company"]

# ---------- Cluster palette ----------
CLUSTER_COLORS = {
    "0": "#4C72B0",
    "1": "#C44E52",
    "2": "#55A868",
    "3": "#8172B2",
}

# ---------- Sector grouping + palette ----------
SECTOR_GROUPS = {
    "AUTOMOBILE": "Automobile",
    "FINANCIAL SERVICES": "Financial Services",
    "IT": "Technology",
    "PHARMA": "Healthcare",
    "TELECOM": "Telecom",
    "ENERGY": "Energy",
    "CONSUMER GOODS": "Consumer & Media",
    "SERVICES": "Consumer & Media",
    "MEDIA & ENTERTAINMENT": "Consumer & Media",
    "CEMENT & CEMENT PRODUCTS": "Industrials & Materials",
    "METALS": "Industrials & Materials",
    "CONSTRUCTION": "Industrials & Materials",
    "FERTILISERS & PESTICIDES": "Industrials & Materials",
}

SECTOR_GROUP_COLORS = {
    "Automobile": "#4C72B0",
    "Financial Services": "#C44E52",
    "Technology": "#55A868",
    "Healthcare": "#8172B2",
    "Telecom": "#CCB974",
    "Energy": "#64B5CD",
    "Consumer & Media": "#DD8452",
    "Industrials & Materials": "#8C8C8C",
}

feature_matrix["Sector_Group"] = feature_matrix["Sector"].map(SECTOR_GROUPS)


def create_scatter_plot(feature_matrix, selected_company=None, color_by="Cluster"):
    if color_by == "Sector":
        color_col = "Sector_Group"
        palette = SECTOR_GROUP_COLORS
        legend_title = "Sector"
    else:
        color_col = "Cluster"
        palette = CLUSTER_COLORS
        legend_title = "Cluster"

    colors = feature_matrix[color_col].map(palette)

    if selected_company is not None:
        opacity = feature_matrix["Company"].apply(
            lambda c: 1.0 if c == selected_company else 0.25
        )
        line_widths = feature_matrix["Company"].apply(
            lambda c: 2.5 if c == selected_company else 0.8
        )
    else:
        opacity = 0.9
        line_widths = 0.8

    mean_return = feature_matrix["Annual_Return"].mean()
    mean_vol = feature_matrix["Annual_Volatility"].mean()

    fig = go.Figure(
        go.Scatter(
            x=feature_matrix["Annual_Volatility"],
            y=feature_matrix["Annual_Return"],
            mode="markers",
            marker=dict(
                size=16,                      # bigger — was 13
                color=colors,
                opacity=opacity,
                line=dict(width=line_widths, color="rgba(0,0,0,0.5)"),
            ),
            customdata=feature_matrix[["Company", "Sector", "Cluster"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sector: %{customdata[1]}<br>"
                "Return: %{y:.2%}<br>"
                "Volatility: %{x:.2%}<br>"
                "Cluster: %{customdata[2]}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    for label, color in palette.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color),
            name=label if color_by == "Sector" else f"Cluster {label}",
            showlegend=True,
        ))

    # Quadrant reference lines — mean volatility & mean return
    fig.add_vline(x=mean_vol, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)
    fig.add_hline(y=mean_return, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)

    fig.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        plot_bgcolor="#FAFAFA",           # very light grey instead of pure white
        paper_bgcolor="white",
        legend_title_text=legend_title,
        font=dict(family="Inter, sans-serif", size=13),
        xaxis_title="Annual Volatility (Risk)",
        yaxis_title="Annual Return",
        clickmode="event",
    )
    fig.update_xaxes(gridcolor="#e0e0e0", tickformat=".0%", zeroline=False)
    fig.update_yaxes(gridcolor="#e0e0e0", tickformat=".0%", zeroline=False)
    return fig

def create_price_chart(company_df, company, view_option):
    if view_option == "price":
        fig = px.line(company_df, x="Date", y="Close",
                       title=f"{company} Historical Closing Price")
        fig.update_traces(line=dict(color="#4C72B0", width=2))
    else:
        company_df = company_df.copy()
        company_df["Cumulative_Return"] = (
            (1 + company_df["Daily_Return"].fillna(0)).cumprod() - 1
        )
        fig = px.line(company_df, x="Date", y="Cumulative_Return",
                       title=f"{company} Cumulative Return")
        fig.update_traces(line=dict(color="#55A868", width=2))
        fig.update_layout(yaxis_tickformat=".0%")

    fig.update_layout(
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
    )
    fig.update_xaxes(gridcolor="#eee")
    fig.update_yaxes(gridcolor="#eee")
    return fig


layout = dbc.Container([
    html.H2("Risk Return Analysis", className="mt-3 mb-1"),
    html.P("Cluster companies by risk vs. return, then click a point to inspect its history.",
           className="text-muted mb-4"),

    dcc.Store(id="selected-company-store", data=None),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                    html.Span("Cluster Scatter Plot", className="fw-bold me-3"),
                    dbc.RadioItems(
                        id="color-by-toggle",
                        options=[
                            {"label": "Cluster", "value": "Cluster"},
                            {"label": "Sector", "value": "Sector"},
                        ],
                        value="Cluster",
                        inline=True,
                        className="d-inline-block",
                        inputClassName="me-1",
                        labelClassName="me-3",
                    ),
                ], className="d-flex align-items-center"),
                dbc.CardBody(
                    dcc.Graph(
                        id="risk-return-scatter",
                        figure=create_scatter_plot(feature_matrix, None, "Cluster"),
                        config={"displayModeBar": False},
                    )
                ),
            ], className="shadow-sm h-100"),
            width=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(id="price-chart-title", className="fw-bold"),
                dbc.CardBody([
                    dbc.RadioItems(
                        id="price-view-toggle",
                        options=[
                            {"label": "Closing Price", "value": "price"},
                            {"label": "Cumulative Return", "value": "cumulative"},
                        ],
                        value="price",
                        inline=True,
                        className="mb-2",
                        inputClassName="me-1",
                        labelClassName="me-3",
                    ),
                    dcc.Graph(id="risk-return-price-chart", config={"displayModeBar": False}),
                ]),
            ], className="shadow-sm h-100"),
            width=6,
        ),
    ], className="g-3"),
], fluid=True, className="px-4 py-3")


@callback(
    Output("selected-company-store", "data"),
    Input("risk-return-scatter", "clickData"),
)
def update_selected_company(click_data):
    if click_data is None:
        return dash.no_update
    point_index = click_data["points"][0]["pointIndex"]
    return feature_matrix.iloc[point_index]["Company"]


@callback(
    Output("risk-return-scatter", "figure"),
    Input("selected-company-store", "data"),
    Input("color-by-toggle", "value"),
)
def update_scatter(company, color_by):
    return create_scatter_plot(feature_matrix, company, color_by)


@callback(
    Output("risk-return-price-chart", "figure"),
    Output("price-chart-title", "children"),
    Input("selected-company-store", "data"),
    Input("price-view-toggle", "value"),
)
def update_price_chart(company, view_option):
    active_company = company if company is not None else DEFAULT_COMPANY
    company_df = df[df["Company"] == active_company]
    fig = create_price_chart(company_df, active_company, view_option)
    return fig, f"Historical Price — {active_company}"