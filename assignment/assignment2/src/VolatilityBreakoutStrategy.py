# VolatilityBreakoutStrategy.py
import pandas as pd
from BaseStrategy import Strategy

class VolatilityBreakoutStrategy(Strategy):
    def __init__(self, shares_per_ticker=1):
        super().__init__(shares_per_ticker)

    def generate_signals(self, prices: pd.DataFrame):
        sig = self.empty_signals(prices)
        returns = prices.pct_change()
        vol = returns.rolling(20).std()
        buy_cond = returns > vol  # buy if today's return > rolling volatility
        sell_cond = returns < -vol  # sell if today's return < -rolling volatility
        sig[buy_cond] = 1
        sig[sell_cond] = -1
        sig[~(buy_cond | sell_cond)] = 0  # hold otherwise
        return sig
