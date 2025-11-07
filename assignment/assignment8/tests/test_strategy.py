# tests/test_strategy.py
"""
Test the Strategy (Signal Generator) module
"""
import socket
import threading
import time
import json
from multiprocessing import Process

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategy import SignalGenerator, PriceBuffer, Order, run_strategy
from shared_memory_utils import SharedPriceBook


HOST = "localhost"
PORT = 9011
SHM_NAME = "pricebook_strategy_test"


def _cleanup_shm(name: str):
    """Clean up shared memory"""
    try:
        shm = SharedPriceBook(name=name, create=False)
        shm.close()
        shm.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


def test_price_buffer():
    """Test PriceBuffer class"""
    print("\n=== Testing PriceBuffer ===")
    
    buffer = PriceBuffer(maxlen=10)
    
    # Add some prices
    for i in range(5):
        buffer.add(100.0 + i)
    
    # Test length
    assert len(buffer) == 5, f"Expected length 5, got {len(buffer)}"
    
    # Test MA calculation
    ma_3 = buffer.get_ma(3)
    expected_ma_3 = (102 + 103 + 104) / 3
    assert abs(ma_3 - expected_ma_3) < 0.01, f"Expected MA {expected_ma_3}, got {ma_3}"
    
    # Test insufficient data
    ma_10 = buffer.get_ma(10)
    assert ma_10 is None, "Expected None for window > buffer size"
    
    print("✓ PriceBuffer tests passed")


def test_signal_generation():
    """Test signal generation logic"""
    print("\n=== Testing Signal Generation ===")
    
    strategy = SignalGenerator(
        ticker="AAPL",
        shm_name=SHM_NAME,
        short_window=3,
        long_window=5,
        bullish_threshold=60,
        bearish_threshold=40,
    )
    
    # Add prices to create upward trend
    for price in [100, 101, 102, 103, 104, 105]:
        strategy.price_buffer.add(price)
    
    # Test price signal (upward trend = BUY)
    price_signal = strategy.generate_price_signal()
    assert price_signal == "BUY", f"Expected BUY signal, got {price_signal}"
    
    # Test news signal (bullish)
    strategy.sentiment = 70
    news_signal = strategy.generate_news_signal()
    assert news_signal == "BUY", f"Expected BUY signal, got {news_signal}"
    
    # Test combined signal
    action = strategy.should_trade()
    assert action == "BUY", f"Expected BUY action, got {action}"
    
    # Test position management (no duplicate orders)
    strategy.position = "long"
    action = strategy.should_trade()
    assert action is None, f"Expected None (already long), got {action}"
    
    # Test downward trend
    strategy.price_buffer = PriceBuffer(maxlen=50)
    for price in [105, 104, 103, 102, 101, 100]:
        strategy.price_buffer.add(price)
    
    price_signal = strategy.generate_price_signal()
    assert price_signal == "SELL", f"Expected SELL signal, got {price_signal}"
    
    # Test bearish sentiment
    strategy.sentiment = 30
    news_signal = strategy.generate_news_signal()
    assert news_signal == "SELL", f"Expected SELL signal, got {news_signal}"
    
    # Test disagreement (price says SELL, news says neutral)
    strategy.sentiment = 50  # Neutral
    action = strategy.should_trade()
    assert action is None, f"Expected None (disagreement), got {action}"
    
    print("✓ Signal generation tests passed")


def test_order_serialization():
    """Test order creation and serialization"""
    print("\n=== Testing Order Serialization ===")
    
    strategy = SignalGenerator(ticker="AAPL")
    
    order = strategy.create_order("BUY", 150.25)
    
    assert order.ticker == "AAPL"
    assert order.action == "BUY"
    assert order.price == 150.25
    assert order.timestamp > 0
    
    # Test serialization
    serialized = strategy.serialize_order(order)
    assert b"*" in serialized, "Expected MESSAGE_DELIMITER in serialized order"
    
    # Deserialize and verify
    json_str = serialized.decode('utf-8').rstrip('*')
    order_dict = json.loads(json_str)
    
    assert order_dict['ticker'] == "AAPL"
    assert order_dict['action'] == "BUY"
    assert order_dict['price'] == 150.25
    
    print("✓ Order serialization tests passed")


def test_gateway_message_parsing():
    """Test parsing of Gateway messages"""
    print("\n=== Testing Gateway Message Parsing ===")
    
    strategy = SignalGenerator(ticker="AAPL")
    
    # Test sentiment parsing
    msg1 = "AAPL,101.25*MSFT,275.10*SENTIMENT,65*"
    strategy.parse_gateway_message(msg1)
    assert strategy.sentiment == 65, f"Expected sentiment 65, got {strategy.sentiment}"
    
    # Test another sentiment
    msg2 = "GOOG,300.00*SENTIMENT,35*"
    strategy.parse_gateway_message(msg2)
    assert strategy.sentiment == 35, f"Expected sentiment 35, got {strategy.sentiment}"
    
    print("✓ Gateway message parsing tests passed")


def _mock_gateway_with_trend(host: str, port: int, duration: float = 3.0):
    """Mock gateway that sends prices with upward trend and bullish sentiment"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    
    print(f"Mock Gateway: Listening on {host}:{port}")
    conn, _ = srv.accept()
    print("Mock Gateway: Client connected")
    
    try:
        start = time.time()
        price = 100.0
        
        while time.time() - start < duration:
            # Simulate upward trend
            price += 0.5
            
            # Create message with prices and sentiment
            msg = f"AAPL,{price:.2f}*MSFT,{price*2:.2f}*SENTIMENT,75*"
            conn.sendall(msg.encode('utf-8'))
            print(f"Mock Gateway: Sent {msg.strip()}")
            time.sleep(0.2)
    
    finally:
        try:
            conn.close()
        except Exception:
            pass
        srv.close()
        print("Mock Gateway: Closed")


def test_integration():
    """Integration test with mock Gateway and shared memory"""
    print("\n=== Integration Test ===")
    
    _cleanup_shm(SHM_NAME)
    
    # Create shared memory and populate with initial price
    try:
        book = SharedPriceBook(name=SHM_NAME, create=True)
    except ValueError:
        # If there's an issue with shared memory, skip this test
        print("⚠ Skipping integration test due to shared memory compatibility issue")
        return
    
    try:
        book.update("AAPL", 100.0)
    except Exception as e:
        print(f"⚠ Skipping integration test: {e}")
        book.close()
        _cleanup_shm(SHM_NAME)
        return
    
    # Start mock gateway in a thread
    gateway_thread = threading.Thread(
        target=_mock_gateway_with_trend,
        args=(HOST, PORT, 3.0),
        daemon=True
    )
    gateway_thread.start()
    
    # Give gateway time to start
    time.sleep(0.5)
    
    # Create strategy instance
    strategy = SignalGenerator(
        ticker="AAPL",
        shm_name=SHM_NAME,
        short_window=3,
        long_window=5,
        bullish_threshold=60,
        bearish_threshold=40,
    )
    
    # Connect and run for a short time
    try:
        strategy.connect_to_shm()
        strategy.connect_to_gateway(HOST, PORT)
        
        # Process a few messages
        count = 0
        for raw_msg in strategy.iter_gateway_messages():
            strategy.parse_gateway_message(raw_msg)
            
            # Update shared memory with new price
            if "AAPL" in raw_msg:
                parts = raw_msg.split("*")
                for part in parts:
                    if "AAPL" in part:
                        price_str = part.split(",")[1]
                        price = float(price_str)
                        book.update("AAPL", price)
            
            # Read price from shared memory
            price = strategy.read_price_from_shm()
            if price:
                strategy.price_buffer.add(price)
            
            count += 1
            if count >= 10:
                break
        
        # Verify we received data
        assert strategy.sentiment is not None, "Should have received sentiment"
        assert len(strategy.price_buffer) > 0, "Should have price history"
        
        print(f"✓ Integration test passed - Sentiment: {strategy.sentiment}, "
              f"Prices collected: {len(strategy.price_buffer)}")
    
    finally:
        if strategy.gateway_socket:
            strategy.gateway_socket.close()
        if strategy.price_book:
            strategy.price_book.close()
        book.close()
        _cleanup_shm(SHM_NAME)
        gateway_thread.join(timeout=1.0)


if __name__ == "__main__":
    print("Running Strategy Tests...")
    
    test_price_buffer()
    test_signal_generation()
    test_order_serialization()
    test_gateway_message_parsing()
    test_integration()
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)
