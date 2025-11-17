# risk_engine.py
class RiskEngine:
    def __init__(self, max_order_size=1000, max_position=2000):
        self.max_order_size = max_order_size
        self.max_position = max_position
        self.positions = {}

    def _signed_qty(self, order):
        if order.side == '1':
            return order.qty
        elif order.side == '2':
            return -order.qty
        else:
            raise ValueError(f'Unknown side: {order.side}')

    def check(self, order):
        if order.qty > self.max_order_size:
            raise ValueError(f'Order size {order.qty} exceeds max_order_size={self.max_order_size}')

        symbol = order.symbol
        curr_pos = self.positions.get(symbol, 0)
        signed_qty = self._signed_qty(order)
        new_pos = curr_pos + signed_qty
        if abs(new_pos) > self.max_position:
            raise ValueError(f'Position limit exceeded for {symbol}: new position {new_pos}, max_position={self.max_position}')

        return True

    def update_position(self, order):
        symbol = order.symbol
        signed_qty = self._signed_qty(order)
        curr_pos = self.positions.get(symbol, 0)
        new_pos = curr_pos + signed_qty
        self.positions[symbol] = new_pos
        print(f'Updated position for {symbol}: {curr_pos} -> {new_pos}')