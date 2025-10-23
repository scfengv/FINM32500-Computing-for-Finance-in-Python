# src/models.py
from dataclasses import dataclass
import datetime

# Define a frozen dataclass MarketDataPoint with attributes timestamp (datetime), symbol (str), and price (float).
@dataclass(frozen=True)
class MarketDataPoint:
    timestamp: datetime.datetime
    symbol: str
    price: float

# Implement an Order class with mutable attributes: symbol, quantity, price, and status.
class Order:
    def __init__(self, symbol, quantity, price, status):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.status = status

    # Need for printing in unit test
    def __repr__(self):
        return f"Order(symbol={self.symbol}, qty={self.quantity}, price={self.price}, status={self.status})"

# Define custom exceptions:
class OrderError(Exception): pass  # Raise OrderError for invalid orders (e.g., qty <= 0, price <= 0, action != BUY or SELL)
class ExecutionError(Exception): pass  # Raise ExecutionError when execution fails (simulated failures)
