from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd


class SQLiteMarketDB:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_schema(self, schema_sql_path: str | Path) -> None:
        schema = Path(schema_sql_path).read_text(encoding="utf-8")
        with self.connect() as conn:
            conn.executescript(schema)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker_ts ON prices(ticker_id, timestamp);")

    def insert_tickers(self, tickers_df: pd.DataFrame) -> None:
        cols = [c for c in ["ticker_id", "symbol", "name", "exchange"] if c in tickers_df.columns]
        rows = tickers_df[cols].itertuples(index=False, name=None)
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT OR REPLACE INTO tickers ({','.join(cols)}) VALUES ({placeholders});"
        with self.connect() as conn:
            conn.executemany(sql, rows)

    def insert_prices(self, market_df: pd.DataFrame, tickers_df: pd.DataFrame, chunk_size: int = 50_000) -> None:
        sym_to_id = tickers_df[["symbol", "ticker_id"]].copy()
        sym_to_id["symbol"] = sym_to_id["symbol"].astype(str).str.upper()
        df = market_df.merge(sym_to_id, left_on="ticker", right_on="symbol", how="inner")
        if len(df) != len(market_df):
            raise ValueError("ticker mapping failed for some rows")

        out = df[["timestamp", "ticker_id", "open", "high", "low", "close", "volume"]].copy()
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

        sql = """
            INSERT INTO prices (timestamp, ticker_id, open, high, low, close, volume)
            VALUES (?,?,?,?,?,?,?);
        """

        rows = out.itertuples(index=False, name=None)
        with self.connect() as conn:
            buf = []
            for r in rows:
                buf.append(r)
                if len(buf) >= chunk_size:
                    conn.executemany(sql, buf)
                    buf.clear()
            if buf:
                conn.executemany(sql, buf)

    def _date_range_to_bounds(self, start_date: str, end_date: str) -> tuple[str, str]:
        start = pd.to_datetime(start_date).strftime("%Y-%m-%d 00:00:00")
        end_excl = (pd.to_datetime(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
        return start, end_excl

    def get_ticker_range(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        start, end_excl = self._date_range_to_bounds(start_date, end_date)
        q = """
            SELECT p.timestamp, t.symbol AS ticker, p.open, p.high, p.low, p.close, p.volume
            FROM prices p
            JOIN tickers t ON t.ticker_id = p.ticker_id
            WHERE t.symbol = ? AND p.timestamp >= ? AND p.timestamp < ?
            ORDER BY p.timestamp;
        """
        with self.connect() as conn:
            df = pd.read_sql_query(q, conn, params=[symbol.upper(), start, end_excl])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def avg_daily_volume(self) -> pd.DataFrame:
        q = """
            WITH daily AS (
              SELECT ticker_id, date(timestamp) AS day, SUM(volume) AS daily_volume
              FROM prices
              GROUP BY ticker_id, day
            )
            SELECT t.symbol, AVG(daily_volume) AS avg_daily_volume
            FROM daily d
            JOIN tickers t ON t.ticker_id = d.ticker_id
            GROUP BY t.symbol
            ORDER BY t.symbol;
        """
        with self.connect() as conn:
            return pd.read_sql_query(q, conn)

    def top_returns(self, limit: int = 3) -> pd.DataFrame:
        q = f"""
            WITH bounds AS (
              SELECT ticker_id, MIN(timestamp) AS first_ts, MAX(timestamp) AS last_ts
              FROM prices
              GROUP BY ticker_id
            ),
            fl AS (
              SELECT b.ticker_id,
                     (SELECT close FROM prices p WHERE p.ticker_id=b.ticker_id AND p.timestamp=b.first_ts) AS first_close,
                     (SELECT close FROM prices p WHERE p.ticker_id=b.ticker_id AND p.timestamp=b.last_ts) AS last_close
              FROM bounds b
            )
            SELECT t.symbol, fl.first_close, fl.last_close, (fl.last_close / fl.first_close - 1.0) AS return
            FROM fl
            JOIN tickers t ON t.ticker_id = fl.ticker_id
            ORDER BY return DESC
            LIMIT {int(limit)};
        """
        with self.connect() as conn:
            return pd.read_sql_query(q, conn)

    def first_last_trade_price_per_day(self) -> pd.DataFrame:
        q = """
            WITH bounds AS (
              SELECT ticker_id, date(timestamp) AS day,
                     MIN(timestamp) AS first_ts,
                     MAX(timestamp) AS last_ts
              FROM prices
              GROUP BY ticker_id, day
            )
            SELECT t.symbol, b.day,
                   (SELECT close FROM prices p WHERE p.ticker_id=b.ticker_id AND p.timestamp=b.first_ts) AS first_price,
                   (SELECT close FROM prices p WHERE p.ticker_id=b.ticker_id AND p.timestamp=b.last_ts) AS last_price
            FROM bounds b
            JOIN tickers t ON t.ticker_id = b.ticker_id
            ORDER BY t.symbol, b.day;
        """
        with self.connect() as conn:
            return pd.read_sql_query(q, conn)


def sqlite_file_size_bytes(db_path: str | Path) -> int:
    p = Path(db_path)
    return p.stat().st_size if p.exists() else 0
