# src/strategy.py
"""
Strategy (Signal Generator)

Responsibilities:
- Reads the latest prices from shared memory
- Connects to the Gateway's news stream to receive sentiment
- Generates trading signals:
  * Price-based: Moving average crossover (short vs long window)
  * News-based: Sentiment > bullish_threshold → Buy; Sentiment < bearish_threshold → Sell
- Only acts when both signals agree
- Sends an Order message to the OrderManager when a trade is decided
- Uses a local rolling buffer for price history
- Manages current position (None, long, short) to avoid duplicate orders
- Serializes orders before sending (e.g. JSON, pickle, or otherwise)
- Respects MESSAGE_DELIMITER in all transmissions
"""

import socket
import json
import time
from collections import deque
from typing import Optional, Literal
from dataclasses import dataclass, asdict

try:
    from .shared_memory_utils import SharedPriceBook
except ImportError:
    from shared_memory_utils import SharedPriceBook


# Configuration
HOST = "localhost"
PORT = 9000
MESSAGE_DELIMITER = b"*"
RECONNECT_BASE = 0.5
RECONNECT_MAX = 5.0
SOCKET_TIMEOUT = 5.0

# Strategy parameters
SHORT_WINDOW = 5
LONG_WINDOW = 20
BULLISH_THRESHOLD = 60
BEARISH_THRESHOLD = 40
PRICE_BUFFER_SIZE = 50

Position = Literal["long", "short", None]


@dataclass
class Order:
    """Order message to be sent to OrderManager"""
    ticker: str
    action: Literal["BUY", "SELL"]
    price: float
    timestamp: float
    reason: str


class PriceBuffer:
    """Local rolling buffer for price history"""
    def __init__(self, maxlen: int = PRICE_BUFFER_SIZE):
        self.buffer = deque(maxlen=maxlen)
    
    def add(self, price: float):
        """Add a price to the buffer"""
        self.buffer.append(price)
    
    def get_ma(self, window: int) -> Optional[float]:
        """Calculate moving average for the given window"""
        if len(self.buffer) < window:
            return None
        recent = list(self.buffer)[-window:]
        return sum(recent) / len(recent)
    
    def __len__(self):
        return len(self.buffer)


class SignalGenerator:
    """
    Strategy that generates trading signals based on:
    1. Price-based signal: Moving average crossover
    2. News-based signal: Sentiment thresholds
    
    Only trades when both signals agree.
    """
    
    def __init__(
        self,
        ticker: str = "AAPL",
        shm_name: str = "pricebook",
        short_window: int = SHORT_WINDOW,
        long_window: int = LONG_WINDOW,
        bullish_threshold: int = BULLISH_THRESHOLD,
        bearish_threshold: int = BEARISH_THRESHOLD,
    ):
        self.ticker = ticker
        self.shm_name = shm_name
        self.short_window = short_window
        self.long_window = long_window
        self.bullish_threshold = bullish_threshold
        self.bearish_threshold = bearish_threshold
        
        # Price history buffer
        self.price_buffer = PriceBuffer(maxlen=PRICE_BUFFER_SIZE)
        
        # Current position: None, "long", or "short"
        self.position: Position = None
        
        # Latest sentiment
        self.sentiment: Optional[int] = None
        
        # Shared memory connection
        self.price_book: Optional[SharedPriceBook] = None
        
        # Gateway connection
        self.gateway_socket: Optional[socket.socket] = None
    
    def connect_to_shm(self):
        """Connect to shared memory to read prices"""
        try:
            self.price_book = SharedPriceBook(name=self.shm_name, create=False)
            print(f"Strategy: Connected to shared memory '{self.shm_name}'")
        except FileNotFoundError:
            print(f"Strategy: Waiting for shared memory '{self.shm_name}' to be created...")
            time.sleep(1)
            self.price_book = SharedPriceBook(name=self.shm_name, create=False)
            print(f"Strategy: Connected to shared memory '{self.shm_name}'")
    
    def connect_to_gateway(self, host: str = HOST, port: int = PORT):
        """Connect to Gateway's news stream"""
        self.gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gateway_socket.settimeout(SOCKET_TIMEOUT)
        self.gateway_socket.connect((host, port))
        self.gateway_socket.settimeout(None)
        print(f"Strategy: Connected to Gateway at {host}:{port}")
    
    def parse_gateway_message(self, raw_msg: str):
        """
        Parse messages from Gateway.
        Expected format: "AAPL,101.25*MSFT,275.10*SENTIMENT,45*"
        
        Updates sentiment if SENTIMENT message is found.
        Note: Prices are handled by OrderBook, we only care about sentiment here.
        """
        if not raw_msg:
            return
        
        parts = raw_msg.strip().split("*")
        for part in parts:
            if not part:
                continue
            
            fields = part.split(",")
            if len(fields) >= 2 and fields[0].strip().upper() == "SENTIMENT":
                try:
                    self.sentiment = int(fields[1])
                    print(f"Strategy: Received sentiment = {self.sentiment}")
                except ValueError:
                    pass
    
    def iter_gateway_messages(self):
        """Yield delimiter-terminated messages from Gateway"""
        buf = bytearray()
        while True:
            try:
                chunk = self.gateway_socket.recv(4096)
                if not chunk:
                    raise ConnectionResetError("Gateway closed")
                buf.extend(chunk)
                
                while True:
                    i = buf.find(MESSAGE_DELIMITER)
                    if i == -1:
                        break
                    raw = bytes(buf[:i])
                    del buf[:i + 1]
                    if raw:
                        yield raw.decode("utf-8", "replace")
            except socket.timeout:
                continue
    
    def read_price_from_shm(self) -> Optional[float]:
        """Read the latest price for our ticker from shared memory"""
        if self.price_book is None:
            return None
        
        price = self.price_book.read_tick(self.ticker)
        return price
    
    def generate_price_signal(self) -> Optional[Literal["BUY", "SELL"]]:
        """
        Generate price-based signal using moving average crossover.
        
        BUY: short MA > long MA (upward trend)
        SELL: short MA < long MA (downward trend)
        None: Not enough data or MAs are equal
        """
        short_ma = self.price_buffer.get_ma(self.short_window)
        long_ma = self.price_buffer.get_ma(self.long_window)
        
        if short_ma is None or long_ma is None:
            return None
        
        if short_ma > long_ma:
            return "BUY"
        elif short_ma < long_ma:
            return "SELL"
        else:
            return None
    
    def generate_news_signal(self) -> Optional[Literal["BUY", "SELL"]]:
        """
        Generate news-based signal using sentiment thresholds.
        
        BUY: sentiment > bullish_threshold
        SELL: sentiment < bearish_threshold
        None: sentiment is neutral
        """
        if self.sentiment is None:
            return None
        
        if self.sentiment > self.bullish_threshold:
            return "BUY"
        elif self.sentiment < self.bearish_threshold:
            return "SELL"
        else:
            return None
    
    def should_trade(self) -> Optional[Literal["BUY", "SELL"]]:
        """
        Determine if we should trade based on both signals.
        
        Only trade when both signals agree AND we're not already in that position.
        """
        price_signal = self.generate_price_signal()
        news_signal = self.generate_news_signal()
        
        # Both signals must agree
        if price_signal is None or news_signal is None:
            return None
        
        if price_signal != news_signal:
            return None
        
        # Don't duplicate positions
        signal = price_signal  # They're the same at this point
        
        if signal == "BUY" and self.position == "long":
            return None  # Already long
        
        if signal == "SELL" and self.position == "short":
            return None  # Already short
        
        return signal
    
    def create_order(self, action: Literal["BUY", "SELL"], price: float) -> Order:
        """Create an Order object"""
        return Order(
            ticker=self.ticker,
            action=action,
            price=price,
            timestamp=time.time(),
            reason=f"MA crossover + sentiment agreement"
        )
    
    def serialize_order(self, order: Order) -> bytes:
        """Serialize order to JSON with MESSAGE_DELIMITER"""
        order_dict = asdict(order)
        json_str = json.dumps(order_dict)
        return json_str.encode('utf-8') + MESSAGE_DELIMITER
    
    def send_order(self, order: Order):
        """
        Send order to OrderManager (stub - would need actual socket connection).
        For now, just print the order.
        """
        serialized = self.serialize_order(order)
        print(f"Strategy: ORDER SENT -> {serialized.decode('utf-8').strip()}")
        
        # Update position
        if order.action == "BUY":
            self.position = "long"
        elif order.action == "SELL":
            self.position = "short"
        
        # In a real implementation, you would send to OrderManager via socket:
        # self.order_manager_socket.sendall(serialized)
    
    def run(self, host: str = HOST, port: int = PORT):
        """
        Main event loop:
        1. Connect to shared memory
        2. Connect to Gateway news stream
        3. Read prices from shared memory
        4. Receive sentiment from Gateway
        5. Generate signals and trade when both agree
        """
        print(f"Strategy: Starting signal generator for {self.ticker}")
        
        # Connect to shared memory
        self.connect_to_shm()
        
        # Connect to Gateway
        try:
            self.connect_to_gateway(host, port)
        except Exception as e:
            print(f"Strategy: Failed to connect to Gateway: {e}")
            return
        
        try:
            # Main loop
            for raw_msg in self.iter_gateway_messages():
                # Parse sentiment from Gateway message
                self.parse_gateway_message(raw_msg)
                
                # Read latest price from shared memory
                price = self.read_price_from_shm()
                
                if price is not None:
                    # Update price buffer
                    self.price_buffer.add(price)
                    
                    # Check if we have enough data
                    if len(self.price_buffer) >= self.long_window:
                        # Generate signals
                        price_signal = self.generate_price_signal()
                        news_signal = self.generate_news_signal()
                        
                        print(f"Strategy: Price={price:.2f}, "
                              f"Short MA={self.price_buffer.get_ma(self.short_window):.2f}, "
                              f"Long MA={self.price_buffer.get_ma(self.long_window):.2f}, "
                              f"Sentiment={self.sentiment}, "
                              f"Price Signal={price_signal}, "
                              f"News Signal={news_signal}, "
                              f"Position={self.position}")
                        
                        # Decide if we should trade
                        action = self.should_trade()
                        
                        if action is not None:
                            # Create and send order
                            order = self.create_order(action, price)
                            self.send_order(order)
        
        except KeyboardInterrupt:
            print("\nStrategy: Shutting down...")
        except Exception as e:
            print(f"Strategy: Error: {e}")
        finally:
            # Cleanup
            if self.gateway_socket:
                try:
                    self.gateway_socket.close()
                except Exception:
                    pass
            
            if self.price_book:
                try:
                    self.price_book.close()
                except Exception:
                    pass


def run_strategy(
    ticker: str = "AAPL",
    host: str = HOST,
    port: int = PORT,
    shm_name: str = "pricebook",
    short_window: int = SHORT_WINDOW,
    long_window: int = LONG_WINDOW,
    bullish_threshold: int = BULLISH_THRESHOLD,
    bearish_threshold: int = BEARISH_THRESHOLD,
):
    """
    Run the strategy signal generator.
    
    Args:
        ticker: The ticker symbol to trade
        host: Gateway host
        port: Gateway port
        shm_name: Shared memory name
        short_window: Short moving average window
        long_window: Long moving average window
        bullish_threshold: Sentiment threshold for bullish signal
        bearish_threshold: Sentiment threshold for bearish signal
    """
    strategy = SignalGenerator(
        ticker=ticker,
        shm_name=shm_name,
        short_window=short_window,
        long_window=long_window,
        bullish_threshold=bullish_threshold,
        bearish_threshold=bearish_threshold,
    )
    strategy.run(host=host, port=port)


if __name__ == "__main__":
    import sys
    
    # Allow ticker to be passed as command line argument
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    run_strategy(ticker=ticker)
