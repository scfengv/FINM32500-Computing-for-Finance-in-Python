# main.py
from fix_parser import FixParser
from order import Order, OrderState
from risk_engine import RiskEngine
from logger import Logger

def handle_message(raw, fix, risk, log):
    msg = fix.parse(raw)
    order = Order(msg['55'], int(msg['38']), msg['54'])
    log.log('OrderCreated', msg)

    try:
        risk.check(order)
        order.transition(OrderState.ACKED)
        # Assume immediate fill
        risk.update_position(order)
        order.transition(OrderState.FILLED)

        log.log('OrderFilled', {'symbol': order.symbol, 'qty': order.qty})
    except ValueError as e:
        order.transition(OrderState.REJECTED)
        log.log('OrderRejected', {'symbol': order.symbol, 'reason': str(e)})

if __name__ == '__main__':
    fix = FixParser()
    risk = RiskEngine()
    log = Logger()

    raw_messages = [
    '8=FIX.4.2|35=D|55=AAPL|54=1|38=500|40=2|44=170.00|10=128',
    '8=FIX.4.2|35=D|55=MSFT|54=1|38=2500|40=2|44=310.25|10=128',
    ]

    for raw in raw_messages:
        handle_message(raw, fix, risk, log)

    log.save()