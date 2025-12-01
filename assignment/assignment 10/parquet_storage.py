from __future__ import annotations

from pathlib import Path
from typing import Tuple

import os
import time

import numpy as np
import pandas as pd

from dataloader import load_and_validate


def write_parquet_partitioned(
    prices_df: pd.DataFrame,
    root_dir: str | Path = "market_data",
) -> None:
    """
    Write OHLCV data to parquet. will partition by symbol under market_data

    structure ex:
      market_data/
        symbol=AAPL/part-*.parquet
        symbol=TSLA/part-*.parquet
    """
    root_dir = Path(root_dir)
    root_dir.mkdir(parents=True, exist_ok=True)

    df = prices_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.to_parquet(
        root_dir,
        engine="pyarrow",
        partition_cols=["symbol"],
        index=False,
    )


def read_ticker_range(
    root_dir: str | Path,
    symbol: str,
    start_ts: str,
    end_ts: str,
) -> pd.DataFrame:
    """
    load all data for a given ticker and date range from parquet store
    """
    root_dir = Path(root_dir)
    df = pd.read_parquet(
        root_dir,
        engine="pyarrow",
        filters=[("symbol", "=", symbol)],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    start = pd.to_datetime(start_ts)
    end = pd.to_datetime(end_ts)

    mask = (df["timestamp"] >= start) & (df["timestamp"] <= end)
    return df.loc[mask].sort_values("timestamp").reset_index(drop=True)


"""Query stuff below"""

def rolling_5min_close_for_aapl(root_dir: str | Path = "market_data") -> pd.DataFrame:
    """
    1. Load all data for AAPL and compute 5-minute rolling avg of the close

    note: assumeing 1-min bars
    """
    df = read_ticker_range(root_dir, "AAPL", "1900-01-01", "2100-01-01")
    df = df.sort_values("timestamp").reset_index(drop=True)

    # step-based
    df["rolling_5min_close"] = df["close"].rolling(window=5, min_periods=1).mean()

    # time0based
    # s = df.set_index("timestamp")["close"]
    # df["rolling_5min_close"] = s.rolling("5T").mean().values

    return df


def rolling_5day_vol_per_ticker(root_dir: str | Path = "market_data") -> pd.DataFrame:
    """
    2. Compute 5-day rolling vol of daily returns for a ticker
    - aggregate to daily close per symbol
    - compute log returns
    - applies rolling 5-day std dev per symbol

    """
    root_dir = Path(root_dir)
    df = pd.read_parquet(root_dir, engine="pyarrow")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # Daily close = last close of each day per symbol
    daily = (
        df.sort_values(["symbol", "timestamp"])
        .groupby(["symbol", "date"])
        .tail(1)
        .reset_index(drop=True)
    )

    daily = daily.sort_values(["symbol", "date"])
    # simple returns
    daily["ret"] = (
        daily.groupby("symbol")["close"].pct_change()
    )
    # log returns
    # daily["ret"] = np.log(daily["close"] / daily.groupby("symbol")["close"].shift(1))

    daily["rolling_5d_vol"] = (
        daily.groupby("symbol")["ret"]
        .rolling(window=5, min_periods=5)
        .std()
        .reset_index(level=0, drop=True)
    )

    return daily[["symbol", "date", "ret", "rolling_5d_vol"]]


def compare_sqlite_vs_parquet_task1(sqlite_conn, parquet_root: str | Path = "market_data") -> dict[str, float]:
    """
    3. compare query time and file size for TSLA/AAPL slice for task 1

    Bencharmking
      - SQLite: TSLA between 2025-11-17 and 2025-11-18
      - Parquet: same slice via read_ticker_range
    """
    from sqlite_storage import get_ticker_data_range

    # Timing
    def time_it(fn, n=5):
        durations = []
        for _ in range(n):
            t0 = time.perf_counter()
            _ = fn()
            durations.append(time.perf_counter() - t0)
        return sum(durations) / len(durations)

    sqlite_fn = lambda: get_ticker_data_range(
        sqlite_conn, "TSLA", "2025-11-17 00:00:00", "2025-11-18 23:59:59"
    )
    parquet_fn = lambda: read_ticker_range(parquet_root, "TSLA", "2025-11-17", "2025-11-18")

    sqlite_time = time_it(sqlite_fn)
    parquet_time = time_it(parquet_fn)

    # File sizes
    sqlite_path = Path(sqlite_conn.execute("PRAGMA database_list;").fetchone()[2])
    sqlite_bytes = sqlite_path.stat().st_size

    parquet_root = Path(parquet_root)
    parquet_bytes = sum(
        f.stat().st_size
        for f in parquet_root.rglob("*.parquet")
    )

    return {
        "sqlite_time_sec": sqlite_time,
        "parquet_time_sec": parquet_time,
        "sqlite_bytes": sqlite_bytes,
        "parquet_bytes": parquet_bytes,
    }


if __name__ == "__main__":
    prices_df, _ = load_and_validate("market_data_multi.csv", "tickers.csv")
    write_parquet_partitioned(prices_df, "market_data")
