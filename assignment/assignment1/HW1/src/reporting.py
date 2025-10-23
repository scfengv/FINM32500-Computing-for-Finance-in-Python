# src/reporting.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def performance_reporting(equity_ts):
    # Convert to DataFrame for easy calculations
    df = pd.DataFrame(equity_ts, columns=['timestamp', 'equity']).set_index('timestamp')

    # Returns series
    r = df['equity'].pct_change()
    r = r.replace([np.inf, -np.inf], np.nan).fillna(0.0)  # Handle bad values
    cum_ret = (1 + r).cumprod() - 1

    # Drawdown
    cum_val = cum_ret + 1
    peak = cum_val.cummax()
    dd = (peak - cum_val) / peak

    # VaR and CVaR (something extra just for fun)
    var = r.quantile(.05)
    es = r[r <= var].mean()

    return {
        'Total Return': cum_ret.iloc[-1],
        'Sharpe': r.mean() / r.std(),
        'Max Drawdown': dd.max(),
        'Value at Risk (95%)': var,
        'Expected Shortfall (Conditional 95% VaR)': es,
        'r_series': r,
        'cum_r_series': cum_ret,
        'dd_series': dd
    }

def plot_r_ts(cum_ret):
    plt.plot(cum_ret.index, cum_ret)
    plt.title("Cumulative Returns")
    plt.ylabel("Cumulative Return")
    plt.xlabel("Time")
    plt.show()

def plot_r_dist(r):
    plt.hist(r, bins=30, density=True)
    plt.title("Distribution of Returns")
    plt.ylabel("Frequency")
    plt.xlabel("Return")
    plt.show()

def plot_dd(dd):
    plt.plot(dd.index, dd)
    plt.title("Drawdown Series")
    plt.ylabel("Drawdown")
    plt.xlabel("Time")
    plt.show()
