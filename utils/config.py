"""
utils/config.py

Centralized configuration for the NIFTY-50 Visual Analytics Dashboard.
Single source of truth for paths, default values, color palettes,
and shared chart layout settings.
"""

import os

# ===========================================================================
# File Paths
# ===========================================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "stocks.duckdb")
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "clean_stock_data.csv")
MASTER_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "master_stock_data.csv")
REPORT_PATH = os.path.join(PROJECT_ROOT, "docs", "data_quality_report.md")

# ===========================================================================
# Default Parameters
# ===========================================================================
DEFAULT_N_CLUSTERS = 5
DEFAULT_LINKAGE_METHOD = "average"
MIN_OVERLAP_PERIODS = 60

# ===========================================================================
# Color Palettes
# ===========================================================================

class ThemeManager:
    @staticmethod
    def get_colors(theme="dark"):
        if theme == "light":
            return {
                "bg_surface": "#ffffff",
                "bg_elevated": "#e9ecef",
                "text_primary": "#1f2937",
                "text_secondary": "#4b5563",
                "grid": "#e5e7eb",
                "zeroline": "#d1d5db",
                "success": "#10b981",
                "danger": "#ef4444",
                "warning": "#f59e0b",
                "info": "#3b82f6",
                "crosshair": "#4b5563",
                "trail": "rgba(0, 0, 0, 0.1)",
                "quant_mid": "#e5e7eb",
                "corr_mid": "rgb(220,220,220)"
            }
        else:
            return {
                "bg_surface": "#131418",
                "bg_elevated": "#1e1f26",
                "text_primary": "#e2e4e9",
                "text_secondary": "#9499a6",
                "grid": "#2a2c33",
                "zeroline": "#3d404a",
                "success": "#21ce99",
                "danger": "#f23645",
                "warning": "#ff9800",
                "info": "#2962ff",
                "crosshair": "#555555",
                "trail": "rgba(255, 255, 255, 0.1)",
                "quant_mid": "#000000",
                "corr_mid": "rgb(247,247,247)"
            }

def get_corr_colorscale(theme="dark"):
    colors = ThemeManager.get_colors(theme)
    return [
        [0.0, "rgb(33,102,172)"],
        [0.25, "rgb(103,169,207)"],
        [0.5, colors["corr_mid"]],
        [0.75, "rgb(239,138,98)"],
        [1.0, "rgb(178,24,43)"],
    ]

def get_quant_colorscale(theme="dark"):
    # Multi-stop colorscale for Treemaps to fix dullness around zero
    if theme == "light":
        return [
            [0.0, "#b91c1c"],     # Deep Red (Extreme Loss)
            [0.45, "#ef4444"],    # Bright Red (Normal Loss)
            [0.49, "#fca5a5"],    # Light Red (Slight Loss)
            [0.5, "#f3f4f6"],     # Neutral (Zero)
            [0.51, "#86efac"],    # Light Green (Slight Gain)
            [0.55, "#10b981"],    # Bright Green (Normal Gain)
            [1.0, "#047857"],     # Deep Green (Extreme Gain)
        ]
    else:
        return [
            [0.0, "#7f1d1d"],     # Deep Red
            [0.45, "#ef4444"],    # Bright Red
            [0.49, "#451a1e"],    # Dark Red
            [0.5, "#1f2937"],     # Neutral Dark
            [0.51, "#143a2a"],    # Dark Green
            [0.55, "#21ce99"],    # Bright Green
            [1.0, "#064e3b"],     # Deep Green
        ]

def get_cluster_colors(theme="dark"):
    # High-contrast, color-blind friendly categorical palette
    if theme == "light":
        return {
            "0": "#3b82f6", # Blue
            "1": "#10b981", # Green
            "2": "#f59e0b", # Amber
            "3": "#8b5cf6", # Purple
        }
    else:
        return {
            "0": "#60a5fa", # Light Blue
            "1": "#34d399", # Light Green
            "2": "#fbbf24", # Light Amber
            "3": "#a78bfa", # Light Purple
        }

# ===========================================================================
# Standard Analytics Interaction Framework (Phase 4)
# ===========================================================================

# Consistent Tooltip HTML structure across all visualizations
# (Removed unused HOVER_TEMPLATE_HTML)

# Standard Animation Frame Config for smooth playback
ANIMATION_CONFIG = dict(
    frame=dict(duration=400, redraw=True),
    transition=dict(duration=250, easing="cubic-in-out")
)

# ===========================================================================
# Chart Layout (Financial Theme — shared across all pages)
# ===========================================================================
def get_plotly_template(theme="dark"):
    colors = ThemeManager.get_colors(theme)
    return dict(
        paper_bgcolor=colors["bg_surface"],
        plot_bgcolor=colors["bg_surface"],
        font=dict(family="Inter, sans-serif", color=colors["text_primary"], size=12),
        margin=dict(l=40, r=20, t=40, b=30),
        hoverlabel=dict(
            bgcolor=colors["bg_elevated"],
            font_size=13,
            font_family="JetBrains Mono, monospace"
        ),
        xaxis=dict(
            showgrid=True, gridcolor=colors["grid"], zerolinecolor=colors["zeroline"],
            tickfont=dict(family="JetBrains Mono, monospace", color=colors["text_secondary"])
        ),
        yaxis=dict(
            showgrid=True, gridcolor=colors["grid"], zerolinecolor=colors["zeroline"],
            tickfont=dict(family="JetBrains Mono, monospace", color=colors["text_secondary"])
        )
    )

def get_rrg_quadrants(theme="dark"):
    colors = ThemeManager.get_colors(theme)
    font_weight = "bold"
    # Make quadrant labels slightly muted but legible
    q_colors = {
        "success": "#10b981" if theme == "light" else "#34d399",
        "warning": "#f59e0b" if theme == "light" else "#fbbf24",
        "danger": "#ef4444" if theme == "light" else "#f87171",
        "info": "#3b82f6" if theme == "light" else "#60a5fa",
    }
    return [
        dict(x=111, y=111, text="LEADING", font=dict(color=q_colors["success"], size=16, family="JetBrains Mono")),
        dict(x=111, y=89, text="WEAKENING", font=dict(color=q_colors["warning"], size=16, family="JetBrains Mono")),
        dict(x=89, y=89, text="LAGGING", font=dict(color=q_colors["danger"], size=16, family="JetBrains Mono")),
        dict(x=89, y=111, text="IMPROVING", font=dict(color=q_colors["info"], size=16, family="JetBrains Mono")),
    ]

# ===========================================================================
# Plotly Modebar Polish
# ===========================================================================
MODEBAR_CONFIG = {
    "displayModeBar": "hover",
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "lasso2d", "select2d", "autoScale2d", "hoverClosestCartesian", "hoverCompareCartesian"
    ],
    "toImageButtonOptions": {"format": "png"}
}
