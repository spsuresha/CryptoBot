"""
Configuration management for the trading bot.
Loads settings from .env and config.yaml files.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv

from .constants import (
    TradingMode,
    DEFAULT_MAX_POSITION_SIZE_PERCENT,
    DEFAULT_STOP_LOSS_PERCENT,
    DEFAULT_TAKE_PROFIT_PERCENT,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_COMMISSION,
    DEFAULT_SLIPPAGE,
)


class Settings:
    """
    Singleton class for managing application settings.
    Loads configuration from .env and config.yaml files.
    """

    _instance: Optional['Settings'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize settings by loading from configuration files."""
        if not self._initialized:
            self._load_env()
            self._load_config()
            self._validate()
            Settings._initialized = True

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        # Get the project root directory
        self.project_root = Path(__file__).parent.parent.parent

        # Load .env file
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Exchange API credentials
        self.binance_api_key = os.getenv("BINANCE_API_KEY", "")
        self.binance_secret_key = os.getenv("BINANCE_SECRET_KEY", "")

        # Telegram configuration
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        # Environment
        self.environment = os.getenv("ENVIRONMENT", "testnet")

        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./trading_bot.db")

    def _load_config(self) -> None:
        """Load configuration from config.yaml file."""
        config_path = self.project_root / "config.yaml"

        # If config.yaml doesn't exist, try config.yaml.example
        if not config_path.exists():
            config_path = self.project_root / "config.yaml.example"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found. Please create config.yaml "
                f"in {self.project_root}"
            )

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Exchange settings
        exchange_config = config.get('exchange', {})
        self.exchange_name = exchange_config.get('name', 'binance')
        self.exchange_testnet = exchange_config.get('testnet', True)
        self.rate_limit_delay = exchange_config.get('rate_limit_delay', 0.1)
        self.enable_rate_limit = exchange_config.get('enable_rate_limit', True)

        # Trading settings
        trading_config = config.get('trading', {})
        self.trading_pairs = trading_config.get('pairs', ['BTCUSDT'])
        self.timeframes = trading_config.get('timeframes', ['5m'])
        self.default_timeframe = trading_config.get('default_timeframe', '5m')
        self.lookback_periods = trading_config.get('lookback_periods', 200)

        # Strategy settings
        strategy_config = config.get('strategy', {})
        self.strategy_name = strategy_config.get('name', 'ma_crossover')
        self.strategy_params = strategy_config.get('parameters', {})

        # Risk management settings
        risk_config = config.get('risk', {})
        self.max_position_size_percent = risk_config.get(
            'max_position_size_percent', DEFAULT_MAX_POSITION_SIZE_PERCENT
        )
        self.position_sizing_method = risk_config.get('position_sizing_method', 'fixed')
        self.stop_loss_percent = risk_config.get('stop_loss_percent', DEFAULT_STOP_LOSS_PERCENT)
        self.take_profit_percent = risk_config.get('take_profit_percent', DEFAULT_TAKE_PROFIT_PERCENT)
        self.trailing_stop_percent = risk_config.get('trailing_stop_percent', 1.5)
        self.use_trailing_stop = risk_config.get('use_trailing_stop', True)
        self.max_concurrent_positions = risk_config.get('max_concurrent_positions', 3)
        self.max_allocation_per_asset = risk_config.get('max_allocation_per_asset', 30)
        self.daily_loss_limit_percent = risk_config.get('daily_loss_limit_percent', 5.0)
        self.max_drawdown_percent = risk_config.get('max_drawdown_percent', 20.0)
        self.enable_circuit_breaker = risk_config.get('enable_circuit_breaker', True)
        self.circuit_breaker_volatility_threshold = risk_config.get(
            'circuit_breaker_volatility_threshold', 10
        )

        # Backtesting settings
        backtest_config = config.get('backtesting', {})
        self.backtest_start_date = backtest_config.get('start_date', '2024-01-01')
        self.backtest_end_date = backtest_config.get('end_date', '2025-01-01')
        self.initial_capital = backtest_config.get('initial_capital', DEFAULT_INITIAL_CAPITAL)
        self.commission = backtest_config.get('commission', DEFAULT_COMMISSION)
        self.slippage = backtest_config.get('slippage', DEFAULT_SLIPPAGE)
        self.save_trades = backtest_config.get('save_trades', True)
        self.generate_report = backtest_config.get('generate_report', True)

        # Monitoring settings
        monitoring_config = config.get('monitoring', {})
        self.log_level = monitoring_config.get('log_level', 'INFO')
        self.log_to_file = monitoring_config.get('log_to_file', True)
        self.log_to_console = monitoring_config.get('log_to_console', True)
        self.max_log_file_size_mb = monitoring_config.get('max_log_file_size_mb', 10)
        self.log_backup_count = monitoring_config.get('log_backup_count', 5)
        self.telegram_alerts = monitoring_config.get('telegram_alerts', True)
        self.alert_on_trade = monitoring_config.get('alert_on_trade', True)
        self.alert_on_error = monitoring_config.get('alert_on_error', True)
        self.alert_on_daily_summary = monitoring_config.get('alert_on_daily_summary', True)
        self.daily_summary_time = monitoring_config.get('daily_summary_time', '23:00')
        self.health_check_interval = monitoring_config.get('health_check_interval', 300)
        self.dashboard_update_interval = monitoring_config.get('dashboard_update_interval', 60)

        # Bot settings
        bot_config = config.get('bot', {})
        mode_str = bot_config.get('mode', 'paper')
        self.bot_mode = TradingMode(mode_str)
        self.save_state_on_exit = bot_config.get('save_state_on_exit', True)
        self.load_state_on_start = bot_config.get('load_state_on_start', True)
        self.auto_restart_on_error = bot_config.get('auto_restart_on_error', True)
        self.max_restart_attempts = bot_config.get('max_restart_attempts', 3)
        self.restart_delay_seconds = bot_config.get('restart_delay_seconds', 60)
        self.update_interval_seconds = bot_config.get('update_interval_seconds', 60)

    def _validate(self) -> None:
        """Validate configuration settings."""
        # Validate trading pairs
        if not self.trading_pairs:
            raise ValueError("At least one trading pair must be specified in config")

        # Validate timeframes
        if not self.timeframes:
            raise ValueError("At least one timeframe must be specified in config")

        # Validate risk parameters
        if self.max_position_size_percent <= 0 or self.max_position_size_percent > 100:
            raise ValueError("max_position_size_percent must be between 0 and 100")

        if self.stop_loss_percent <= 0:
            raise ValueError("stop_loss_percent must be positive")

        if self.take_profit_percent <= 0:
            raise ValueError("take_profit_percent must be positive")

        if self.max_concurrent_positions <= 0:
            raise ValueError("max_concurrent_positions must be positive")

        # Warn if API keys are not set for live trading
        if self.bot_mode == TradingMode.LIVE:
            if not self.binance_api_key or not self.binance_secret_key:
                raise ValueError(
                    "Binance API keys must be set in .env file for live trading"
                )

    def is_live_mode(self) -> bool:
        """Check if bot is running in live trading mode."""
        return self.bot_mode == TradingMode.LIVE

    def is_paper_mode(self) -> bool:
        """Check if bot is running in paper trading mode."""
        return self.bot_mode == TradingMode.PAPER

    def is_dry_run_mode(self) -> bool:
        """Check if bot is running in dry run mode."""
        return self.bot_mode == TradingMode.DRY_RUN

    def get_strategy_param(self, param_name: str, default: Any = None) -> Any:
        """Get a strategy parameter with optional default value."""
        return self.strategy_params.get(param_name, default)

    def __repr__(self) -> str:
        """String representation of settings."""
        return (
            f"Settings(\n"
            f"  Environment: {self.environment}\n"
            f"  Bot Mode: {self.bot_mode.value}\n"
            f"  Exchange: {self.exchange_name} (testnet={self.exchange_testnet})\n"
            f"  Trading Pairs: {self.trading_pairs}\n"
            f"  Strategy: {self.strategy_name}\n"
            f"  Max Position Size: {self.max_position_size_percent}%\n"
            f"  Stop Loss: {self.stop_loss_percent}%\n"
            f"  Take Profit: {self.take_profit_percent}%\n"
            f")"
        )


# Global settings instance
def get_settings() -> Settings:
    """Get the global settings instance."""
    return Settings()
