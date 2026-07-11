import dash
<<<<<<< HEAD
from dash import State, html, dcc, callback, Input, Output, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

from utils.analytics.risk_return import prepare_plot_data, get_portfolio_performance
from utils.config import get_cluster_colors, get_quant_colorscale, MODEBAR_CONFIG, ThemeManager
from utils.visuals import apply_shared_layout
from components.cards import create_stat_card

dash.register_page(__name__, path="/risk_return", name="Risk vs Return")

def create_scatter_plot(feature_matrix, cov_matrix, frontier_df, tangency, selected_company=None, portfolio_weights=None, theme="dark"):
    colors = feature_matrix["Risk_Class"].map({
        "Defensive": ThemeManager.get_colors(theme)["success"],
        "Balanced": ThemeManager.get_colors(theme)["info"],
        "Growth": ThemeManager.get_colors(theme)["warning"],
        "Aggressive": ThemeManager.get_colors(theme)["danger"],
    })
    
    tm_colors = ThemeManager.get_colors(theme)
    base_rgb = "0,0,0" if theme == "light" else "255,255,255"
    
    # Base scatter for companies
=======
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

_, feature_matrix = prepare_plot_data()

# ---------- Cluster palette ----------
# Keyed by the raw KMeans cluster id. The *meaning* behind each color (the
# legend text) is computed dynamically by label_clusters() since cluster ids
# are arbitrary and can be reshuffled by KMeans whenever filters change.
CLUSTER_COLORS = {
    "0": "#4C72B0",
    "1": "#C44E52",
    "2": "#55A868",
    "3": "#8172B2",
}


def create_scatter_plot(feature_matrix, highlighted_company=None):
    cluster_labels = label_clusters(feature_matrix)  # {cluster_id: readable label}
    colors = feature_matrix["Cluster"].map(CLUSTER_COLORS)

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

    mean_return = feature_matrix["Annual_Return"].mean()
    mean_vol = feature_matrix["Annual_Volatility"].mean()

    hover_df = feature_matrix[["Company", "Sector", "Cluster"]].copy()
    hover_df["Cluster_Label"] = feature_matrix["Cluster"].map(cluster_labels)

>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
    fig = go.Figure(
        go.Scattergl(
            x=feature_matrix["Annual_Volatility"],
            y=feature_matrix["Annual_Return"],
            mode="markers+text",
            text=[c if c == selected_company else "" for c in feature_matrix["Company"]],
            textposition="top center",
            textfont=dict(size=10, color=tm_colors["text_primary"]),
            marker=dict(
<<<<<<< HEAD
                size=[16 if c == selected_company else 10 for c in feature_matrix["Company"]],
                color=feature_matrix["Sharpe_Ratio"],
                colorscale=get_quant_colorscale(theme),
                cmid=0,
                showscale=True,
                colorbar=dict(
                    title="Sharpe",
                    thickness=12, len=0.6,
                    x=1.02, xanchor="left",
                ),
                opacity=[1.0 if c == selected_company else 0.6 for c in feature_matrix["Company"]],
                line=dict(width=1.5, color=tm_colors["bg_surface"]),
            ),
            customdata=feature_matrix[["Company", "Sector", "Risk_Class"]],
=======
                size=16,
                color=colors,
                opacity=opacity,
                line=dict(width=line_widths, color="rgba(0,0,0,0.5)"),
            ),
            customdata=hover_df[["Company", "Sector", "Cluster_Label"]],
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sector: %{customdata[1]}<br>"
                "Risk Class: %{customdata[2]}<br>"
                "Return: %{y:.2%}<br>"
<<<<<<< HEAD
                "Volatility: %{x:.2%}<extra></extra>"
            ),
            name="Assets"
        )
    )

    # Efficient Frontier
    if not frontier_df.empty:
        fig.add_trace(go.Scatter(
            x=frontier_df["Annual_Volatility"],
            y=frontier_df["Annual_Return"],
            mode="lines",
            line=dict(color=tm_colors["text_primary"], width=2),
            name="Efficient Frontier"
=======
                "Volatility: %{x:.2%}<br>"
                "Profile: %{customdata[2]}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    for cluster_id in sorted(cluster_labels.keys(), key=lambda c: int(c)):
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=CLUSTER_COLORS.get(cluster_id, "#999999")),
            name=cluster_labels[cluster_id],
            showlegend=True,
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
        ))
        
    # Capital Market Line & Tangency
    if tangency:
        risk_free = 0.05
        # Line from (0, rf) to Tangency Portfolio
        cml_x = [0, tangency["Annual_Volatility"], tangency["Annual_Volatility"] * 1.5]
        slope = (tangency["Annual_Return"] - risk_free) / tangency["Annual_Volatility"]
        cml_y = [risk_free, tangency["Annual_Return"], risk_free + slope * (tangency["Annual_Volatility"] * 1.5)]
        
        fig.add_trace(go.Scatter(
            x=cml_x, y=cml_y,
            mode="lines",
            line=dict(color=tm_colors["success"], width=2, dash="dash"),
            name="Capital Market Line"
        ))
        
        fig.add_trace(go.Scatter(
            x=[tangency["Annual_Volatility"]],
            y=[tangency["Annual_Return"]],
            mode="markers",
            marker=dict(size=14, color=tm_colors["success"], symbol="star", line=dict(width=1, color="white")),
            name="Tangency Portfolio",
            hovertemplate="<b>Tangency Portfolio</b><br>Return: %{y:.2%}<br>Volatility: %{x:.2%}<br>Sharpe: " + f"{tangency['Sharpe_Ratio']:.2f}<extra></extra>"
        ))
        
    # Custom Portfolio Marker
    if portfolio_weights is not None and not feature_matrix.empty:
        # We need to map the dict of {company: weight} to an array aligned with cov_matrix
        companies = cov_matrix.columns
        w_array = np.zeros(len(companies))
        for i, c in enumerate(companies):
            w_array[i] = portfolio_weights.get(c, 0)
            
        if np.sum(w_array) > 0:
            # normalize just in case
            w_array = w_array / np.sum(w_array)
            returns_aligned = feature_matrix.set_index("Company").loc[companies]["Annual_Return"].values
            p_ret, p_vol, p_sharpe = get_portfolio_performance(w_array, returns_aligned, cov_matrix, 0.05)
            
            fig.add_trace(go.Scatter(
                x=[p_vol],
                y=[p_ret],
                mode="markers",
                marker=dict(size=14, color=tm_colors["warning"], symbol="diamond", line=dict(width=1, color="white")),
                name="Custom Portfolio",
                hovertemplate="<b>Custom Portfolio</b><br>Return: %{y:.2%}<br>Volatility: %{x:.2%}<br>Sharpe: " + f"{p_sharpe:.2f}<extra></extra>"
            ))

<<<<<<< HEAD
    fig = apply_shared_layout(
        fig,
        theme=theme,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.15,
            xanchor="left", x=0,
            font=dict(size=11),
        ),
        xaxis_title="Annual Volatility (Risk)",
        yaxis_title="Annual Return",
        margin=dict(l=50, r=80, t=30, b=80),
        clickmode="event"
    )
    
    # Force X axis to start from 0 to show CML intersection
    fig.update_xaxes(rangemode="tozero")
    return fig

layout = dbc.Container([
    html.H2("Risk Return Analytics", className="mt-3 mb-1 text-primary fw-bold"),
    html.P("Modern Portfolio Theory workspace. Construct portfolios, analyze the Efficient Frontier, and evaluate risk-adjusted returns.",
           className="text-muted mb-4"),
           
    html.Div(id="risk-smart-narrative", className="mb-4"),
=======
    fig.add_vline(x=mean_vol, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)
    fig.add_hline(y=mean_return, line_dash="dot", line_color="rgba(0,0,0,0.3)", line_width=1)

    fig.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="white",
        legend_title_text="Risk Profile",
        font=dict(family="Inter, sans-serif", size=13),
        xaxis_title="Annual Volatility (Risk)",
        yaxis_title="Annual Return",
        clickmode="event",
        uirevision="constant",
    )
    fig.update_xaxes(gridcolor="#e0e0e0", tickformat=".0%", zeroline=False)
    fig.update_yaxes(gridcolor="#e0e0e0", tickformat=".0%", zeroline=False)
    return fig


def create_price_chart(company_df, company, benchmark_df=None):
    fig = go.Figure()

    if company_df is not None and not company_df.empty:
        company_df = company_df.copy()
        if "Daily_Return" not in company_df.columns:
            company_df["Daily_Return"] = company_df["Close"].pct_change()

        company_df["Cumulative_Return"] = (
            (1 + company_df["Daily_Return"].fillna(0)).cumprod() - 1
        )
        # A more intuitive companion figure alongside the %: what ₹100
        # invested on day one would be worth today.
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

        final_ret = company_df["Cumulative_Return"].iloc[-1]
        final_val = company_df["Indexed_Value"].iloc[-1]
        fig.add_annotation(
            x=company_df["Date"].iloc[-1], y=final_ret,
            text=f"{company}: {final_ret:+.1%}  (₹{final_val:,.0f})",
            showarrow=True, arrowhead=2, ax=-60, ay=-25,
            font=dict(color="#3d7a4d", size=12),
            bgcolor="rgba(255,255,255,0.85)",
        )

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

    dcc.Store(id="selected-company-store", data=None),
    dcc.Store(id="highlight-company-store", data=None),
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474

    dbc.Row([
        # Main Scatter Plot
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

    # ---------------- Scatter Plot ----------------
    dbc.Row([
        dbc.Col(
            dbc.Card([
<<<<<<< HEAD
                dbc.CardHeader("Efficient Frontier & Asset Distribution", className="fw-bold text-primary"),
                dbc.CardBody(
                    dcc.Loading(
                        dcc.Graph(
                            id="risk-return-scatter",
                            config=MODEBAR_CONFIG,
                            style={"height": "500px"}
                        ),
                        type="circle", color="var(--accent-primary)"
                    )
                ),
            ], className="shadow-sm border-0 bg-surface h-100"),
            lg=8, md=12, className="mb-4"
        ),
        
        # Portfolio Builder
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Portfolio Builder", className="fw-bold text-primary"),
                dbc.CardBody([
                    html.P("Select assets to build a custom equally-weighted portfolio and compare it against the Efficient Frontier.", className="small text-muted mb-3"),
                    dcc.Dropdown(
                        id="portfolio-asset-selector",
                        multi=True,
                        placeholder="Search & Select Assets...",
                        className="mb-4"
                    ),
                    html.Div(id="portfolio-analytics-panel")
                ]),
            ], className="shadow-sm border-0 bg-surface h-100"),
            lg=4, md=12, className="mb-4"
        ),
    ], className="g-3"),
    
    # Ranking Table
    dbc.Row([
        dbc.Col([
            html.H6("ASSET RANKING", className="text-muted text-uppercase fw-bold mb-3 mt-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
            html.Div(id="risk-ranking-table-container")
        ], width=12)
    ])
], fluid=True, className="px-4 py-3")
=======
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

    # ---------------- Cumulative Return Plot ----------------
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
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474

], fluid=True, className="px-4 py-3")

@callback(
<<<<<<< HEAD
    Output("portfolio-asset-selector", "options"),
    Input("theme-store", "data")
)
def populate_dropdown(theme):
    _, feature_matrix, _, _, _ = prepare_plot_data()
    if feature_matrix.empty:
        return []
    return [{"label": c, "value": c} for c in sorted(feature_matrix["Company"].tolist())]


@callback(
    Output("risk-return-scatter", "figure"),
    Output("portfolio-analytics-panel", "children"),
    Output("risk-smart-narrative", "children"),
    Input("portfolio-asset-selector", "value"),
    Input("theme-store", "data")
)
def update_workspace(portfolio_assets, theme):
    df, feature_matrix, cov_matrix, frontier_df, tangency = prepare_plot_data()
    
    if feature_matrix.empty:
        from utils.visuals import create_empty_figure
        return create_empty_figure("No data available", theme=theme), html.Div("No Data"), html.Div("No Data")
        
    selected_company = None

            
    # Calculate Custom Portfolio
    portfolio_weights = None
    analytics_panel = html.Div([
        html.Div("No assets selected.", className="text-muted text-center p-4")
    ])
    
    if portfolio_assets and len(portfolio_assets) > 0:
        weight = 1.0 / len(portfolio_assets)
        portfolio_weights = {c: weight for c in portfolio_assets}
        
        companies = cov_matrix.columns
        w_array = np.zeros(len(companies))
        for i, c in enumerate(companies):
            w_array[i] = portfolio_weights.get(c, 0)
            
        returns_aligned = feature_matrix.set_index("Company").loc[companies]["Annual_Return"].values
        p_ret, p_vol, p_sharpe = get_portfolio_performance(w_array, returns_aligned, cov_matrix, 0.05)
        
        analytics_panel = html.Div([
            html.H6("PORTFOLIO METRICS", className="text-muted text-uppercase fw-bold mb-3", style={"letterSpacing": "1px", "fontSize": "11px"}),
            dbc.Row([
                dbc.Col(create_stat_card("Expected Return", f"{p_ret:.2%}", "bi-graph-up-arrow", "success"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Volatility (Risk)", f"{p_vol:.2%}", "bi-activity", "warning"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Sharpe Ratio", f"{p_sharpe:.2f}", "bi-lightning-charge", "info"), width=6, className="mb-3"),
                dbc.Col(create_stat_card("Holdings", f"{len(portfolio_assets)}", "bi-collection", "primary"), width=6, className="mb-3"),
            ]),
            dbc.Button([html.I(className="bi bi-download me-2"), "Export Weights"], id="btn-export-portfolio", color="secondary", outline=True, size="sm", className="w-100 fw-bold shadow-sm")
        ])
        
    fig = create_scatter_plot(feature_matrix, cov_matrix, frontier_df, tangency, selected_company, portfolio_weights, theme)
    
    # Generate Smart Narrative based on Tangency Portfolio
    narrative_text = "Analysis complete."
    if tangency:
        best_ret = tangency["Annual_Return"]
        best_vol = tangency["Annual_Volatility"]
        best_sharpe = tangency["Sharpe_Ratio"]
        narrative_text = f"The Tangency Portfolio achieves an optimal Expected Return of {best_ret:.2%} with {best_vol:.2%} Volatility (Sharpe: {best_sharpe:.2f}). Adjust your holdings to approximate this risk-adjusted profile."
        
    narrative_div = dbc.Alert([
        html.I(className="bi bi-lightbulb-fill text-warning me-2"),
        html.Span(narrative_text, className="small fw-bold text-muted")
    ], color="secondary", className="border-0 shadow-sm py-2 px-3 bg-surface bg-opacity-50")
    
    return fig, analytics_panel, narrative_div


@callback(
    Output("event-bus", "data", allow_duplicate=True),
    Input("risk-return-scatter", "clickData"),
    prevent_initial_call=True
)
def handle_scatter_click(click_data):
    if not click_data:
        return no_update
    try:
        company = click_data["points"][0]["customdata"][0]
        return {"type": "OPEN_COMPANY_DRAWER", "payload": f"Company:{company}"}
    except Exception:
        return no_update


@callback(
    Output("risk-ranking-table-container", "children"),
    Input("theme-store", "data")
)
def render_ranking_table(theme):
    _, feature_matrix, _, _, _ = prepare_plot_data()
    if feature_matrix.empty:
        return ""
        
    df_display = feature_matrix[["Company", "Sector", "Risk_Class", "Annual_Return", "Annual_Volatility", "Sharpe_Ratio"]].copy()
    df_display = df_display.sort_values("Sharpe_Ratio", ascending=False).round(4)
    
    # Format percentages
    df_display["Annual_Return"] = df_display["Annual_Return"].apply(lambda x: f"{x:.2%}")
    df_display["Annual_Volatility"] = df_display["Annual_Volatility"].apply(lambda x: f"{x:.2%}")
    df_display["Sharpe_Ratio"] = df_display["Sharpe_Ratio"].apply(lambda x: f"{x:.2f}")
    
    tm_colors = ThemeManager.get_colors(theme)
    
    table = dag.AgGrid(
        id="risk-ranking-table",
        className="ag-theme-alpine-dark" if theme == "dark" else "ag-theme-alpine",
        columnDefs=[{"field": i, "headerName": i, "sortable": True} for i in df_display.columns],
        rowData=df_display.to_dict("records"),
        dashGridOptions={"pagination": True, "paginationPageSize": 10, "domLayout": "autoHeight"},
    )
    
    return dbc.Card([
        dbc.CardBody(table, className="p-0")
    ], className="shadow-sm border-0 bg-surface overflow-hidden")

@callback(
    Output("event-bus", "data", allow_duplicate=True),
    Input("risk-ranking-table", "cellClicked"),
    State("risk-ranking-table", "rowData"),
    prevent_initial_call=True
)
def handle_table_click(cell_clicked, row_data):
    if cell_clicked and row_data:
        row_idx = cell_clicked.get("rowIndex")
        if row_idx is not None and row_idx < len(row_data):
            company = row_data[row_idx].get("Company")
            if company:
                return {"type": "OPEN_COMPANY_DRAWER", "payload": f"Company:{company}"}
    return no_update
=======
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
    if trigger == "reset-risk-return-btn":
        return None
    

    if trigger == "company-filter":
        # Includes the case where the user clears the filter (company_filter
        # is None/""); we clear the selection rather than guessing a company.
        return company_filter or None

    if trigger == "risk-return-scatter":
        if click_data is None:
            return dash.no_update
        return click_data["points"][0]["customdata"][0]

    if trigger in ("sector-filter", "start-date-filter", "end-date-filter"):
        if current_company is None:
            # Nothing was selected before the filter changed — keep it that
            # way instead of auto-picking a company (previously this fell
            # through to sorted(available)[0], which always defaulted to
            # ADANIPORTS alphabetically).
            return dash.no_update

        available = load_data(
            start_date=start_date, end_date=end_date, sector=sector, company=company_filter
        )["Company"].unique()

        if current_company in available:
            return dash.no_update
        # The previously selected company no longer matches the filters —
        # clear the selection instead of silently swapping to a new one.
        return None

    return dash.no_update


@callback(
    Output("highlight-company-store", "data"),
    Input("risk-return-scatter", "clickData"),
    Input("risk-return-scatter", "relayoutData"),
    Input("reset-risk-return-btn", "n_clicks"),
    prevent_initial_call=True,
)
def update_highlight(click_data, relayout_data, reset_clicks):
    trigger = ctx.triggered_id

    # Reset button clears highlight
    if trigger == "reset-risk-return-btn":
        return None

    # Reset axes (double click or toolbar reset)
    if trigger == "risk-return-scatter":
        if click_data:
            return click_data["points"][0]["customdata"][0]

    if trigger == "risk-return-scatter.relayoutData":
        if relayout_data and (
            "xaxis.autorange" in relayout_data or
            "yaxis.autorange" in relayout_data
        ):
            return None

    return dash.no_update

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


@callback(
    Output("risk-return-price-chart", "figure"),
    Output("price-chart-title", "children"),
    Input("selected-company-store", "data"),
    Input("start-date-filter", "value"),
    Input("end-date-filter", "value"),
)
def update_price_chart(company, start_date, end_date):
    if not company:
        # Nothing selected yet — show the market benchmark on its own
        # instead of defaulting to an arbitrary company.
        benchmark_df = compute_benchmark_cumulative_return(
            start_date=start_date, end_date=end_date
        )
        fig = create_price_chart(None, None, benchmark_df)
        return fig, "Nifty 50 Average — click a point or pick a company to compare"

    company_df = load_company_prices(company, start_date=start_date, end_date=end_date)

    benchmark_df = None
    if not company_df.empty:
        aligned_start = company_df["Date"].min()
        benchmark_df = compute_benchmark_cumulative_return(
            start_date=aligned_start, end_date=end_date
        )

    fig = create_price_chart(company_df, company, benchmark_df)
    return fig, f"Historical Price — {company}"
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
