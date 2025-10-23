# Data Loader
import csv
from pathlib import Path
from datetime import datetime
from models import MarketDataPoint

class MarketDataLoader:
    """
    CSV -> list of MarketDataPoint
    """
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.dataPoints: list[MarketDataPoint] = []
        
    def load(self) -> list[MarketDataPoint]:
        with open(self.filepath, "r", newline = "", encoding = "utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.dataPoints.append(
                    MarketDataPoint(
                        timestamp = datetime.fromisoformat(row["timestamp"]),
                        symbol = row["symbol"],
                        price = float(row["price"]),
                    )
                )
        return self.dataPoints