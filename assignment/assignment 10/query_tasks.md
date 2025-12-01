# Query Tasks

## SQLite3

### 1. Retrieve all data for TSLA between 2025-11-17 and 2025-11-18

**SQL:**

```sql
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
```

**Sample output (first 5 rows):
**
```text
          timestamp symbol   open   high    low  close  volume
2025-11-17 09:30:00   TSLA 268.31 268.51 267.95 268.07    1609
2025-11-17 09:31:00   TSLA 268.94 269.11 268.28 269.04    4809
2025-11-17 09:32:00   TSLA 267.70 267.94 267.69 267.92    1997
2025-11-17 09:33:00   TSLA 268.45 268.64 268.00 268.56    3461
2025-11-17 09:34:00   TSLA 269.01 269.57 268.21 269.23    4003
```

### 2. Calculate average daily volume per ticker

**SQL:**

```sql
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
```

**Sample output (first 5 rows):
**
```text
symbol  avg_daily_volume
  AAPL         1082222.6
  AMZN         1076588.8
  GOOG         1071402.8
  MSFT         1050441.4
  TSLA         1085973.0
```

### 3. Identify the top 3 tickers by return over the full period

**SQL:**

```sql
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
```

**Output:**

```text
symbol  first_open  last_close  return_pct
  MSFT      184.21      245.70    0.333804
  AAPL      271.45      334.57    0.232529
  GOOG      139.29      153.90    0.104889
```

### 4. Find the first and last trade price for each ticker per day

**SQL:**

```sql
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
```

**Sample output (first 5 rows):
**
```text
symbol trade_date  first_price  last_price
  AAPL 2025-11-17       271.45      287.68
  AAPL 2025-11-18       287.95      289.52
  AAPL 2025-11-19       288.69      295.87
  AAPL 2025-11-20       296.51      319.43
  AAPL 2025-11-21       319.44      334.57
```

## Parquet

### 1. Load all data for AAPL and compute 5-minute rolling average of close price

**Python:**

```python
from parquet_storage import rolling_5min_close_for_aapl

df = rolling_5min_close_for_aapl("market_data")
print(df[["timestamp", "symbol", "close", "rolling_5min_close"]].head())
```

**Sample output (first 5 rows):
**
```text
          timestamp symbol  close  rolling_5min_close
2025-11-17 09:30:00   AAPL 270.88          270.880000
2025-11-17 09:31:00   AAPL 269.24          270.060000
2025-11-17 09:32:00   AAPL 270.86          270.326667
2025-11-17 09:33:00   AAPL 269.28          270.065000
2025-11-17 09:34:00   AAPL 269.32          269.916000
```

### 2. Compute 5-day rolling volatility (std dev) of returns for each ticker

**Python:**

```python
from parquet_storage import rolling_5day_vol_perticker

vol_df = rolling_5day_vol_perticker("market_data")
print(vol_df.head())
```

**Sample output (first 5 rows):
**
```text
symbol       date      ret  rolling_5d_vol
  AAPL 2025-11-17      NaN             NaN
  AAPL 2025-11-18 0.006396             NaN
  AAPL 2025-11-19 0.021933             NaN
  AAPL 2025-11-20 0.079630             NaN
  AAPL 2025-11-21 0.047397             NaN
```

### 3. Compare query time and file size with SQLite3 for Task 1 (TSLA slice)

**Python:**

```python
from sqlite_storage import get_connection
from parquet_storage import compare_sqlite_vs_parquet_task1

conn = get_connection("market_data.db")
metrics = compare_sqlite_vs_parquet_task1(conn, "market_data")
conn.close()

print(metrics)
```

**Measured metrics:**

```text
{'sqlite_time_sec': 0.0014136835699900985, 'parquet_time_sec': 0.0032855749828740954, 'sqlite_bytes': 1015808, 'parquet_bytes': 339842}
```
