import pandas as pd
import pytest
from unittest.mock import MagicMock
from .strategy import VolatilityBreakoutStrategy

class Backtester:
    def __init__(self, strategy, broker, qty: int = 1):
        self.strategy = strategy
        self.broker = broker
        self.qty = qty

    def run(self, prices: pd.Series):
        if len(prices) < 2:
            raise ValueError("need at least 2 price points")

        sigs = self.strategy.signals(prices)
        if len(sigs) != len(prices):
            raise ValueError("signals must align with prices")

        for t in range(1, len(prices)):
            sig_prev = sigs.iloc[t - 1]
            p = float(prices.iloc[t])
            if sig_prev > 0:
                self.broker.market_order("BUY", self.qty, p)
            elif sig_prev < 0:
                self.broker.market_order("SELL", self.qty, p)

        equity = self.broker.cash + self.broker.position * float(prices.iloc[-1])
        return equity