from __future__ import annotations

from pathlib import Path
import shutil
import time
import pandas as pd

try:
    import pyarrow  # noqa: F401
    _HAS_PYARROW = True
except Exception:
    _HAS_PYARROW = False


def _need_pyarrow() -> None:
    if not _HAS_PYARROW:
        raise RuntimeError("pyarrow is required for Parquet tasks: pip install pyarrow")


def write_partitioned_parquet(df: pd.DataFrame, out_dir: str | Path, overwrite: bool = True) -> None:
    _need_pyarrow()
    out = Path(out_dir)
    if overwrite and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, engine="pyarrow", partition_cols=["ticker"], index=False)


def read_ticker_range_parquet(out_dir: str | Path, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    _need_pyarrow()
    start = pd.to_datetime(start_date)
    end_excl = pd.to_datetime(end_date) + pd.Timedelta(days=1)
    df = pd.read_parquet(
        out_dir,
        engine="pyarrow",
        filters=[("ticker", "==", symbol.upper())],
        columns=["timestamp", "ticker", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[(df["timestamp"] >= start) & (df["timestamp"] < end_excl)].sort_values("timestamp").reset_index(drop=True)
    return df


def aapl_5min_rolling_close_avg(out_dir: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(
        out_dir,
        engine="pyarrow",
        filters=[("ticker", "==", "AAPL")],
        columns=["timestamp", "ticker", "close"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["roll5_close_avg"] = df["close"].rolling(window=5, min_periods=5).mean()
    return df


def rolling_5d_volatility_of_daily_returns(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["ticker", "timestamp"])
    df["day"] = df["timestamp"].dt.date
    daily_close = df.groupby(["ticker", "day"], as_index=False)["close"].last()
    daily_close["ret"] = daily_close.groupby("ticker")["close"].pct_change()
    daily_close["vol_5d"] = daily_close.groupby("ticker")["ret"].rolling(window=5, min_periods=5).std().reset_index(level=0, drop=True)
    return daily_close


def parquet_dir_size_bytes(out_dir: str | Path) -> int:
    p = Path(out_dir)
    if not p.exists():
        return 0
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def timed(fn, runs: int = 3):
    vals = []
    out = None
    for _ in range(runs):
        t0 = time.perf_counter()
        out = fn()
        vals.append(time.perf_counter() - t0)
    return out, sum(vals) / len(vals)
