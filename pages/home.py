import dash
<<<<<<< HEAD
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc

from components.cards import create_feature_card
from components.shared.cards import create_kpi_card
from components.home.hero import create_executive_hero
from components.home.movers import create_movers_section
from components.home.snapshot import create_market_snapshot
from utils.analytics.home import compute_executive_metrics
from utils.config import ThemeManager
=======
from dash import html, Input, Output, callback
import dash_bootstrap_components as dbc

from components.hero import create_hero
from components.cards import create_stat_card
from components.feature_card import create_feature_card
from components.workflow import create_workflow
from utils.database import run_query

# ============================
# Dashboard Statistics
# ============================

def get_stats(start_date=None, end_date=None, sector=None, company=None):
    conditions = []
    params = []
    if start_date is not None:
        conditions.append("Date >= CAST(? AS DATE)")
        params.append(start_date)
    if end_date is not None:
        conditions.append("Date <= CAST(? AS DATE)")
        params.append(end_date)
    if sector is not None:
        conditions.append("Sector = ?")
        params.append(sector)
    if company is not None:
        conditions.append("Company = ?")
        params.append(company)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
    SELECT
        COUNT(DISTINCT Company) AS num_stocks,
        COUNT(DISTINCT Sector) AS num_sectors,
        COUNT(DISTINCT EXTRACT(YEAR FROM Date)) AS num_years,
        COUNT(*) AS num_records
    FROM clean_stock_data
    {where_clause}
    """
    return run_query(query, tuple(params) if params else None)


stats = get_stats()

num_stocks = int(stats.loc[0, "num_stocks"])
num_sectors = int(stats.loc[0, "num_sectors"])
num_years = int(stats.loc[0, "num_years"])
num_records = int(stats.loc[0, "num_records"])
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474

dash.register_page(__name__, path="/")

def create_kpi_overview(metrics):
    return dbc.Row([
        dbc.Col(create_kpi_card("Total Companies", str(metrics["num_stocks"]), "bi-building-fill", "primary"), lg=2, md=4, sm=6, className="mb-4"),
        dbc.Col(create_kpi_card("Total Sectors", str(metrics["num_sectors"]), "bi-diagram-3-fill", "info"), lg=2, md=4, sm=6, className="mb-4"),
        dbc.Col(create_kpi_card("Average Return", f"{metrics['avg_return']:.2%}", "bi-graph-up-arrow", "success"), lg=2, md=4, sm=6, className="mb-4"),
        dbc.Col(create_kpi_card("Avg Volatility", f"{metrics['avg_vol']:.1%}", "bi-activity", "warning"), lg=2, md=4, sm=6, className="mb-4"),
        dbc.Col(create_kpi_card("Highest CAGR", f"{metrics['highest_cagr_name']} ({metrics['highest_cagr']:.1%})", "bi-star-fill", "success"), lg=2, md=4, sm=6, className="mb-4"),
        dbc.Col(create_kpi_card("Best Sector", metrics["best_sector"], "bi-trophy-fill", "primary"), lg=2, md=4, sm=6, className="mb-4"),
    ])

def create_quick_navigation():
    return html.Div([
        html.H6("QUICK NAVIGATION", className="fw-bold text-muted mb-3 mt-4 text-uppercase", style={"letterSpacing": "1px", "fontSize": "11px"}),
        dbc.Row([
            dbc.Col(create_feature_card(
                "Treemap Analytics", 
                "Explore market capitalization and performance hierarchically.",
                "bi bi-layout-wtf",
                "/treemap"
            ), md=6, lg=3, className="mb-4"),
            
            dbc.Col(create_feature_card(
                "Correlation Matrix", 
                "Discover hidden sector couplings using K-Means clustered returns.",
                "bi bi-grid-3x3-gap-fill",
                "/correlation"
            ), md=6, lg=3, className="mb-4"),
            
            dbc.Col(create_feature_card(
                "Risk vs Return", 
                "Map out optimal Sharpe clusters on a volatility frontier.",
                "bi bi-graph-up-arrow",
                "/risk_return"
            ), md=6, lg=3, className="mb-4"),
            
            dbc.Col(create_feature_card(
                "Market Shocks", 
                "Detect systemic anomalies via Z-Score divergence.",
                "bi bi-lightning-charge-fill",
                "/market_shock"
            ), md=6, lg=3, className="mb-4"),
        ])
    ])

def create_dashboard_status(metrics, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Span("SYSTEM STATUS", className="text-muted text-uppercase fw-bold small", style={"letterSpacing": "1px"}),
                ], width="auto"),
                dbc.Col([
                    html.I(className="bi bi-circle-fill text-success me-2 small"),
                    html.Span("All Systems Operational", className="text-success small fw-bold")
                ], width="auto", className="ms-auto"),
            ], className="align-items-center mb-3"),
            
            dbc.Row([
                dbc.Col([html.Span("Data Version:", className="text-muted small"), html.Span(f" {metrics['last_updated']}", className="small fw-bold ms-2", style={"color": colors["text_primary"]})], width="auto", className="me-4"),
                dbc.Col([html.Span("Total Records:", className="text-muted small"), html.Span(f" {metrics['num_records']:,}", className="small fw-bold ms-2", style={"color": colors["text_primary"]})], width="auto", className="me-4"),
                dbc.Col([html.Span("Active Theme:", className="text-muted small"), html.Span(f" {theme.capitalize()}", className="small fw-bold ms-2", style={"color": colors["text_primary"]})], width="auto"),
            ])
        ])
    ], className="shadow-sm border-0 bg-surface mb-5")

def layout():
    # We fetch metrics synchronously for initial render
    # Caching ensures this is virtually instant after first run
    metrics = compute_executive_metrics()
    
    return dbc.Container([
        html.Div(id="home-dashboard-content")
    ], fluid=True, className="py-4")

@callback(
    Output("home-dashboard-content", "children"),
    Input("theme-store", "data")
)
def update_home_layout(theme):
    metrics = compute_executive_metrics()
    
    return html.Div([
        # SECTION 1: HERO (MARKET AT A GLANCE)
        create_executive_hero(metrics, theme),
        
<<<<<<< HEAD
        # SECTION 2: EXECUTIVE KPI OVERVIEW
        create_kpi_overview(metrics),
        
        # SECTION 3 & 4: MARKET SNAPSHOT & TRENDS + SECTION 5: MOVERS
        dbc.Row([
            dbc.Col(create_market_snapshot(metrics, theme), lg=4, className="mb-4"),
            dbc.Col(html.Div([
                html.H6("MARKET MOVERS", className="fw-bold text-muted mb-3 text-uppercase", style={"letterSpacing": "1px", "fontSize": "11px"}),
                create_movers_section(metrics, theme)
            ]), lg=8, className="mb-4")
        ]),
        
        # SECTION 6: QUICK NAVIGATION
        create_quick_navigation(),
        
        # SECTION 7: DASHBOARD STATUS
        create_dashboard_status(metrics, theme)
    ])
=======

        # ============================================================
        # Dashboard Statistics
        # ============================================================

        html.H3(
            "Dashboard Overview",
            className="fw-bold mb-4"
        ),

        dbc.Row(

            [

                dbc.Col(
                    create_stat_card(
                        "Stocks",
                        str(num_stocks),
                        "bi bi-graph-up-arrow",
                        "success",
                        value_id="stat-stocks-value",
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Sectors",
                        str(num_sectors),
                        "bi bi-building",
                        "primary",
                        value_id="stat-sectors-value",
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Years",
                        str(num_years),
                        "bi bi-calendar3",
                        "warning",
                        value_id="stat-years-value",
                    ),
                    md=3
                ),

                dbc.Col(
                    create_stat_card(
                        "Records",
                        str(num_records),
                        "bi bi-database",
                        "danger",
                        value_id="stat-records-value",
                    ),
                    md=3
                ),

            ],

            className="mb-3"

        ),

        dbc.Alert(
            [
                html.I(className="bi bi-info-circle-fill me-2"),
                html.B("Dataset Note: "),
                "Historical trading data for ",
                html.B("Infratel"),
                " was unavailable in the collected dataset. "
                "Therefore, all visualizations and analyses are based on ",
                html.B("49 companies"),
                " instead of the complete NIFTY-50."
            ],
          color="light",
          className="shadow-sm border-start border-4 border-primary mt-2 mb-4",
        )

    ],

    fluid=True

)


@callback(
    Output("stat-stocks-value", "children"),
    Output("stat-sectors-value", "children"),
    Output("stat-years-value", "children"),
    Output("stat-records-value", "children"),
    Input("start-date-filter", "value"),
    Input("end-date-filter", "value"),
    Input("sector-filter", "value"),
    Input("company-filter", "value"),
)
def update_stats(start_date, end_date, sector, company):
    filtered = get_stats(start_date=start_date, end_date=end_date, sector=sector, company=company)
    return (
        str(int(filtered.loc[0, "num_stocks"])),
        str(int(filtered.loc[0, "num_sectors"])),
        str(int(filtered.loc[0, "num_years"])),
        str(int(filtered.loc[0, "num_records"])),
    )
>>>>>>> 6b1a46747fde769582d0d639f05459894af4b474
