import dash
from dash import html

dash.register_page(__name__)

layout = html.Div(
    [
        html.H2("Correlation Heatmap"),
        html.P("Under Development")
    ]
)