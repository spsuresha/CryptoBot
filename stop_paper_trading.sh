#!/bin/bash
# Stop Paper Trading Script

cd /c/temp/Crypto_Bot

if [ -f paper_trading.pid ]; then
    PID=$(cat paper_trading.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✓ Paper trading stopped (PID: $PID)"
        rm paper_trading.pid
    else
        echo "! Process $PID not running"
        rm paper_trading.pid
    fi
else
    echo "! No PID file found. Searching for python process..."
    pkill -f "python.*main.py paper" && echo "✓ Killed paper trading process" || echo "! No process found"
fi
