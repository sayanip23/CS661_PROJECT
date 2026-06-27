import dash
from dash import html

dash.register_page(
    __name__,
    path="/risk_return"
)

layout = html.Div(
    [
        html.H2("Risk Return Analysis"),
        html.P("Under Development")
    ]
)