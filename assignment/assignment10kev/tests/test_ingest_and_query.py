from __future__ import annotations

from pathlib import Path
import pytest
import pandas as pd

from assignment10kev.data_loader import Paths, load_and_validate
from sqlite_storage import SQLiteMarketDB
from parquet_storage import write_partitioned_parquet, read_ticker_range_parquet

try:
    import pyarrow  # noqa: F401
    HAS_PYARROW = True
except Exception:
    HAS_PYARROW = False


@pytest.fixture()
def root(tmp_path: Path):
    return tmp_path


@pytest.fixture()
def sample_data():
    here = Path(__file__).resolve().parents[1]
    market_csv = here / "data" / "market_data_multi.csv"
    tickers_csv = here / "data" / "tickers.csv"
    schema_sql = here / "data" / "schema.sql"
    market, tickers = load_and_validate(Paths(market_csv=market_csv, tickers_csv=tickers_csv))
    return market, tickers, schema_sql


def test_ingest_valid(sample_data):
    market, tickers, _ = sample_data
    assert set(tickers["symbol"]) <= set(market["ticker"])
    assert market.isna().sum().sum() == 0


def test_sqlite_roundtrip(sample_data, tmp_path: Path):
    market, tickers, schema_sql = sample_data
    db_path = tmp_path / "market_data.db"

    db = SQLiteMarketDB(db_path)
    db.create_schema(schema_sql)
    db.insert_tickers(tickers)
    db.insert_prices(market, tickers)

    got = db.get_ticker_range("TSLA", "2025-11-17", "2025-11-18")
    assert len(got) == len(market[(market["ticker"] == "TSLA") & (market["timestamp"].dt.date.isin([pd.to_datetime("2025-11-17").date(), pd.to_datetime("2025-11-18").date()]))])

    avg_vol = db.avg_daily_volume()
    assert {"symbol", "avg_daily_volume"} <= set(avg_vol.columns)

    top3 = db.top_returns(3)
    assert len(top3) == 3
    assert "return" in top3.columns

    fl = db.first_last_trade_price_per_day()
    assert {"symbol", "day", "first_price", "last_price"} <= set(fl.columns)


@pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")
def test_parquet_partition_query(sample_data, tmp_path: Path):
    market, _, _ = sample_data
    out_dir = tmp_path / "market_data"
    write_partitioned_parquet(market, out_dir, overwrite=True)

    got = read_ticker_range_parquet(out_dir, "TSLA", "2025-11-17", "2025-11-18")
    want = market[(market["ticker"] == "TSLA") & (market["timestamp"] >= pd.to_datetime("2025-11-17")) & (market["timestamp"] < pd.to_datetime("2025-11-19"))]
    assert len(got) == len(want)
