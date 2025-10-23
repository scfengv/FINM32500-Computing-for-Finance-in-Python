# HW1: CSV-Based Algorithmic Trading Backtester

## Authors
Nicholas Kebo

## Repo Structure
```
HW1/
├── src/
│   ├── data_generator.py       # Data generator provided on Canvas
│   ├── data_loader.py          # Contains load_market_data function
│   ├── models.py               # Dataclasses, Order, exceptions
│   ├── strategies.py           # MR and Momentum strategies
│   ├── engine.py               # Order execution engine
│   ├── reporting.py            # Computes performance metrics, functions for plots
│   └── main.py                 # Data loading, strategy execution, and reporting
├── unit_tests.ipynb            # Unit tests
├── performance.ipynb           # Performance report
└── README.md                    
```

## Setup Instructions
Generate market data with:
```
python -m src.data_generator
```

Ensure pandas and matplotlib are installed:
```
pip install pandas matplotlib
```

If having issues with pulling `market_data.csv`, manually set `filename` to local path in `load_market_data` functions.

Run `unit_tests.ipynb` to see unit test. 

Run `main.py` to see backtesting. 

Run `performance.ipynb` to regenerate metrics and plots.
