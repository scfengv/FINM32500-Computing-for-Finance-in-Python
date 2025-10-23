# src/strategies.py
# Create an abstract base class:
from abc import ABC, abstractmethod
from models import MarketDataPoint

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list:
        pass

# Provide two concrete strategies (e.g., moving average crossover, momentum) that inherit from Strategy.
# Encapsulate any internal buffers or indicator values as private attributes (e.g., self._prices, self._window).
# Signals are lists of tuples (action, symbol, qty, price); they are converted to Order objects in engine.py
class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strat:
        - Keep track of the moving average of an equity's price
        - If price exceeds the historical average by some statistical threshold -> short
        - Elif price below historical average by significant amount (determined by threshold) -> long
    """
    def __init__(self, window, quantity):
        self._window = window
        self._quantity = quantity
        self._prices = []  # for tracking past prices

    def generate_signals(self, tick: MarketDataPoint) -> list:
        signals = []
        self._prices.append(tick.price)

        # We want to calculate the moving average (don't look at prices outside of the rolling window)
        if len(self._prices) > self._window:
            self._prices.pop(0)

        moving_avg = sum(self._prices) / len(self._prices)

        if tick.price > moving_avg:  # above average -> short
            signals.append(('SELL', tick.symbol, self._quantity, tick.price))
        elif tick.price < moving_avg:  # below average -> long
            signals.append(('BUY', tick.symbol, self._quantity, tick.price))

        return signals


class MomentumStrategy(Strategy):
    """
    Momentum Strat:
        - Compare price of equity to price at a certain number of ticks ago (determined by lookback window)
        - If price significantly higher than it was -> long
        - Elif significantly lower -> short
    """
    def __init__(self, window, quantity):
        self._window = window
        self._quantity = quantity
        self._prices = []  # past prices

    def generate_signals(self, tick: MarketDataPoint) -> list:
        signals = []
        self._prices.append(tick.price)

        if len(self._prices) > self._window:  # Once we have enough price data (i.e., can compare today's price to the one "window" ticks ago),
            past_price = self._prices[-self._window]  # the past price we'll use is the one from "window" periods ago

            if tick.price > past_price:  # upward momentum -> long
                signals.append(('BUY', tick.symbol, self._quantity, tick.price))
            elif tick.price < past_price:  # downward momentum -> short
                signals.append(('SELL', tick.symbol, self._quantity, tick.price))

        return signals
