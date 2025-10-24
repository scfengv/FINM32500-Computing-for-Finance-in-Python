# decorator.py

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
        prices = self._get_price_history(self._instrument.symbol)