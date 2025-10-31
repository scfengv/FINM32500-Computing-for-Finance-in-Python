import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

from data_loader import *

def Rolling_with_Pandas(path: str):
    df = load_csv_with_pandas(path)
    results = {}
    
    for symbol in ["AAPL", "MSFT", "SPY"]:
        symbol_df = df[df["symbol"] == symbol].copy()
        prices = symbol_df["price"]
        
        rolling_ma = prices.rolling(window=20).mean()
        rolling_std = prices.rolling(window=20).std()
        
        # Calculate returns and Sharpe
        returns = prices.pct_change()
        rolling_sharpe = (
            returns.rolling(window=20).mean() / 
            returns.rolling(window=20).std() * 
            (252 ** 0.5)
        )
        
        results[symbol] = {
            'rolling_ma': rolling_ma,
            'rolling_std': rolling_std,
            'rolling_sharpe': rolling_sharpe,
            'price': prices
        }
    
    return results

def Rolling_with_Polars(path: str):
    df = load_csv_with_polars(path)
    df = df.sort(['symbol', 'timestamp'])
    
    # Use .with_columns() and .over() for rolling calculations
    results = df.with_columns([
        # Rolling mean - calculated per symbol group
        pl.col("price").rolling_mean(window_size=20).over("symbol").alias("rolling_ma"),
        
        # Rolling std - calculated per symbol group
        pl.col("price").rolling_std(window_size=20).over("symbol").alias("rolling_std"),
        
        # Returns
        pl.col("price").pct_change().over("symbol").alias("returns")
    ]).with_columns([
        # Sharpe ratio (needs returns first)
        (
            pl.col("returns").rolling_mean(window_size=20) /
            pl.col("returns").rolling_std(window_size=20) *
            (252 ** 0.5)
        ).over("symbol").alias("rolling_sharpe")
    ])
    
def visualization(results_pandas, symbol="AAPL"):
    """Create a single figure with all metrics."""
    data = results_pandas[symbol]
    
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Primary axis: Price and MA
    ax1.plot(data['rolling_ma'].index, data['rolling_ma'].values, 
             label='20-day MA', color='red', linewidth=2)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Price ($)', fontsize=12, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, alpha=0.3)
    
    # Secondary axis: Sharpe Ratio
    ax2 = ax1.twinx()
    ax2.plot(data['rolling_sharpe'].index, data['rolling_sharpe'].values, 
             label='Sharpe Ratio', color='green', linewidth=2, alpha=0.7)
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Sharpe Ratio', fontsize=12, color='green')
    ax2.tick_params(axis='y', labelcolor='green')
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    plt.title(f'{symbol} - Price, MA, and Sharpe Ratio', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'output/{symbol}_results.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    path = "data/market_data-1.csv"
    
    print("=== Rolling Metrics with Pandas ===")
    df_pandas, time_pandas, mem_pandas = profiling(load_csv_with_pandas, path)
    print(f"Time: {time_pandas:.4f} seconds")
    print(f"Memory: {mem_pandas:.2f} MB")
    print(f"Shape: {df_pandas.shape}")
    print(f"Columns: {df_pandas.columns.tolist()}")
    print()
    
    print("=== Rolling Metrics with Polars ===")
    df_polars, time_polars, mem_polars = profiling(load_csv_with_polars, path)
    print(f"Time: {time_polars:.4f} seconds")
    print(f"Memory: {mem_polars:.2f} MB")
    print(f"Shape: {df_polars.shape}")
    print(f"Columns: {df_polars.columns}")
    print()
    
    # Comparison
    print("=== Comparison ===")
    print(f"Polars is {time_pandas/time_polars:.2f}x faster")
    print(f"Polars uses {mem_pandas/mem_polars:.2f}x less memory")
    
    # Visualization
    results_pandas = Rolling_with_Pandas(path)
    visualization(results_pandas, symbol = "AAPL")