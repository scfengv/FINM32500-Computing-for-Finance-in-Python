import json
import pandas as pd

from data_loader import load_csv_with_pandas

def load_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data

def output_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

class Portfolio:
    def __init__(self, name, positions, sub_portfolios) -> None:
        self.name = name
        self.total_value = sum(pos["value"] for pos in positions)
        self.aggregate_volatility = sum(pos["volatility"] * pos["value"] for pos in positions) / self.total_value if positions else 0
        self.max_drawdown = min(pos["drawdown"] for pos in positions) if positions else 0
        self.positions = positions
        self.sub_portfolios = sub_portfolios
    

class PortfolioBuilder:
    def __init__(self) -> None:
        self._name = None
        self._positions = list()
        self._sub_portfolios = list() # hold Portfolio object
        
    def set_name(self, name):
        self._name = name
        return self
    
    def add_position(self, symbol, quantity, price, historical_prices):
        self._positions.append({
            "symbol": symbol,
            "value": quantity * price,
            "volatility": historical_prices.pct_change().std(),
            "drawdown": (historical_prices / historical_prices.cummax() - 1).min()
        })
        return self
    
    def add_subportfolio(self, builder):
        self._sub_portfolios.append(builder.build())
        return self
    
    def build(self):
        return Portfolio(
            name = self._name,
            positions = self._positions,
            sub_portfolios = self._sub_portfolios
        )

def main(data: dict, price_data: pd.DataFrame) -> Portfolio:
    builder = PortfolioBuilder()
    builder.set_name(data.get("name"))
    
    # position
    for pos in data.get("positions", []):
        historical_prices = price_data[price_data["symbol"] == pos.get("symbol")]["price"]
        builder.add_position(
            pos.get("symbol"),
            pos.get("quantity"),
            pos.get("price"),
            historical_prices
        )
    
    # sub-portfolio
    for sub_port_data in data.get("sub_portfolios", []):
        sub_port = main(sub_port_data, price_data)
        
        sub_builder = PortfolioBuilder()
        sub_builder.set_name(sub_port.name)
        sub_builder._positions = sub_port.positions
        sub_builder._sub_portfolios = sub_port.sub_portfolios

        builder.add_subportfolio(sub_builder)
    
    return builder.build()


if __name__ == "__main__":
    data = load_json("data/portfolio_structure-1.json")
    price_data = load_csv_with_pandas("data/market_data-1.csv")
    
    portfolio = main(data, price_data)
    sub_port_result = {}
    for sub_port in portfolio.sub_portfolios:
        sub_port_result = {
            "name": sub_port.name,
            "total_value": sub_port.total_value,
            "aggregate_volatility": sub_port.aggregate_volatility,
            "max_drawdown": sub_port.max_drawdown,
            "positions": sub_port.positions
        }

    result = {
        "name": portfolio.name,
        "total_value": portfolio.total_value,
        "aggregate_volatility": portfolio.aggregate_volatility,
        "max_drawdown": portfolio.max_drawdown,
        "positions": portfolio.positions,
        "sub_portfolios": sub_port_result
    }

    output_json("output/portfolio_output-1.json", result)