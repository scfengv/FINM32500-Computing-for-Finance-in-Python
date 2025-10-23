# MovingAverageStrategy.py
import pandas as pd
from BaseStrategy import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, shares_per_ticker=1):
        super().__init__(shares_per_ticker)

    def generate_signals(self, prices: pd.DataFrame):
        sig = self.empty_signals(prices)
        short_ma = prices.rolling(20).mean()
        long_ma = prices.rolling(50).mean()
        sig[short_ma > long_ma] = 1  # buy when short MA > long MA
        sig[short_ma < long_ma] = -1 # sell when short MA < long MA

        return sig
