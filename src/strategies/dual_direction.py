"""
Dual Direction Strategy - Trades BOTH long and short
Combines Buy Low Sell High (LONG) with Bearish Short (SHORT)
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class DualDirectionStrategy(BaseStrategy):
    """
    Dual Direction Strategy - Can trade both LONG and SHORT.

    LONG Entries:
    - RSI oversold (< 30)
    - Price near lower Bollinger Band
    - Stochastic oversold
    - Designed for buying dips

    SHORT Entries:
    - RSI overbought (> 70)
    - Price near upper Bollinger Band
    - Reversal patterns
    - Designed for shorting tops

    Never holds both LONG and SHORT simultaneously (no hedging)
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__()

        # LONG parameters (buy low sell high)
        self.long_rsi_oversold = parameters.get('long_rsi_oversold', 30)
        self.long_rsi_extreme = parameters.get('long_rsi_extreme', 20)
        self.long_stoch_oversold = parameters.get('long_stoch_oversold', 20)
        self.long_stop_loss_pct = parameters.get('long_stop_loss_pct', 10.0)
        self.long_take_profit_pct = parameters.get('long_take_profit_pct', 30.0)

        # SHORT parameters (bearish short)
        self.short_rsi_overbought = parameters.get('short_rsi_overbought', 70)
        self.short_stop_loss_pct = parameters.get('short_stop_loss_pct', 2.0)
        self.short_take_profit_pct = parameters.get('short_take_profit_pct', 4.0)

        # General parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.bb_period = parameters.get('bb_period', 20)
        self.bb_std = parameters.get('bb_std', 2.0)
        self.stoch_period = parameters.get('stoch_period', 14)
        self.atr_period = parameters.get('atr_period', 14)

        # Volume confirmation
        self.volume_ma_period = parameters.get('volume_ma_period', 20)
        self.require_volume_confirmation = parameters.get('require_volume_confirmation', True)
        self.min_volume_ratio = parameters.get('min_volume_ratio', 1.2)

        # Strategy mode
        self.enable_longs = parameters.get('enable_longs', True)
        self.enable_shorts = parameters.get('enable_shorts', True)

        logger.info(f"Initialized DualDirectionStrategy")
        logger.info(f"LONG: RSI<{self.long_rsi_oversold}, SL={self.long_stop_loss_pct}%, TP={self.long_take_profit_pct}%")
        logger.info(f"SHORT: RSI>{self.short_rsi_overbought}, SL={self.short_stop_loss_pct}%, TP={self.short_take_profit_pct}%")
        logger.info(f"Enabled: LONG={self.enable_longs}, SHORT={self.enable_shorts}")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for both directions."""
        df = df.copy()

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)

        # Distance from Bollinger Bands (percentage)
        df['dist_from_lower'] = ((df['close'] - df['bb_lower']) / df['bb_lower']) * 100
        df['dist_from_upper'] = ((df['bb_upper'] - df['close']) / df['bb_upper']) * 100

        # Stochastic Oscillator
        low_min = df['low'].rolling(window=self.stoch_period).min()
        high_max = df['high'].rolling(window=self.stoch_period).max()
        df['stoch'] = 100 * (df['close'] - low_min) / (high_max - low_min)

        # ATR for volatility
        df['atr'] = self._calculate_atr(df, self.atr_period)

        # Volume
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Candle patterns
        df['red_candle'] = df['close'] < df['open']
        df['green_candle'] = df['close'] > df['open']
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['body_size'] = abs(df['close'] - df['open'])

        # Reversal patterns
        df['bullish_reversal'] = df['green_candle'] & (df['lower_wick'] > df['body_size'] * 1.5)
        df['bearish_reversal'] = df['red_candle'] & (df['upper_wick'] > df['body_size'] * 1.5)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate both LONG and SHORT signals."""
        df = df.copy()
        df['signal'] = 0

        # ========== LONG SIGNALS (Buy Low) ==========
        if self.enable_longs:
            # Oversold conditions
            rsi_oversold = df['rsi'] < self.long_rsi_oversold
            extreme_oversold = df['rsi'] < self.long_rsi_extreme
            stoch_oversold = df['stoch'] < self.long_stoch_oversold
            near_lower_bb = df['dist_from_lower'] < 5  # Within 5% of lower band

            # Volume confirmation
            volume_confirm = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True

            # Multiple confirmation (2 of 3)
            oversold_score = rsi_oversold.astype(int) + stoch_oversold.astype(int) + near_lower_bb.astype(int)
            long_condition = (oversold_score >= 2) & volume_confirm

            # Extra strong signal for extreme oversold
            strong_long = extreme_oversold & stoch_oversold & volume_confirm

            # Detect new long signals
            long_signal = (long_condition | strong_long) & ~(long_condition | strong_long).shift(1).fillna(False)
            df.loc[long_signal, 'signal'] = 1  # LONG

        # ========== SHORT SIGNALS (Sell High) ==========
        if self.enable_shorts:
            # Overbought conditions
            rsi_overbought = df['rsi'] > self.short_rsi_overbought
            near_upper_bb = df['close'] >= df['bb_upper'] * 0.98
            bearish_pattern = df['bearish_reversal']

            # Volume confirmation
            volume_confirm = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True

            # Multiple confirmation
            short_condition = rsi_overbought & near_upper_bb & bearish_pattern & volume_confirm

            # Detect new short signals
            short_signal = short_condition & ~short_condition.shift(1).fillna(False)
            df.loc[short_signal, 'signal'] = -1  # SHORT

        return df

    def should_enter(self, row: pd.Series) -> bool:
        """Check if should enter a position (long or short)."""
        return row['signal'] != 0

    def should_exit(self, row: pd.Series, position) -> bool:
        """Check if should exit current position."""
        if position is None:
            return False

        # Exit LONG if becomes overbought
        if position.get('side') == 'long':
            if 'rsi' in row and row['rsi'] > 70:  # Overbought - take profit
                return True

        # Exit SHORT if becomes oversold
        if position.get('side') == 'short':
            if 'rsi' in row and row['rsi'] < 30:  # Oversold - cover short
                return True

        return False

    def calculate_stop_loss(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate stop loss based on position direction."""
        if side == 'long':
            return entry_price * (1 - self.long_stop_loss_pct / 100)
        else:  # short
            return entry_price * (1 + self.short_stop_loss_pct / 100)

    def calculate_take_profit(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate take profit based on position direction."""
        if side == 'long':
            return entry_price * (1 + self.long_take_profit_pct / 100)
        else:  # short
            return entry_price * (1 - self.short_take_profit_pct / 100)

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
