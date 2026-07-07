import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from utils.analytics.risk_return import prepare_plot_data

dash.register_page(__name__, path="/risk_return", name="Risk vs Return")

df, feature_matrix = prepare_plot_data()

# Muted, professional palette — one color per cluster (0,1,2,3)
CLUSTER_COLORS = {
    "0": "#4C72B0",  # muted navy blue
    "1": "#C44E52",  # muted brick red
    "2": "#55A868",  # muted green
    "3": "#8172B2",  # muted purple
}


def create_scatter_plot(feature_matrix, selected_company=None):
    colors = feature_matrix["Cluster"].map(CLUSTER_COLORS)

    if selected_company is not None:
        opacity = feature_matrix["Company"].apply(
            lambda c: 1.0 if c == selected_company else 0.25
        )
        line_widths = feature_matrix["Company"].apply(
            lambda c: 2 if c == selected_company else 0.5
        )
    else:
        opacity = 1.0
        line_widths = 0.5

    fig = go.Figure(
        go.Scatter(
            x=feature_matrix["Annual_Volatility"],
            y=feature_matrix["Annual_Return"],
            mode="markers",
            marker=dict(
                size=13,
                color=colors,
                opacity=opacity,
                line=dict(width=line_widths, color="black"),
            ),
            customdata=feature_matrix[["Company", "Sector", "Cluster"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sector: %{customdata[1]}<br>"
                "Return: %{y:.2%}<br>"
                "Volatility: %{x:.2%}<br>"
                "Cluster: %{customdata[2]}<extra></extra>"
            ),
        )
    )

    # Manual legend since single-trace scatter has no auto cluster legend
    for cluster_id, color in CLUSTER_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color),
            name=f"Cluster {cluster_id}",
            showlegend=True,
        ))

    fig.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title_text="Cluster",
        font=dict(family="Inter, sans-serif", size=13),
        xaxis_title="Annual_Volatility",
        yaxis_title="Annual_Return",
        clickmode="event",
    )
    fig.update_xaxes(gridcolor="#eee")
    fig.update_yaxes(gridcolor="#eee")
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

    dcc.Store(id="selected-company-store", data=feature_matrix.iloc[0]["Company"]),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Cluster Scatter Plot", className="fw-bold"),
                dbc.CardBody(
                    dcc.Graph(
                        id="risk-return-scatter",
                        figure=create_scatter_plot(feature_matrix, feature_matrix.iloc[0]["Company"]),
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
)
def update_scatter_highlight(company):
    return create_scatter_plot(feature_matrix, company)


@callback(
    Output("risk-return-price-chart", "figure"),
    Output("price-chart-title", "children"),
    Input("selected-company-store", "data"),
    Input("price-view-toggle", "value"),
)
def update_price_chart(company, view_option):
    company_df = df[df["Company"] == company]
    fig = create_price_chart(company_df, company, view_option)
    return fig, f"Historical Price — {company}"