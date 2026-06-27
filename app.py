import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

sidebar = dbc.Nav(
    [
        dbc.NavLink("Home", href="/", active="exact"),
        dbc.NavLink("Correlation", href="/correlation", active="exact"),
        dbc.NavLink("Risk Return", href="/risk_return", active="exact"),
        dbc.NavLink("Market Shock", href="/market_shock", active="exact"),
        dbc.NavLink("Sector Rotation", href="/sector_rotation", active="exact"),
        dbc.NavLink("Treemap", href="/treemap", active="exact"),
    ],
    vertical=True,
    pills=True,
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=2),
                dbc.Col(dash.page_container, width=10),
            ]
        )
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run(debug=True)