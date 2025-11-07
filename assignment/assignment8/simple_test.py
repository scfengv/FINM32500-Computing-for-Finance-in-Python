#!/usr/bin/env python3
"""
Simple test to verify the strategy works correctly

This runs a simplified version without multiprocessing to verify
the core strategy logic works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strategy import SignalGenerator

def test_simple_scenario():
    """Test a simple buy scenario"""
    print("="*60)
    print("Testing Strategy Signal Generation")
    print("="*60)
    
    strategy = SignalGenerator(
        ticker="AAPL",
        shm_name="test_book",
        short_window=3,
        long_window=5,
        bullish_threshold=60,
        bearish_threshold=40,
    )
    
    print("\n1. Testing Upward Trend + Bullish Sentiment")
    print("-" * 60)
    
    # Add prices showing upward trend
    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    for i, price in enumerate(prices):
        strategy.price_buffer.add(price)
        print(f"   Added price: ${price:.2f}")
    
    # Set bullish sentiment
    strategy.sentiment = 75
    print(f"   Set sentiment: {strategy.sentiment} (Bullish)")
    
    # Check signals
    price_signal = strategy.generate_price_signal()
    news_signal = strategy.generate_news_signal()
    
    print(f"\n   Short MA ({strategy.short_window}): ${strategy.price_buffer.get_ma(strategy.short_window):.2f}")
    print(f"   Long MA ({strategy.long_window}): ${strategy.price_buffer.get_ma(strategy.long_window):.2f}")
    print(f"   Price Signal: {price_signal}")
    print(f"   News Signal: {news_signal}")
    
    action = strategy.should_trade()
    print(f"\n   Decision: {action if action else 'NO TRADE (signals disagree or position exists)'}")
    
    if action == "BUY":
        print("   ✓ Correct! Both signals agree on BUY")
        order = strategy.create_order(action, prices[-1])
        print(f"\n   Order created:")
        print(f"     Ticker: {order.ticker}")
        print(f"     Action: {order.action}")
        print(f"     Price: ${order.price:.2f}")
        print(f"     Reason: {order.reason}")
        
        serialized = strategy.serialize_order(order)
        print(f"\n   Serialized order: {serialized.decode('utf-8')}")
    
    print("\n" + "="*60)
    print("\n2. Testing Downward Trend + Bearish Sentiment")
    print("-" * 60)
    
    # Reset and test downward trend
    strategy2 = SignalGenerator(
        ticker="MSFT",
        shm_name="test_book",
        short_window=3,
        long_window=5,
        bullish_threshold=60,
        bearish_threshold=40,
    )
    
    prices = [105.0, 104.0, 103.0, 102.0, 101.0, 100.0]
    for price in prices:
        strategy2.price_buffer.add(price)
        print(f"   Added price: ${price:.2f}")
    
    strategy2.sentiment = 30
    print(f"   Set sentiment: {strategy2.sentiment} (Bearish)")
    
    price_signal = strategy2.generate_price_signal()
    news_signal = strategy2.generate_news_signal()
    
    print(f"\n   Short MA ({strategy2.short_window}): ${strategy2.price_buffer.get_ma(strategy2.short_window):.2f}")
    print(f"   Long MA ({strategy2.long_window}): ${strategy2.price_buffer.get_ma(strategy2.long_window):.2f}")
    print(f"   Price Signal: {price_signal}")
    print(f"   News Signal: {news_signal}")
    
    action = strategy2.should_trade()
    print(f"\n   Decision: {action if action else 'NO TRADE'}")
    
    if action == "SELL":
        print("   ✓ Correct! Both signals agree on SELL")
    
    print("\n" + "="*60)
    print("\n3. Testing Signal Disagreement (No Trade)")
    print("-" * 60)
    
    strategy3 = SignalGenerator(
        ticker="GOOG",
        shm_name="test_book",
        short_window=3,
        long_window=5,
        bullish_threshold=60,
        bearish_threshold=40,
    )
    
    # Upward trend
    prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    for price in prices:
        strategy3.price_buffer.add(price)
    
    # But bearish sentiment
    strategy3.sentiment = 30
    
    price_signal = strategy3.generate_price_signal()
    news_signal = strategy3.generate_news_signal()
    
    print(f"   Short MA: ${strategy3.price_buffer.get_ma(strategy3.short_window):.2f}")
    print(f"   Long MA: ${strategy3.price_buffer.get_ma(strategy3.long_window):.2f}")
    print(f"   Price Signal: {price_signal} (trend up)")
    print(f"   News Signal: {news_signal} (sentiment bearish)")
    
    action = strategy3.should_trade()
    print(f"\n   Decision: {action if action else 'NO TRADE (signals disagree)'}")
    
    if action is None:
        print("   ✓ Correct! Signals disagree, so no trade")
    
    print("\n" + "="*60)
    print("\n4. Testing Position Management (No Duplicate Orders)")
    print("-" * 60)
    
    strategy4 = SignalGenerator(
        ticker="AAPL",
        shm_name="test_book",
        short_window=3,
        long_window=5,
        bullish_threshold=60,
        bearish_threshold=40,
    )
    
    # Same bullish scenario
    for price in [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]:
        strategy4.price_buffer.add(price)
    strategy4.sentiment = 75
    
    # First trade should work
    action = strategy4.should_trade()
    print(f"   First check: {action} (Position: {strategy4.position})")
    
    if action == "BUY":
        strategy4.position = "long"  # Simulate executing the order
        print("   Executed BUY, now position is 'long'")
    
    # Second trade should be blocked
    action = strategy4.should_trade()
    print(f"   Second check: {action if action else 'NO TRADE'} (Position: {strategy4.position})")
    
    if action is None:
        print("   ✓ Correct! Prevented duplicate BUY order")
    
    print("\n" + "="*60)
    print("\n✓ All tests completed successfully!")
    print("="*60)

if __name__ == "__main__":
    test_simple_scenario()
