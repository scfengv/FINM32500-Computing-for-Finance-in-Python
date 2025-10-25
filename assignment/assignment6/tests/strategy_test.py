from datetime import datetime, timedelta
from src.patterns.strategy import MarketDataPoint, MeanReversionStrategy, BreakoutStrategy

def test_mean_reversion_buy_and_sell_signals():
    base = datetime(2024, 1, 1, 9, 30)
    mr = MeanReversionStrategy(window=5, k=1.0, qty=10)

    prices = [100, 100, 100, 100, 100, 95, 105]
    signals = []
    for i, px in enumerate(prices):
        sigs = mr.generate_signals(MarketDataPoint("AAA", base + timedelta(minutes=i), px))
        signals.extend(sigs)

    actions = [s["action"] for s in signals]
    assert "BUY" in actions
    assert "SELL" in actions
    for s in signals:
        assert s["strategy"] == "MeanReversion"
        assert "z=" in s["reason"]

def test_breakout_strategy_triggers_on_high_and_low():
    base = datetime(2024, 1, 1, 9, 30)
    br = BreakoutStrategy(lookback=3, qty=5)

    prices = [10, 11, 12, 13, 12, 14, 9]
    signals = []
    for i, px in enumerate(prices):
        sigs = br.generate_signals(
            {"symbol": "BBB", "timestamp": base + timedelta(minutes=i), "price": px}
        )
        signals.extend(sigs)

    actions = [s["action"] for s in signals]
    assert "BUY" in actions
    assert "SELL" in actions
    for s in signals:
        assert s["strategy"] == "Breakout"
        assert s["symbol"] == "BBB"
        assert "Break" in s["reason"]
