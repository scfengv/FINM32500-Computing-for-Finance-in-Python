#!/usr/bin/env python3
"""
Demo script to run the complete trading system

This script demonstrates how to run all components:
1. Gateway (market data provider)
2. OrderBook (writes prices to shared memory)
3. Strategy (generates trading signals)

Run this to see the system in action!
"""

import subprocess
import time
import sys
import os

def print_banner(text):
    """Print a nice banner"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def main():
    print_banner("Assignment 8 - Trading System Demo")
    
    print("""
This demo will start three processes:

1. Gateway    - Simulates market data feed (prices + sentiment)
2. OrderBook  - Reads from Gateway, writes prices to shared memory
3. Strategy   - Reads prices from shared memory, generates signals

Each process will run in a separate terminal window.
Press Ctrl+C in any terminal to stop that process.
    """)
    
    input("Press Enter to start the demo...")
    
    # Get the current directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src')
    
    print_banner("Starting Gateway")
    print("Gateway will send prices and sentiment every 0.5 seconds")
    print("Look for the terminal window titled 'Gateway'\n")
    
    # Start gateway in a new terminal
    gateway_cmd = f"cd '{base_dir}' && python src/gateway.py"
    subprocess.Popen([
        'osascript', '-e',
        f'tell app "Terminal" to do script "{gateway_cmd}"'
    ])
    
    time.sleep(2)
    
    print_banner("Starting OrderBook")
    print("OrderBook will read from Gateway and update shared memory")
    print("Look for the terminal window titled 'OrderBook'\n")
    
    # Start orderbook in a new terminal
    orderbook_cmd = f"cd '{base_dir}' && python -c 'from src.orderbook import run_orderbook; run_orderbook()'"
    subprocess.Popen([
        'osascript', '-e',
        f'tell app "Terminal" to do script "{orderbook_cmd}"'
    ])
    
    time.sleep(2)
    
    print_banner("Starting Strategy")
    print("Strategy will generate trading signals based on:")
    print("  - Moving average crossover (price signal)")
    print("  - Sentiment thresholds (news signal)")
    print("  - Only trades when both signals agree")
    print("Look for the terminal window titled 'Strategy'\n")
    
    # Start strategy in a new terminal
    strategy_cmd = f"cd '{base_dir}' && python src/strategy.py AAPL"
    subprocess.Popen([
        'osascript', '-e',
        f'tell app "Terminal" to do script "{strategy_cmd}"'
    ])
    
    print_banner("System Running")
    print("""
All components are now running!

What to watch for:
- Gateway: Sending random prices and sentiment
- OrderBook: Receiving and storing prices in shared memory
- Strategy: 
  * Accumulating price history (needs 20 prices for long MA)
  * Monitoring sentiment
  * Will generate BUY signal when:
    - Short MA > Long MA (upward trend)
    - Sentiment > 60 (bullish)
  * Will generate SELL signal when:
    - Short MA < Long MA (downward trend)
    - Sentiment < 40 (bearish)

Press Ctrl+C in any terminal window to stop that component.
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Please close the terminal windows manually.")
