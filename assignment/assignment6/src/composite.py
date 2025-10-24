# composite.py
import json

from abc import ABC, abstractmethod

def load_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data

class PortfolioComponent:
    @abstractmethod
    def get_value(self):
        pass
    
    @abstractmethod
    def get_position(self):
        pass

class Position(PortfolioComponent):
    def __init__(self, symbol, quantity, price) -> None:
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
    
    def get_value(self) -> float:
        return self.quantity * self.price
    
    def get_positions(self) -> list:
        return [self]
    
    def __repr__(self) -> str:
        return f"Position({self.symbol}, qty={self.quantity}, price=${self.price:.2f})"

class PortfolioGroup(PortfolioComponent):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.children = list()
    
    def add(self, component: PortfolioComponent):
        self.children.append(component) # position or sub_portfolio
    
    def get_value(self):
        total = 0
        for child in self.children:
            total += child.get_value()
        
        return total

    def get_positions(self) -> list:
        all_positions = list()
        for child in self.children:
            all_positions.append(child.get_positions())
        
        return all_positions
    
    def __repr__(self):
        return f"PortfolioGroup({self.name}, value=${self.get_value():.2f})"
    
if __name__ == "__main__":
    data = load_json("../data/portfolio_structure.json")
    
    # main portfolio
    name = data.get("name")
    main_portfolio = PortfolioGroup(name)
    for port in data["positions"]:
        main_portfolio.add(
            Position(
                symbol = port["symbol"],
                quantity = port["quantity"],
                price = port["price"]
            )
        )
    
    # Sub_portfolio
    for sub in data.get("sub_portfolios"):
        sub_data = sub
        sub_name = sub_data.get("name")
        sub_portfolio = PortfolioGroup(sub_name)
        for sub_port in sub_data["positions"]:
            sub_portfolio.add(
                Position(
                    symbol = sub_port["symbol"],
                    quantity = sub_port["quantity"],
                    price = sub_port["price"]
                )
            )
            
    main_portfolio.add(sub_portfolio)
    
    # Demonstrate uniform interface
    print("=== Total Value (Recursive) ===")
    print(f"Main Portfolio: ${main_portfolio.get_value():.2f}")
    print(f"Index Holdings: ${sub_portfolio.get_value():.2f}")
    
    print("\n=== All Positions (Flattened) ===")
    for pos in main_portfolio.get_positions():
        print(f"  {pos}")
    
    print("\n=== Tree Structure ===")
    print(main_portfolio)
    for child in main_portfolio.children:
        print(f"  └─ {child}")
        if isinstance(child, PortfolioGroup):
            for grandchild in child.children:
                print(f"      └─ {grandchild}")