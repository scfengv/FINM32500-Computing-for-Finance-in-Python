# strategy.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import sqrt
from typing import Deque, Dict, List, Optional

try:
    from singleton import Config  # type: ignore
except Exception:
    Config = None  


@dataclass
class MarketDataPoint:
    symbol: str
    timestamp: datetime
    price: float
    volume: Optional[float] = None


class Strategy(ABC):
    """Base interface; each tick returns 0..n signals (dicts)."""

    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint | Dict) -> List[Dict]:
        ...



class _RollingStats:
    """Fixed-window rolling mean/std for a single stream."""
    def __init__(self, window: int):
        self.window = int(window)
        self.q: Deque[float] = deque(maxlen=self.window)
        self._sum = 0.0
        self._sum2 = 0.0

    def add(self, x: float):
        if len(self.q) == self.window:
            old = self.q[0]
            self._sum -= old
            self._sum2 -= old * old
        self.q.append(x)
        self._sum += x
        self._sum2 += x * x

    @property
    def ready(self) -> bool:
        return len(self.q) == self.window

    @property
    def mean(self) -> float:
        n = len(self.q)
        return self._sum / n if n else 0.0

    @property
    def std(self) -> float:
        n = len(self.q)
        if n <= 1:
            return 0.0
        mean = self._sum / n
        var = max(self._sum2 / n - mean * mean, 0.0)
        return sqrt(var)


def _coerce_tick(tick: MarketDataPoint | Dict) -> MarketDataPoint:
    if isinstance(tick, MarketDataPoint):
        return tick
    # minimal coercion from dict
    return MarketDataPoint(
        symbol=tick["symbol"],
        timestamp=tick["timestamp"],
        price=float(tick["price"]),
        volume=tick.get("volume"),
    )



class MeanReversionStrategy(Strategy):
    """
    Buys when price << rolling mean (k std), sells when price >> mean (+k std).
    Keeps per-symbol rolling state.
    """
    def __init__(
        self,
        window: Optional[int] = None,
        k: Optional[float] = None,
        qty: Optional[int] = None,
        params: Optional[Dict] = None,
    ):
        cfg_params = {}
        if params:
            cfg_params = params
        elif Config:
            try:
                cfg = Config()
                cfg_params = cfg.data.get("strategy_params", {}).get("mean_reversion", {})
            except Exception:
                cfg_params = {}

        self.window = int(window or cfg_params.get("window", 20))
        self.k = float(k or cfg_params.get("k", 2.0))
        self.qty = int(qty or cfg_params.get("qty", 10))

        self.stats: Dict[str, _RollingStats] = defaultdict(lambda: _RollingStats(self.window))

    def generate_signals(self, tick: MarketDataPoint | Dict) -> List[Dict]:
        t = _coerce_tick(tick)
        rs = self.stats[t.symbol]
        rs.add(t.price)

        if not rs.ready:
            return []

        mu, sd = rs.mean, rs.std
        if sd == 0.0:
            return []

        z = (t.price - mu) / sd
        signals: List[Dict] = []

        if z <= -self.k:
            signals.append({
                "type": "ORDER",
                "action": "BUY",
                "symbol": t.symbol,
                "qty": self.qty,
                "price": t.price,
                "reason": f"MeanReversion z={z:.2f} <= -{self.k}",
                "ts": t.timestamp,
                "strategy": "MeanReversion",
            })
        elif z >= self.k:
            signals.append({
                "type": "ORDER",
                "action": "SELL",
                "symbol": t.symbol,
                "qty": self.qty,
                "price": t.price,
                "reason": f"MeanReversion z={z:.2f} >= {self.k}",
                "ts": t.timestamp,
                "strategy": "MeanReversion",
            })

        return signals



class BreakoutStrategy(Strategy):
    """
    Buys on price > prior N-day high; sells on price < prior N-day low.
    """
    def __init__(
        self,
        lookback: Optional[int] = None,
        qty: Optional[int] = None,
        params: Optional[Dict] = None,
    ):
        cfg_params = {}
        if params:
            cfg_params = params
        elif Config:
            try:
                cfg = Config()
                cfg_params = cfg.data.get("strategy_params", {}).get("breakout", {})
            except Exception:
                cfg_params = {}

        self.lookback = int(lookback or cfg_params.get("lookback", 20))
        self.qty = int(qty or cfg_params.get("qty", 10))

        self.windows: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=self.lookback))

    def generate_signals(self, tick: MarketDataPoint | Dict) -> List[Dict]:
        t = _coerce_tick(tick)
        w = self.windows[t.symbol]

        prior_high = max(w) if w else None
        prior_low = min(w) if w else None

        signals: List[Dict] = []
        if len(w) == self.lookback:
            if prior_high is not None and t.price > prior_high:
                signals.append({
                    "type": "ORDER",
                    "action": "BUY",
                    "symbol": t.symbol,
                    "qty": self.qty,
                    "price": t.price,
                    "reason": f"Breakout > {prior_high:.4f}",
                    "ts": t.timestamp,
                    "strategy": "Breakout",
                })
            elif prior_low is not None and t.price < prior_low:
                signals.append({
                    "type": "ORDER",
                    "action": "SELL",
                    "symbol": t.symbol,
                    "qty": self.qty,
                    "price": t.price,
                    "reason": f"Breakdown < {prior_low:.4f}",
                    "ts": t.timestamp,
                    "strategy": "Breakout",
                })

        w.append(t.price)
        return signals



if __name__ == "__main__":
    base_time = datetime(2024, 1, 1, 9, 30)
    # Mean Reversion test
    mr = MeanReversionStrategy(window=5, k=1.5, qty=3)
    series = [100, 100, 100, 100, 100, 95, 105]
    print("MeanReversion signals:")
    for i, px in enumerate(series):
        sigs = mr.generate_signals({"symbol": "AAA", "timestamp": base_time + timedelta(minutes=i), "price": px})
        for s in sigs:
            print(s)

    # Breakout test
    br = BreakoutStrategy(lookback=3, qty=2)
    series2 = [10, 11, 12, 13, 12, 14, 9]
    print("\nBreakout signals:")
    for i, px in enumerate(series2):
        sigs = br.generate_signals({"symbol": "BBB", "timestamp": base_time + timedelta(minutes=i), "price": px})
        for s in sigs:
            print(s)