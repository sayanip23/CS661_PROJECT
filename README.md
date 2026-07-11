# NIFTY-50 Visual Analytics Dashboard

![Dashboard Preview](https://via.placeholder.com/1200x600.png?text=NIFTY-50+Dashboard)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Dash](https://img.shields.io/badge/dash-2.18.2-008DE4.svg)](https://dash.plotly.com/)
[![DuckDB](https://img.shields.io/badge/duckdb-1.3.2-FFF000.svg)](https://duckdb.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A professional, institutional-grade quantitative analytics platform for the Indian NIFTY 50 stock market index. Built with Python, Dash, Plotly, and DuckDB.

## 🚀 Features

- **Correlation Heatmap**: Hierarchical agglomerative clustering (K-Means) to identify hidden sector couplings.
- **Risk vs Return (Efficient Frontier)**: Analyzes asset volatility versus annualized return, highlighting Sharpe Ratios and an empirical efficient frontier.
- **Market Shocks (Anomaly Detection)**: Detects systemic anomalies using Z-Score divergence and cross-sectional dispersion over a 10-year period.
- **Relative Rotation Graphs (RRG)**: Tracks institutional momentum (RS-Ratio vs RS-Momentum) to visualize leading, weakening, lagging, and improving sectors over time.
- **Market Attribution Treemap**: Maps NIFTY-50 composition by size (Volume/Turnover) and performance (CAGR/Sharpe).
- **Smart Narratives**: Algorithmic generation of contextual insights for every visualization based on active filters.

## 🛠 Technology Stack

- **Frontend**: Dash, Dash Bootstrap Components (DARKLY theme), Plotly
- **Backend / Analytics**: Pandas, NumPy, Scikit-learn, SciPy
- **Database**: DuckDB (In-memory SQL analytics)
- **Testing**: PyTest

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/NIFTY50-Dashboard.git
   cd NIFTY50-Dashboard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Dashboard**
   ```bash
   python app.py
   ```
   *The application will initialize the DuckDB database on its first run and launch at `http://127.0.0.1:8050`.*

## 📚 Documentation

For more detailed information on usage and architecture, please see:
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](#).

## 📄 License

This project is licensed under the MIT License.
