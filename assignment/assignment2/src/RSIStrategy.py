# Buy if RSI < 30 (oversold)
# Sell if RSI > 70 (overbought)
import pandas as pd
from BaseStrategy import Strategy

class RSIStrategy(Strategy):
    def __init__(self, shares_per_ticker=1):
        super().__init__(shares_per_ticker)

    def compute_rsi(self, prices: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, prices: pd.DataFrame):
        sig = self.empty_signals(prices)
        rsi = self.compute_rsi(prices)
        sig[(rsi < 30) & (rsi.shift(1) >= 30)] = 1    # Buy when crossing below 30
        sig[(rsi > 80) & (rsi.shift(1) <= 80)] = -1  # Sell when crossing above 80

        return sig