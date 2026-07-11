from dash import html, dcc
import dash_bootstrap_components as dbc

def create_year_range_filter(id_prefix, min_year=2000, max_year=2022):
    """Generic year range filter with a slider and input boxes."""
    return html.Div([
        html.Span(str(min_year), className="static-bound-label text-muted fw-bold small me-2"),
        dcc.Input(id=f"{id_prefix}-min-box", type="number", min=min_year, max=max_year, step=1, value=min_year, 
                  className="form-control text-center p-0", 
                  style={"width": "45px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "24px", "fontSize": "12px"}),
        dcc.RangeSlider(
            id=f"{id_prefix}-slider", min=min_year, max=max_year, step=1, 
            value=[min_year, max_year],
            marks=None, tooltip={"placement": "bottom", "always_visible": False},
            className="slider-track flex-grow-1 mx-2"
        ),
        dcc.Input(id=f"{id_prefix}-max-box", type="number", min=min_year, max=max_year, step=1, value=max_year, 
                  className="form-control text-center p-0", 
                  style={"width": "45px", "fontWeight": "bold", "color": "black", "backgroundColor": "white", "height": "24px", "fontSize": "12px"}),
        html.Span(str(max_year), className="static-bound-label text-muted fw-bold small ms-2"),
    ], className="d-flex align-items-center mb-4")

def create_metric_toggle(id_prefix, options, default_value, label="Metric"):
    """Generic radio buttons toggle for metrics."""
    return html.Div([
        html.Div(label, className="fw-bold text-muted small mb-1"),
        dbc.RadioItems(
            id=id_prefix,
            options=options,
            value=default_value, inline=True, className="mb-3 btn-group w-100", 
            inputClassName="btn-check", 
            labelClassName="btn btn-outline-primary btn-sm transition-all py-1"
        )
    ])
