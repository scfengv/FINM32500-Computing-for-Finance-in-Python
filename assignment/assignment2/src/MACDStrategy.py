# Buy if MACD line crosses above signal line
import pandas as pd
from BaseStrategy import Strategy

class MACDStrategy(Strategy):
    def __init__(self, shares_per_ticker = 1):
        super().__init__(shares_per_ticker)

    def generate_signals(self, prices: pd.DataFrame):
        sig = self.empty_signals(prices)
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        sig[macd > signal] = 1  # buy when MACD > signal line
        sig[macd < signal] = -1 # sell when MACD < signal line
        return sig
