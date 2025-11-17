import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from order import Order
from risk_engine import RiskEngine

def test_risk_engine_rejects_large_order():
    risk = RiskEngine(max_order_size=1000)
    with pytest.raises(ValueError):
        risk.check(Order('AAPL', 5000, '1'))

def test_risk_engine_updates_position():
    risk = RiskEngine()
    o = Order('AAPL', 100, '1')
    risk.check(o)
    risk.update_position(o)
    assert risk.positions['AAPL'] == 100