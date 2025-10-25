from __future__ import annotations
from typing import List
from src.patterns.strategy import SignalPublisher, LoggerObserver, AlertObserver

def attach_default_observers(pub: SignalPublisher, logs: List[str], alerts: List[str], alert_notional=10_000.0):
    pub.attach(LoggerObserver(log_fn=logs.append))
    pub.attach(AlertObserver(notional_threshold=alert_notional, alert_fn=alerts.append))
    return pub
