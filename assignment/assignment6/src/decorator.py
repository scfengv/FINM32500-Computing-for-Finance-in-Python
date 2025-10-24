# decorator.py
import numpy as np
import pandas as pd

class Instrument:
    """
    Base class
    """
    def __init__(self, symbol, price, quantity) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
    
    def get_metrics(self):
        return {
            "symbol": self.symbol,
            "value": self.price * self.quantity
        }

class InstrumentDecorator:
    """
    Base decorator that wraps an Instrument.
    """
    
    def __init__(self, instrument) -> None:
        self._instrument = instrument
        
    def get_metrics(self):
        return self._instrument.get_metrics()

    @property
    def symbol(self):
        return self._instrument.symbol
    
class VolatilityDecorator(InstrumentDecorator):
    """
    Add volatility metric
    """
    
    def __init__(self, instrument, market_data) -> None:
        super().__init__(instrument)
        self.market_data = market_data
    
    def get_metrics(self):
        metrics =  super().get_metrics()
        
        # Volatility
        symbol = self._instrument.symbol
        prices = self._get_price_history(symbol)
        metrics["volatility"] = self._calculate_vol(prices)
        return metrics
        
    def _get_price_history(self, symbol):
        history = self.market_data[self.market_data["symbol"] == symbol]
        history = history.sort_values('timestamp')
        return history["price"] # Pandas Series

    def _calculate_vol(self, prices):
        returns = prices.pct_change().dropna()
        std = returns.std()
        return float(std)

class BetaDecorator(InstrumentDecorator):
    def __init__(self, instrument, market_data, benchmark) -> None:
        super().__init__(instrument)
        self.market_data = market_data
        self.benchmark = benchmark
    
    def get_metrics(self):
        metrics = super().get_metrics()
        
        # Beta
        stock_returns = self._get_returns(self._instrument.symbol)
        market_returns = self._get_returns(self.benchmark)
        metrics["beta"] = self._calculate_beta(stock_returns, market_returns)
        return metrics

    def _get_returns(self, symbol):
        prices = self._get_price_history(symbol)
        return prices.pct_change().dropna()
    
    def _get_price_history(self, symbol):
        history = self.market_data[self.market_data["symbol"] == symbol]
        history = history.sort_values('timestamp')
        return history["price"] # Pandas Series
    
    def _calculate_beta(self, stock_returns, market_returns):
        
        # align length
        min_len = min(len(stock_returns), len(market_returns))
        stock_returns = stock_returns[:min_len]
        market_returns = market_returns[:min_len]
        
        # [0, 0]: var(stock)
        # [0, 1] = [1, 0]: cov(stock, market)
        # [1, 1]: var(market)
        covMat = np.cov(stock_returns, market_returns)
        cov = covMat[1, 0]
        market_var = covMat[1, 1]
        return float(cov / market_var)
    
class DrawdownDecorator(InstrumentDecorator):
    def __init__(self, instrument, market_data) -> None:
        super().__init__(instrument)
        self.market_data = market_data
    
    def get_metrics(self):
        metrics = super().get_metrics()
        
        # Max Drawdown
        symbol = self._instrument.symbol
        prices = self._get_price_history(symbol)
        metrics["max_drawdown"] = self._calculate_drawdown(prices)
        return metrics
        
    def _get_price_history(self, symbol):
        history = self.market_data[self.market_data["symbol"] == symbol]
        history = history.sort_values('timestamp')
        return history["price"] # Pandas Series

    def _calculate_drawdown(self, prices):
        cumulative_max = prices.cummax()
        drawdown = (prices - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        return float(max_drawdown)
    
if __name__ == "__main__":
    market_data = pd.read_csv("../data/market_data.csv")
    market_data["timestamp"] = pd.to_datetime(market_data["timestamp"])
    
    # Basic Instrument
    aapl = Instrument(symbol = "AAPL", price = market_data[market_data["symbol"] == "AAPL"]["price"].iloc[0], quantity = 100)
    
    # Test 1: Basic Metrics
    print("=== Base Instrument ===")
    print(aapl.get_metrics())
    print()
    
    # Test 2: With volatility
    print("=== With Volatility ===")
    aapl_vol = VolatilityDecorator(aapl, market_data)
    print(aapl_vol.get_metrics())
    print()

    # Test 3: With volatility + beta
    print("=== With Volatility + Beta ===")
    aapl_vol_beta = BetaDecorator(
        aapl_vol, 
        market_data, 
        benchmark = "SPY"
    )
    print(aapl_vol_beta.get_metrics())
    print()
    
    # Test 4: Full stack (all decorators)
    print("=== Fully Decorated (All Metrics) ===")
    aapl_decorated = DrawdownDecorator(
        BetaDecorator(
            VolatilityDecorator(aapl, market_data),
            market_data,
            benchmark = "SPY"
        ),
        market_data
    )
    print(aapl_decorated.get_metrics())
    print()