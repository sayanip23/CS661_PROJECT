from dash import html
import dash_bootstrap_components as dbc


def create_feature_card(title, description, icon, link):

    return dbc.Card(

        dbc.CardBody(

            [

                html.Div(

                    html.I(
                        className=icon,
                        style={"fontSize": "45px"}
                    ),

                    className="text-success mb-3"

                ),

                html.H5(title),

                html.P(
                    description,
                    className="text-muted"
                ),

                dbc.Button(

                    "Open",

                    href=link,

                    color="primary",

                    className="mt-2"

                )

            ]

        ),

        className="shadow-sm rounded-4 border-0 h-100"

    )