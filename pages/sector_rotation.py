import dash
from dash import html

dash.register_page(
    __name__,
    path="/sector_rotation"
)

layout = html.Div(
    [
        html.H2("Sector Rotation"),
        html.P("Under Development")
    ]
)