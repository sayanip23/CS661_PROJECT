from dash import html
import dash_bootstrap_components as dbc


def create_stat_card(title, value, icon, color="primary"):

    return dbc.Card(

        dbc.CardBody(

            [

                html.Div(

                    html.I(
                        className=icon,
                        style={"fontSize": "34px"}
                    ),

                    className=f"text-{color} text-center mb-2"

                ),

                html.H6(
                    title,
                    className="text-center text-muted mb-2"
                ),

                html.H3(
                    value,
                    className=f"text-center text-{color} fw-bold mb-0"
                )

            ],

            className="py-3"

        ),

        className="shadow-sm rounded-4 border-0 h-100"

    )