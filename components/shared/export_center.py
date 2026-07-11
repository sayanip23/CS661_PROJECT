import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
import pandas as pd

def create_export_center():
    return html.Div([
        # Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([html.I(className="bi bi-cloud-download me-2"), "Export Center"])),
            dbc.ModalBody([
                html.P("Download your current analytical context and data.", className="text-muted small"),
                
                html.Div([
                    dbc.Button([html.I(className="bi bi-list-columns me-2"), "Export Comparison State (CSV)"], id="export-btn-comparison", color="secondary", outline=True, className="w-100 mb-3 text-start"),
                ], className="mt-4"),
                
            ]),
        ],
        id="export-center-modal",
        is_open=False,
        centered=True,
        ),
        
        dcc.Download(id="download-dataframe-csv"),
    ])

@callback(
    Output("export-center-modal", "is_open"),
    Input("export-center-toggle", "n_clicks"),
    State("export-center-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_export_modal(n_clicks, is_open):
    return not is_open

@callback(
    Output("download-dataframe-csv", "data"),
    Output("notification-bus", "data", allow_duplicate=True),
    Input("export-btn-comparison", "n_clicks"),
    State("comparison-state", "data"),
    prevent_initial_call=True
)
def export_data(comp_clicks, comparison):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update
        
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "export-btn-comparison":
        if not comparison:
            return no_update, {"message": "Comparison is empty", "type": "warning", "icon": "bi-exclamation-triangle"}
        df = pd.DataFrame([{"Company": c} for c in comparison])
        return dcc.send_data_frame(df.to_csv, "comparison.csv", index=False), {"message": "Comparison exported", "type": "success", "icon": "bi-check-circle"}
        
    return no_update, no_update
