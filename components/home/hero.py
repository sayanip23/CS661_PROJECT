from dash import html
import dash_bootstrap_components as dbc
from utils.config import ThemeManager

def create_executive_hero(metrics, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    
    # ------------------------------------------------------------------------------
    # Market Health Score
    # ------------------------------------------------------------------------------
    score = metrics["health_score"]
    status = metrics["health_status"]
    
    if score >= 80:
        health_color = "success"
    elif score >= 60:
        health_color = "primary"
    elif score >= 40:
        health_color = "warning"
    else:
        health_color = "danger"

    health_section = html.Div([
        html.H6("MARKET HEALTH", className="text-muted text-uppercase fw-bold mb-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
        html.Div([
            html.Span(f"{score}", className=f"text-{health_color} fw-bold", style={"fontSize": "48px", "lineHeight": "1"}),
            html.Span("/100", className="text-muted ms-1", style={"fontSize": "18px"})
        ], className="d-flex align-items-baseline mb-2"),
        dbc.Progress(value=score, color=health_color, className="mb-2", style={"height": "6px"}),
        html.Div([
            html.Span("Status: ", className="text-muted small"),
            html.Span(status, className=f"text-{health_color} fw-bold small")
        ])
    ])

    # ------------------------------------------------------------------------------
    # Market Direction Indicator
    # ------------------------------------------------------------------------------
    direction = metrics["direction"]
    if direction == "Bullish":
        dir_icon = "bi-arrow-up-right-circle-fill"
        dir_color = "success"
    elif direction == "Bearish":
        dir_icon = "bi-arrow-down-right-circle-fill"
        dir_color = "danger"
    else:
        dir_icon = "bi-dash-circle-fill"
        dir_color = "warning"

    direction_section = html.Div([
        html.H6("DIRECTION", className="text-muted text-uppercase fw-bold mb-3", style={"letterSpacing": "1px", "fontSize": "11px"}),
        html.Div([
            html.I(className=f"bi {dir_icon} text-{dir_color} me-3", style={"fontSize": "32px"}),
            html.Span(direction, className=f"text-{dir_color} fw-bold", style={"fontSize": "24px"})
        ], className="d-flex align-items-center")
    ])

    # ------------------------------------------------------------------------------
    # Market Summary & Key Insight
    # ------------------------------------------------------------------------------
    summary_section = html.Div([
        html.H6("EXECUTIVE SUMMARY", className="text-muted text-uppercase fw-bold mb-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
        html.P(metrics["summary"], style={"fontSize": "15px", "color": colors["text_primary"], "lineHeight": "1.6"}, className="mb-3"),
        
        html.H6("KEY INSIGHT", className="text-muted text-uppercase fw-bold mb-2", style={"letterSpacing": "1px", "fontSize": "11px"}),
        html.Div([
            html.I(className="bi bi-lightbulb-fill text-warning me-2"),
            html.Span(metrics["insight"], className="fw-bold", style={"fontSize": "14px", "color": colors["text_primary"]})
        ], className="p-3 rounded bg-warning bg-opacity-10 border border-warning border-opacity-25")
    ])

    # ------------------------------------------------------------------------------
    # Final Assembly
    # ------------------------------------------------------------------------------
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                # Health Score Column
                dbc.Col(health_section, lg=3, md=6, className="mb-4 mb-lg-0 border-end border-secondary border-opacity-25"),
                
                # Direction Column
                dbc.Col(direction_section, lg=3, md=6, className="mb-4 mb-lg-0 border-end border-secondary border-opacity-25 px-lg-4"),
                
                # Summary & Insight Column
                dbc.Col(summary_section, lg=6, md=12, className="px-lg-4")
            ]),
            
            # Footer / Last Updated
            html.Div([
                html.Span(f"Last Updated: {metrics['last_updated']}", className="text-muted small"),
                html.Span(" • ", className="text-muted mx-2"),
                html.Span("Status: ", className="text-muted small"),
                html.Span("Online", className="text-success small fw-bold")
            ], className="mt-4 pt-3 border-top border-secondary border-opacity-25 text-end")
        ]),
        className="shadow-sm border-0 bg-surface mb-4"
    )
