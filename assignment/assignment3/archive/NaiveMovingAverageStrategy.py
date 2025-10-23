# NaiveMovingAverageStrategy.py

import numpy as np
import pandas as pd
from BaseStrategy import Strategy
from models import MarketDataPoint

class NaiveMovingAverageStrategy(Strategy):
    def __init__(self):
        self.MA = 0
        self.prices = list()
        self.signals = list()

    def generate_signals(self, tick: MarketDataPoint) -> list:
        currentPrice = tick.price
        self.prices.append(currentPrice)
        
        # correct me if wrong, I think we cannot use .rolling to compute ma
        self.MA = np.mean(self.prices)
        
        if currentPrice > self.MA:
            self.signals.append(1)
        elif currentPrice < self.MA:
            self.signals.append(-1)
        else:
            self.signals.append(0)
            
        return self.signals
