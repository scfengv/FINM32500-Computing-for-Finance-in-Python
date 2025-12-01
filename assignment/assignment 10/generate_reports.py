"""
Generates tasks required for query_tasks.md
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from sqlite_storage import (
    get_connection,
    get_ticker_data_range,
    get_avg_daily_volume,
    get_top_3_tickers_by_return_full_period,
    get_first_last_trade_price_per_day,
)
from parquet_storage import (
    rolling_5min_close_for_aapl,
    rolling_5day_vol_per_ticker,
    compare_sqlite_vs_parquet_task1,
)


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "market_data.db"
PARQUET_ROOT = ROOT / "market_data"
QUERY_TASKS_MD = ROOT / "query_tasks.md"


def df_to_code_block(df: pd.DataFrame, n: int = 5) -> str:
    """
    Convert the first n rows of a DataFrame into a fenced code block
    using plain text (no extra deps).
    """
    if df.empty:
        body = "<no rows>"
    else:
        body = df.head(n).to_string(index=False)
    return f"```text\n{body}\n```"


# ----------------- Main data collection ----------------- #

def run_sqlite_tasks():
    """Run all required SQLite queries and return their DataFrames."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"{DB_PATH} does not exist. Build the DB first.")

    conn = get_connection(DB_PATH)

    tsla = get_ticker_data_range(
        conn,
        symbol="TSLA",
        start_ts="2025-11-17 00:00:00",
        end_ts="2025-11-18 23:59:59",
    )
    avg_vol = get_avg_daily_volume(conn)
    top3 = get_top_3_tickers_by_return_full_period(conn)
    first_last = get_first_last_trade_price_per_day(conn)

    conn.close()
    return tsla, avg_vol, top3, first_last


def run_parquet_tasks():
    """Run all required Parquet queries and return their DataFrames + metrics."""
    if not PARQUET_ROOT.exists():
        raise FileNotFoundError(f"{PARQUET_ROOT} does not exist. Build Parquet first.")

    aapl_5 = rolling_5min_close_for_aapl(PARQUET_ROOT)
    vol_df = rolling_5day_vol_per_ticker(PARQUET_ROOT)

    conn = get_connection(DB_PATH)
    metrics = compare_sqlite_vs_parquet_task1(conn, PARQUET_ROOT)
    conn.close()

    return aapl_5, vol_df, metrics


def generate_query_tasks_md(
    tsla: pd.DataFrame,
    avg_vol: pd.DataFrame,
    top3: pd.DataFrame,
    first_last: pd.DataFrame,
    aapl_5: pd.DataFrame,
    vol_df: pd.DataFrame,
    metrics: dict,
) -> str:
    """Build the full contents of query_tasks.md as a string."""

    sql_tsla = """\
SELECT
    p.timestamp,
    t.symbol,
    p.open, p.high, p.low, p.close, p.volume
FROM prices p
JOIN tickers t ON p.ticker_id = t.ticker_id
WHERE t.symbol = 'TSLA'
  AND p.timestamp >= '2025-11-17 00:00:00'
  AND p.timestamp <= '2025-11-18 23:59:59'
ORDER BY p.timestamp;
"""

    sql_avg_vol = """\
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

    sql_top3 = """\
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

    sql_first_last = """\
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

    # Python snippets for Parquet tasks
    py_aapl_5 = """\
from parquet_storage import rolling_5min_close_for_aapl

df = rolling_5min_close_for_aapl("market_data")
print(df[["timestamp", "symbol", "close", "rolling_5min_close"]].head())
"""

    py_vol = """\
from parquet_storage import rolling_5day_vol_perticker

vol_df = rolling_5day_vol_perticker("market_data")
print(vol_df.head())
"""

    py_metrics = """\
from sqlite_storage import get_connection
from parquet_storage import compare_sqlite_vs_parquet_task1

conn = get_connection("market_data.db")
metrics = compare_sqlite_vs_parquet_task1(conn, "market_data")
conn.close()

print(metrics)
"""

    # Build markdown
    md = []

    md.append("# Query Tasks\n")

    # sql stuff
    md.append("## SQLite3\n")

    # 1) TSLA range
    md.append("### 1. Retrieve all data for TSLA between 2025-11-17 and 2025-11-18\n")
    md.append("**SQL:**\n")
    md.append("```sql\n" + sql_tsla + "```\n")
    md.append("**Sample output (first 5 rows):\n**")
    md.append(df_to_code_block(tsla, n=5) + "\n")

    # 2) Avg daily volume
    md.append("### 2. Calculate average daily volume per ticker\n")
    md.append("**SQL:**\n")
    md.append("```sql\n" + sql_avg_vol + "```\n")
    md.append("**Sample output (first 5 rows):\n**")
    md.append(df_to_code_block(avg_vol, n=5) + "\n")

    # 3) Top 3 by return
    md.append("### 3. Identify the top 3 tickers by return over the full period\n")
    md.append("**SQL:**\n")
    md.append("```sql\n" + sql_top3 + "```\n")
    md.append("**Output:**\n")
    md.append(df_to_code_block(top3, n=3) + "\n")

    # 4) First/last trade per day
    md.append("### 4. Find the first and last trade price for each ticker per day\n")
    md.append("**SQL:**\n")
    md.append("```sql\n" + sql_first_last + "```\n")
    md.append("**Sample output (first 5 rows):\n**")
    md.append(df_to_code_block(first_last, n=5) + "\n")

    # parquet stuff
    md.append("## Parquet\n")

    # 1) AAPL rolling 5-min
    md.append("### 1. Load all data for AAPL and compute 5-minute rolling average of close price\n")
    md.append("**Python:**\n")
    md.append("```python\n" + py_aapl_5 + "```\n")
    md.append("**Sample output (first 5 rows):\n**")
    md.append(df_to_code_block(aapl_5[["timestamp", "symbol", "close", "rolling_5min_close"]], n=5) + "\n")

    # 2) 5-day rolling vol
    md.append("### 2. Compute 5-day rolling volatility (std dev) of returns for each ticker\n")
    md.append("**Python:**\n")
    md.append("```python\n" + py_vol + "```\n")
    md.append("**Sample output (first 5 rows):\n**")
    md.append(df_to_code_block(vol_df, n=5) + "\n")

    # 3) Performance comparison
    md.append("### 3. Compare query time and file size with SQLite3 for Task 1 (TSLA slice)\n")
    md.append("**Python:**\n")
    md.append("```python\n" + py_metrics + "```\n")
    md.append("**Measured metrics:**\n")
    md.append("```text\n" + str(metrics) + "\n```\n")

    return "\n".join(md)


# entry

def main():
    # Run queries
    tsla, avg_vol, top3, first_last = run_sqlite_tasks()
    aapl_5, vol_df, metrics = run_parquet_tasks()

    # Build markdown contents
    query_md = generate_query_tasks_md(
        tsla=tsla,
        avg_vol=avg_vol,
        top3=top3,
        first_last=first_last,
        aapl_5=aapl_5,
        vol_df=vol_df,
        metrics=metrics,
    )

    # Write file (overwrite)
    QUERY_TASKS_MD.write_text(query_md, encoding="utf-8")
    print(f"Wrote {QUERY_TASKS_MD}")


if __name__ == "__main__":
    main()
