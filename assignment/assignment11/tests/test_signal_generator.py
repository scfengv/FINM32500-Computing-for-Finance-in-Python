import pandas as pd
from src.signal_generator import generate_signals_from_prob

def test_signal_generation():
    df = pd.DataFrame({'p': [0.2, 0.6, 0.8]})
    out = generate_signals_from_prob(df, 'p', threshold=0.5)
    assert list(out['signal']) == [0, 1, 1]