# src/engine.py
import random
from models import *

class ExecutionEngine:
    def __init__(self):
        self.portfolio = {}  # Store open positions in a dictionary keyed by symbol: {'AAPL': {'quantity': 0, 'avg_price': 0.0}}.
        self.error_log = []  # For logging errors

        # For tracking equity time series
        self.last_price = {}
        self.equity = 0.0
        self.equity_ts = []
        self.cash = 0.0

    def process(self, ticks, strategies):
        # Ensure processing in chronological order
        ticks = sorted(ticks, key=lambda t: t.timestamp)

        for tick in ticks:  # For each tick:
            self.last_price[tick.symbol] = tick.price  # Track last seen price
            tick_signals = []  # Invoke each strategy to generate signals.
            for strat in strategies:
                signals = strat.generate_signals(tick)
                for signal in signals:
                    tick_signals.append(signal)

            # Instantiate and validate Order objects.
            for action, symbol, quantity, price in tick_signals:
                order = None
                try:  # Wrap order creation and execution in try/except blocks for resilience.
                    signed_q = -quantity if action == 'SELL' else quantity  # We don't track side in Order objects, so let quantity == signed qty
                    order = Order(symbol, signed_q, price, 'NEW')

                    if action not in ('BUY', 'SELL'):
                        raise OrderError(f"Order Error! Invalid action: {action}")
                    if not symbol:
                        raise OrderError("Order Error! Symbol is empty")
                    if quantity <= 0:
                        raise OrderError(f"Order Error! Invalid quantity: {quantity}")
                    if price <= 0:
                        raise OrderError(f"Order Error! Invalid price: {price}")
                    if random.random() < 0.005:  # Simulate occasional failures ("occasional" == 0.5% chance of failure)
                        raise ExecutionError("Execution Error! Order execution failed")
                
                    # Execute orders by updating the portfolio dictionary.
                    position = self.portfolio.get(symbol, {'quantity': 0, 'avg_price': 0.0})  # Start w/ existing position (or create new position if none)
                    
                    # Update average price: for tracking position, we want the weighted average price from all BUY orders
                    #                       when we sell, price is always price we sold at
                    if order.quantity > 0:
                        denom = position['quantity'] + order.quantity
                        if denom == 0:  # Prevent division by 0 error
                            new_wap = 0.0
                        else:
                            equity_old = position['quantity'] * position['avg_price']  # Equity (exposure) before order
                            order_equity = order.quantity * order.price  # Equity/Exposure from only the new order
                            new_wap = (equity_old + order_equity) / denom  # New weighted average price
                    else:
                        new_wap = position['avg_price']  # Weighted avg price doesn't change w/ sell

                    position['avg_price'] = new_wap  # Update price to new weighted average
                    position['quantity'] += order.quantity  # Update (signed) quantity
                    self.portfolio[symbol] = position  # Update portfolio

                    self.cash -= order.quantity * order.price  # SELL -> make cash, BUY -> lose cash

                    order.status = 'FILLED'  # Mark order as FILLED

                except OrderError as e:
                    if order is not None:
                        order.status = 'INVALID'  # If Order Error (invalid order) -> order status == INVALID
                    self.error_log.append(str(e))
                except ExecutionError as e:
                    if order is not None:
                        order.status = 'FAILED'  # If Execution Error -> order status == FAILED
                    self.error_log.append(str(e))

            # TRACK EQUITY
            self.equity = self.cash + sum(pos['quantity'] * self.last_price.get(sym, pos['avg_price']) for sym, pos in self.portfolio.items())
            self.equity_ts.append((tick.timestamp, self.equity))
            