import sqlite3
import pandas as pd

# Tests from chatgpt btw, credit where credit is due
DB_PATH = "market_data.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

# Any prices whose ticker_id has no matching ticker?
orphans = conn.execute("""
    SELECT COUNT(*) 
    FROM prices p
    LEFT JOIN tickers t ON p.ticker_id = t.ticker_id
    WHERE t.ticker_id IS NULL;
""").fetchone()[0]

print("Orphan prices (should be 0):", orphans)

# How many distinct symbols in prices vs tickers?
price_syms = conn.execute("""
    SELECT COUNT(DISTINCT t.symbol)
    FROM prices p
    JOIN tickers t ON p.ticker_id = t.ticker_id;
""").fetchone()[0]

ticker_syms = conn.execute("SELECT COUNT(DISTINCT symbol) FROM tickers;").fetchone()[0]

print("Distinct symbols in prices:", price_syms)
print("Distinct symbols in tickers:", ticker_syms)

conn.close()
