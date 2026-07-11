# User Guide

Welcome to the NIFTY-50 Visual Analytics Dashboard. This guide will help you navigate and extract insights from the platform.

## Navigation
Use the **sidebar** to navigate between different analytical models. You can toggle the sidebar by clicking the hamburger menu icon (☰) in the top left.

## Global Filters
Your selected filters (e.g., Sectors, Companies) persist as you move between pages. They are displayed in the **Top Bar**. 
- You can clear all active filters by clicking the "Clear All" button in the Top Bar.
- Interactions on the **Treemap** and **Correlation Heatmap** automatically update your global filters.

## Analytical Tools

### 1. Market Attribution Treemap
Visualize the composition of the NIFTY-50 index. 
- **Size**: Represents market liquidity (Volume or Turnover).
- **Color**: Represents performance (CAGR or Sharpe Ratio).
- **Interaction**: Click on a Sector block to "zoom in" and lock that sector into the Global Filters. Click on a specific Company tile to view its historical tear sheet on the right panel.

### 2. Risk vs Return
A scatter plot plotting Annualized Volatility against Annualized Return.
- **Efficient Frontier**: The dashed line represents the Empirical Efficient Frontier, marking the maximum historical return achieved for a given level of risk.
- **Sharpe Ratio**: Nodes are colored by their Sharpe Ratio (Risk-adjusted return).

### 3. Correlation Heatmap
Discover how stocks move together. The algorithm automatically clusters highly correlated stocks using Hierarchical Agglomerative Clustering (K-Means).
- **Interaction**: Drag a selection box over a cluster of squares to instantly view their synchronized time-series price movements below. This also adds the selected companies to your Global Filter.

### 4. Sector Rotation (RRG)
Relative Rotation Graphs (RRG) track the institutional momentum of stocks. 
- **X-Axis (RS-Ratio)**: Indicates the long-term trend (Leading vs Lagging).
- **Y-Axis (RS-Momentum)**: Indicates the short-term velocity (Improving vs Weakening).
- **Interaction**: Select a year and watch the animation play. The fading trails help you track the trajectory of momentum shifts.

### 5. Market Shocks
A macro-to-micro view of market volatility.
- **Top Chart (Timeline)**: Shows days where the market exhibited extreme aggregate volatility (Z-Scores). Red indicates a systemic crash, Green indicates a systemic rally.
- **Interaction**: Hover your mouse over any spike on the timeline to instantly view the cross-sectional dispersion of all stocks on that specific day in the Beeswarm plot below.
