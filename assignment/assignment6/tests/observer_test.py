# tests/observer_command_test.py
from datetime import datetime
from src.patterns.strategy import SignalPublisher, LoggerObserver, AlertObserver
from src.patterns.command import ExecutionContext, ExecuteOrderCommand, CommandInvoker

def test_observer_notifications():
    logs = []
    alerts = []

    pub = SignalPublisher()
    pub.attach(LoggerObserver(log_fn=logs.append))
    pub.attach(AlertObserver(notional_threshold=5000, alert_fn=alerts.append))

    sig = {
        "type": "ORDER",
        "strategy": "Demo",
        "action": "BUY",
        "qty": 10,
        "symbol": "AAA",
        "price": 600.0,
        "ts": datetime(2024, 1, 1, 9, 30),
        "reason": "trigger",
    }

    pub.notify(sig)

    assert len(logs) == 1
    assert "AAA" in logs[0]
    assert "BUY" in logs[0]

    assert len(alerts) == 1
    assert "Large trade" in alerts[0]

def test_command_execute_and_undo_logic():
    ctx = ExecutionContext(cash=100000.0)
    inv = CommandInvoker()

    signal = {
        "action": "BUY",
        "symbol": "XYZ",
        "qty": 100,
        "price": 50.0,
        "type": "ORDER",
        "ts": "T1",
        "reason": "demo",
        "strategy": "Demo",
    }

    cmd = ExecuteOrderCommand(ctx, signal)
    inv.execute(cmd)

    assert ctx.positions["XYZ"] == 100
    assert ctx.cash == 100000.0 - 100 * 50.0

    inv.undo()
    assert ctx.positions["XYZ"] == 0
    assert abs(ctx.cash - 100000.0) < 1e-9

    inv.redo()
    assert ctx.positions["XYZ"] == 100
    assert ctx.cash == 100000.0 - 100 * 50.0