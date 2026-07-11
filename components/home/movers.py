from dash import html
import dash_bootstrap_components as dbc
from utils.config import ThemeManager

def _format_metric(val):
    color = "text-success" if val > 0 else ("text-danger" if val < 0 else "text-muted")
    icon = "bi-arrow-up-right" if val > 0 else ("bi-arrow-down-right" if val < 0 else "bi-dash")
    sign = "+" if val > 0 else ""
    return html.Div([
        html.I(className=f"bi {icon} {color} me-2 small flex-shrink-0"),
        html.Span(f"{sign}{val:.2%}", className=f"{color} fw-bold font-mono flex-shrink-0")
    ], className="d-flex align-items-center justify-content-end", style={"flex": "0 0 auto"})

def _create_ranking_list(items, name_key, val_key, theme):
    colors = ThemeManager.get_colors(theme)
    list_items = []
    for i, item in enumerate(items):
        list_items.append(
            dbc.ListGroupItem([
                html.Div([
                    html.Span(f"#{i+1}", className="text-muted small fw-bold me-3 flex-shrink-0", style={"width": "20px"}),
                    html.Span(item[name_key], className="fw-bold text-truncate", style={"color": colors["text_primary"]}),
                ], className="d-flex align-items-center flex-grow-1", style={"minWidth": "0", "marginRight": "10px"}),
                _format_metric(item[val_key])
            ], className="d-flex justify-content-between align-items-center py-2 px-3 border-0 border-bottom border-secondary border-opacity-10 bg-transparent")
        )
    return dbc.ListGroup(list_items, flush=True, className="rounded")

def create_movers_section(metrics, theme="dark"):
    return dbc.Row([
        # Companies
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top Companies (CAGR)", className="fw-bold text-success bg-transparent border-0 pt-3 pb-0"),
                dbc.CardBody(_create_ranking_list(metrics["top_companies"], "Company", "CAGR", theme), className="p-2")
            ], className="shadow-sm border-0 bg-surface h-100"),
            lg=6, md=12, className="mb-4"
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Bottom Companies (CAGR)", className="fw-bold text-danger bg-transparent border-0 pt-3 pb-0"),
                dbc.CardBody(_create_ranking_list(metrics["bottom_companies"], "Company", "CAGR", theme), className="p-2")
            ], className="shadow-sm border-0 bg-surface h-100"),
            lg=6, md=12, className="mb-4"
        ),
        # Sectors
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top Sectors (CAGR)", className="fw-bold text-success bg-transparent border-0 pt-3 pb-0"),
                dbc.CardBody(_create_ranking_list(metrics["top_sectors"], "Sector", "CAGR", theme), className="p-2")
            ], className="shadow-sm border-0 bg-surface h-100"),
            lg=6, md=12, className="mb-4"
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Bottom Sectors (CAGR)", className="fw-bold text-danger bg-transparent border-0 pt-3 pb-0"),
                dbc.CardBody(_create_ranking_list(metrics["bottom_sectors"], "Sector", "CAGR", theme), className="p-2")
            ], className="shadow-sm border-0 bg-surface h-100"),
            lg=6, md=12, className="mb-4"
        ),
    ])
