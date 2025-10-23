import pytest
import pandas as pd
from backtester.price_loader import PriceLoader

def test_price_loader_basic():
    loader = PriceLoader(seed=42)
    prices = loader.load(100)
    assert len(prices) == 100
    assert isinstance(prices, pd.Series)

def test_price_loader_custom_params():
    loader = PriceLoader(seed=42)
    prices = loader.load(50, start_price=200.0, drift=0.001, vol=0.02)
    assert len(prices) == 50
    assert prices.iloc[0] > 199  # Should be near 200

def test_price_loader_negative_n():
    loader = PriceLoader()
    with pytest.raises(ValueError, match='n must be positive'):
        loader.load(-1)

def test_price_loader_zero_n():
    loader = PriceLoader()
    with pytest.raises(ValueError, match='n must be positive'):
        loader.load(0)