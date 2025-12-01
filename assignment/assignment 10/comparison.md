# SQLite3 vs Parquet – Format Comparison

## File Size

- `market_data.db` (SQLite): ~0.9688 MB

- `market_data/` (Parquet, sum of partitions): ~0.3241 MB


Parquet is smaller in this dataset, which is expected due to columnar storage and compression.

## Query Speed (TSLA slice – ticker + date range)

- SQLite (indexed on `ticker_id, timestamp`): ~0.001385 seconds

- Parquet (partitioned by `symbol` + timestamp filter in pandas): ~0.002739 seconds


For this small time-range query, SQLite is slightly faster, likely due to its B-tree index on `(ticker_id, timestamp)`.

## Ease of Integration and Use Cases

### SQLite3

- **Strengths:**

  - ACID-compliant, supports transactions and concurrent readers.

  - SQL interface is convenient for ad-hoc queries and joins (e.g., prices ↔ tickers ↔ news).

  - Single `.db` file is easy to ship with a small trading tool.

- **Typical uses in trading systems:**

  - Storing orders, trades, and configuration for a small/medium-sized trading bot.

  - Lightweight research databases where you frequently join multiple tables.

  - Prototyping execution logic or backtests that rely heavily on SQL-style filtering.



### Parquet

- **Strengths:**

  - Columnar + compressed, so large historical datasets are space-efficient.

  - Integrates naturally with pandas / PyArrow / Spark for vectorized analytics.

  - Partitioning by `symbol` (or date) lets you read only the subset you need.

- **Typical uses in trading systems:**

  - Research and backtesting on large universes and long histories.

  - Factor construction (cross-sectional signals, rolling vol, momentum, etc.).

  - Storing append-only historical data that is rarely updated in place.



## When to Use Which in This Context

- **Backtesting:**

  - Parquet is usually better when you load years of data for many tickers at once; you can read only the needed columns (e.g., `close`) and run vectorized operations.

  - SQLite can work well if you pre-aggregate into daily bars or build helper tables and then query with SQL.

- **Live Trading:**

  - SQLite is a more natural fit for recording live trades, positions, and small snapshots of market data where you need transactional guarantees.

  - Parquet is not ideal for frequent in-place updates; it’s better as an archival / historical store.

- **Research / Analytics:**

  - Parquet integrates seamlessly with Python data science workflows; computing rolling 5-day volatility in pandas over Parquet data is straightforward.

  - SQLite is nice when you want to express more complex filtering, grouping, or joining logic in SQL, or when collaborating with people who are comfortable with SQL but not Python.
