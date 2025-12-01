# SQLite3 vs Parquet (Notes)

## SQLite3
- Good for predicates + joins + small/medium datasets
- ACID transactions; easy incremental appends

## Parquet
- Good for analytics scans and column pruning
- Fits data-lake style workflows; cheap storage + fast batch reads

## Trading use cases
- Backtesting/research: Parquet (batch analytics, large history)
- Apps/services, query APIs: SQLite3 (simple relational querying)
