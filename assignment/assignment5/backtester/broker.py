class Broker:
    def __init__(self, cash: float = 1_000_000):
        self.cash = cash
        self.position = 0

    def market_order(self, side: str, qty: int, price: float):
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        if qty <= 0:
            raise ValueError("qty must be positive")
        if price <= 0:
            raise ValueError("price must be positive")

        cost = qty * price
        if side == "BUY":
            if cost > self.cash:
                raise RuntimeError("insufficient cash")
            self.cash -= cost
            self.position += qty
        else:  # SELL
            if qty > self.position:
                raise RuntimeError("insufficient shares")
            self.cash += cost
            self.position -= qty
