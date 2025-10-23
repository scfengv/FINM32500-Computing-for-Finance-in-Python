import pandas as pd
import numpy as np

class VolatilityBreakoutStrategy:
    def __init__(self, lookback: int = 20):
        if lookback <= 1:
            raise ValueError("lookback must be > 1")
        self.lookback = lookback

    def signals(self, prices: pd.Series):
        if not isinstance(prices, pd.Series):
            raise TypeError("prices must be a pandas Series")
        if prices.empty:
            return pd.Series(dtype=float)

        r = prices.pct_change()
        vol = r.rolling(self.lookback, min_periods=self.lookback).std()

        sigs = pd.Series(0, index=prices.index, dtype=int)
        sigs[r > vol] = 1
        sigs[r < -vol] = -1
        sigs.iloc[: self.lookback] = 0
        return sigs