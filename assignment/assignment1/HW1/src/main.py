# src/main.py
from data_loader import load_market_data
from strategies import MeanReversionStrategy, MomentumStrategy
from engine import ExecutionEngine
from reporting import performance_reporting

def run_strategy(ticks, strategy, name):
    """
    Helper function for executing each strat individually.
    """
    engine = ExecutionEngine()
    engine.process(ticks, [strategy])
    results = performance_reporting(engine.equity_ts)

    print(f"\n==== {name} ====")
    for key, val in results.items():
        if isinstance(val, (float, int)):  # We'll plot series later using fncs; no need to print here
            print(f"{key}: {val:.4f}")
    return results, engine

def main():
    # Load data
    ticks = load_market_data("market_data.csv")

    # Window for MR is 5, 3 for Momentum; we always trade 10 shares for both
    mr = MeanReversionStrategy(window=5, quantity=10)
    mom = MomentumStrategy(window=3, quantity=10)

    mr_res, mr_eng = run_strategy(ticks, mr, "Mean Reversion (window = 5, trade size = 10)")
    mom_res, mom_eng = run_strategy(ticks, mom, "Momentum (window = 3, trade size = 10)")

    return {'mr': mr_res, 'mom': mom_res}, {'mr': mr_eng, 'mom': mom_eng}
        
if __name__ == "__main__":
    main()
