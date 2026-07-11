import plotly.graph_objects as go
from utils.config import get_plotly_template, ThemeManager

def apply_shared_layout(fig: go.Figure, title: str = None, theme: str = "dark", **kwargs) -> go.Figure:
    """
    Applies the central theme and layout configuration to any Plotly figure.
    This eliminates the duplicated update_layout calls across all pages.
    """
    colors = ThemeManager.get_colors(theme)
    
    layout_update = dict(
        template=f"financial_{theme}",
        margin=dict(l=40, r=20, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    if title:
        layout_update["title"] = title
        
    layout_update.update(kwargs)
    
    fig.update_layout(**layout_update)
    return fig

def create_empty_figure(message: str = "No data available", theme: str = "dark") -> go.Figure:
    """Creates a standard empty figure to display when data is missing."""
    fig = go.Figure()
    fig = apply_shared_layout(fig, theme=theme)
    fig.update_layout(
        title=message,
        xaxis_visible=False,
        yaxis_visible=False
    )
    return fig
