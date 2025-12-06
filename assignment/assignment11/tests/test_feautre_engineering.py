import pandas as pd
from src.feature_engineering import add_labels, add_technical_features

def test_technical_features():
    df = pd.DataFrame({
        'ticker': ['A'] * 10,
        'date': pd.date_range('2020-01-01', periods=10),
        'close': range(10),
        'open': range(10),
        'high': range(10),
        'low': range(10),
        'volume': range(10),
    })

    out = add_technical_features(df)
    assert 'return' in out.columns
    assert 'sma_5' in out.columns
    assert 'macd' in out.columns

def test_labels():
    df = pd.DataFrame({
        'ticker': ['A'] * 5,
        'date': pd.date_range('2020-01-01', periods=5),
        'close': [10, 11, 12, 13, 14],
        'open': [10, 11, 12, 13, 14],
        'high': [10, 11, 12, 13, 14],
        'low': [10, 11, 12, 13, 14],
        'volume': [1, 1, 1, 1, 1],
    })

    df = add_technical_features(df)
    df = add_labels(df)

    assert 'target' in df.columns