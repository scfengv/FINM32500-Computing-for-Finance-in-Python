from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional


class Observer(ABC):
    @abstractmethod
    def update(self, signal: Dict) -> None:
        ...


class SignalPublisher:
    """Simple pub-sub for signals."""
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, obs: Observer) -> None:
        if obs not in self._observers:
            self._observers.append(obs)

    def detach(self, obs: Observer) -> None:
        if obs in self._observers:
            self._observers.remove(obs)

    def notify(self, signal: Dict) -> None:
        for obs in list(self._observers):
            try:
                obs.update(signal)
            except Exception:
                pass


class LoggerObserver(Observer):
    """Logs all signals via a provided callable or print."""
    def __init__(self, log_fn: Optional[Callable[[str], None]] = None):
        self.log_fn = log_fn or (lambda s: print(s))

    def update(self, signal: Dict) -> None:
        self.log_fn(f"[LOG] {signal.get('ts')} | {signal.get('strategy')} | "
                    f"{signal.get('action')} {signal.get('qty')} {signal.get('symbol')} @ {signal.get('price')} | "
                    f"{signal.get('reason')}")


class AlertObserver(Observer):
    """Alerts when notional (|qty|*price) >= threshold."""
    def __init__(self, notional_threshold: float = 10000.0,
                 alert_fn: Optional[Callable[[str], None]] = None):
        self.threshold = float(notional_threshold)
        self.alert_fn = alert_fn or (lambda s: print(s))

    def update(self, signal: Dict) -> None:
        if signal.get("type") != "ORDER":
            return
        qty = abs(float(signal.get("qty", 0)))
        price = float(signal.get("price", 0.0))
        notion = qty * price
        if notion >= self.threshold:
            self.alert_fn(f"[ALERT] Large trade: ${notion:,.2f} | {signal}")


if __name__ == "__main__":
    pub = SignalPublisher()
    logs: List[str] = []
    alerts: List[str] = []

    pub.attach(LoggerObserver(log_fn=logs.append))
    pub.attach(AlertObserver(notional_threshold=5000, alert_fn=alerts.append))

    s1 = {"type": "ORDER", "strategy": "Test", "action": "BUY", "qty": 10, "symbol": "AAA", "price": 400.0, "ts": "T1", "reason": "demo"}
    s2 = {"type": "ORDER", "strategy": "Test", "action": "SELL", "qty": 5, "symbol": "BBB", "price": 200.0, "ts": "T2", "reason": "demo"}

    pub.notify(s1) 
    pub.notify({**s1, "price": 600.0}) 
    pub.notify(s2)

    print("Logs:")
    for x in logs:
        print(x)
    print("\nAlerts:")
    for x in alerts:
        print(x)