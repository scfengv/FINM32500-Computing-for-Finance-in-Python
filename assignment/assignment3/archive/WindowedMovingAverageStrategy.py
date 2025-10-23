# WindowedMovingAverageStrategy.py

import numpy as np
import pandas as pd
from collections import deque
from BaseStrategy import Strategy
from models import MarketDataPoint

class WindowedMovingAverageStrategy(Strategy):
    def __init__(self, window = 20):
        self.rollingSum = 0
        self.window = window
        self.signals = list()
        self.bufferWindow = deque(maxlen = window)

    def generate_signals(self, tick: MarketDataPoint) -> list:
        self.rollingSum += tick.price
        self.bufferWindow.append(tick.price)
        
        if len(self.bufferWindow) == self.window:
            self.rollingSum -= self.bufferWindow[0]
            self.bufferWindow.popleft()
            MA = self.rollingSum / self.window
            if tick.price > MA:
                self.signals.append(1)
            elif tick.price < MA:
                self.signals.append(-1)
            else:
                self.signals.append(0)

        return self.signals