import tracemalloc
import pandas as pd
import polars as pl

from time import time

def load_csv_with_pandas(path: str) -> pd.DataFrame:
    """Load a CSV file into a Pandas DataFrame."""
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    return df

def load_csv_with_polars(path: str) -> pl.DataFrame:
    """Load a CSV file into a Polars DataFrame."""
    df = pl.read_csv(path)
    df = df.with_columns(
        pl.col('timestamp').str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
    )
    return df

def profiling(func, *args, **kwargs):
    """Profile execution time and memory usage of a function"""
    # Memory
    tracemalloc.start()
    
    # Time
    start = time()
    result = func(*args, **kwargs)
    end = time()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    execution_time = end - start
    peak_MB = peak / (1024**2)
    
    return result, execution_time, peak_MB

if __name__ == "__main__":
    
    path = "data/market_data-1.csv"
    print("=== Profiling Data Loading ===\n")
    
    # Profile Pandas
    print("--- Pandas ---")
    df_pandas, time_pandas, mem_pandas = profiling(load_csv_with_pandas, path)
    print(f"Time: {time_pandas:.4f} seconds")
    print(f"Memory: {mem_pandas:.2f} MB")
    print(f"Shape: {df_pandas.shape}")
    print(f"Columns: {df_pandas.columns.tolist()}")
    print()
    
    # Profile Polars
    print("--- Polars ---")
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