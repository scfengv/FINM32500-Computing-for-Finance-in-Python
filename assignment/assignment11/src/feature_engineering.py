import pandas as pd
import numpy as np

def load_market_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['ticker', 'date']).reset_index(drop=True)
    return df

def load_tickers(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    return df

def _compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def _compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for window in (5, 10, 20):
        df[f'sma_{window}'] = (df.groupby('ticker')['close'].transform(lambda x: x.rolling(window).mean()))

    df['return'] = df.groupby('ticker')['close'].pct_change()
    df['log_return'] = np.log1p(df['return'])

    df['return_1d'] = df.groupby('ticker')['return'].shift(1)
    df['return_3d'] = df.groupby('ticker')['return'].shift(3)
    df['return_5d'] = df.groupby('ticker')['return'].shift(5)

    df['rsi_14'] = df.groupby('ticker')['close'].transform(_compute_rsi)

    macd_data = []
    signal_data = []
    for _, grp in df.groupby('ticker'):
        macd, sig = _compute_macd(grp['close'])
        macd_data.append(macd)
        signal_data.append(sig)

    df['macd'] = pd.concat(macd_data).sort_index()
    df['macd_signal'] = pd.concat(signal_data).sort_index()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    return df

def add_labels(df: pd.DataFrame, horizon: int = 1, task: str = 'classification') -> pd.DataFrame:
    df = df.copy()
    fut_ret = df.groupby('ticker')['log_return'].shift(-horizon)

    if task == 'classification':
        df['direction'] = (fut_ret > 0).astype(int)
    else:
        df['direction'] = fut_ret

    df = df.dropna().reset_index(drop=True)
    return df

def build_feature_dataset(market_path: str, tickers_path: str, task: str = 'classification', horizon: int = 1) -> pd.DataFrame:
    md = load_market_data(market_path)
    tickers = load_tickers(tickers_path)

    md = md[md['ticker'].isin(tickers['symbol'])]
    md = add_technical_features(md)
    md = add_labels(md, horizon=horizon, task=task)
    return md