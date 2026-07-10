import dash
from dash import State, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from utils.analytics.risk_return import prepare_plot_data
from utils.config import get_cluster_colors, get_quant_colorscale, MODEBAR_CONFIG, ThemeManager

dash.register_page(__name__, path="/risk_return", name="Risk vs Return")

from utils.database import run_query

def _get_default_company():
    try:
        # Just grab the first alphabetical company
        query = "SELECT MIN(Company) as Company FROM clean_stock_data"
        return run_query(query)["Company"].iloc[0]
    except Exception:
        return "RELIANCE"

DEFAULT_COMPANY = _get_default_company()


def create_scatter_plot(feature_matrix, selected_company=None, theme="dark"):
    # Identify top performers to label (Top 3 by Sharpe) plus the selected company
    labels = []
    top_performers = (feature_matrix.nlargest(3, "Sharpe_Ratio")["Company"].tolist()
                      if "Sharpe_Ratio" in feature_matrix.columns else [])
    
    for c in feature_matrix["Company"]:
        if c == selected_company or c in top_performers:
            labels.append(c)
        else:
            labels.append("")

    colors = feature_matrix["Cluster"].map(get_cluster_colors(theme))
    tm_colors = ThemeManager.get_colors(theme)
    base_rgb = "0,0,0" if theme == "light" else "255,255,255"

    if selected_company is not None:
        opacity = feature_matrix["Company"].apply(
            lambda c: 1.0 if c == selected_company else 0.4
        )
        sizes = feature_matrix["Company"].apply(
            lambda c: 16 if c == selected_company else 12
        )
        line_widths = feature_matrix["Company"].apply(
            lambda c: 2.0 if c == selected_company else 1.5
        )
        line_colors = tm_colors["bg_surface"]
    else:
        opacity = 0.9
        sizes = 13
        line_widths = 1.5
        line_colors = tm_colors["bg_surface"]
        
    has_sharpe = "Sharpe_Ratio" in feature_matrix.columns

    fig = go.Figure(
        go.Scattergl(
            x=feature_matrix["Annual_Volatility"],
            y=feature_matrix["Annual_Return"],
            mode="markers+text",
            text=labels,
            textposition="top center",
            textfont=dict(size=10, color=tm_colors["text_primary"]),
            marker=dict(
                size=sizes,
                color=feature_matrix["Sharpe_Ratio"] if has_sharpe else colors,
                colorscale=get_quant_colorscale(theme) if has_sharpe else None,
                cmid=0 if has_sharpe else None,
                showscale=has_sharpe,
                colorbar=dict(
                    title="Sharpe",
                    thickness=12, len=0.6,
                    x=1.02, xanchor="left",
                ) if has_sharpe else None,
                opacity=opacity,
                line=dict(width=line_widths, color=line_colors),
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

    # Empirical Efficient Frontier (Upper Envelope)
    if len(feature_matrix) > 5:
        sorted_fm = feature_matrix.sort_values("Annual_Volatility")
        envelope_x = []
        envelope_y = []
        max_y = -float('inf')
        for _, row in sorted_fm.iterrows():
            if row["Annual_Return"] > max_y:
                max_y = row["Annual_Return"]
                envelope_x.append(row["Annual_Volatility"])
                envelope_y.append(row["Annual_Return"])
                
        fig.add_trace(go.Scatter(
            x=envelope_x, y=envelope_y, 
            mode="lines", 
            line=dict(color=tm_colors["info"], width=2.5, dash="dash"),
            name="Empirical Frontier",
            hoverinfo="skip"
        ))

    # Manual legend since single-trace scatter has no auto cluster legend
    for cluster_id, color in get_cluster_colors(theme).items():
        fig.add_trace(go.Scattergl(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color),
            name=f"Cluster {cluster_id}",
            showlegend=True,
        ))

    fig.update_layout(
        legend=dict(
            title_text="Cluster",
            orientation="h",
            yanchor="top", y=-0.12,
            xanchor="left", x=0,
            font=dict(size=11),
        ),
        xaxis_title="Annual Volatility",
        yaxis_title="Annual Return",
        margin=dict(l=50, r=80, t=30, b=80),
        clickmode="event",
        template=f"financial_{theme}"
    )
    return fig


def create_price_chart(company_df, company, view_option, theme="dark"):
    if view_option == "price":
        fig = px.line(company_df, x="Date", y="Close")
        fig.update_traces(line=dict(color=ThemeManager.get_colors(theme)["info"], width=2))
    else:
        company_df = company_df.copy()
        company_df["Cumulative_Return"] = (
            (1 + company_df["Daily_Return"].fillna(0)).cumprod() - 1
        )
        fig = px.line(company_df, x="Date", y="Cumulative_Return")
        fig.update_traces(line=dict(color=ThemeManager.get_colors(theme)["success"], width=2))
        fig.update_layout(yaxis_tickformat=".0%")

    fig.update_layout(title=None, template=f"financial_{theme}") # We rely on CardHeader for the title
    return fig


layout = dbc.Container([
    html.H2("Risk Return Analysis", className="mt-3 mb-1 text-primary fw-bold"),
    html.Div(id="risk-smart-narrative"),
    html.P("Analyze the volatility vs. return of companies. The dashed line represents the Empirical Efficient Frontier.",
           className="text-muted mb-4"),

    dcc.Store(id="selected-company-store", data=DEFAULT_COMPANY),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Cluster Scatter Plot", className="fw-bold text-primary"),
                dbc.CardBody(
                    dcc.Loading(
                        dcc.Graph(
                            id="risk-return-scatter",
                            config=MODEBAR_CONFIG,
                        ),
                        type="circle", color="var(--accent-primary)"
                    )
                ),
            ], className="shadow-sm border-0 bg-surface h-100"),
            width=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(id="price-chart-title", className="fw-bold text-primary"),
                dbc.CardBody([
                    dbc.RadioItems(
                        id="price-view-toggle",
                        options=[
                            {"label": "Closing Price", "value": "price"},
                            {"label": "Cumulative Return", "value": "cumulative"},
                        ],
                        value="price",
                        inline=True,
                        className="mb-3",
                    ),
                    dcc.Loading(
                        dcc.Graph(id="risk-return-price-chart", config=MODEBAR_CONFIG),
                        type="circle", color="var(--accent-primary)"
                    )
                ]),
            ], className="shadow-sm border-0 bg-surface h-100"),
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
    
    # We can rely on customdata[0] which contains the company name
    return click_data["points"][0]["customdata"][0]


@callback(
    Output("risk-return-scatter", "figure"),
    Output("risk-smart-narrative", "children"),
    Input("selected-company-store", "data", allow_optional=True),
    Input("global-state", "data"),
    Input("theme-store", "data"),
    State("url", "pathname")
)
def update_scatter_highlight(company, global_state, theme, pathname):
    import dash
    if pathname != "/risk-return" and pathname != "/risk_return":
        raise dash.exceptions.PreventUpdate
        
    from components.narrative import generate_smart_narrative
    df, feature_matrix = prepare_plot_data()
    
    if global_state and global_state.get("sectors"):
        feature_matrix = feature_matrix[feature_matrix["Sector"].isin(global_state["sectors"])]
        
    if feature_matrix.empty:
        import plotly.graph_objects as go
        empty_fig = go.Figure().update_layout(title="No data available", xaxis_visible=False, yaxis_visible=False, template=f"financial_{theme}")
        return empty_fig, html.Div("No data available for the selected filters.", className="text-muted")
        
    fig = create_scatter_plot(feature_matrix, company, theme)
    narrative = generate_smart_narrative(feature_matrix, context="risk")
    return fig, narrative


@callback(
    Output("risk-return-price-chart", "figure"),
    Output("price-chart-title", "children"),
    Input("selected-company-store", "data"),
    Input("price-view-toggle", "value"),
    Input("theme-store", "data")
)
def update_price_chart(company, view_option, theme):
    df, _ = prepare_plot_data()
    company_df = df[df["Company"] == company]
    
    if company_df.empty:
        import plotly.graph_objects as go
        empty_fig = go.Figure().update_layout(title="No data available", xaxis_visible=False, yaxis_visible=False, template=f"financial_{theme}")
        return empty_fig, f"Historical Price — {company}"
        
    fig = create_price_chart(company_df, company, view_option, theme)
    return fig, f"Historical Price — {company}"