# Developer Guide

## Architecture Overview
The NIFTY-50 Dashboard follows a strict separation of concerns, separating the analytical processing from UI rendering.

```
CS661_PROJECT/
├── app.py                     # Entry point & Global State Management
├── assets/                    # Static assets & Design Tokens (style.css)
├── components/                # Reusable UI elements (Sidebar, Narratives, Cards)
├── pages/                     # Dash Page Layouts & Callbacks
├── tests/                     # PyTest Unit Tests
├── utils/                     # Core Utilities
│   ├── analytics/             # Mathematical Pipelines & SQL
│   ├── config.py              # Centralized configuration & Theming
│   ├── database.py            # DuckDB connection handling
│   ├── loader.py              # Data initialization
│   └── preprocessing.py       # Raw CSV cleaning
```

## State Management
We use a centralized `dcc.Store(id="global-state", storage_type="local")` in `app.py`. 
Any interaction that should persist across pages (like selecting a sector in the Treemap) must update this store. Other pages read from this store to filter their analytical dataframes before plotting.

## Design System
We maintain a strict dark theme (`FINANCIAL_THEME` in `utils/config.py`). Do not override `plot_bgcolor` or `paper_bgcolor` in individual pages. Use the predefined bootstrap utility classes for layouts and `assets/style.css` for custom elements.

## Testing
Core analytical functions (CAGR, Volatility calculations) are unit tested. To run tests:
```bash
python -m pytest tests/
```

## Adding a New Page
1. Create `pages/my_page.py`.
2. Add `dash.register_page(__name__)`.
3. Create your layout and localized callbacks.
4. Ensure any cross-filtering respects `Input("global-state", "data")`.
