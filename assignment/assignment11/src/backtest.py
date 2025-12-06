import pandas as pd

def backtest_signals(df: pd.DataFrame, signal_col: str = 'signal'):
    df = df.copy()
    df = df.sort_values(['ticker', 'date'])

    df['return'] = df.groupby('ticker')['close'].pct_change()
    df['signal_lag'] = df.groupby('ticker')[signal_col].shift(1)
    df['strategy_return'] = df['signal_lag'] * df['return']

    daily = (df.groupby('date').agg(strategy_return=('strategy_return', 'mean'), benchmark_return=('return', 'mean')).sort_index())
    daily['strategy_equity'] = (1 + daily['strategy_return'].fillna(0)).cumprod()
    daily['benchmark_equity'] = (1 + daily['benchmark_return'].fillna(0)).cumprod()
    return daily

def summarize_performance(df):
    strat = df['strategy_return']
    bench = df['benchmark_return']

    def ann_ret(r):
        if len(r) == 0:
            return 0
        total = (1 + r).prod()
        return total ** (252 / len(r)) - 1

    def ann_vol(r):
        return r.std() * (252 ** 0.5)

    def sharpe(r):
        if ann_vol(r) == 0:
            return 0
        return (ann_ret(r)) / ann_vol(r)

    return {
        'strategy_cum': df['strategy_equity'].iloc[-1] - 1,
        'benchmark_cum': df['benchmark_equity'].iloc[-1] - 1,
        'strategy_ann': ann_ret(strat),
        'benchmark_ann': ann_ret(bench),
        'strategy_vol': ann_vol(strat),
        'benchmark_vol': ann_vol(bench),
        'strategy_sharpe': sharpe(strat),
    }