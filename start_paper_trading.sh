#!/bin/bash
# Paper Trading Startup Script for 6h LONG-only strategy

cd /c/temp/Crypto_Bot

# Activate virtual environment
source venv311/Scripts/activate

# Run paper trading in background with nohup
nohup python main.py paper --pair BTC/USDT --timeframe 6h >> paper_trading_6h.log 2>&1 &

# Get PID
PAPER_PID=$!
echo $PAPER_PID > paper_trading.pid

echo "✓ Paper trading started with PID: $PAPER_PID"
echo "✓ Log file: paper_trading_6h.log"
echo "✓ To stop: kill \$(cat paper_trading.pid)"
echo ""
echo "Monitor with: tail -f paper_trading_6h.log"
