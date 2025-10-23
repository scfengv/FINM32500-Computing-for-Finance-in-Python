import pandas as pd
import numpy as np

class PriceLoader:
    def __init__(self, seed: int=42):
        self.rng = np.random.default_rng(seed)

    def load(self, n, start_price: float = 100.0, drift: float = 0.0003, vol: float = 0.01):
        if n <= 0:
            raise ValueError('n must be positive')
        returns = drift + vol * self.rng.standard_normal(n)
        prices = start_price * np.exp(np.cumsum(returns))
        return pd.Series(prices)
        