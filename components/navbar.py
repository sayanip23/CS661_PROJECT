# =============================================================================
# NAVBAR
# =============================================================================

from dash import html
import dash_bootstrap_components as dbc


def create_navbar():

    return dbc.Navbar(

        dbc.Container(

            [

                

                html.Div(

                    "CS661 • IIT Kanpur",

                    className="navbar-subtitle",

                ),

            ],

            fluid=True,

        ),

        color="dark",

        dark=True,

        fixed="top",

        className="navbar-custom",

    )