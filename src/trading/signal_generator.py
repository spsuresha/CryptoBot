"""
Signal generator for real-time trading signals.
"""
import logging
from typing import Dict, Optional, Tuple
import pandas as pd

from ..strategies.base_strategy import BaseStrategy
from ..exchange.data_fetcher import DataFetcher
from ..config.settings import Settings
from ..config.constants import SignalType

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generate trading signals from strategy and market data.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        data_fetcher: DataFetcher,
        settings: Optional[Settings] = None
    ):
        """
        Initialize signal generator.

        Args:
            strategy: Trading strategy
            data_fetcher: Data fetcher for market data
            settings: Application settings
        """
        self.strategy = strategy
        self.data_fetcher = data_fetcher
        self.settings = settings or Settings()
        self.last_signal_time: Dict[str, pd.Timestamp] = {}

    def generate_signal(
        self,
        symbol: str,
        timeframe: str,
        has_position: bool = False
    ) -> Tuple[SignalType, str, pd.Series]:
        """
        Generate trading signal for a symbol.

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            has_position: Whether currently holding position

        Returns:
            Tuple of (signal_type, reason, latest_bar_data)
        """
        try:
            # Fetch latest data
            df = self.data_fetcher.fetch_latest_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=self.settings.lookback_periods
            )

            if df.empty or len(df) < self.settings.lookback_periods:
                logger.warning(f"Insufficient data for {symbol}")
                return SignalType.HOLD, "Insufficient data", pd.Series()

            # Prepare data with indicators and signals
            df = self.strategy.prepare_data(df)

            # Get latest bar
            latest = df.iloc[-1]

            # Determine signal
            signal = SignalType(int(latest.get('signal', 0)))

            # Generate appropriate reason
            if signal == SignalType.BUY and not has_position:
                return SignalType.BUY, self.strategy.get_entry_reason(latest), latest

            elif signal == SignalType.SELL and has_position:
                return SignalType.SELL, self.strategy.get_exit_reason(latest), latest

            else:
                return SignalType.HOLD, "No actionable signal", latest

        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return SignalType.HOLD, f"Error: {e}", pd.Series()

    def should_enter_position(
        self,
        symbol: str,
        timeframe: str
    ) -> Tuple[bool, str, Optional[pd.Series]]:
        """
        Check if should enter a new position.

        Args:
            symbol: Trading pair
            timeframe: Timeframe

        Returns:
            Tuple of (should_enter, reason, bar_data)
        """
        signal, reason, bar_data = self.generate_signal(
            symbol, timeframe, has_position=False
        )

        if signal == SignalType.BUY:
            # Validate signal
            if not self.strategy.validate_signal(bar_data, SignalType.BUY):
                return False, "Signal validation failed", bar_data

            # Check if we recently signaled
            if self._is_recent_signal(symbol, bar_data):
                return False, "Recent signal already processed", bar_data

            self._update_signal_time(symbol, bar_data)
            return True, reason, bar_data

        return False, reason, bar_data

    def should_exit_position(
        self,
        symbol: str,
        timeframe: str,
        position: Dict
    ) -> Tuple[bool, str, Optional[pd.Series]]:
        """
        Check if should exit current position.

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            position: Current position data

        Returns:
            Tuple of (should_exit, reason, bar_data)
        """
        signal, reason, bar_data = self.generate_signal(
            symbol, timeframe, has_position=True
        )

        if signal == SignalType.SELL:
            # Additional validation using strategy
            if self.strategy.should_exit(bar_data, position):
                self._update_signal_time(symbol, bar_data)
                return True, reason, bar_data

        return False, reason, bar_data

    def get_current_market_data(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Get current market data with indicators.

        Args:
            symbol: Trading pair
            timeframe: Timeframe

        Returns:
            DataFrame with market data and indicators
        """
        try:
            df = self.data_fetcher.fetch_latest_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=self.settings.lookback_periods
            )

            if df.empty:
                return None

            # Add indicators
            df = self.strategy.calculate_indicators(df)

            return df

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None

    def _is_recent_signal(self, symbol: str, bar_data: pd.Series) -> bool:
        """
        Check if we recently processed a signal for this symbol.

        Args:
            symbol: Trading pair
            bar_data: Current bar data

        Returns:
            True if signal is recent
        """
        if symbol not in self.last_signal_time:
            return False

        if not hasattr(bar_data, 'name') or bar_data.name is None:
            return False

        current_time = bar_data.name
        last_time = self.last_signal_time[symbol]

        # Avoid duplicate signals on same bar
        return current_time == last_time

    def _update_signal_time(self, symbol: str, bar_data: pd.Series) -> None:
        """Update last signal time for symbol."""
        if hasattr(bar_data, 'name') and bar_data.name is not None:
            self.last_signal_time[symbol] = bar_data.name
