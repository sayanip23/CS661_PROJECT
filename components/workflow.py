from dash import html
import dash_bootstrap_components as dbc


def create_workflow():

    steps = [

        "Raw Data",

        "Cleaning",

        "Preprocessing",

        "Visual Analytics",

        "Insights"

    ]

    cards = []

    for i, step in enumerate(steps):

        cards.append(

            dbc.Col(

                dbc.Card(

                    dbc.CardBody(

                        html.H5(
                            step,
                            className="text-center"
                        )

                    ),

                    className="shadow-sm rounded-4 border-0"

                ),

                width=2

            )

        )

        if i != len(steps)-1:

            cards.append(

                dbc.Col(

                    html.H2(
                        "→",
                        className="text-center text-success"
                    ),

                    width=0.5

                )

            )

    return dbc.Row(cards, className="align-items-center")