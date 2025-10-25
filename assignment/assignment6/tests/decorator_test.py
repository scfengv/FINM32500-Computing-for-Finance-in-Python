import pandas as pd
from src.decorator import Instrument, VolatilityDecorator, BetaDecorator, DrawdownDecorator

def _make_fake_market_data():
    data = {
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='D').repeat(2),
        'symbol': ['AAPL','SPY'] * 5,
        'price': [100,100,101,102,99,103,104,105,103,106]
    }
    df = pd.DataFrame(data)
    return df

def test_volatility_decorator_adds_metric():
    market_data = _make_fake_market_data()
    inst = Instrument('AAPL', 100, 10)
    decorated = VolatilityDecorator(inst, market_data)
    m = decorated.get_metrics()
    assert 'volatility' in m
    assert isinstance(m['volatility'], float)

def test_beta_decorator_adds_metric():
    market_data = _make_fake_market_data()
    inst = Instrument('AAPL', 100, 10)
    decorated = BetaDecorator(inst, market_data, 'SPY')
    m = decorated.get_metrics()
    assert 'beta' in m
    assert isinstance(m['beta'], float)

def test_drawdown_decorator_adds_metric():
    market_data = _make_fake_market_data()
    inst = Instrument('AAPL', 100, 10)
    decorated = DrawdownDecorator(inst, market_data)
    m = decorated.get_metrics()
    assert 'max_drawdown' in m
    assert isinstance(m['max_drawdown'], float)

def test_full_stack_of_decorators():
    market_data = _make_fake_market_data()
    inst = Instrument('AAPL', 100, 10)
    full = DrawdownDecorator(BetaDecorator(VolatilityDecorator(inst, market_data), market_data, 'SPY'), market_data)
    m = full.get_metrics()
    assert all(k in m for k in ['volatility','beta','max_drawdown'])
