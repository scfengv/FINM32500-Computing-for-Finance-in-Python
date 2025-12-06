import pandas as pd

def generate_signals_from_prob(df, prob_col: str, threshold: float = 0.5, signal_col: str = 'signal'):
    df = df.copy()
    df[signal_col] = (df[prob_col] > threshold).astype(int)
    return df