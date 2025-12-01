from __future__ import annotations

from pathlib import Path
import pandas as pd

from data_loader import Paths, load_and_validate
from sqlite_storage import SQLiteMarketDB, sqlite_file_size_bytes
from parquet_storage import (
    write_partitioned_parquet,
    read_ticker_range_parquet,
    aapl_5min_rolling_close_avg,
    rolling_5d_volatility_of_daily_returns,
    parquet_dir_size_bytes,
    timed,
)

ROOT = Path(__file__).resolve().parent


def main():
    market_csv = ROOT / "data" / "market_data_multi.csv"
    tickers_csv = ROOT / "data" / "tickers.csv"
    schema_sql = ROOT / "data" / "schema.sql"

    db_path = ROOT / "market_data.db"
    pq_dir = ROOT / "market_data"

    market, tickers = load_and_validate(Paths(market_csv=market_csv, tickers_csv=tickers_csv))

    db = SQLiteMarketDB(db_path)
    db.create_schema(schema_sql)
    db.insert_tickers(tickers)
    db.insert_prices(market, tickers)

    task1 = db.get_ticker_range("TSLA", "2025-11-17", "2025-11-18")
    avg_vol = db.avg_daily_volume()
    top3 = db.top_returns(3)
    first_last = db.first_last_trade_price_per_day()

    try:
        write_partitioned_parquet(market, pq_dir, overwrite=True)
        aapl_roll = aapl_5min_rolling_close_avg(pq_dir)
        vol5d = rolling_5d_volatility_of_daily_returns(market)

        _, t_sql = timed(lambda: db.get_ticker_range("TSLA", "2025-11-17", "2025-11-18"), runs=5)
        _, t_pq = timed(lambda: read_ticker_range_parquet(pq_dir, "TSLA", "2025-11-17", "2025-11-18"), runs=5)

        sz_sql = sqlite_file_size_bytes(db_path)
        sz_pq = parquet_dir_size_bytes(pq_dir)
    except Exception as e:
        aapl_roll = pd.DataFrame()
        vol5d = pd.DataFrame()
        t_sql = t_pq = None
        sz_sql = sqlite_file_size_bytes(db_path)
        sz_pq = 0
        e_msg = str(e)
    else:
        e_msg = ""

    out_md = ROOT / "query_tasks.md"
    out_md.write_text(
        "\n".join(
            [
                "# Query Tasks Results",
                "",
                "## SQLite3",
                f"- Task 1 rows (TSLA 2025-11-17..2025-11-18): {len(task1)}",
                f"- Task 2 rows (avg daily volume): {len(avg_vol)}",
                f"- Task 3 rows (top 3): {len(top3)}",
                f"- Task 4 rows (first/last per day): {len(first_last)}",
                "",
                "## Parquet",
                f"- Task 1 AAPL rolling rows: {len(aapl_roll)}",
                f"- Task 2 5d vol rows: {len(vol5d)}",
                "",
                "## Performance / Size (Task 1)",
                f"- SQLite avg time (s): {t_sql}" if t_sql is not None else "- SQLite avg time (s): n/a",
                f"- Parquet avg time (s): {t_pq}" if t_pq is not None else "- Parquet avg time (s): n/a",
                f"- SQLite size (bytes): {sz_sql}",
                f"- Parquet size (bytes): {sz_pq}",
                (f"- Parquet error: {e_msg}" if e_msg else ""),
                "",
            ]
        ),
        encoding="utf-8",
    )

    (ROOT / "comparison.md").write_text(
        "\n".join(
            [
                "# SQLite3 vs Parquet (Notes)",
                "",
                "## SQLite3",
                "- Good for predicates + joins + small/medium datasets",
                "- ACID transactions; easy incremental appends",
                "",
                "## Parquet",
                "- Good for analytics scans and column pruning",
                "- Fits data-lake style workflows; cheap storage + fast batch reads",
                "",
                "## Trading use cases",
                "- Backtesting/research: Parquet (batch analytics, large history)",
                "- Apps/services, query APIs: SQLite3 (simple relational querying)",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
