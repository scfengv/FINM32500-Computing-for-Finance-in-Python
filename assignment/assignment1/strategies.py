from abc import ABC, abstractmethod
from models import OrderError, ExecutionError, MarketDataPoint

class Strategy(ABC):
    
    def __init__(self) -> None:
        self.positions = dict()
        self.signals = list()
        self.pendingOrders = list() # data buffer
        
    @abstractmethod
    def GenerateSignals(self, tick: MarketDataPoint) -> list:
        pass

    def AddSignal(self, action, symbol, quantity, price) -> tuple:
        return (action, symbol, quantity, price)
    
    def Getposition(self, symbol) -> dict:
        return self.positions.get(symbol, {"quantity": 0, "avg_price": 0.0})

class Strategy1(Strategy):
    def __init__(self) -> None:
        super().__init__()
        pass
    
    def GenerateSignals(self, tick: MarketDataPoint) -> list:
        self.pendingOrders.append(tick)
        signals = list()
        return signals
    
class Strategy2(Strategy):
    def __init__(self) -> None:
        super().__init__()
        pass
    
    def GenerateSignals(self, tick: MarketDataPoint) -> list:
        self.pendingOrders.append(tick)
        signals = list()
        return signals