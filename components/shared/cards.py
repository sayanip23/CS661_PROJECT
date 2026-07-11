from dash import html
import dash_bootstrap_components as dbc

def create_kpi_card(title, value, icon, color="primary"):
    """Generic KPI card used across the dashboard."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div([
                    html.Div([
                        html.H6(title, className="text-muted text-uppercase fw-bold mb-1", style={"fontSize": "11px", "letterSpacing": "1px"}),
                        html.H3(value, className="mb-0 font-mono tabular-nums")
                    ]),
                    html.Div(
                        html.I(className=f"{icon} text-{color}", style={"fontSize": "24px"}),
                        className=f"p-2 bg-{color} bg-opacity-10 rounded-3 d-flex align-items-center justify-content-center",
                        style={"width": "48px", "height": "48px"}
                    )
                ], className="d-flex justify-content-between align-items-center")
            ]
        ),
        className="h-100"
    )

def create_feature_card(title, description, icon, link):
    """Generic feature card for navigation or external links."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.I(className=f"{icon} text-primary mb-3 d-block", style={"fontSize": "32px"}),
                html.H5(title, className="fw-bold mb-2"),
                html.P(description, className="text-muted small mb-4", style={"minHeight": "60px"}),
                dbc.Button("Launch Tool", href=link, color="primary", outline=True, className="w-100 fw-bold")
            ],
            className="p-4"
        ),
        className="h-100 feature-card"
    )

def create_insight_card(title, content):
    """Generic card for displaying insights, smart narratives, or AI-generated text."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(className="bi bi-lightbulb-fill text-warning fs-5"),
                        html.H6(title, className="fw-bold mb-0 text-primary font-mono ms-2")
                    ],
                    className="d-flex align-items-center mb-2"
                ),
                html.P(content, className="text-muted small mb-0")
            ],
            className="p-3"
        ),
        className="mb-3 border border-secondary border-opacity-25 bg-transparent shadow-none rounded-3"
    )
