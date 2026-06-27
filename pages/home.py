import dash
from dash import html

dash.register_page(__name__, path="/")

layout = html.Div(
    [
        html.H1("NIFTY-50 Visual Analytics"),
        html.Hr(),
        html.H3("CS661 Course Project"),
        html.P("Interactive Visual Analytics Dashboard")
    ]
)