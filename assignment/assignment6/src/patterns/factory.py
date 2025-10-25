# factory.py
import pandas as pd

class Stock:
    def __init__(self, data: dict):
        self.symbol = data.get("symbol")
        self.type = data.get("type")
        self.price = data.get("price")
        self.sector = data.get("sector")
        self.issuer = data.get("issuer")

class Bond:
    def __init__(self, data: dict):
        self.symbol = data.get("symbol")
        self.type = data.get("type")
        self.price = data.get("price")
        self.sector = data.get("sector")
        self.issuer = data.get("issuer")
        self.maturity = data.get("maturity")

class ETF:
    def __init__(self, data: dict):
        self.symbol = data.get("symbol")
        self.type = data.get("type")
        self.price = data.get("price")
        self.sector = data.get("sector")
        self.issuer = data.get("issuer")

class InstrumentFactory:
    @staticmethod
    def create_instrument(data: dict):
        instrument_type = data.get("type")
        if instrument_type == "Stock":
            return Stock(data)
        elif instrument_type == "Bond":
            return Bond(data)
        elif instrument_type == "ETF":
            return ETF(data)
        else:
            raise ValueError(f"Unknown instrument type: {instrument_type}")

if __name__ == "__main__":
    data = pd.read_csv("../data/instruments.csv")
    dataList = data.to_dict(orient = "records")
    instruments = [InstrumentFactory.create_instrument(item) for item in dataList]
    print([instrument.symbol for instrument in instruments])
    
    