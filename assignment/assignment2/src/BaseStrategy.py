# Strategy.py
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class StrategyResult:
    positions: pd.DataFrame
    cash: pd.Series
    port_val: pd.Series
    cum_pnl: pd.Series
    signals: pd.DataFrame

class Strategy:
    """
    Base class for all strategies.
    """
    def __init__(self, shares_per_ticker):
        self.qty = shares_per_ticker

    def empty_signals(self, prices: pd.DataFrame):
        return pd.DataFrame(0, index=prices.index, columns=prices.columns)  # DataFrame for signals

    def generate_signals(self, prices: pd.DataFrame):
        raise NotImplementedError("Must implement generate_signals")

    def run(self, prices: pd.DataFrame, transaction_cost: float = 0.0035) -> StrategyResult:
        positions = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        cash = 1000000.0  # Initial cash is 1 mil for all strats
        signals = self.generate_signals(prices)

        cash_series = pd.Series(0.0, index=prices.index)
        port_val = pd.Series(0.0, index=prices.index)
        
        for i in range(1, len(prices)):
            curr_signals = signals.iloc[i-1]  # act on previous day's signal
            curr_prices = prices.iloc[i]
            curr_pos = positions.iloc[i - 1].copy()  # Carry positions forward to amend today
            
            for tick in prices.columns:
                if curr_signals[tick] == -1 and curr_pos[tick] > 0:  # No shorting
                    sell = min(self.qty, curr_pos[tick])  # Again, can't sell more than we have
                    cash += (sell * curr_prices[tick]) * (1 - transaction_cost)
                    curr_pos[tick] -= sell

                elif curr_signals[tick] == 1:
                    buy = min(self.qty, cash // curr_prices[tick]) # No leverage
                    cash -= (buy * curr_prices[tick]) * (1 + transaction_cost)
                    curr_pos[tick] += buy
                
            positions.iloc[i] = curr_pos
            cash_series.iloc[i] = cash
            port_val.iloc[i] = cash + (positions.iloc[i] * curr_prices).sum()
        
        cum_pnl = port_val - 1000000.0

        return StrategyResult(
            positions=positions,
            cash=cash_series,
            port_val=port_val,
            cum_pnl=cum_pnl,
            signals=signals
        )
