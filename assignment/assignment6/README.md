# Design Patterns in Financial Software Architecture
## Repo Layout
```
assignment/assignment6/
├─ src/
│  ├─ patterns/
│  │  ├─ factory.py            
│  │  ├─ singleton.py          
│  │  ├─ builder.py            
│  │  ├─ decorator.py          
│  │  ├─ strategy.py           
│  │  └─ command.py            
│  │  └─ observer.py           
│  ├─ composite.py             
│  ├─ data_loader.py           
│  ├─ analytics.py             
│  ├─ reporting.py             
│  └─ main.py                  
│
├─ data/
│  ├─ config.json
│  ├─ external_data_yahoo.json
│  ├─ external_data_bloomberg.xml
│  ├─ instruments.csv
│  ├─ market_data.csv
│  ├─ portfolio_structure.json
│  └─ strategy_params.json
│
├─ tests/
│  ├─ factory_test.py                  
│  ├─ singleton_test.py                
│  ├─ decorator_test.py                
│  ├─ strategy_test.py                 
│  └─ observer_command_test.py         
│
├─ design_report.md
└─ README.md
```

## Run Quickly

```bash
# from assignment/assignment6
python -m src.main
