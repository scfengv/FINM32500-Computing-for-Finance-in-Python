from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen = True)
class MarketDataPoint:
    timestamp: datetime
    symbol: str
    price: float
    
class Order:
    def __init__(self, symbol, quantity, price, status) -> None:
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.status = status
        self._ValidateOrder()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return (self.symbol == other.symbol and
                self.quantity == other.quantity and
                self.price == other.price and
                self.status == other.status)

    def __repr__(self):
        return f"Order(symbol = {self.symbol}, quantity = {self.quantity}, price = {self.price}, status = {self.status})"
    
    def _ValidateOrder(self):
        if self.quantity <= 0:
            raise OrderError("Invalid order: quantity must be positive")
        
        if self.price <= 0:
            raise OrderError("Invalid order: price must be positive")

class OrderError(Exception):
    """
    Raise OrderError for invalid orders (e.g., zero or negative quantity)
    """
    pass

class ExecutionError(Exception):
    """Raised when order execution fails"""
    pass