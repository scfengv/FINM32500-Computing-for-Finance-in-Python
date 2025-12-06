import pandas as pd
from src.backtest import backtest_signals

def test_backtest_runs():
    df = pd.DataFrame({
        'ticker': ['A'] * 5,
        'date': pd.date_range('2020-01-01', periods=5),
        'close': [10, 11, 12, 11, 12],
        'signal': [1, 1, 1, 1, 1],
    })

    out = backtest_signals(df)
    assert 'strategy_equity' in out.columns
    assert len(out) == 5