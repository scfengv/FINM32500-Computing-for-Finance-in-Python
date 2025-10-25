from __future__ import annotations
from pathlib import Path

from src.engine import run_engine
from src.reporting import attach_default_observers
from src.patterns.strategy import SignalPublisher

def main():
    root = Path(__file__).resolve().parents[2]
    market_csv = root / "data" / "market_data.csv"

    logs: list[str] = []
    alerts: list[str] = []
    pub = attach_default_observers(SignalPublisher(), logs, alerts, alert_notional=5_000.0)

    ctx = run_engine(market_csv, publisher=pub)

    print("Final positions:", ctx.positions)
    print("Final cash:", ctx.cash)
    print(f"Trades executed: {len(ctx.trades)}")
    print(f"Logs: {len(logs)} | Alerts: {len(alerts)}")

if __name__ == "__main__":
    main()
