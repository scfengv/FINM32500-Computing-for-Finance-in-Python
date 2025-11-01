import os
import psutil
import threading
import tracemalloc
import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

from pathlib import Path
from time import time, perf_counter
from data_loader import load_csv_with_pandas, load_csv_with_polars
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed


# =========================================================
# 1. POLARS: PREPARE WHOLE FRAME (show max strength)
# =========================================================
def polars_prepare_full(df: pl.DataFrame, win: int = 20) -> pl.DataFrame:
    """
    Take the raw polars DataFrame and compute ALL columns we care about
    (rolling mean, rolling std on price, Sharpe on returns) in ONE expression.
    This is what polars is good at.
    """
    return (
        df.sort(["symbol", "timestamp"])
        .with_columns(
            # daily returns per symbol
            pl.col("price")
            .pct_change()
            .over("symbol")
            .alias("ret")
        )
        .with_columns(
            # rolling on PRICE
            pl.col("price").rolling_mean(win).over("symbol").alias("rolling_ma"),
            pl.col("price").rolling_std(win).over("symbol").alias("rolling_std"),
        )
        .with_columns(
            # rolling Sharpe on RETURNS
            (
                pl.col("ret").rolling_mean(win).over("symbol")
                / pl.col("ret").rolling_std(win).over("symbol")
                * np.sqrt(252)
            ).alias("rolling_sharpe")
        )
    )


# =========================================================
# 2. METRIC FUNCTIONS (same outputs as before)
# =========================================================
def Calculate_Metrics_for_Symbol_Pandas(df: pd.DataFrame, symbol: str):
    symbol_df = df[df["symbol"] == symbol].copy()
    prices = symbol_df["price"]

    rolling_ma = prices.rolling(window=20).mean()
    rolling_std = prices.rolling(window=20).std()

    # returns + Sharpe (same math as before)
    returns = prices.pct_change()
    rolling_sharpe = (
        returns.rolling(window=20).mean()
        / returns.rolling(window=20).std()
        * np.sqrt(252)
    )

    return (
        symbol,
        {
            "rolling_ma": rolling_ma,
            "rolling_std": rolling_std,
            "rolling_sharpe": rolling_sharpe,
            "price": prices,
        },
    )


def Calculate_Metrics_for_Symbol_Polars(df: pl.DataFrame, symbol: str):
    """
    IMPORTANT CHANGE:
    - We assume df ALREADY has rolling_ma, rolling_std, rolling_sharpe
      because we ran `polars_prepare_full(...)` once in the rolling function.
    - That way we do NOT recompute per-symbol in Python — we just slice.
    """
    symbol_df = df.filter(pl.col("symbol") == symbol)

    return (
        symbol,
        {
            "rolling_ma": symbol_df["rolling_ma"],
            "rolling_std": symbol_df["rolling_std"],
            "rolling_sharpe": symbol_df["rolling_sharpe"],
            "price": symbol_df["price"],
        },
    )


# =========================================================
# 3. ROLLING MODES (seq / thread / process)
# =========================================================
def Rolling_Sequential(df, Metrics_Function):
    """Baseline: sequential."""
    symbols = ["AAPL", "MSFT", "SPY"]

    # if it's polars + polars metrics: precompute once (this is the key change)
    if isinstance(df, pl.DataFrame) and Metrics_Function is Calculate_Metrics_for_Symbol_Polars:
        df = polars_prepare_full(df)

    results = {}
    for symbol in symbols:
        _, metrics = Metrics_Function(df, symbol)
        results[symbol] = metrics

    return results


def Rolling_with_Threading(df, Metrics_Function):
    symbols = ["AAPL", "MSFT", "SPY"]

    # same idea: precompute once for polars
    if isinstance(df, pl.DataFrame) and Metrics_Function is Calculate_Metrics_for_Symbol_Polars:
        df = polars_prepare_full(df)

    result = {}
    with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
        futures = {
            executor.submit(Metrics_Function, df, symbol): symbol for symbol in symbols
        }

        for fut in as_completed(futures):
            sym, metrics = fut.result()
            result[sym] = metrics

    return result


# =========================================================
# 4. MULTIPROCESSING (better, using ProcessPoolExecutor)
# =========================================================
# We DO NOT pass the whole df to child processes.
# We pass: data_path + symbol(s). Each worker loads what it needs.
# This is the fairest way to compare Pandas vs Polars multiprocessing.


def _pandas_worker(data_path: str, symbol: str):
    df = load_csv_with_pandas(data_path)
    return Calculate_Metrics_for_Symbol_Pandas(df, symbol)


def _polars_worker(data_path: str, symbol: str):
    df = load_csv_with_polars(data_path)
    df = polars_prepare_full(df)  # precompute once inside the worker
    return Calculate_Metrics_for_Symbol_Polars(df, symbol)


def Rolling_with_MultiProcessing_Pandas(data_path: str):
    symbols = ["AAPL", "MSFT", "SPY"]
    results = {}
    with ProcessPoolExecutor(max_workers=len(symbols)) as executor:
        futures = {executor.submit(_pandas_worker, data_path, s): s for s in symbols}
        for fut in as_completed(futures):
            sym, metrics = fut.result()
            results[sym] = metrics
    return results


def Rolling_with_MultiProcessing_Polars(data_path: str):
    symbols = ["AAPL", "MSFT", "SPY"]
    results = {}
    with ProcessPoolExecutor(max_workers=len(symbols)) as executor:
        futures = {executor.submit(_polars_worker, data_path, s): s for s in symbols}
        for fut in as_completed(futures):
            sym, metrics = fut.result()
            results[sym] = metrics
    return results


# =========================================================
# 5. BETTER CPU PROFILER
#    - samples parent+children every 0.1s
#    - returns timeline so you can save it
# =========================================================
def Profiling(func, *args, **kwargs):
    """
    Profile execution time, memory usage, and CPU utilization
    (parent + all children). Also return the CPU timeline.
    Returns:
        result, execution_time, memory_MB, avg_cpu, cpu_timeline
    """
    process = psutil.Process()
    tracemalloc.start()

    cpu_timeline = []
    stop_flag = threading.Event()

    def sampler():
        # prime
        process.cpu_percent(interval=None)
        t0 = perf_counter()
        while not stop_flag.is_set():
            procs = [process] + process.children(recursive=True)
            total_cpu = 0.0
            for p in procs:
                try:
                    total_cpu += p.cpu_percent(interval=None)
                except psutil.NoSuchProcess:
                    pass
            t_rel = perf_counter() - t0
            cpu_timeline.append((t_rel, total_cpu))
            # sample every 0.1s
            stop_flag.wait(0.1)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()

    start_time = time()
    result = func(*args, **kwargs)
    end_time = time()

    stop_flag.set()
    th.join()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # avg over samples
    avg_cpu = sum(c for _, c in cpu_timeline) / len(cpu_timeline) if cpu_timeline else 0.0
    # memory of parent + children
    procs = [process] + process.children(recursive=True)
    memory_MB = sum(p.memory_info().rss for p in procs) / (1024 * 1024)

    return result, end_time - start_time, memory_MB, avg_cpu, cpu_timeline


# =========================================================
# 6. BENCHMARK HELPER
# =========================================================
def benchmark(name, func, *args, **kwargs):
    result, exec_time, memory, cpu, cpu_timeline = Profiling(func, *args, **kwargs)

    print(f"\n{'='*50}")
    print(name)
    print(f"{'='*50}")
    print(f"Execution Time:  {exec_time:.4f} seconds")
    print(f"Peak Memory:     {memory:.2f} MB")
    print(f"CPU Utilization: {cpu:.2f}%")
    print(f"Symbols:         {list(result.keys())}")

    # If you want to dump CPU timeline for your report:
    # pd.DataFrame(cpu_timeline, columns=["t", "cpu"]).to_csv(f"{name.replace(' ', '_')}_cpu.csv", index=False)

    return result, exec_time, memory, cpu, cpu_timeline


# =========================================================
# 7. MAIN
# =========================================================
if __name__ == "__main__":
    data_path = "data/market_data-1.csv"
    records = []

    # ----- Pandas -----
    pdf = load_csv_with_pandas(data_path)
    r = benchmark("Pandas - Sequential", Rolling_Sequential, pdf, Calculate_Metrics_for_Symbol_Pandas); records.append(("Pandas - Seq",) + r[1:4])
    r = benchmark("Pandas - Threading", Rolling_with_Threading, pdf, Calculate_Metrics_for_Symbol_Pandas); records.append(("Pandas - Thr",) + r[1:4])
    r = benchmark("Pandas - Multiprocessing", Rolling_with_MultiProcessing_Pandas, data_path); records.append(("Pandas - MP",) + r[1:4])

    # ----- Polars -----
    pl_df = load_csv_with_polars(data_path)
    r = benchmark("Polars - Sequential", Rolling_Sequential, pl_df, Calculate_Metrics_for_Symbol_Polars); records.append(("Polars - Seq",) + r[1:4])
    r = benchmark("Polars - Threading", Rolling_with_Threading, pl_df, Calculate_Metrics_for_Symbol_Polars); records.append(("Polars - Thr",) + r[1:4])
    r = benchmark("Polars - Multiprocessing", Rolling_with_MultiProcessing_Polars, data_path); records.append(("Polars - MP",) + r[1:4])

    # records = [(name, time, mem_MB, cpu_pct), ...]

    names  = [x[0] for x in records]
    times  = [x[1] for x in records]
    mems   = [x[2] for x in records]
    cpus   = [x[3] for x in records]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # --- left: time ---
    axes[0].bar(names, times)
    axes[0].set_title("Execution Time (s)")
    axes[0].set_ylabel("seconds")
    axes[0].set_xticklabels(names, rotation=30, ha="right")

    # --- right: cpu ---
    axes[1].bar(names, cpus)
    axes[1].set_title("Avg CPU Utilization (%)")
    axes[1].set_ylabel("%")
    axes[1].set_xticklabels(names, rotation=30, ha="right")

    plt.tight_layout()
    fig.savefig("output/polars_vs_pandas.png", dpi=300, bbox_inches="tight")
    plt.show()