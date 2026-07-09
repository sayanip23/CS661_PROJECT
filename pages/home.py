import dash
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

dash.register_page(__name__, path="/")

layout = dbc.Container(

    [

        # ============================================================
        # Hero Section
        # ============================================================

        create_hero(),

        

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