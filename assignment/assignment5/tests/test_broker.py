# tests/test_broker.py
import pytest
from backtester.broker import Broker

def test_buy_and_sell_updates_cash_and_pos(broker):
    broker.market_order("BUY", 2, 10.0)
    assert (broker.position, broker.cash) == (2, 1000 - 20.0)

    broker.market_order("SELL", 1, 10.0)
    assert (broker.position, broker.cash) == (1, 980 + 10.0)

def test_rejects_bad_orders(broker):
    with pytest.raises(ValueError):
        broker.market_order("BUY", 0, 10)
    with pytest.raises(ValueError):
        broker.market_order("BUY", 1, 0)
    with pytest.raises(ValueError):
        broker.market_order("B", 0, 10)

def test_insufficient_cash_or_shares():
    b = Broker(cash=5)
    with pytest.raises(RuntimeError):
        b.market_order("BUY", 1, 10)
    b = Broker(cash=100)
    with pytest.raises(RuntimeError):
        b.market_order("SELL", 1, 10)
