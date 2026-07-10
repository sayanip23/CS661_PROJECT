from dash import html
import dash_bootstrap_components as dbc

PAGES = [
    ("Home", "/", "bi bi-house-fill"),
    ("Correlation Heatmap", "/correlation", "bi bi-grid-3x3-gap-fill"),
    ("Risk vs Return", "/risk_return", "bi bi-bar-chart-fill"),
    ("Market Shock", "/market_shock", "bi bi-lightning-fill"),
    ("Sector Rotation", "/sector_rotation", "bi bi-arrow-repeat"),
    ("Treemap", "/treemap", "bi bi-diagram-3-fill"),
]

def create_sidebar():
    return html.Div(
        [
            html.Div("ANALYTICS", className="text-muted small fw-bold mb-3 ms-2 nav-text", style={"letterSpacing": "1px"}),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [
                            html.I(className=f"{icon} fs-5"),
                            # Added 'nav-text' class so CSS can hide this span on collapse
                            html.Span(name, className="ms-3 nav-text"), 
                        ],
                        href=path,
                        active="exact",
                        className="nav-link-custom d-flex align-items-center mb-1",
                    )
                    for name, path, icon in PAGES
                ],
                vertical=True,
                pills=True,
            ),
        ]
    )