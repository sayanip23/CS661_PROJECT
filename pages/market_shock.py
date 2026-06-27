import dash
from dash import html

dash.register_page(
    __name__,
    path="/market_shock"
)

layout = html.Div(
    [
        html.H2("Market Shock Detection"),
        html.P("Under Development")
    ]
)