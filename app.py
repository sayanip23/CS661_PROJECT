import dash
from dash import html
import dash_bootstrap_components as dbc

from components.navbar import create_navbar
from components.sidebar import create_sidebar

# =============================================================================
# DASH APP
# =============================================================================

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP
    ],
)

app.title = "NIFTY-50 Visual Analytics"






# =============================================================================
# MAIN CONTENT
# =============================================================================

content = html.Div(

    dash.page_container,

    className="content",

)

# =============================================================================
# APP LAYOUT
# =============================================================================

app.layout = html.Div(

    [

        create_navbar(),

        create_sidebar(),

        content,

    ]

)

# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    app.run(debug=False)
    