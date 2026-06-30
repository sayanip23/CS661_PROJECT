from dash import html
import dash_bootstrap_components as dbc


def create_hero():

    return dbc.Card(

        dbc.CardBody(

            [

                html.H1(
                    "NIFTY-50 Visual Analytics",
                    className="display-5 fw-bold mb-2"
                ),

                html.P(
                    "Interactive dashboard for exploring historical stock market behaviour using visual analytics.",
                    className="lead text-muted mb-0"
                ),

            ],

            className="py-3 px-4"

        ),

        className="shadow rounded-4 border-0 mb-3"

    )