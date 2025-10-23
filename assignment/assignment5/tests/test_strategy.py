# tests/test_strategy.py
import pandas as pd
import pytest
from backtester.strategy import VolatilityBreakoutStrategy

def test_signals_length(strategy, prices):
    sig = strategy.signals(prices)
    assert len(sig) == len(prices)

def test_empty_series(strategy):
    s = pd.Series(dtype=float)
    sig = strategy.signals(s)
    assert sig.empty

def test_constant_series(strategy):
    const = pd.Series([100.0] * 50)
    sig = strategy.signals(const)
    assert sig.sum() == 0

def test_nans_at_head(strategy):
    s = pd.Series([float('nan')] + list(range(1, 30)))
    sig = strategy.signals(s)
    assert len(sig) == len(s)

def test_strategy_generates_short_signal():
    strat = VolatilityBreakoutStrategy(lookback=2)
    prices = pd.Series([100.0, 101.0, 96.0, 94.0])
    sig = strat.signals(prices)
    assert sig.iloc[3] == -1
    
def test_strategy_invalid_lookback():
    with pytest.raises(ValueError, match="lookback must be > 1"):
        VolatilityBreakoutStrategy(lookback=1)

def test_strategy_prices_not_series():
    strat = VolatilityBreakoutStrategy()
    with pytest.raises(TypeError, match="prices must be a pandas Series"):
        strat.signals([100, 101, 102])