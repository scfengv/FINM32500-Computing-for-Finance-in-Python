from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict

from src.patterns.strategy import MarketDataPoint, MeanReversionStrategy, BreakoutStrategy, SignalPublisher
from src.patterns.command import ExecutionContext, ExecuteOrderCommand, CommandInvoker

def load_ticks_csv(path: str | Path, symbol_col="symbol", ts_col="timestamp", px_col="price", vol_col="volume") -> Iterable[MarketDataPoint]:
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            yield MarketDataPoint(
                symbol=row[symbol_col],
                timestamp=datetime.fromisoformat(row[ts_col]),
                price=float(row[px_col]),
                volume=float(row[vol_col]) if row.get(vol_col) else None,
            )

def run_engine(market_csv: str | Path, strategies=None, publisher: SignalPublisher | None = None):
    strategies = strategies or [MeanReversionStrategy(window=5, k=1.0, qty=10), BreakoutStrategy(lookback=3, qty=5)]
    pub = publisher or SignalPublisher()
    ctx = ExecutionContext(cash=100_000.0)
    inv = CommandInvoker()

    for tick in load_ticks_csv(market_csv):
        for strat in strategies:
            for sig in strat.generate_signals(tick):
                pub.notify(sig)
                if sig.get("type") == "ORDER":
                    inv.execute(ExecuteOrderCommand(ctx, sig))
    return ctx  
