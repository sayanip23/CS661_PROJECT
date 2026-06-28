from dash import html
import dash_bootstrap_components as dbc


def create_hero():

    return dbc.Card(

        dbc.CardBody(

            [

                html.H1(
                    "NIFTY-50 Visual Analytics",
                    className="display-4 fw-bold"
                ),

                html.P(
                    "Interactive dashboard for exploring historical stock market behaviour using visual analytics.",
                    className="lead text-muted"
                ),

                dbc.Button(
                    "Explore Dashboard",
                    color="success",
                    size="lg",
                    className="me-3"
                ),

                dbc.Button(
                    "Project Overview",
                    color="outline-primary",
                    size="lg"
                ),

            ]

        ),

        className="shadow rounded-4 border-0 mb-4"

    )