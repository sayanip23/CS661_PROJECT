from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.visuals import apply_shared_layout
from utils.config import ThemeManager, MODEBAR_CONFIG

def create_market_snapshot(metrics, theme="dark"):
    colors = ThemeManager.get_colors(theme)
    
    # ------------------------------------------------------------------------------
    # Market Breadth Bar
    # ------------------------------------------------------------------------------
    adv = metrics["breadth"]["advancing"]
    dec = metrics["breadth"]["declining"]
    total = adv + dec
    
    adv_pct = (adv / total * 100) if total > 0 else 0
    dec_pct = (dec / total * 100) if total > 0 else 0
    
    breadth_bar = html.Div([
        html.Div([
            html.Span("Advancing", className="text-success small fw-bold"),
            html.Span("Declining", className="text-danger small fw-bold")
        ], className="d-flex justify-content-between mb-1"),
        dbc.Progress([
            dbc.Progress(value=adv_pct, color="success", bar=True),
            dbc.Progress(value=dec_pct, color="danger", bar=True)
        ], className="mb-1", style={"height": "12px"}),
        html.Div([
            html.Span(f"{adv} Stocks", className="text-muted small", style={"fontSize": "11px"}),
            html.Span(f"{dec} Stocks", className="text-muted small", style={"fontSize": "11px"})
        ], className="d-flex justify-content-between")
    ], className="mb-4")

    # ------------------------------------------------------------------------------
    # Mini Sparkline Trend
    # ------------------------------------------------------------------------------
    df_trend = metrics["market_trend"]
    if not df_trend.empty:
        fig = go.Figure(go.Scatter(
            x=df_trend["Date"],
            y=df_trend["Close"] / df_trend["Close"].iloc[0] * 100,
            mode="lines",
            line=dict(color=colors["info"], width=2),
            fill='tozeroy',
            fillcolor=colors["info"].replace("rgb", "rgba").replace(")", ", 0.1)") if "rgb" in colors["info"] else "rgba(41, 98, 255, 0.1)"
        ))
        
        fig = apply_shared_layout(
            fig,
            theme=theme,
            margin=dict(l=0, r=0, t=10, b=0),
            height=120,
            xaxis=dict(visible=False, fixedrange=True),
            yaxis=dict(visible=False, fixedrange=True),
            showlegend=False,
            hovermode="x unified"
        )
        trend_chart = dcc.Graph(figure=fig, config=MODEBAR_CONFIG)
    else:
        trend_chart = html.Div("No trend data available", className="text-muted small")

    # ------------------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------------------
    return dbc.Card([
        dbc.CardHeader("Market Snapshot", className="fw-bold text-primary bg-transparent border-0 pt-4 pb-0"),
        dbc.CardBody([
            html.H6("MARKET BREADTH", className="text-muted text-uppercase fw-bold mb-3", style={"letterSpacing": "1px", "fontSize": "11px"}),
            breadth_bar,
            
            html.H6("NIFTY-50 TREND (BASE 100)", className="text-muted text-uppercase fw-bold mb-2 mt-4", style={"letterSpacing": "1px", "fontSize": "11px"}),
            trend_chart
        ])
    ], className="shadow-sm border-0 bg-surface h-100")
