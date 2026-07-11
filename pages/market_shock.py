import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.analytics.market_shock import run_scenario_simulation, SCENARIO_LIBRARY, calculate_historical_betas
from utils.config import MODEBAR_CONFIG, ThemeManager, get_quant_colorscale
from utils.visuals import apply_shared_layout, create_empty_figure
from components.cards import create_stat_card

dash.register_page(__name__, path="/market_shock", name="Market Shocks")

# Sector Options for Custom Builder
@dash.callback(Output("scenario-target-sector", "options"), Input("theme-store", "data"))
def get_sector_options(_):
    beta_df = calculate_historical_betas()
    if beta_df.empty:
        return []
    sectors = sorted(beta_df["Sector"].unique())
    return [{"label": "All Sectors", "value": "All"}] + [{"label": s, "value": s} for s in sectors]


def create_timeline_figure(full_timeline, selected_company, theme):
    colors = ThemeManager.get_colors(theme)
    
    # Base figure
    fig = go.Figure()
    
    # 1. Plot Market Baseline
    market_data = full_timeline[full_timeline["Company"] == "Market Baseline"]
    if not market_data.empty:
        fig.add_trace(go.Scatter(
            x=market_data["Day"], y=market_data["Value"] - 1.0,
            mode="lines",
            line=dict(color=colors["text_primary"], width=3, dash="dash"),
            name="Market Baseline",
            hovertemplate="Day %{x}<br>Market Impact: %{y:.2%}<extra></extra>"
        ))
        
    # 2. Plot Sectors (light gray)
    sectors = full_timeline[full_timeline["Sector"] == full_timeline["Company"].str.replace(" (Avg)", "", regex=False)]["Company"].unique()
    for s in sectors:
        s_data = full_timeline[full_timeline["Company"] == s]
        fig.add_trace(go.Scatter(
            x=s_data["Day"], y=s_data["Value"] - 1.0,
            mode="lines",
            line=dict(color=colors["text_secondary"], width=1),
            opacity=0.3,
            name=s,
            showlegend=False,
            hoverinfo="skip"
        ))
        
    # 3. Plot Selected Company if exists
    if selected_company:
        c_data = full_timeline[full_timeline["Company"] == selected_company]
        if not c_data.empty:
            fig.add_trace(go.Scatter(
                x=c_data["Day"], y=c_data["Value"] - 1.0,
                mode="lines",
                line=dict(color=colors["warning"], width=3),
                name=f"{selected_company}",
                hovertemplate=f"<b>{selected_company}</b><br>Day %{{x}}<br>Impact: %{{y:.2%}}<extra></extra>"
            ))
            
    fig = apply_shared_layout(
        fig, theme=theme,
        xaxis_title="Days Since Shock Initiation",
        yaxis_title="Cumulative Impact",
        showlegend=True,
        margin=dict(l=50, r=20, t=30, b=50),
        clickmode="event"
    )
    fig.update_yaxes(tickformat=".0%")
    fig.add_hline(y=0, line_dash="solid", line_color=colors["success"], opacity=0.5)
    
    return fig


def create_resilience_bar_chart(summary_df, theme):
    colors = ThemeManager.get_colors(theme)
    
    sector_summary = summary_df.groupby("Sector").agg({
        "Max_Drawdown": "mean",
        "Resilience_Score": "mean"
    }).reset_index().sort_values("Max_Drawdown", ascending=False)
    
    fig = px.bar(
        sector_summary, x="Max_Drawdown", y="Sector",
        orientation="h",
        color="Resilience_Score",
        color_continuous_scale=get_quant_colorscale(theme),
        labels={"Max_Drawdown": "Average Max Drawdown"}
    )
    
    fig = apply_shared_layout(fig, theme=theme, margin=dict(l=150, r=20, t=30, b=50))
    fig.update_xaxes(tickformat=".0%")
    fig.update_layout(coloraxis_showscale=False)
    
    return fig


layout = dbc.Container([
    html.H2("Market Shock & Scenario Simulation", className="mt-3 mb-1 text-primary fw-bold"),
    html.P("Simulate stress events to evaluate systemic resilience. Customize shock vectors to analyze cascading impacts.",
           className="text-muted mb-4"),
           
    html.Div(id="scenario-smart-narrative", className="mb-4"),

    dbc.Row([
        # --- LEFT PANEL: Controls ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Scenario Library", className="fw-bold text-primary"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id="scenario-selector",
                        options=[{"label": v["label"], "value": k} for k, v in SCENARIO_LIBRARY.items()],
                        value="standard_correction",
                        clearable=False,
                        className="mb-3"
                    ),
                    
                    dbc.Accordion([
                        dbc.AccordionItem([
                            html.Label("Shock Magnitude", className="small fw-bold text-muted"),
                            dcc.Slider(id="shock-mag-slider", min=-0.50, max=-0.01, step=0.01, value=-0.10, marks={-0.5: "-50%", 0: "0%"}, tooltip={"placement": "bottom", "always_visible": False}, className="mb-3"),
                            
                            html.Label("Shock Duration (Days)", className="small fw-bold text-muted"),
                            dcc.Slider(id="shock-days-slider", min=1, max=100, step=1, value=15, marks={1: "1d", 100: "100d"}, className="mb-3"),
                            
                            html.Label("Recovery Duration (Days)", className="small fw-bold text-muted"),
                            dcc.Slider(id="recovery-days-slider", min=0, max=500, step=10, value=60, marks={0: "0d", 500: "500d"}, className="mb-3"),
                            
                            html.Hr(className="my-3"),
                            
                            html.Label("Target Sector Bias", className="small fw-bold text-muted"),
                            dcc.Dropdown(id="scenario-target-sector", options=[], value="All", clearable=False, className="mb-3"),
                            
                            html.Label("Sector Multiplier", className="small fw-bold text-muted"),
                            dcc.Slider(id="scenario-multiplier-slider", min=0.5, max=3.0, step=0.1, value=1.0, marks={0.5: "0.5x", 3.0: "3.0x"}),
                            
                        ], title="Custom Shock Builder", className="border-0 bg-transparent p-0")
                    ], start_collapsed=True, className="border-0")
                ])
            ], className="shadow-sm border-0 bg-surface h-100")
        ], lg=3, md=12, className="mb-4"),
        
        # --- RIGHT PANEL: Timeline & Resilience ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Simulated Recovery Timeline", className="fw-bold text-primary"),
                dbc.CardBody([
                    dcc.Loading(
                        dcc.Graph(id="scenario-timeline-chart", config=MODEBAR_CONFIG, style={"height": "350px"}),
                        type="circle", color="var(--accent-primary)"
                    )
                ], className="p-2")
            ], className="shadow-sm border-0 bg-surface mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Sector Resilience", className="fw-bold text-primary"),
                        dbc.CardBody([
                            dcc.Loading(
                                dcc.Graph(id="scenario-resilience-chart", config=MODEBAR_CONFIG, style={"height": "250px"}),
                                type="circle", color="var(--accent-primary)"
                            )
                        ], className="p-2")
                    ], className="shadow-sm border-0 bg-surface h-100")
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Systemic KPIs", className="fw-bold text-primary"),
                        dbc.CardBody([
                            html.Div(id="scenario-kpi-panel", className="h-100 d-flex flex-column justify-content-center")
                        ], className="p-3")
                    ], className="shadow-sm border-0 bg-surface h-100")
                ], md=6)
            ], className="g-3")
        ], lg=9, md=12, className="mb-4")
    ]),
    
    # --- BOTTOM PANEL: Company Data Table ---
    dbc.Row([
        dbc.Col([
            html.H6("COMPANY IMPACT RANKINGS", className="text-muted text-uppercase fw-bold mb-3 mt-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
            dbc.Card([
                dbc.CardBody(
                    dag.AgGrid(
                        id="scenario-impact-table",
                        dashGridOptions={"pagination": True, "paginationPageSize": 10, "domLayout": "autoHeight"},
                    ),
                    className="p-0"
                )
            ], className="shadow-sm border-0 bg-surface overflow-hidden")
        ], width=12)
    ])

], fluid=True, className="px-4 py-3")


@callback(
    Output("shock-mag-slider", "value"),
    Output("shock-days-slider", "value"),
    Output("recovery-days-slider", "value"),
    Output("scenario-target-sector", "value"),
    Output("scenario-multiplier-slider", "value"),
    Input("scenario-selector", "value")
)
def sync_scenario_library(scenario_id):
    if not scenario_id or scenario_id not in SCENARIO_LIBRARY:
        return no_update
        
    s = SCENARIO_LIBRARY[scenario_id]
    return s["shock_mag"], s["shock_days"], s["recovery_days"], s["target_sector"], s["multiplier"]


@callback(
    Output("scenario-timeline-chart", "figure"),
    Output("scenario-resilience-chart", "figure"),
    Output("scenario-kpi-panel", "children"),
    Output("scenario-impact-table", "rowData"),
    Output("scenario-impact-table", "columnDefs"),
    Output("scenario-impact-table", "className"),
    Output("scenario-smart-narrative", "children"),
    Input("shock-mag-slider", "value"),
    Input("shock-days-slider", "value"),
    Input("recovery-days-slider", "value"),
    Input("scenario-target-sector", "value"),
    Input("scenario-multiplier-slider", "value"),
    Input("theme-store", "data")
)
def update_simulation(shock_mag, shock_days, rec_days, target_sector, multiplier, theme):
    full_timeline, summary_df = run_scenario_simulation(shock_mag, shock_days, rec_days, target_sector, multiplier)
    
    if summary_df.empty:
        return create_empty_figure("No Data", theme=theme), create_empty_figure("No Data", theme=theme), html.Div("No Data"), [], [], html.Div("No Data"), ""
    selected_company = None

    fig_timeline = create_timeline_figure(full_timeline, selected_company, theme)
    fig_resilience = create_resilience_bar_chart(summary_df, theme)
    
    # KPIs
    avg_drawdown = summary_df["Max_Drawdown"].mean()
    recovered_count = (summary_df["Recovery_Days"] != -1).sum()
    total_count = len(summary_df)
    rec_pct = recovered_count / total_count
    
    avg_rec_days = summary_df[summary_df["Recovery_Days"] != -1]["Recovery_Days"].mean()
    if pd.isna(avg_rec_days): avg_rec_days = 0
    
    kpis = html.Div([
        dbc.Row([
            dbc.Col(create_stat_card("Avg Drawdown", f"{avg_drawdown:.2%}", "bi-graph-down-arrow", "danger"), width=6, className="mb-3"),
            dbc.Col(create_stat_card("Recovery Rate", f"{rec_pct:.1%}", "bi-check2-circle", "success"), width=6, className="mb-3"),
            dbc.Col(create_stat_card("Avg Recovery Time", f"{avg_rec_days:.0f} Days", "bi-clock-history", "info"), width=6, className="mb-3"),
            dbc.Col(create_stat_card("Total Days", f"{shock_days + rec_days}", "bi-calendar-event", "primary"), width=6, className="mb-3"),
        ])
    ])
    
    # DataTable
    df_display = summary_df.sort_values("Resilience_Score", ascending=False).round(4)
    df_display["Max_Drawdown"] = df_display["Max_Drawdown"].apply(lambda x: f"{x:.2%}")
    df_display["Recovery_Days"] = df_display["Recovery_Days"].apply(lambda x: "Never" if x == -1 else f"{x} Days")
    df_display["Resilience_Score"] = df_display["Resilience_Score"].apply(lambda x: f"{x:.1f}")
    
    tm_colors = ThemeManager.get_colors(theme)
    columns = [{"field": i, "headerName": i, "sortable": True} for i in df_display.columns]
    data = df_display.to_dict("records")
    
    # Smart Narrative
    worst_sector = summary_df.groupby("Sector")["Max_Drawdown"].mean().idxmin()
    best_sector = summary_df.groupby("Sector")["Max_Drawdown"].mean().idxmax()
    
    narrative_text = f"Simulation indicates {worst_sector} is the most vulnerable sector to this shock profile, while {best_sector} demonstrates the highest resilience. {rec_pct:.0%} of the market fully recovers within the timeframe."
    
    narrative_div = dbc.Alert([
        html.I(className="bi bi-shield-check text-info me-2"),
        html.Span(narrative_text, className="small fw-bold text-muted")
    ], color="secondary", className="border-0 shadow-sm py-2 px-3 bg-surface bg-opacity-50")
    
    return fig_timeline, fig_resilience, kpis, data, columns, "ag-theme-alpine-dark" if theme == "dark" else "ag-theme-alpine", narrative_div


@callback(
    Output("event-bus", "data", allow_duplicate=True),
    Input("scenario-impact-table", "cellClicked"),
    State("scenario-impact-table", "rowData"),
    prevent_initial_call=True
)
def handle_selections(cell_clicked, row_data):
    if cell_clicked and row_data:
        row_idx = cell_clicked.get("rowIndex")
        if row_idx is not None and row_idx < len(row_data):
            company = row_data[row_idx].get("Company")
            if company:
                return {"type": "OPEN_COMPANY_DRAWER", "payload": f"Company:{company}"}
    return no_update