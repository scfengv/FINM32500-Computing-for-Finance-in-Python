import psutil
import threading
import tracemalloc
import numpy as np
import pandas as pd

from time import time
from data_loader import load_csv_with_pandas
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

def Calculate_Metrics_for_Symbol(df, symbol):
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

def Rolling_Sequential(df: pd.DataFrame):
    """Baseline: Sequential processing."""
    symbols = ["AAPL", "MSFT", "SPY"]
    results = {}
    
    for symbol in symbols:
        _, metrics = Calculate_Metrics_for_Symbol(df, symbol)
        results[symbol] = metrics
    
    return results

def Rolling_with_Threading(df: pd.DataFrame):
    symbols = ["AAPL", "MSFT", "SPY"]
    result = {}

    with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
        futures = {
            executor.submit(Calculate_Metrics_for_Symbol, df, symbol): symbol for symbol in symbols
        }

    # as_completed: a generator that yields futures in the order they finish, not in the order you submitted them.
    for future in as_completed(futures):
        sym, metrics = future.result()
        result[sym] = metrics

    return result

def Rolling_with_MultiProcessing(df: pd.DataFrame):
    symbols = ["AAPL", "MSFT", "SPY"]
    result = {}

    with ProcessPoolExecutor(max_workers=len(symbols)) as executor:
        futures = {
            executor.submit(Calculate_Metrics_for_Symbol, df, symbol) for symbol in symbols
        }

    for future in as_completed(futures):
        sym, metrics = future.result()
        result[sym] = metrics

    return result
            
def Profiling(func, *args, **kwargs):
    """
    Profile execution time, memory usage, and CPU utilization.
    
    Returns:
        tuple: (result, execution_time, peak_memory_mb, avg_cpu_percent)
    """
    # CPU Tracking
    process = psutil.Process()
    # Memory Tracking
    tracemalloc.start()
    
    # .cpu_percent(): needs two measurements to give a real %
    # First call = “prime” / baseline (returns 0.0 or junk).
    # Second call (later) = real % over the time since the first call.
    cpu_samples = []
    stop_sampling = threading.Event() # A threading flag/signal to tell the background thread when to stop
    
    def sample_cpu(): #  repeatedly measure CPU usage
        process.cpu_percent()  # initializes/primes the measurement # returns 0.0
        while not stop_sampling.is_set(): # Keep looping until the Event flag has been raised
            processes = [process] + process.children(recursive=True) # 'recursive = True' means it gets children, grandchildren, etc.
            # Get a list of main process and all child processes, and sum their CPU %
            cpu = sum(p.cpu_percent(interval=0.1) for p in processes if p.is_running()) # wait 0.1 seconds and measure CPU during that time
            cpu_samples.append(cpu)
    
    sampler = threading.Thread(target=sample_cpu, daemon=True) # 'daemon=True': Thread will automatically die when main program exits
    sampler.start()

    # Time Tracking
    start_time = time()
    
    result = func(*args, **kwargs)
    
    end_time = time()
    
    stop_sampling.set() # Signals the background thread to stop sampling, which makes 'stop_sampling.is_set()' return True
    sampler.join() # Waits for the sampler thread to finish cleanly
    
    current, peak = tracemalloc.get_traced_memory() # Memory used right now & Maximum memory used during execution
    tracemalloc.stop()
    
    # With a ProcessPoolExecutor, most CPU is in child processes, not the main one.
    processes = [process] + process.children(recursive=True) # list the main process and all its children, and sum their CPU %
    cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
    
    execution_time = end_time - start_time
    memory_MB = sum(p.memory_info().rss for p in processes) / (1024 * 1024)
    
    return result, execution_time, memory_MB, cpu

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
    df = load_csv_with_pandas(data_path)

    benchmark("Sequential Processing", Rolling_Sequential, df)
    benchmark("Threading Processing", Rolling_with_Threading, df)
    benchmark("Multiprocessing Processing", Rolling_with_MultiProcessing, df)