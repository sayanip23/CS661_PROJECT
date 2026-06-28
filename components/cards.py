from dash import html
import dash_bootstrap_components as dbc


def create_stat_card(title, value, icon, color="primary"):
    """
    Reusable dashboard statistic card.

    Parameters
    ----------
    title : str
        Card title

    value : str
        Main value

    icon : str
        Bootstrap icon class

    color : str
        Bootstrap text color
    """

    return dbc.Card(

        dbc.CardBody(

            [

                html.Div(

                    html.I(
                        className=icon,
                        style={"fontSize": "40px"}
                    ),

                    className=f"text-{color} text-center mb-3"

                ),

                html.H6(
                    title,
                    className="text-center text-muted"
                ),

                html.H3(
                    value,
                    className=f"text-center text-{color} fw-bold"
                )

            ]

        ),

        className="shadow-sm rounded-4 border-0 h-100"

    )