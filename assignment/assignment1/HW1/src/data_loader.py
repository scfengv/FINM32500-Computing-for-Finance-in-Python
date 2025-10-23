# src/data_loader.py
import csv
import datetime
from models import MarketDataPoint

def load_market_data(filename):
    """
    Reads market_data.csv (columns: timestamp, symbol, price) using the built-in csv module,
    collecting rows into a list.
    """
    mkt_data =[]  # mkt_data is a list of MarketDataPoint instances (i.e., this is the buffer)
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            t = datetime.datetime.fromisoformat(row['timestamp'])
            sym = row['symbol']
            p = float(row['price'])
            mkt_data.append(MarketDataPoint(timestamp=t, symbol=sym, price=p))
    return mkt_data
