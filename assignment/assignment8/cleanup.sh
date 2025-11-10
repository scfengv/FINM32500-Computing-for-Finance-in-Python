#!/bin/bash
# Cleanup script for Assignment 8
# Kills all running processes and cleans up shared memory

echo "=================================================="
echo "Assignment 8 Cleanup Script"
echo "=================================================="

# Kill Gateway (port 9000)
if lsof -ti:9000 > /dev/null 2>&1; then
    echo "✓ Killing Gateway on port 9000..."
    kill -9 $(lsof -ti:9000) 2>/dev/null
else
    echo "  No process on port 9000"
fi

# Kill OrderManager (port 9001)
if lsof -ti:9001 > /dev/null 2>&1; then
    echo "✓ Killing OrderManager on port 9001..."
    kill -9 $(lsof -ti:9001) 2>/dev/null
else
    echo "  No process on port 9001"
fi

# Clean up shared memory
echo "✓ Cleaning up shared memory..."
python3 -c "
from multiprocessing import shared_memory
import sys

try:
    shm = shared_memory.SharedMemory(name='pricebook')
    shm.close()
    shm.unlink()
    print('  Removed shared memory: pricebook')
except FileNotFoundError:
    print('  No shared memory to clean')
except Exception as e:
    print(f'  Shared memory cleanup: {e}')
" 2>/dev/null

echo "=================================================="
echo "✓ Cleanup complete!"
echo "=================================================="
echo ""
echo "You can now start the system fresh:"
echo "  1. python src/gateway.py"
echo "  2. python src/OrderManager.py"
echo "  3. python -c \"from src.orderbook import run_orderbook; run_orderbook()\""
echo "  4. python src/strategy.py AAPL"
