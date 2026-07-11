import dash
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
    fig = go.Figure(
        go.Scattergl(
            x=feature_matrix["Annual_Volatility"],
            y=feature_matrix["Annual_Return"],
            mode="markers+text",
            text=[c if c == selected_company else "" for c in feature_matrix["Company"]],
            textposition="top center",
            textfont=dict(size=10, color=tm_colors["text_primary"]),
            marker=dict(
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
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sector: %{customdata[1]}<br>"
                "Risk Class: %{customdata[2]}<br>"
                "Return: %{y:.2%}<br>"
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

    dbc.Row([
        # Main Scatter Plot
        dbc.Col(
            dbc.Card([
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


@callback(
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