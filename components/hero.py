from dash import html
import dash_bootstrap_components as dbc

def create_hero():
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div([
                    html.H1(
                        "NIFTY-50 Quantitative Analytics",
                        className="display-6 fw-bold mb-3 text-primary"
                    ),
                    html.P(
                        "Institutional-grade dashboard for exploring historical stock market behaviour. "
                        "Leverage clustering, cross-sectional dispersion, and relative rotation to uncover systemic anomalies.",
                        className="lead text-muted mb-4",
                        style={"maxWidth": "800px"}
                    ),
                    html.Div([
                        dbc.Button(
                            [html.I(className="bi bi-grid-3x3-gap-fill me-2"), "Explore Correlations"], 
                            href="/correlation", color="primary", className="me-3 px-4 py-2 fw-bold"
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-arrow-repeat me-2"), "View Sector Rotation"], 
                            href="/sector_rotation", outline=True, color="primary", className="px-4 py-2 fw-bold"
                        ),
                    ], className="d-flex align-items-center")
                ])
            ],
            className="p-5"
        ),
        className="mb-4 border-0"
    )