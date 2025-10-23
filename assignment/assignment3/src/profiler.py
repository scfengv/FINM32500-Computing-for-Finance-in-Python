import timeit
import random
import matplotlib.pyplot as plt
from memory_profiler import memory_usage
from datetime import datetime
from models import MarketDataPoint
from strategies import NaiveMovingAverageStrategy, WindowedMovingAverageStrategy, OptimizedNaiveMovingAverageStrategy


def generate_data(n: int):
    return [
        MarketDataPoint(
            timestamp=datetime.now(),
            symbol="AAPL",
            price=random.uniform(150, 160)
        )
        for _ in range(n)
    ]


def benchmark_time(strategy_class, data):
    strat = strategy_class()
    start = timeit.default_timer()
    for tick in data:
        strat.generate_signals(tick)
    return timeit.default_timer() - start


def benchmark_memory(strategy_class, data):
    def run_strategy():
        strat = strategy_class()
        for tick in data:
            strat.generate_signals(tick)
    mem_usage = memory_usage((run_strategy,), max_iterations=1, interval=0.1)
    return max(mem_usage) - min(mem_usage)


if __name__ == "__main__":
    input_sizes = [1_000, 10_000, 100_000]
    runtime_results = {"Naive": [], "Windowed": [], "OptimizedNaive": []}
    memory_results = {"Naive": [], "Windowed": [], "OptimizedNaive": []}

    for n in input_sizes:
        data = generate_data(n)

        naive_time = benchmark_time(NaiveMovingAverageStrategy, data)
        window_time = benchmark_time(WindowedMovingAverageStrategy, data)
        naive_mem = benchmark_memory(NaiveMovingAverageStrategy, data)
        window_mem = benchmark_memory(WindowedMovingAverageStrategy, data)
        optimizednaive_time = benchmark_time(OptimizedNaiveMovingAverageStrategy, data)
        optimizednaive_mem = benchmark_memory(OptimizedNaiveMovingAverageStrategy, data)

        runtime_results["Naive"].append(naive_time)
        runtime_results["Windowed"].append(window_time)
        memory_results["Naive"].append(naive_mem)
        memory_results["Windowed"].append(window_mem)

        runtime_results["OptimizedNaive"].append(optimizednaive_time)
        memory_results["OptimizedNaive"].append(optimizednaive_mem)

        print(f"\n--- {n} ticks ---")
        print(f"Naive: {naive_time:.4f}s, {naive_mem:.2f} MB")
        print(f"Windowed: {window_time:.4f}s, {window_mem:.2f} MB")
        print(f"Optimized: {optimizednaive_time:.4f}s, {optimizednaive_mem:.2f} MB")

    # Runtime plot
    plt.figure(figsize=(8, 4))
    plt.plot(input_sizes, runtime_results["Naive"], label="Naive (O(n))")
    plt.plot(input_sizes, runtime_results["Windowed"], label="Windowed (O(1))")
    plt.plot(input_sizes, runtime_results["OptimizedNaive"], label="OptimizedNaive")
    plt.title("Runtime vs Input Size")
    plt.xlabel("Number of Ticks")
    plt.ylabel("Runtime (s)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Memory plot
    plt.figure(figsize=(8, 4))
    plt.plot(input_sizes, memory_results["Naive"], label="Naive (O(n))")
    plt.plot(input_sizes, memory_results["Windowed"], label="Windowed (O(k))")
    plt.plot(input_sizes, memory_results["OptimizedNaive"], label="OptimizedNaive")
    plt.title("Memory Usage vs Input Size")
    plt.xlabel("Number of Ticks")
    plt.ylabel("Memory (MB)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
