import pytest
from src.factory import InstrumentFactory, Stock, Bond, ETF

def test_factory_creates_stock():
    data = {'type': 'Stock', 'symbol': 'AAPL', 'price': 185.0, 'sector': 'Tech', 'issuer': 'Apple'}
    inst = InstrumentFactory.create_instrument(data)
    assert isinstance(inst, Stock)
    assert inst.symbol == 'AAPL'
    assert inst.price == 185.0

def test_factory_creates_bond():
    data = {'type': 'Bond', 'symbol': 'UST10', 'price': 99.5, 'sector': 'Govt', 'issuer': 'US Treasury', 'maturity': '2034-01-01'}
    inst = InstrumentFactory.create_instrument(data)
    assert isinstance(inst, Bond)
    assert inst.maturity == '2034-01-01'

def test_factory_creates_etf():
    data = {'type': 'ETF', 'symbol': 'SPY', 'price': 500.0, 'sector': 'Index', 'issuer': 'State Street'}
    inst = InstrumentFactory.create_instrument(data)
    assert isinstance(inst, ETF)
    assert inst.symbol == 'SPY'

def test_factory_invalid_type_raises():
    bad_data = {'type': 'Crypto', 'symbol': 'BTC'}
    with pytest.raises(ValueError):
        InstrumentFactory.create_instrument(bad_data)
