# order.py
from enum import Enum, auto

class OrderState(Enum):
    NEW = auto()
    ACKED = auto()
    FILLED = auto()
    CANCELED = auto()
    REJECTED = auto()

class Order:
    def __init__(self, symbol, qty, side):
        self.state = OrderState.NEW
        self.symbol = symbol
        self.qty = qty
        self.side = side

    def transition(self, new_state: OrderState):
        allowed = {
            OrderState.NEW:      {OrderState.ACKED, OrderState.REJECTED},
            OrderState.ACKED:    {OrderState.FILLED, OrderState.CANCELED},
            OrderState.FILLED:   set(),   # no transitions allowed
            OrderState.CANCELED: set(),
            OrderState.REJECTED: set(),
        }

        if new_state not in allowed[self.state]:
            print(f'Invalid transition for {self.symbol}: {self.state.name} -> {new_state.name}')
            return

        self.state = new_state
        print(f'Order {self.symbol} is now {self.state.name}')