import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from order import Order, OrderState

def test_order_state_transitions():
    order = Order('AAPL', 100, '1')
    assert order.state == OrderState.NEW

    order.transition(OrderState.ACKED)
    assert order.state == OrderState.ACKED

    order.transition(OrderState.FILLED)
    assert order.state == OrderState.FILLED

    prev = order.state
    order.transition(OrderState.NEW)
    assert order.state == prev