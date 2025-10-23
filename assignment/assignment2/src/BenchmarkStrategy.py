# BenchmarkStrategy.py
import pandas as pd
from BaseStrategy import Strategy, StrategyResult

class BenchmarkStrategy(Strategy):
    def __init__(self):
        super().__init__(shares_per_ticker=0)  # for benchmark, set qty later in run (equal allocation)

    def generate_signals(self, prices: pd.DataFrame):
        sig = self.empty_signals(prices)
        sig.iloc[0] = 1
        return sig

    def run(self, prices: pd.DataFrame):
        positions = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        cash = 1000000.0
        signals = self.generate_signals(prices)
        
        spent = 0
        for tick in prices.columns:
            first_p = prices.iloc[0][tick]
            if pd.notna(first_p):
                qty = int((cash / len(prices.columns)) / first_p)  # X shares per ticker
            else:
                qty = 0
            positions.loc[positions.index[0], tick] = qty
            spent += qty * (0 if pd.isna(first_p) else first_p)
        cash -= spent
        positions.iloc[1:] = positions.iloc[0]  # Hold forever

        cash_series = pd.Series(cash, index=prices.index, name='cash')
        port_val = (positions * prices).sum(axis=1) + cash_series
        cum_pnl = port_val - 1000000.0

        return StrategyResult(
            positions=positions,
            cash=cash_series,
            port_val=port_val,
            cum_pnl=cum_pnl,
            signals=signals
        )
