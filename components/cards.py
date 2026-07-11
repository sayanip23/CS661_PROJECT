from dash import html
import dash_bootstrap_components as dbc


def create_stat_card(title, value, icon, color="primary"):
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
        className="h-100" # Let CSS handle .card borders/backgrounds
    )


def create_feature_card(title, description, icon, link):
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