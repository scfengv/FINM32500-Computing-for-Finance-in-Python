# Assignment 8 - Multi-Process Trading System

A real-time trading system that demonstrates inter-process communication using TCP sockets and shared memory. The system consists of four components that work together to simulate market data reception, price aggregation, signal generation, and order execution.

## 🏗️ System Architecture

```
┌─────────────────┐
│    Gateway      │  Port 9000 (TCP Server)
│  Market Data    │  • Simulates market feed
│    Provider     │  • Sends prices + sentiment
└────────┬────────┘
         │
         │ TCP Stream: "AAPL,101.25*MSFT,275.10*SENTIMENT,65*"
         │
         ├──────────────────────────────┐
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────┐
│   OrderBook     │          │    Strategy     │
│                 │          │ (Signal Gen)    │
│ • Parses prices │          │ • Parses        │
│ • Writes to SHM │          │   sentiment     │
└────────┬────────┘          │ • Reads prices  │
         │                   │   from SHM      │
         ▼                   │ • Generates     │
┌─────────────────┐          │   signals       │
│ Shared Memory   │◄─────────┤ • Sends orders  │
│  (Price Book)   │          └────────┬────────┘
└─────────────────┘                   │
                                      │ TCP: JSON Orders
                                      ▼
                             ┌─────────────────┐
                             │  OrderManager   │  Port 9001 (TCP Server)
                             │                 │  • Receives orders
                             │ • Logs trades   │  • Executes trades
                             └─────────────────┘
```

## 📦 Components

### 1. Gateway (`gateway.py`)
**Role:** Market data simulator
- **Port:** 9000 (TCP Server)
- **Function:** Sends simulated price updates and sentiment data every 0.5 seconds
- **Message Format:** `AAPL,101.25*MSFT,275.10*GOOG,300.00*SENTIMENT,65*`
- **Data:**
  - Price updates for 3 tickers (AAPL, MSFT, GOOG)
  - Random walk price movements (±0.1%)
  - Sentiment score (0-100)

### 2. OrderBook (`orderbook.py`)
**Role:** Price aggregator
- **Connects to:** Gateway (port 9000)
- **Function:** 
  - Receives price + sentiment stream from Gateway
  - Parses and extracts price data (ignores sentiment)
  - Writes prices to shared memory
  - Auto-reconnects on connection loss
- **Shared Memory:** Creates/attaches to `pricebook` shared memory block
- **Message Handling:** Uses `*` delimiter to parse messages

### 3. Strategy (`strategy.py`)
**Role:** Signal generator and trading logic
- **Connects to:** 
  - Gateway (port 9000) - for sentiment data
  - Shared Memory - for price data
  - OrderManager (port 9001) - for sending orders
- **Function:**
  - Reads latest prices from shared memory
  - Receives sentiment from Gateway stream
  - Generates trading signals using:
    - **Price Signal:** Moving average crossover (MA)
      - Short MA (5 periods) > Long MA (20 periods) → BUY
      - Short MA < Long MA → SELL
    - **News Signal:** Sentiment thresholds
      - Sentiment > 60 → BUY (Bullish)
      - Sentiment < 40 → SELL (Bearish)
  - **Trading Rule:** Only trades when BOTH signals agree
  - **Position Management:** Prevents duplicate orders (tracks long/short/none)
  - Sends JSON-serialized orders to OrderManager

### 4. OrderManager (`OrderManager.py`)
**Role:** Order execution and logging
- **Port:** 9001 (TCP Server)
- **Function:**
  - Receives order messages from Strategy
  - Decodes JSON orders
  - Logs trade execution
  - Handles multiple concurrent clients (multi-threaded)
- **Expected Order Format:**
  ```json
  {
    "id": "ORD_AAPL_1_1762738418",
    "ticker": "AAPL",
    "action": "BUY",
    "quantity": 100,
    "price": 150.25,
    "timestamp": 1762738418.177732,
    "reason": "MA crossover + sentiment agreement"
  }*
  ```

## 🚀 How to Run

### Option 1: Manual Start (Recommended for Learning)

Open **4 separate terminal windows** and run in this order:

**Terminal 1 - Start Gateway:**
```bash
cd assignment8
python src/gateway.py
```
Expected output: `Gateway TCP server running on localhost:9000`

**Terminal 2 - Start OrderManager:**
```bash
cd assignment8
python src/OrderManager.py
```
Expected output: `OrderManager listening on localhost:9001`

**Terminal 3 - Start OrderBook:**
```bash
cd assignment8
python -c "from src.orderbook import run_orderbook; run_orderbook()"
```
Expected output: `OrderBook: created shm 'pricebook'` → `OrderBook: connected`

**Terminal 4 - Start Strategy:**
```bash
cd assignment8
python src/strategy.py AAPL
```
Expected output: 
```
Strategy: Starting signal generator for AAPL
Strategy: Connected to shared memory 'pricebook'
Strategy: Connected to Gateway at localhost:9000
Strategy: Connected to OrderManager at localhost:9001
```

### Option 2: Automated Demo (macOS only)
```bash
cd assignment8
python demo.py
```
This will open 3 terminal windows automatically (Gateway, OrderBook, Strategy).
You'll need to manually start OrderManager in a 4th terminal.

### Option 3: Run Tests
```bash
cd assignment8

# Test basic functionality
python simple_test.py

# Test OrderManager integration
python test_ordermanager_integration.py

# Full test suite
python tests/test_strategy.py
```

## 📊 What to Expect

### Initial Phase (First ~20 messages)
```
Strategy: Received sentiment = 75
Strategy: Price=101.25, Short MA=None, Long MA=None, ...
```
The strategy is **accumulating price history**. It needs at least 20 prices to calculate the long moving average.

### Trading Phase (After 20+ messages)
```
Strategy: Price=102.50, Short MA=101.80, Long MA=100.20, 
          Sentiment=75, Price Signal=BUY, News Signal=BUY, Position=None
Strategy: ORDER SENT -> {"id": "ORD_AAPL_1_...", "action": "BUY", ...}*
```

**OrderManager will log:**
```
Received Order ORD_AAPL_1_1762738418: BUY 100 AAPL @ 102.50
```

### When Signals Disagree
```
Strategy: Price Signal=BUY, News Signal=SELL, Position=None
(No trade - signals disagree)
```

### Position Management
```
Strategy: Price Signal=BUY, News Signal=BUY, Position=long
(No trade - already long, preventing duplicate)
```

## 🎯 Trading Signal Logic

### Signal Generation

| Condition | Price Signal | News Signal | Action |
|-----------|--------------|-------------|--------|
| Short MA > Long MA **AND** Sentiment > 60 | BUY | BUY | ✅ **EXECUTE BUY** |
| Short MA < Long MA **AND** Sentiment < 40 | SELL | SELL | ✅ **EXECUTE SELL** |
| Short MA > Long MA **BUT** Sentiment < 40 | BUY | SELL | ❌ No trade (disagree) |
| Short MA < Long MA **BUT** Sentiment > 60 | SELL | BUY | ❌ No trade (disagree) |
| Any **BUT** Sentiment = 40-60 | Any | None | ❌ No trade (neutral) |
| BUY signal **BUT** already long | BUY | BUY | ❌ No trade (duplicate) |
| SELL signal **BUT** already short | SELL | SELL | ❌ No trade (duplicate) |

### Configuration Parameters

Edit `src/strategy.py` to tune the strategy:

```python
SHORT_WINDOW = 5          # Short moving average window
LONG_WINDOW = 20          # Long moving average window
BULLISH_THRESHOLD = 60    # Sentiment > 60 → Bullish
BEARISH_THRESHOLD = 40    # Sentiment < 40 → Bearish
PRICE_BUFFER_SIZE = 50    # Max price history retained
```

## 🔧 Technical Details

### Inter-Process Communication

1. **TCP Sockets:**
   - Gateway ↔ OrderBook: Streaming price data
   - Gateway ↔ Strategy: Streaming sentiment data
   - Strategy ↔ OrderManager: Sending orders
   - **Protocol:** Delimiter-based (`*`) message framing

2. **Shared Memory:**
   - OrderBook → Strategy: Price sharing
   - **Library:** `multiprocessing.shared_memory`
   - **Format:** Pickled dictionary `{ticker: price}`
   - **Size:** 4096 bytes

### Message Formats

**Gateway → OrderBook/Strategy:**
```
AAPL,101.25*MSFT,275.10*GOOG,300.00*SENTIMENT,65*
```

**Strategy → OrderManager:**
```json
{"id": "ORD_AAPL_1_...", "ticker": "AAPL", "action": "BUY", 
 "quantity": 100, "price": 150.25, "timestamp": 1762738418.177732,
 "reason": "MA crossover + sentiment agreement"}*
```

### Error Handling

- **OrderBook:** Auto-reconnects to Gateway with exponential backoff
- **Strategy:** Graceful shutdown on Ctrl+C
- **OrderManager:** Multi-threaded, handles multiple clients
- **Shared Memory:** Create on first use, attach for subsequent processes

## 🧪 Testing

### Unit Tests
```bash
# Test Strategy signal generation
python simple_test.py

# Expected: All 4 scenarios pass
# 1. ✓ Upward trend + Bullish sentiment → BUY
# 2. ✓ Downward trend + Bearish sentiment → SELL
# 3. ✓ Signal disagreement → No trade
# 4. ✓ Position management → Prevents duplicates
```

### Integration Tests
```bash
# Test Strategy ↔ OrderManager integration
python test_ordermanager_integration.py

# Verifies:
# - Order has all required fields (id, ticker, action, quantity, price)
# - JSON serialization works correctly
# - OrderManager can decode orders
# - TCP communication works end-to-end
```

### Smoke Tests
```bash
# Test Gateway connectivity
python tests/gateway_test.py

# Test OrderBook
python tests/orderbook_smoke_test.py

# Test Shared Memory
python tests/shared_mem_test.py
```

## 📁 Project Structure

```
assignment8/
├── src/
│   ├── gateway.py              # Market data simulator
│   ├── orderbook.py            # Price aggregator (writes to SHM)
│   ├── strategy.py             # Signal generator (reads SHM, sends orders)
│   ├── OrderManager.py         # Order execution service
│   └── shared_memory_utils.py  # Shared memory wrapper
│
├── tests/
│   ├── gateway_test.py         # Gateway connectivity test
│   ├── orderbook_smoke_test.py # OrderBook functional test
│   ├── shared_mem_test.py      # Shared memory test
│   └── test_strategy.py        # Strategy unit tests
│
├── simple_test.py              # Quick verification script
├── test_ordermanager_integration.py  # Integration test
├── demo.py                     # Automated launcher (macOS)
└── README.md                   # This file
```

## 🐛 Troubleshooting

### Problem: "FileNotFoundError: No such file or directory: '/pricebook'"
**Solution:** Start OrderBook first. It creates the shared memory block that Strategy reads from.

### Problem: "ConnectionRefusedError" from Strategy
**Solution:** 
- Start Gateway first (port 9000)
- Start OrderManager first (port 9001)
- Then start Strategy

### Problem: Strategy not generating signals
**Possible causes:**
1. **Not enough data:** Wait for 20+ price updates to accumulate
2. **Signals disagree:** Price says BUY but sentiment is neutral/bearish
3. **Already in position:** Prevents duplicate orders

### Problem: "Address already in use"
**Solution:** Kill existing process on that port:
```bash
# Find process using port 9000 or 9001
lsof -ti:9000
lsof -ti:9001

# Kill it
kill -9 <PID>
```

### Problem: Shared memory cleanup
If you need to clean up shared memory manually:
```python
python -c "from multiprocessing import shared_memory; shm = shared_memory.SharedMemory(name='pricebook'); shm.close(); shm.unlink()"
```

## 🎓 Key Concepts Demonstrated

1. **Multi-Process Architecture:** Independent processes communicating via sockets and shared memory
2. **TCP Socket Programming:** Client-server communication with custom protocols
3. **Shared Memory IPC:** Fast inter-process data sharing
4. **Message Framing:** Delimiter-based protocol for streaming data
5. **Signal Processing:** Moving average calculations, threshold-based decisions
6. **State Management:** Position tracking to prevent duplicate orders
7. **JSON Serialization:** Structured data exchange between processes
8. **Error Handling:** Reconnection logic, graceful shutdown
9. **Multi-threading:** OrderManager handles concurrent clients
10. **Real-time Systems:** Continuous data processing and decision making

## 📝 Assignment Requirements Met

✅ **Gateway:** Simulates market data feed (prices + sentiment)  
✅ **OrderBook:** Aggregates prices into shared memory  
✅ **Strategy:** Generates signals based on price + news  
✅ **OrderManager:** Receives and logs orders  
✅ **TCP Communication:** All components communicate via sockets  
✅ **Shared Memory:** Price data shared between OrderBook and Strategy  
✅ **Message Protocol:** Delimiter-based message framing  
✅ **JSON Orders:** Structured order format with all required fields  
✅ **Position Management:** Prevents duplicate orders  
✅ **Signal Agreement:** Only trades when price + news signals match  

## 📚 Further Enhancements

Potential improvements for production use:

- [ ] Add database persistence for orders and trades
- [ ] Implement risk management (position limits, stop-loss)
- [ ] Add more sophisticated signals (RSI, MACD, Bollinger Bands)
- [ ] Support multiple tickers simultaneously
- [ ] Add backtesting capabilities
- [ ] Implement order execution simulation with slippage
- [ ] Add monitoring and alerting
- [ ] Create web dashboard for visualization
- [ ] Add authentication and encryption for TCP connections
- [ ] Implement order book with bid/ask spreads

## 📄 License

Educational project for FINM 32500 - Computing for Finance in Python

---

**Happy Trading! 🚀📈**
