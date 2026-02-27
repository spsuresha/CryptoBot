"""
Trading bot constants and enumerations.
"""
from enum import Enum
from typing import Dict


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class PositionStatus(str, Enum):
    """Position status enumeration."""
    OPEN = "open"
    CLOSED = "closed"


class TradingMode(str, Enum):
    """Trading mode enumeration."""
    DRY_RUN = "dry_run"  # Print actions without execution
    PAPER = "paper"  # Simulate trades without real API calls
    LIVE = "live"  # Real trading with real money


class SignalType(int, Enum):
    """Trading signal type."""
    SELL = -1
    HOLD = 0
    BUY = 1


class PositionSizingMethod(str, Enum):
    """Position sizing method enumeration."""
    FIXED = "fixed"  # Fixed percentage of portfolio
    VOLATILITY = "volatility"  # Based on ATR/volatility


class ExitReason(str, Enum):
    """Reason for closing a position."""
    SIGNAL = "signal"  # Strategy exit signal
    STOP_LOSS = "stop_loss"  # Stop loss hit
    TAKE_PROFIT = "take_profit"  # Take profit hit
    TRAILING_STOP = "trailing_stop"  # Trailing stop hit
    MANUAL = "manual"  # Manual exit by user
    RISK_LIMIT = "risk_limit"  # Risk limit exceeded
    CIRCUIT_BREAKER = "circuit_breaker"  # Circuit breaker triggered


# Timeframe mappings
TIMEFRAME_MINUTES: Dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}

# Default values
DEFAULT_RETRY_ATTEMPTS = 5
DEFAULT_RETRY_DELAY = 1  # seconds
DEFAULT_MAX_RETRY_DELAY = 60  # seconds
DEFAULT_RATE_LIMIT_DELAY = 0.1  # seconds

# Risk management defaults
DEFAULT_MAX_POSITION_SIZE_PERCENT = 10
DEFAULT_STOP_LOSS_PERCENT = 2.0
DEFAULT_TAKE_PROFIT_PERCENT = 4.0
DEFAULT_TRAILING_STOP_PERCENT = 1.5
DEFAULT_MAX_CONCURRENT_POSITIONS = 3
DEFAULT_DAILY_LOSS_LIMIT_PERCENT = 5.0

# Technical analysis defaults
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_OVERBOUGHT = 70
DEFAULT_RSI_OVERSOLD = 30
DEFAULT_MACD_FAST = 12
DEFAULT_MACD_SLOW = 26
DEFAULT_MACD_SIGNAL = 9
DEFAULT_BB_PERIOD = 20
DEFAULT_BB_STD = 2

# Backtesting defaults
DEFAULT_INITIAL_CAPITAL = 10000
DEFAULT_COMMISSION = 0.001  # 0.1%
DEFAULT_SLIPPAGE = 0.0005  # 0.05%

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File paths
DATABASE_FILE = "trading_bot.db"
MAIN_LOG_FILE = "logs/main.log"
TRADING_LOG_FILE = "logs/trading.log"
ERROR_LOG_FILE = "logs/errors.log"
