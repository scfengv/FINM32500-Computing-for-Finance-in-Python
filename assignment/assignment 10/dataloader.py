# data_loader.py
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


PRICE_REQUIRED_COLS = {"timestamp", "ticker", "open", "high", "low", "close", "volume"}
TICKER_REQUIRED_COLS = {"ticker_id", "symbol", "name", "exchange"}


def load_market_data(csv_path: str | Path) -> pd.DataFrame:
    """
    Load raw multi-ticker OHLCV data from market_data_multi.csv with cols timestamp, ticker, open, high, low, close, volume
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    # normalize col names
    df.columns = [c.strip().lower() for c in df.columns]

    missing = PRICE_REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"market_data_multi.csv missing columns: {missing}")

    # parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # use 'symbol' instead of 'ticker' internally
    df = df.rename(columns={"ticker": "symbol"})

    # ensure numeric
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    return df


def load_tickers(csv_path: str | Path) -> pd.DataFrame:
    """
    Load tickers.csv with ticker_id, symbol, name, exchange
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = TICKER_REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"tickers.csv missing columns: {missing}")

    # make sure types are correct and clean
    df["ticker_id"] = df["ticker_id"].astype(int)
    df["symbol"] = df["symbol"].astype(str)
    df["name"] = df["name"].astype(str)
    df["exchange"] = df["exchange"].astype(str)

    df = df.drop_duplicates(subset=["ticker_id", "symbol"]).reset_index(drop=True)
    return df[["ticker_id", "symbol", "name", "exchange"]]


def validate_no_missing_prices(prices: pd.DataFrame) -> None:
    """
    Check for NaN in timestamp and OHLCV
    """
    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    bad = prices[cols].isna().any(axis=1)
    if bad.any():
        raise ValueError(
            f"Found {bad.sum()} rows with missing timestamps or prices/volume."
        )


def validate_all_tickers_present(prices: pd.DataFrame, tickers: pd.DataFrame) -> None:
    """
    Ensure every symbol in tickers.csv appears in the price data at least once
    """
    price_syms = set(prices["symbol"].unique())
    expected_syms = set(tickers["symbol"].unique())

    missing = expected_syms - price_syms
    if missing:
        raise ValueError(f"Tickers missing in price data: {sorted(missing)}")


def load_and_validate(
    prices_csv: str | Path = "market_data_multi.csv",
    tickers_csv: str | Path = "tickers.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    entrypoint for the assignment.

    returns: (prices_df, tickers_df)
    """
    prices = load_market_data(prices_csv)
    tickers = load_tickers(tickers_csv)

    validate_no_missing_prices(prices)
    validate_all_tickers_present(prices, tickers)

    return prices, tickers
