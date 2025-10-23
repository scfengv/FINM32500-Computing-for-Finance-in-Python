from typing import List
from collections import deque
from models import MarketDataPoint
from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        pass


class NaiveMovingAverageStrategy(Strategy):
    # Time: O(n) per tick (sum over all prices)
    # Space: O(n) (store full history)
    def __init__(self):
        self.prices = []

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        currentPrice = tick.price
        self.prices.append(currentPrice)  # O(1)
        avg_price = sum(self.prices) / len(self.prices)  # O(n)
        if currentPrice < avg_price:
            return [f"BUY {tick.symbol} at {currentPrice:.2f}"]
        elif currentPrice > avg_price:
            return [f"SELL {tick.symbol} at {currentPrice:.2f}"]
        return []


class WindowedMovingAverageStrategy(Strategy):
    # Time: O(1) per tick (constant updates)
    # Space: O(k) (fixed-size window)
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.prices = deque(maxlen=window_size)
        self.running_sum = 0.0

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        currentPrice = tick.price
        if len(self.prices) == self.window_size:
            self.running_sum -= self.prices[0]  # O(1)
        self.prices.append(currentPrice)          # O(1)
        self.running_sum += currentPrice          # O(1)
        avg_price = self.running_sum / len(self.prices)  # O(1)
        if currentPrice < avg_price:
            return [f"BUY {tick.symbol} at {currentPrice:.2f}"]
        elif currentPrice > avg_price:
            return [f"SELL {tick.symbol} at {currentPrice:.2f}"]
        return []


class OptimizedNaiveMovingAverageStrategy(Strategy):
    # Time: O(1) per tick (constant updates)
    # Space: O(1) (number of variables)
    def __init__(self):
        self.count = 0
        self.running_sum = 0

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        currentPrice = tick.price
        self.count += 1
        self.running_sum += currentPrice          # O(1)
        avg_price = self.running_sum / self.count  # O(1)
        
        if currentPrice < avg_price:
            return [f"BUY {tick.symbol} at {currentPrice:.2f}"]
        elif currentPrice > avg_price:
            return [f"SELL {tick.symbol} at {currentPrice:.2f}"]
        return []