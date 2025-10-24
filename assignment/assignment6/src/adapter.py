# adapter.py
import json
import xml.etree.ElementTree as ET

from datetime import datetime
from dataclasses import dataclass

def load_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data

def load_xml(path):
    """Load and parse XML file."""
    tree = ET.parse(path)
    root = tree.getroot()
    return root

@dataclass(frozen = True)
class MarketDataPoint:
    timestamp: datetime
    symbol: str
    price: float

class YahooFinanceAdapter:
    def __init__(self, data: dict) -> None:
        self.data = data
    
    def get_data(self, symbol: str) -> MarketDataPoint:
        if self.data.get("ticker") != symbol:
            return None
        
        return MarketDataPoint(
            timestamp = self.data.get("timestamp"),
            symbol = self.data.get("ticker"),
            price = self.data.get("last_price")
        )
        
class BloombergXMLAdapter:
    def __init__(self, data) -> None:
        self.xml_element = data
    
    def get_data(self, symbol: str) -> MarketDataPoint:
        xml_symbol = self.xml_element.find("symbol").text
        
        if xml_symbol != symbol:
            return None
        
        price = float(self.xml_element.find("price").text)
        
        timestamp = self.xml_element.find("timestamp").text
        
        return MarketDataPoint(
            # timestamp = timestamp,
            timestamp = timestamp,
            symbol = symbol,
            price = price
        )

if __name__ == "__main__":
    ticker = "AAPL"
    yahooData = load_json("../data/external_data_yahoo.json")
    yahoooDataPoint = YahooFinanceAdapter(yahooData).get_data(ticker)
    print(f"From Yahoo: {yahoooDataPoint}")
    
    bloombergData = load_xml("../data/external_data_bloomberg.xml")
    bloombergDataPoint = BloombergXMLAdapter(bloombergData).get_data(ticker)
    print(f"From Bloomberg: {bloombergDataPoint}")
    