# builder.py
import json

def load_json(path):
    with open(path, "r") as f:
        config_data = json.load(f)
    return config_data

class Portfolio:
    def __init__(self, name, owner, positions, sub_portfolios) -> None:
        self.name = name
        self.owner = owner
        self.positions = positions
        self.sub_portfolios = sub_portfolios
    
    def display(self, indent=0):
        """Display portfolio structure with indentation."""
        prefix = "  " * indent
        print(f"{prefix}Portfolio: {self.name}")
        print(f"{prefix}Owner: {self.owner}")
        print(f"{prefix}Positions:")
        for pos in self.positions:
            print(f"{prefix}  - {pos}")
        if self.sub_portfolios:
            print(f"{prefix}Sub-Portfolios:")
            for sub in self.sub_portfolios:
                sub.display(indent + 1)

class PortfolioBuilder:
    def __init__(self) -> None:
        self._name = None
        self._owner = None
        self._positions = list()
        self._sub_portfolios = list() # hold Portfolio object
        
    def set_name(self, name):
        self._name = name
        return self
    
    def set_owner(self, owner):
        self._owner = owner
        return self
    
    def add_position(self, symbol, quantity, price):
        self._positions.append({
            "symbol": symbol,
            "quantity": quantity,
            "price": price
        })
        return self
    
    def add_subportfolio(self, builder):
        self._sub_portfolios.append(builder.build())
        return self
    
    def build(self):
        return Portfolio(
            name = self._name,
            owner = self._owner,
            positions = self._positions,
            sub_portfolios = self._sub_portfolios
        )

def main(data: dict) -> Portfolio:
    builder = PortfolioBuilder()
    builder.set_name(data.get("name"))
    builder.set_owner(data.get("owner"))
    
    # position
    for pos in data.get("positions", []):
        builder.add_position(
            pos.get("symbol"),
            pos.get("quantity"),
            pos.get("price")
        )
    
    # sub-portfolio
    for sub_port_data in data.get("sub_portfolios", []):
        sub_port = main(sub_port_data)
        
        sub_builder = PortfolioBuilder()
        sub_builder.set_name(sub_port.name)
        sub_builder.set_owner(sub_port.owner)
        sub_builder._positions = sub_port.positions
        sub_builder._sub_portfolios = sub_port.sub_portfolios

        builder.add_subportfolio(sub_builder)
    
    return builder.build()

if __name__ == "__main__":
    data = load_json("data/portfolio_structure.json")
    portfolio = main(data)
    portfolio.display()
    