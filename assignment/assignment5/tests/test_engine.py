# tests/test_engine.py
import pytest
import pandas as pd
from unittest.mock import MagicMock
from backtester.engine import Backtester

# example
def test_engine_uses_tminus1_signal(prices, broker, strategy, monkeypatch):
    # Force exactly one buy at t=10 by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals.return_value = prices*0
    fake_strategy.signals.return_value.iloc[9] = 1  # triggers buy at t=10
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    assert broker.position == 1
    assert broker.cash == 1000 - float(prices.iloc[10])

def test_engine_very_short_series(broker):
    bt = Backtester(MagicMock(), broker)
    with pytest.raises(ValueError):
        bt.run(pd.Series([100.0]))

def test_engine_logs_broker_failure(prices, broker):
    fake_strategy = MagicMock()
    fake_strategy.signals.return_value = prices*0
    fake_strategy.signals.return_value.iloc[5] = 1

    broker.market_order = MagicMock(side_effect=RuntimeError('broker failure'))
    with pytest.raises(RuntimeError, match='broker failure'):
        Backtester(fake_strategy, broker).run(prices)

def test_engine_executes_sell(prices, broker):
    fake_strategy = MagicMock()
    sigs = prices * 0
    sigs.iloc[5] = -1
    fake_strategy.signals.return_value = sigs
    broker.position = 1
    broker.cash = 900
    equity = Backtester(fake_strategy, broker).run(prices)
    assert broker.position == 0
    assert broker.cash == pytest.approx(900 + float(prices.iloc[6]))
    assert equity == pytest.approx(broker.cash)
    
def test_engine_signal_length_mismatch(prices, broker):
    fake_strategy = MagicMock()
    fake_strategy.signals.return_value = pd.Series([1, 0])
    with pytest.raises(ValueError, match="signals must align with prices"):
        Backtester(fake_strategy, broker).run(prices)