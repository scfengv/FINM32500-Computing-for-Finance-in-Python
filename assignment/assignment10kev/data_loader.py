from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd


REQUIRED_MARKET_COLS = ["timestamp", "ticker", "open", "high", "low", "close", "volume"]
REQUIRED_TICKER_COLS = ["ticker_id", "symbol"]


@dataclass(frozen=True)
class Paths:
    market_csv: Path
    tickers_csv: Path


def load_tickers(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = sorted(set(REQUIRED_TICKER_COLS) - set(df.columns))
    if missing:
        raise ValueError(f"tickers.csv missing columns: {missing}")
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    return df


def load_market_data(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = sorted(set(REQUIRED_MARKET_COLS) - set(df.columns))
    if missing:
        raise ValueError(f"market_data_multi.csv missing columns: {missing}")

    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")

    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    df["volume"] = pd.to_numeric(df["volume"], errors="raise").astype("int64")

    df = df.sort_values(["ticker", "timestamp"]).reset_index(drop=True)
    return df


def validate_market_data(market_df: pd.DataFrame, tickers_df: pd.DataFrame) -> None:
    if market_df[["timestamp", "ticker", "open", "high", "low", "close", "volume"]].isna().any().any():
        bad = market_df[market_df[["timestamp", "ticker", "open", "high", "low", "close", "volume"]].isna().any(axis=1)]
        raise ValueError(f"missing required values (showing up to 5):\n{bad.head()}")

    expected = set(tickers_df["symbol"].unique())
    found = set(market_df["ticker"].unique())
    missing = sorted(expected - found)
    if missing:
        raise ValueError(f"tickers missing from market data: {missing}")

    if market_df.duplicated(subset=["ticker", "timestamp"]).any():
        dups = market_df[market_df.duplicated(subset=["ticker", "timestamp"], keep=False)].head()
        raise ValueError(f"duplicate bars found (showing up to 5):\n{dups}")

    for (ticker, day), g in market_df.groupby(["ticker", market_df["timestamp"].dt.date], sort=False):
        ts = g["timestamp"]
        rng = pd.date_range(ts.min(), ts.max(), freq="min")
        if len(rng) != len(g):
            have = set(ts.astype("datetime64[ns]").to_list())
            want = set(rng.to_list())
            sample = sorted(want - have)[:5]
            raise ValueError(f"missing timestamps for {ticker} {day}; sample: {sample}")


def load_and_validate(paths: Paths) -> tuple[pd.DataFrame, pd.DataFrame]:
    tickers = load_tickers(paths.tickers_csv)
    market = load_market_data(paths.market_csv)
    validate_market_data(market, tickers)
    return market, tickers


