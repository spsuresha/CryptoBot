# Quick Start Guide

Get your trading bot running in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Create Configuration Files

```bash
# Copy example files
cp .env.example .env
cp config.yaml.example config.yaml
```

## 3. Configure API Keys (Optional for backtesting)

Edit `.env` file:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
ENVIRONMENT=testnet
```

**Note**: For backtesting only, you don't need real API keys immediately. The bot can fetch historical data without authentication.

## 4. Run Your First Backtest

```bash
python main.py backtest --pair BTC/USDT --start 2024-01-01 --end 2024-06-01
```

This will:
- Fetch historical BTC/USDT data from Binance
- Calculate moving averages and technical indicators
- Generate buy/sell signals
- Show you the results

## 5. Try Paper Trading (Requires API Keys)

Once you have API keys configured:

```bash
python main.py paper --pair BTC/USDT --timeframe 5m
```

This will:
- Monitor BTC/USDT in real-time
- Generate signals using your strategy
- Simulate trades without real money
- Update you on performance

Press `Ctrl+C` to stop.

## 6. Customize Your Strategy

Edit `config.yaml` to adjust strategy parameters:

```yaml
strategy:
  parameters:
    fast_period: 10      # Try 5, 10, 20
    slow_period: 30      # Try 20, 30, 50
    use_rsi_filter: true # true or false
    rsi_overbought: 70   # Try 65-75
    rsi_oversold: 30     # Try 25-35
```

## What's Next?

1. **Run more backtests** with different pairs and timeframes
2. **Tune strategy parameters** in config.yaml
3. **Try paper trading** to see real-time performance
4. **Review logs** in the `logs/` directory
5. **Check trade history** in the database

## Need Help?

- Check [README.md](README.md) for full documentation
- Look at `logs/main.log` for detailed information
- Review `config.yaml.example` for all available options

## Common Issues

**"Module not found" error**:
```bash
pip install -r requirements.txt
```

**"API key" error during backtest**:
- Backtesting works without API keys for some data
- For full features, add API keys to `.env`

**No signals generated**:
- Try different date ranges (need enough data)
- Adjust MA periods in config.yaml
- Check logs for details

Happy trading! 🚀
