from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Tuple

import pandas as pd

from dataloader import load_and_validate


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: str | Path = "schema.sql") -> None:
    schema_path = Path(schema_path)
    sql_text = schema_path.read_text(encoding="utf-8")
    conn.executescript(sql_text)
    conn.commit()

    # Optional but highly recommended for performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker_ts ON prices(ticker_id, timestamp);")
    conn.commit()


def insert_tickers(conn: sqlite3.Connection, tickers_df: pd.DataFrame) -> None:
    """
    insert tickers from tickers.csv using existing ticker_id
    """
    df = tickers_df.copy()

    # enforce dtypes here
    df["ticker_id"] = df["ticker_id"].astype(int)
    df["symbol"] = df["symbol"].astype(str)
    df["name"] = df["name"].astype(str)
    df["exchange"] = df["exchange"].astype(str)

    # build list of tuples with pure Python types
    records = [
        (
            int(row.ticker_id),
            row.symbol,
            row.name,
            row.exchange,
        )
        for row in df.itertuples(index=False)
    ]

    with conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO tickers(ticker_id, symbol, name, exchange)
            VALUES (?, ?, ?, ?)
            """,
            records,
        )


def insert_prices(conn: sqlite3.Connection, prices_df: pd.DataFrame) -> None:
    """
    Insert OHLCV prices with prices_df columns timestamp, symbol, open, high, low, close, volume
    """
    df = prices_df.copy()

    # 1) Build symbol -> ticker_id map from tickers table
    rows = conn.execute("SELECT ticker_id, symbol FROM tickers;").fetchall()
    sym_to_id = {symbol: ticker_id for (ticker_id, symbol) in rows}

    # 2) Check that every symbol in prices has a ticker_id
    missing_syms = set(df["symbol"].unique()) - set(sym_to_id.keys())
    if missing_syms:
        raise ValueError(f"Symbols in prices not found in tickers table: {missing_syms}")

    df["ticker_id"] = df["symbol"].map(sym_to_id)

    # 3) Normalize types
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df["ticker_id"] = df["ticker_id"].astype(int)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(int)

    # 4) ❗ Build plain Python tuples instead of using .to_records()
    records = [
        (
            row.timestamp,
            int(row.ticker_id),
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            int(row.volume),
        )
        for row in df.itertuples(index=False)
    ]

    # 5) Insert
    with conn:
        conn.executemany(
            """
            INSERT INTO prices(timestamp, ticker_id, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )



# Query stuff

def get_ticker_data_range(
    conn: sqlite3.Connection,
    symbol: str,
    start_ts: str,
    end_ts: str,
) -> pd.DataFrame:
    """
    1. retrieve all data for a ticker and date range
    """
    sql = """
        SELECT
            p.timestamp,
            t.symbol,
            p.open, p.high, p.low, p.close, p.volume
        FROM prices p
        JOIN tickers t ON p.ticker_id = t.ticker_id
        WHERE t.symbol = ?
          AND p.timestamp >= ?
          AND p.timestamp <= ?
        ORDER BY p.timestamp;
    """
    df = pd.read_sql_query(sql, conn, params=(symbol, start_ts, end_ts))
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def get_avg_daily_volume(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    2. average daily volume per ticker
    """
    sql = """
        WITH daily AS (
            SELECT
                t.symbol,
                DATE(p.timestamp) AS trade_date,
                SUM(p.volume) AS daily_volume
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.ticker_id
            GROUP BY t.symbol, DATE(p.timestamp)
        )
        SELECT
            symbol,
            AVG(daily_volume) AS avg_daily_volume
        FROM daily
        GROUP BY symbol
        ORDER BY symbol;
    """
    return pd.read_sql_query(sql, conn)


def get_top_3_tickers_by_return_full_period(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    3. get top 3 tickers by return over the full period.
    """
    sql = """
        WITH with_symbol AS (
            SELECT
                p.*,
                t.symbol
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.ticker_id
        ),
        first_last AS (
            SELECT
                symbol,
                MIN(timestamp) AS first_ts,
                MAX(timestamp) AS last_ts
            FROM with_symbol
            GROUP BY symbol
        ),
        joined AS (
            SELECT
                fl.symbol,
                w1.open  AS first_open,
                w2.close AS last_close
            FROM first_last fl
            JOIN with_symbol w1
              ON w1.symbol = fl.symbol
             AND w1.timestamp = fl.first_ts
            JOIN with_symbol w2
              ON w2.symbol = fl.symbol
             AND w2.timestamp = fl.last_ts
        )
        SELECT
            symbol,
            first_open,
            last_close,
            (last_close - first_open) / first_open AS return_pct
        FROM joined
        ORDER BY return_pct DESC
        LIMIT 3;
    """
    return pd.read_sql_query(sql, conn)


def get_first_last_trade_price_per_day(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    4. get first and last trade price per day for a ticker
    """
    sql = """
        WITH with_symbol AS (
            SELECT
                p.*,
                t.symbol,
                DATE(p.timestamp) AS trade_date
            FROM prices p
            JOIN tickers t ON p.ticker_id = t.ticker_id
        ),
        ranked AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol, trade_date
                    ORDER BY timestamp ASC
                ) AS rn_open,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol, trade_date
                    ORDER BY timestamp DESC
                ) AS rn_close
            FROM with_symbol
        )
        SELECT
            symbol,
            trade_date,
            MAX(CASE WHEN rn_open  = 1 THEN open  END) AS first_price,
            MAX(CASE WHEN rn_close = 1 THEN close END) AS last_price
        FROM ranked
        GROUP BY symbol, trade_date
        ORDER BY symbol, trade_date;
    """
    return pd.read_sql_query(sql, conn)


# cli-style entrypoint i guess
if __name__ == "__main__":
    prices_df, tickers_df = load_and_validate("market_data_multi.csv", "tickers.csv")
    conn = get_connection("market_data.db")
    init_schema(conn, "schema.sql")
    insert_tickers(conn, tickers_df)
    insert_prices(conn, prices_df)
    conn.close()
