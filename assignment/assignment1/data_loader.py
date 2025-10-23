import csv
import time
import random
import datetime
from models import MarketDataPoint
    
    
def ReadMarketCSV(filename):
    MarketData = list()
    with open(filename, 'r', newline = '') as f:
        csvReader = csv.reader(f)
        next(csvReader)  # Skip header row
        for row in csvReader:
            timestamp = datetime.datetime.fromisoformat(row[0])
            symbol = row[1]
            price = float(row[2])
            MarketData.append(MarketDataPoint(timestamp, symbol, price))
    return MarketData