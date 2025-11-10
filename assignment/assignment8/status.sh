#!/bin/bash
# Startup helper for Assignment 8
# Shows which components are running and what's needed

echo "=================================================="
echo "Assignment 8 - System Status Check"
echo "=================================================="
echo ""

# Check Gateway (port 9000)
echo "1. Gateway (port 9000):"
if lsof -i:9000 > /dev/null 2>&1; then
    echo "   ✓ RUNNING"
else
    echo "   ✗ NOT RUNNING"
    echo "   → Start with: python src/gateway.py"
fi
echo ""

# Check OrderManager (port 9001)
echo "2. OrderManager (port 9001):"
if lsof -i:9001 > /dev/null 2>&1; then
    echo "   ✓ RUNNING"
else
    echo "   ✗ NOT RUNNING"
    echo "   → Start with: python src/OrderManager.py"
fi
echo ""

# Check Shared Memory
echo "3. Shared Memory (pricebook):"
python3 -c "
from multiprocessing import shared_memory
try:
    shm = shared_memory.SharedMemory(name='pricebook')
    shm.close()
    print('   ✓ EXISTS')
except FileNotFoundError:
    print('   ✗ NOT CREATED')
    print('   → Will be created when OrderBook starts')
except Exception as e:
    print(f'   ? {e}')
" 2>/dev/null
echo ""

echo "=================================================="
echo "Startup Order (if components are missing):"
echo "=================================================="
echo ""
echo "Terminal 1: python src/gateway.py"
echo "Terminal 2: python src/OrderManager.py" 
echo "Terminal 3: python -c \"from src.orderbook import run_orderbook; run_orderbook()\""
echo "Terminal 4: python src/strategy.py AAPL"
echo ""
echo "Or run: ./cleanup.sh first, then start fresh"
