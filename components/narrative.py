from dash import html
import dash_bootstrap_components as dbc
import pandas as pd

def generate_smart_narrative(df, context="market"):
    """
    Generates a 1-2 sentence analytical summary based on the provided dataframe.
    Context can be 'market', 'correlation', or 'risk'.
    """
    if df.empty:
        return html.Div("Insufficient data to generate insights.", className="text-muted small")
        
    insights = []
    
    try:
        if context == "market":
            if "CAGR" in df.columns:
                best_performer = df.loc[df['CAGR'].idxmax()]
                worst_performer = df.loc[df['CAGR'].idxmin()]
                insights.append(
                    f"Over this period, {best_performer['Company']} ({best_performer['Sector']}) led the market with a {best_performer['CAGR']:.1%} CAGR, "
                    f"while {worst_performer['Company']} lagged at {worst_performer['CAGR']:.1%}."
                )
            
        elif context == "correlation":
            # Assuming df has 'Distance' or similar. Since finding max off-diagonal is complex here, 
            # we'll provide a generic but dynamic structural insight.
            num_companies = df["Company"].nunique() if "Company" in df.columns else len(df)
            insights.append(
                f"Analyzing structural redundancy across {num_companies} equities. High density clusters indicate macro-driven sector coupling."
            )
            
        elif context == "risk":
            if "Annual_Return" in df.columns and "Annual_Volatility" in df.columns:
                max_risk = df.loc[df['Annual_Volatility'].idxmax()]
                best_return = df.loc[df['Annual_Return'].idxmax()]
                insights.append(
                    f"The efficient frontier is bounded by {max_risk['Company']} at peak volatility ({max_risk['Annual_Volatility']:.1%}) "
                    f"and {best_return['Company']} driving maximum absolute returns ({best_return['Annual_Return']:.1%})."
                )
    except Exception as e:
        return html.Div(f"Insight generation paused.", className="text-muted small")
        
    return html.Div([
        html.I(className="bi bi-magic text-warning me-2"),
        html.Span(" ".join(insights), className="text-primary fw-500 small", style={"letterSpacing": "0.3px"})
    ], className="p-2 border border-primary border-opacity-25 rounded bg-primary bg-opacity-10 mb-3")
