# Strategy.py
import numpy as np
import pandas as pd
from dataclasses import dataclass
from models import MarketDataPoint
from abc import ABC, abstractmethod
    
class Strategy(ABC):
    
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list:
        raise NotImplementedError