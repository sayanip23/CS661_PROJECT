import pytest
import pandas as pd
import numpy as np
from utils.analytics.treemap import compute_cagr, compute_volatility

def test_compute_cagr():
    # 3 years exactly (1095 days)
    # Starting at 100, ending at 133.1 (approx 10% CAGR)
    assert round(compute_cagr(100, 133.1, 1095), 2) == 0.10
    
    # Negative growth
    assert round(compute_cagr(100, 50, 365), 2) == -0.50
    
    # Zero days should return 0.0 per our implementation
    assert compute_cagr(100, 150, 0) == 0.0

def test_compute_volatility():
    # Volatility of a flat line is 0
    returns = pd.Series([0.0, 0.0, 0.0, 0.0])
    assert compute_volatility(returns) == 0.0
    
    # Simple known volatility
    returns = pd.Series([0.01, -0.01, 0.01, -0.01])
    # std deviation of [0.01, -0.01, 0.01, -0.01] is ~0.011547
    # annualized = 0.011547 * sqrt(252) = 0.183
    assert round(compute_volatility(returns), 3) == 0.183
