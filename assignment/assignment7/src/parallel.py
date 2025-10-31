import psutil
import tracemalloc
import numpy as np
import pandas as pd

from time import time
from data_loader import load_csv_with_pandas
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

def Calculate_Metrics_for_Symbol(path, symbol):
    df = load_csv_with_pandas(path)
    symbol_df = df[df["symbol"] == symbol].copy()
    prices = symbol_df["price"]
        
    rolling_ma = prices.rolling(window=20).mean()
    rolling_std = prices.rolling(window=20).std()
    
    # Calculate returns and Sharpe
    returns = prices.pct_change()
    rolling_sharpe = (
        returns.rolling(window=20).mean() / 
        returns.rolling(window=20).std() * 
        np.sqrt(252)
    )
    
    return (symbol, {
        'rolling_ma': rolling_ma,
        'rolling_std': rolling_std,
        'rolling_sharpe': rolling_sharpe,
        'price': prices
    })

def Rolling_Sequential(path: str):
    """Baseline: Sequential processing."""
    symbols = ["AAPL", "MSFT", "SPY"]
    results = {}
    
    for symbol in symbols:
        _, metrics = Calculate_Metrics_for_Symbol(path, symbol)
        results[symbol] = metrics
    
    return results

def Rolling_with_Threading(path: str):
    symbols = ["AAPL", "MSFT", "SPY"]
    result = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(Calculate_Metrics_for_Symbol, path, symbol) for symbol in symbols
        ]

    for future in futures:
        result[future.result()[0]] = future.result()[1]

    return result

def Rolling_with_MultiProcessing(path: str):
    symbols = ["AAPL", "MSFT", "SPY"]
    result = {}

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(Calculate_Metrics_for_Symbol, path, symbol) for symbol in symbols
        ]

    for future in futures:
        result[future.result()[0]] = future.result()[1]

    return result

def Profiling(func, *args, **kwargs):
    """
    Profile execution time, memory usage, and CPU utilization.
    
    Returns:
        tuple: (result, execution_time, peak_memory_mb, avg_cpu_percent)
    """
    # CPU
    process = psutil.Process()
    cpu_percentages = []
    
    # Memory Tracking
    tracemalloc.start()
    
    # Time Tracking
    start_time = time()
    
    # CPU Tracking
    process.cpu_percent(interval=None)
    
    result = func(*args, **kwargs)
    
    cpu_usage = process.cpu_percent(interval=0.1)
    cpu_percentages.append(cpu_usage)
    
    end_time = time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    execution_time = end_time - start_time
    peak_memory_mb = peak / (1024 * 1024)
    avg_cpu_percent = sum(cpu_percentages) / len(cpu_percentages)

    return result, execution_time, peak_memory_mb, avg_cpu_percent

def benchmark(name, func, path):
    """Benchmark a function with detailed profiling."""
    result, exec_time, memory, cpu = Profiling(func, path)
    
    print(f"\n{'='*50}")
    print(f"{name}")
    print(f"{'='*50}")
    print(f"Execution Time:  {exec_time:.4f} seconds")
    print(f"Peak Memory:     {memory:.2f} MB")
    print(f"CPU Utilization: {cpu:.2f}%")
    print(f"Symbols:         {list(result.keys())}")
    
    return result, exec_time, memory, cpu

if __name__ == "__main__":
    data_path = "data/market_data-1.csv"
    
    benchmark("Sequential Processing", Rolling_Sequential, data_path)
    benchmark("Threading Processing", Rolling_with_Threading, data_path)
    benchmark("Multiprocessing Processing", Rolling_with_MultiProcessing, data_path)