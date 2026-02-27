"""
Moving Average Crossover Strategy.

Buy signal: Fast MA crosses above Slow MA
Sell signal: Fast MA crosses below Slow MA
Optional filters: RSI, MACD, Bollinger Bands
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional

from .base_strategy import BaseStrategy
from .indicators import (
    calculate_sma,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    detect_ma_crossover,
    is_overbought,
    is_oversold,
    is_bullish_macd,
    is_bearish_macd,
)
from ..config.constants import SignalType

logger = logging.getLogger(__name__)


class MACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy with optional filters.
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize MA Crossover Strategy.

        Parameters:
            fast_period: Fast MA period (default: 10)
            slow_period: Slow MA period (default: 30)
            use_rsi_filter: Enable RSI filter (default: False)
            rsi_period: RSI period (default: 14)
            rsi_overbought: RSI overbought threshold (default: 70)
            rsi_oversold: RSI oversold threshold (default: 30)
            use_macd_filter: Enable MACD filter (default: False)
            macd_fast: MACD fast period (default: 12)
            macd_slow: MACD slow period (default: 26)
            macd_signal: MACD signal period (default: 9)
            use_bb_filter: Enable Bollinger Bands filter (default: False)
            bb_period: BB period (default: 20)
            bb_std: BB standard deviation (default: 2.0)
        """
        super().__init__(parameters)

        # MA parameters
        self.fast_period = self.get_parameter('fast_period', 10)
        self.slow_period = self.get_parameter('slow_period', 30)

        # RSI filter
        self.use_rsi_filter = self.get_parameter('use_rsi_filter', False)
        self.rsi_period = self.get_parameter('rsi_period', 14)
        self.rsi_overbought = self.get_parameter('rsi_overbought', 70)
        self.rsi_oversold = self.get_parameter('rsi_oversold', 30)

        # MACD filter
        self.use_macd_filter = self.get_parameter('use_macd_filter', False)
        self.macd_fast = self.get_parameter('macd_fast', 12)
        self.macd_slow = self.get_parameter('macd_slow', 26)
        self.macd_signal = self.get_parameter('macd_signal', 9)

        # Bollinger Bands filter
        self.use_bb_filter = self.get_parameter('use_bb_filter', False)
        self.bb_period = self.get_parameter('bb_period', 20)
        self.bb_std = self.get_parameter('bb_std', 2.0)

        logger.info(f"MA Crossover: fast={self.fast_period}, slow={self.slow_period}")
        if self.use_rsi_filter:
            logger.info(f"RSI Filter enabled: period={self.rsi_period}")
        if self.use_macd_filter:
            logger.info(f"MACD Filter enabled")
        if self.use_bb_filter:
            logger.info(f"BB Filter enabled: period={self.bb_period}")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all required indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with indicators
        """
        df = df.copy()

        # Calculate moving averages
        df['fast_ma'] = calculate_sma(df, self.fast_period)
        df['slow_ma'] = calculate_sma(df, self.slow_period)

        # RSI filter
        if self.use_rsi_filter:
            df['rsi'] = calculate_rsi(df, self.rsi_period)

        # MACD filter
        if self.use_macd_filter:
            macd, macd_signal, macd_hist = calculate_macd(
                df,
                fast=self.macd_fast,
                slow=self.macd_slow,
                signal=self.macd_signal
            )
            df['macd'] = macd
            df['macd_signal'] = macd_signal
            df['macd_hist'] = macd_hist

        # Bollinger Bands filter
        if self.use_bb_filter:
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
                df,
                period=self.bb_period,
                std=self.bb_std
            )
            df['bb_upper'] = bb_upper
            df['bb_middle'] = bb_middle
            df['bb_lower'] = bb_lower

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on MA crossover and filters.

        Args:
            df: DataFrame with indicators

        Returns:
            DataFrame with 'signal' column
        """
        df = df.copy()

        # Detect MA crossovers
        df['ma_crossover'] = detect_ma_crossover(df['fast_ma'], df['slow_ma'])

        # Initialize signal column
        df['signal'] = SignalType.HOLD.value

        # Apply crossover signals
        df.loc[df['ma_crossover'] == 1, 'signal'] = SignalType.BUY.value
        df.loc[df['ma_crossover'] == -1, 'signal'] = SignalType.SELL.value

        # Apply filters
        if self.use_rsi_filter:
            df = self._apply_rsi_filter(df)

        if self.use_macd_filter:
            df = self._apply_macd_filter(df)

        if self.use_bb_filter:
            df = self._apply_bb_filter(df)

        return df

    def _apply_rsi_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter signals based on RSI.

        Buy signals: Only when RSI is not overbought
        Sell signals: Only when RSI is not oversold
        """
        # Cancel buy signals if RSI is overbought
        overbought_mask = (df['signal'] == SignalType.BUY.value) & \
                         (df['rsi'] > self.rsi_overbought)
        df.loc[overbought_mask, 'signal'] = SignalType.HOLD.value

        # Cancel sell signals if RSI is oversold
        oversold_mask = (df['signal'] == SignalType.SELL.value) & \
                       (df['rsi'] < self.rsi_oversold)
        df.loc[oversold_mask, 'signal'] = SignalType.HOLD.value

        return df

    def _apply_macd_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter signals based on MACD.

        Buy signals: Only when MACD is bullish (MACD > Signal)
        Sell signals: Only when MACD is bearish (MACD < Signal)
        """
        # Cancel buy signals if MACD is bearish
        bearish_macd = (df['signal'] == SignalType.BUY.value) & \
                      (df['macd'] <= df['macd_signal'])
        df.loc[bearish_macd, 'signal'] = SignalType.HOLD.value

        # Cancel sell signals if MACD is bullish
        bullish_macd = (df['signal'] == SignalType.SELL.value) & \
                      (df['macd'] >= df['macd_signal'])
        df.loc[bullish_macd, 'signal'] = SignalType.HOLD.value

        return df

    def _apply_bb_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter signals based on Bollinger Bands.

        Buy signals: Only when price is not above upper band
        Sell signals: Only when price is not below lower band
        """
        # Cancel buy signals if price is above upper band
        above_upper = (df['signal'] == SignalType.BUY.value) & \
                     (df['close'] > df['bb_upper'])
        df.loc[above_upper, 'signal'] = SignalType.HOLD.value

        # Cancel sell signals if price is below lower band
        below_lower = (df['signal'] == SignalType.SELL.value) & \
                     (df['close'] < df['bb_lower'])
        df.loc[below_lower, 'signal'] = SignalType.HOLD.value

        return df

    def get_entry_reason(self, row: pd.Series) -> str:
        """Get detailed entry reason."""
        reasons = [f"Fast MA ({self.fast_period}) crossed above Slow MA ({self.slow_period})"]

        if self.use_rsi_filter and 'rsi' in row:
            reasons.append(f"RSI={row['rsi']:.1f}")

        if self.use_macd_filter and 'macd' in row:
            reasons.append(f"MACD bullish")

        if self.use_bb_filter:
            reasons.append(f"Price within BB")

        return ", ".join(reasons)

    def get_exit_reason(self, row: pd.Series) -> str:
        """Get detailed exit reason."""
        reasons = [f"Fast MA ({self.fast_period}) crossed below Slow MA ({self.slow_period})"]

        if self.use_rsi_filter and 'rsi' in row:
            reasons.append(f"RSI={row['rsi']:.1f}")

        if self.use_macd_filter and 'macd' in row:
            reasons.append(f"MACD bearish")

        return ", ".join(reasons)

    def validate_signal(self, row: pd.Series, signal_type: SignalType) -> bool:
        """
        Validate signal reliability.

        Args:
            row: Current candle data
            signal_type: Signal type to validate

        Returns:
            True if signal is valid
        """
        # Check if we have enough data for MAs
        if pd.isna(row.get('fast_ma')) or pd.isna(row.get('slow_ma')):
            return False

        # Check if filters have valid data
        if self.use_rsi_filter and pd.isna(row.get('rsi')):
            return False

        if self.use_macd_filter and (pd.isna(row.get('macd')) or pd.isna(row.get('macd_signal'))):
            return False

        if self.use_bb_filter and (pd.isna(row.get('bb_upper')) or pd.isna(row.get('bb_lower'))):
            return False

        return True
