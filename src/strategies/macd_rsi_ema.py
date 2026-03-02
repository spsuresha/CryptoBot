"""
MACD + RSI + EMA Strategy
Combines three powerful indicators for daily trading
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class MacdRsiEmaStrategy(BaseStrategy):
    """
    Strategy combining MACD, RSI, and EMA indicators for daily timeframe.

    Entry Logic:
    - LONG: EMA fast > EMA slow (bullish trend) AND
            MACD line > Signal line (momentum) AND
            RSI > oversold threshold (not oversold) AND
            RSI < overbought threshold (not overbought)

    - SHORT: EMA fast < EMA slow (bearish trend) AND
             MACD line < Signal line (momentum down) AND
             RSI < overbought threshold (not overbought) AND
             RSI > oversold threshold (not oversold)

    Exit Logic:
    - ATR-based stop loss and take profit
    - Exit when signals reverse
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__()

        # EMA parameters
        self.ema_fast = parameters.get('ema_fast', 12)
        self.ema_slow = parameters.get('ema_slow', 26)

        # MACD parameters
        self.macd_fast = parameters.get('macd_fast', 12)
        self.macd_slow = parameters.get('macd_slow', 26)
        self.macd_signal = parameters.get('macd_signal', 9)

        # RSI parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_oversold = parameters.get('rsi_oversold', 30)
        self.rsi_overbought = parameters.get('rsi_overbought', 70)

        # Risk management
        self.atr_period = parameters.get('atr_period', 14)
        self.atr_stop_multiplier = parameters.get('atr_stop_multiplier', 2.0)
        self.atr_target_multiplier = parameters.get('atr_target_multiplier', 4.0)

        # Filter: only trade if RSI is in active zone
        self.use_rsi_filter = parameters.get('use_rsi_filter', True)
        # Filter: require MACD histogram to be positive/negative
        self.use_histogram_filter = parameters.get('use_histogram_filter', True)

        logger.info("Initialized MacdRsiEmaStrategy")
        logger.info(f"EMA: {self.ema_fast}/{self.ema_slow}")
        logger.info(f"MACD: {self.macd_fast}/{self.macd_slow}/{self.macd_signal}")
        logger.info(f"RSI: {self.rsi_period} (oversold: {self.rsi_oversold}, overbought: {self.rsi_overbought})")
        logger.info(f"ATR stops: {self.atr_stop_multiplier}x / {self.atr_target_multiplier}x")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()

        # EMA indicators
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()

        # MACD indicator
        exp1 = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # RSI indicator
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # ATR for stops
        df['atr'] = self._calculate_atr(df, self.atr_period)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on indicators."""
        df = df.copy()

        # Initialize signals
        df['signal'] = 0
        df['position'] = 0

        # LONG conditions
        ema_bullish = df['ema_fast'] > df['ema_slow']
        macd_bullish = df['macd'] > df['macd_signal']
        rsi_not_oversold = df['rsi'] > self.rsi_oversold
        rsi_not_overbought = df['rsi'] < self.rsi_overbought

        # Optional filters
        if self.use_histogram_filter:
            histogram_positive = df['macd_histogram'] > 0
        else:
            histogram_positive = True

        if self.use_rsi_filter:
            rsi_active = (df['rsi'] > self.rsi_oversold) & (df['rsi'] < self.rsi_overbought)
        else:
            rsi_active = True

        long_condition = (
            ema_bullish &
            macd_bullish &
            rsi_not_oversold &
            rsi_not_overbought &
            histogram_positive &
            rsi_active
        )

        # SHORT conditions
        ema_bearish = df['ema_fast'] < df['ema_slow']
        macd_bearish = df['macd'] < df['macd_signal']

        if self.use_histogram_filter:
            histogram_negative = df['macd_histogram'] < 0
        else:
            histogram_negative = True

        short_condition = (
            ema_bearish &
            macd_bearish &
            rsi_not_oversold &
            rsi_not_overbought &
            histogram_negative &
            rsi_active
        )

        # Detect transitions (when condition becomes True)
        long_condition_prev = long_condition.shift(1).fillna(False)
        short_condition_prev = short_condition.shift(1).fillna(False)

        long_entry = long_condition & ~long_condition_prev
        short_entry = short_condition & ~short_condition_prev

        # Set signals
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_enter(self, row: pd.Series) -> bool:
        """Check if should enter a position."""
        return row['signal'] != 0

    def should_exit(self, row: pd.Series, position) -> bool:
        """Check if should exit current position."""
        if position is None:
            return False

        # Exit on opposite signal (when new signal appears)
        # Signal 1 = long, -1 = short, so exit long if signal becomes -1
        # We'll rely on stop loss and take profit for exits
        # Signal-based exits can be too frequent for daily timeframe
        return False

    def calculate_stop_loss(self, entry_price: float, side: str, atr: float) -> float:
        """Calculate stop loss based on ATR."""
        if side == 'long':
            return entry_price - (atr * self.atr_stop_multiplier)
        else:
            return entry_price + (atr * self.atr_stop_multiplier)

    def calculate_take_profit(self, entry_price: float, side: str, atr: float) -> float:
        """Calculate take profit based on ATR."""
        if side == 'long':
            return entry_price + (atr * self.atr_target_multiplier)
        else:
            return entry_price - (atr * self.atr_target_multiplier)

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr
