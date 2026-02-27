# Cryptocurrency Trading Bot

A professional Python cryptocurrency trading bot with backtesting capabilities, risk management, and 24/7 trading support.

## Features

- **Multiple Trading Modes**: Dry-run, paper trading, and live trading
- **Backtesting Engine**: Test strategies on historical data with comprehensive metrics
- **Web Dashboard**: Mobile-friendly interface to monitor bot from your phone
- **Modular Strategy System**: Easy to create and swap trading strategies
- **Risk Management**: Stop loss, take profit, position sizing, daily loss limits
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages, and more
- **Database Persistence**: SQLite database for trade history and bot state
- **Comprehensive Logging**: Multiple log files with rotation
- **Telegram Alerts**: Real-time notifications for trades and errors
- **Exchange Support**: Built on CCXT library (supports 100+ exchanges)
- **Safety Features**: Circuit breaker, position limits, balance checks
- **24/7 Operation**: Windows service setup with automatic restart on failure

## Project Structure

```
crypto_bot/
├── src/
│   ├── config/          # Configuration management
│   ├── exchange/        # Exchange connectivity and data fetching
│   ├── strategies/      # Trading strategies and indicators
│   ├── risk/            # Risk management and position sizing
│   ├── database/        # Database models and repository
│   ├── monitoring/      # Logging and alerts
│   ├── backtesting/     # Backtesting engine (in development)
│   └── trading/         # Live trading components (in development)
├── data/                # Cached market data
├── logs/                # Log files
├── reports/             # Backtest reports
├── main.py              # CLI entry point
├── config.yaml          # Configuration file
├── .env                 # Environment variables (secrets)
└── requirements.txt     # Python dependencies
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create configuration files**:
```bash
cp .env.example .env
cp config.yaml.example config.yaml
```

4. **Configure your API keys** (edit `.env`):
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # Optional
TELEGRAM_CHAT_ID=your_telegram_chat_id      # Optional
ENVIRONMENT=testnet  # Use testnet for testing!
```

**Important**: Start with `ENVIRONMENT=testnet` to test without real money!

5. **Customize trading parameters** (edit `config.yaml`):
   - Trading pairs
   - Strategy parameters (MA periods, RSI thresholds, etc.)
   - Risk management settings
   - Position sizing rules

## Usage

### 1. Backtesting

Test your strategy on historical data:

```bash
# Basic backtest on BTCUSDT
python main.py backtest --pair BTC/USDT --start 2024-01-01 --end 2024-12-31

# Backtest with different timeframe
python main.py backtest --pair ETH/USDT --start 2024-01-01 --end 2024-12-31 --timeframe 1h

# Backtest on 5-minute data
python main.py backtest --pair BTC/USDT --start 2024-06-01 --end 2024-06-30 --timeframe 5m
```

The backtest will:
- Fetch historical data from the exchange
- Calculate technical indicators
- Generate buy/sell signals
- Display signal statistics

### 2. Paper Trading

Practice trading without real money:

```bash
# Start paper trading on BTCUSDT
python main.py paper --pair BTC/USDT --timeframe 5m

# Paper trade ETHUSDT on 1-hour timeframe
python main.py paper --pair ETH/USDT --timeframe 1h
```

Paper trading will:
- Monitor the market in real-time
- Generate signals based on your strategy
- Simulate trades without executing real orders
- Track performance in memory

Press `Ctrl+C` to stop the bot gracefully.

### 3. Live Trading

**⚠️ WARNING: Live trading uses REAL MONEY!**

Before live trading:
1. Test extensively with backtesting
2. Run paper trading for at least a week
3. Start with small position sizes
4. Use testnet first (`ENVIRONMENT=testnet` in `.env`)

```bash
# Live trading (requires confirmation)
python main.py live --pair BTC/USDT --timeframe 5m
```

You will be prompted to confirm before live trading starts.

### 4. Performance Analysis

Analyze your trading performance:

```bash
# Analyze last 30 days
python main.py analyze --days 30

# Analyze last 7 days
python main.py analyze --days 7
```

### 5. Web Dashboard (Mobile Monitoring)

Monitor your bot from anywhere with the mobile-friendly web dashboard:

```bash
# Start the dashboard
python web_dashboard.py
```

Then access from:
- **Computer**: http://localhost:5000
- **Phone**: http://YOUR_IP:5000 (find IP with `ipconfig`)

**Features:**
- Real-time bot status and uptime
- Open positions with unrealized P&L
- Recent trades with filters
- Daily P&L chart
- System resource monitoring
- Auto-refresh every 10 seconds

**Login:** Default username is `admin`, password is `crypto123` (change in `.env`!)

**See [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md) for complete setup guide.**

## Configuration

### Environment Variables (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Binance API key | Yes (for live/paper) |
| `BINANCE_SECRET_KEY` | Binance secret key | Yes (for live/paper) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | No |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | No |
| `ENVIRONMENT` | `testnet` or `mainnet` | Yes |
| `DATABASE_URL` | Database connection URL | No (default: SQLite) |
| `DASHBOARD_USERNAME` | Dashboard login username | No (default: admin) |
| `DASHBOARD_PASSWORD` | Dashboard login password | No (default: crypto123) |
| `DASHBOARD_HOST` | Dashboard host IP | No (default: 0.0.0.0) |
| `DASHBOARD_PORT` | Dashboard port | No (default: 5000) |

### Trading Configuration (config.yaml)

#### Strategy Parameters

```yaml
strategy:
  name: ma_crossover
  parameters:
    fast_period: 10      # Fast MA period
    slow_period: 30      # Slow MA period
    use_rsi_filter: true # Enable RSI filter
    rsi_period: 14
    rsi_overbought: 70
    rsi_oversold: 30
```

#### Risk Management

```yaml
risk:
  max_position_size_percent: 10  # Max % of portfolio per trade
  stop_loss_percent: 2.0         # Stop loss %
  take_profit_percent: 4.0       # Take profit %
  trailing_stop_percent: 1.5     # Trailing stop %
  max_concurrent_positions: 3     # Max open positions
  daily_loss_limit_percent: 5.0  # Stop if daily loss exceeds this
```

## Trading Strategy

### Moving Average Crossover Strategy

The default strategy uses moving average crossovers with optional filters:

**Entry Signal (BUY)**:
- Fast MA crosses above Slow MA
- AND (if enabled) RSI is not overbought (< 70)
- AND (if enabled) MACD is bullish

**Exit Signal (SELL)**:
- Fast MA crosses below Slow MA
- OR Stop loss hit
- OR Take profit hit

### Creating Custom Strategies

1. Create a new file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement required methods:
   - `calculate_indicators()`: Add technical indicators
   - `generate_signals()`: Generate buy/sell signals
   - `should_enter()`: Entry logic
   - `should_exit()`: Exit logic

Example:

```python
from src.strategies.base_strategy import BaseStrategy
from src.config.constants import SignalType

class MyCustomStrategy(BaseStrategy):
    def calculate_indicators(self, df):
        # Add your indicators
        df['custom_indicator'] = ...
        return df

    def generate_signals(self, df):
        # Generate signals
        df['signal'] = SignalType.HOLD.value
        # Your logic here
        return df
```

4. Update `config.yaml` to use your strategy:
```yaml
strategy:
  name: my_custom_strategy
```

## Safety Features

### 1. Dry Run Mode
Set `bot.mode: dry_run` in config.yaml to print actions without executing.

### 2. Paper Trading
Set `bot.mode: paper` to simulate trades without real API calls.

### 3. Position Limits
- Maximum position size per trade
- Maximum concurrent positions
- Per-asset allocation limits

### 4. Risk Limits
- Stop loss (percentage-based and trailing)
- Take profit targets
- Daily loss limit (stops trading if exceeded)

### 5. Circuit Breaker
Pauses trading if unusual price volatility is detected.

### 6. Pre-execution Validation
Every order is validated before execution:
- Balance check
- Position size validation
- Risk limit verification

## Logging

Logs are stored in the `logs/` directory:

- `main.log`: All log messages (DEBUG level)
- `trading.log`: Trading-related logs (INFO level)
- `errors.log`: Errors only (ERROR level)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Configure logging in `config.yaml`:
```yaml
monitoring:
  log_level: INFO
  log_to_file: true
  log_to_console: true
```

## Database

The bot uses SQLite database (`trading_bot.db`) to store:
- Trade history (entry/exit prices, PnL, fees)
- Open positions
- Bot state (for persistence across restarts)
- Performance metrics

### Viewing Database

```bash
# Install SQLite browser
# Linux: sudo apt install sqlitebrowser
# Mac: brew install --cask db-browser-for-sqlite
# Windows: Download from https://sqlitebrowser.org/

# Open database
sqlitebrowser trading_bot.db
```

## Troubleshooting

### Issue: "Connection Error" or "Exchange Not Available"

**Solution**:
- Check your internet connection
- Verify API keys are correct
- Check if exchange is down (visit exchange status page)
- Increase `rate_limit_delay` in config.yaml

### Issue: "Invalid API Key" or "Authentication Failed"

**Solution**:
- Verify API keys in `.env` file
- Ensure no extra spaces in API keys
- Check API key permissions (needs: Read, Trade)
- For testnet, ensure you're using testnet API keys

### Issue: "No signals generated" during backtest

**Solution**:
- Check your strategy parameters (MA periods might be too long)
- Ensure enough historical data is fetched
- Try adjusting RSI/MACD filter settings
- Check if filters are too restrictive

### Issue: "Insufficient Balance" error

**Solution**:
- Check your account balance on the exchange
- Reduce `max_position_size_percent` in config.yaml
- Ensure `initial_capital` matches your actual balance

### Issue: Bot crashes or stops unexpectedly

**Solution**:
- Check `logs/errors.log` for error messages
- Ensure stable internet connection
- Verify exchange API is working
- Enable `auto_restart_on_error` in config.yaml

## Best Practices

1. **Always test first**: Backtest → Paper Trading → Live Trading (testnet) → Live Trading (mainnet)

2. **Start small**: Begin with minimum position sizes

3. **Monitor closely**: Watch the bot for the first few days

4. **Set realistic expectations**: No strategy wins 100% of the time

5. **Use stop losses**: Always have risk management enabled

6. **Keep logs**: Review logs regularly to understand bot behavior

7. **Stay updated**: Keep exchange connection stable and monitor for API changes

## Development Status

### ✅ Completed
- Configuration management
- Exchange connectivity (CCXT)
- Data fetching and caching
- Strategy framework (base class, indicators, MA crossover)
- Risk management (position sizing, stop loss, take profit)
- Database models and repository
- Logging system
- CLI interface

### 🚧 In Development
- Full backtesting engine with metrics (Sharpe ratio, drawdown, etc.)
- Performance visualization (equity curves, charts)
- Live trading execution engine
- Position manager for real-time tracking
- Telegram alerts and notifications
- Health monitoring dashboard
- Unit tests for all components

## Contributing

To extend this bot:

1. **Add new strategies**: Create files in `src/strategies/`
2. **Add new indicators**: Add functions to `src/strategies/indicators.py`
3. **Add new exchanges**: Configure in `config.yaml` (CCXT supports 100+ exchanges)
4. **Improve risk management**: Modify `src/risk/` modules

## Disclaimer

**⚠️ IMPORTANT: Trading cryptocurrencies carries significant risk. This bot is provided as-is with no guarantees of profitability. You can lose all your invested capital. Always:**

- Test thoroughly before live trading
- Never invest more than you can afford to lose
- Understand the risks involved in algorithmic trading
- Monitor your bot regularly
- Keep your API keys secure
- Start with testnet/paper trading

The authors and contributors are not responsible for any financial losses incurred while using this software.

## Support

For issues, questions, or contributions:
- Check the troubleshooting section above
- Review the logs in `logs/` directory
- Check configuration in `config.yaml` and `.env`

## License

This project is provided for educational and research purposes.

---

**Happy Trading! 🚀📈**
