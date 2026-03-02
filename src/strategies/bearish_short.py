"""
Bearish Short Strategy - SHORT positions only for futures trading
Identifies overbought conditions, resistance rejections, and bearish momentum
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class BearishShortStrategy(BaseStrategy):
    """
    SHORT-ONLY strategy for futures trading.

    Enters SHORT when:
    - Price is overbought (RSI > 70)
    - Bearish EMA crossover occurs
    - Price rejects resistance levels
    - Volume confirms selling pressure
    - Bearish momentum detected

    Never takes LONG positions - only SHORTS
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__()

        # Strategy type
        self.strategy_type = parameters.get('strategy_type', 'rsi_overbought')

        # EMA parameters for trend
        self.ema_fast = parameters.get('ema_fast', 9)
        self.ema_slow = parameters.get('ema_slow', 21)
        self.ema_resistance = parameters.get('ema_resistance', 50)

        # RSI parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_overbought = parameters.get('rsi_overbought', 70)
        self.rsi_extreme_overbought = parameters.get('rsi_extreme_overbought', 80)

        # Bollinger Bands (for overbought detection)
        self.bb_period = parameters.get('bb_period', 20)
        self.bb_std = parameters.get('bb_std', 2.0)

        # ATR for volatility
        self.atr_period = parameters.get('atr_period', 14)

        # Volume parameters
        self.volume_ma_period = parameters.get('volume_ma_period', 20)
        self.min_volume_ratio = parameters.get('min_volume_ratio', 1.2)

        # Risk management
        self.stop_loss_atr_multiplier = parameters.get('stop_loss_atr_multiplier', 2.0)
        self.take_profit_atr_multiplier = parameters.get('take_profit_atr_multiplier', 3.0)

        # Fixed percentage stops (alternative)
        self.use_fixed_stops = parameters.get('use_fixed_stops', False)
        self.stop_loss_pct = parameters.get('stop_loss_pct', 2.0)
        self.take_profit_pct = parameters.get('take_profit_pct', 4.0)

        # Filters
        self.require_bearish_trend = parameters.get('require_bearish_trend', True)
        self.require_volume_confirmation = parameters.get('require_volume_confirmation', True)
        self.require_ema_resistance = parameters.get('require_ema_resistance', True)

        logger.info(f"Initialized BearishShortStrategy - Type: {self.strategy_type}")
        logger.info(f"SHORT ONLY - No longs will be taken")
        logger.info(f"RSI Overbought: {self.rsi_overbought}")
        logger.info(f"Stops: {self.stop_loss_atr_multiplier}x ATR SL, {self.take_profit_atr_multiplier}x ATR TP")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()

        # EMAs
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        df['ema_resistance'] = df['close'].ewm(span=self.ema_resistance, adjust=False).mean()

        # EMA signals
        df['ema_bearish'] = df['ema_fast'] < df['ema_slow']  # Bearish cross
        df['below_resistance'] = df['close'] < df['ema_resistance']  # Below major EMA

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)

        # At upper band (overbought)
        df['at_upper_bb'] = df['close'] >= df['bb_upper'] * 0.98

        # ATR
        df['atr'] = self._calculate_atr(df, self.atr_period)

        # Volume
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Price momentum (negative = bearish)
        df['momentum'] = df['close'].pct_change(5) * 100

        # Candle analysis
        df['red_candle'] = df['close'] < df['open']
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['body_size'] = abs(df['close'] - df['open'])

        # Rejection at resistance (long upper wick)
        df['resistance_rejection'] = (df['upper_wick'] > df['body_size'] * 1.5) & df['red_candle']

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate SHORT signals only."""
        df = df.copy()
        df['signal'] = 0

        if self.strategy_type == 'rsi_overbought':
            df = self._rsi_overbought_short(df)
        elif self.strategy_type == 'ema_rejection':
            df = self._ema_rejection_short(df)
        elif self.strategy_type == 'bb_reversal':
            df = self._bb_reversal_short(df)
        elif self.strategy_type == 'combo_bearish':
            df = self._combo_bearish_short(df)
        else:
            df = self._rsi_overbought_short(df)

        return df

    def _rsi_overbought_short(self, df: pd.DataFrame) -> pd.DataFrame:
        """SHORT when RSI is overbought."""
        # SHORT conditions
        rsi_overbought = df['rsi'] > self.rsi_overbought
        bearish_trend = df['ema_bearish'] if self.require_bearish_trend else True
        volume_confirm = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True

        short_condition = rsi_overbought & bearish_trend & volume_confirm

        # Detect new signal (transition)
        short_signal = short_condition & ~short_condition.shift(1).fillna(False)

        df.loc[short_signal, 'signal'] = -1  # SHORT

        return df

    def _ema_rejection_short(self, df: pd.DataFrame) -> pd.DataFrame:
        """SHORT when price rejects EMA resistance."""
        # Price touches EMA resistance and rejects
        touches_ema = (df['high'] >= df['ema_resistance']) & (df['close'] < df['ema_resistance'])
        rejection = df['resistance_rejection']
        bearish_trend = df['ema_bearish'] if self.require_bearish_trend else True
        volume_confirm = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True

        short_condition = touches_ema & rejection & bearish_trend & volume_confirm

        # Detect new signal
        short_signal = short_condition & ~short_condition.shift(1).fillna(False)

        df.loc[short_signal, 'signal'] = -1  # SHORT

        return df

    def _bb_reversal_short(self, df: pd.DataFrame) -> pd.DataFrame:
        """SHORT when price touches upper Bollinger Band and reverses."""
        # At upper band and shows reversal
        at_upper = df['at_upper_bb']
        reversal = df['red_candle'] & (df['resistance_rejection'])
        rsi_overbought = df['rsi'] > self.rsi_overbought
        volume_confirm = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True

        short_condition = at_upper & reversal & rsi_overbought & volume_confirm

        # Detect new signal
        short_signal = short_condition & ~short_condition.shift(1).fillna(False)

        df.loc[short_signal, 'signal'] = -1  # SHORT

        return df

    def _combo_bearish_short(self, df: pd.DataFrame) -> pd.DataFrame:
        """SHORT when multiple bearish indicators align (2 of 3)."""
        # Three bearish conditions
        rsi_condition = df['rsi'] > self.rsi_overbought
        ema_condition = df['ema_bearish'] & (df['close'] < df['ema_resistance'])
        bb_condition = df['at_upper_bb'] & df['resistance_rejection']

        # Count how many are true
        bearish_score = rsi_condition.astype(int) + ema_condition.astype(int) + bb_condition.astype(int)

        # Require 2 of 3
        short_condition = bearish_score >= 2

        if self.require_volume_confirmation:
            short_condition = short_condition & (df['volume_ratio'] > self.min_volume_ratio)

        # Detect new signal
        short_signal = short_condition & ~short_condition.shift(1).fillna(False)

        df.loc[short_signal, 'signal'] = -1  # SHORT

        return df

    def should_enter(self, row: pd.Series) -> bool:
        """Check if should enter a SHORT position."""
        return row['signal'] == -1  # Only SHORT signals

    def should_exit(self, row: pd.Series, position) -> bool:
        """Check if should exit current SHORT position."""
        if position is None:
            return False

        # Exit SHORT if price becomes oversold (potential bounce)
        if position.get('side') == 'short':
            if 'rsi' in row and row['rsi'] < 30:  # Oversold - exit short
                return True

        return False

    def calculate_stop_loss(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate stop loss for SHORT positions."""
        if self.use_fixed_stops:
            # Fixed percentage stops
            if side == 'short':
                return entry_price * (1 + self.stop_loss_pct / 100)  # Stop above entry
            else:
                return entry_price * (1 - self.stop_loss_pct / 100)
        else:
            # ATR-based stops
            if row is not None and 'atr' in row:
                atr = row['atr']
                if side == 'short':
                    return entry_price + (atr * self.stop_loss_atr_multiplier)  # Stop above
                else:
                    return entry_price - (atr * self.stop_loss_atr_multiplier)
            else:
                # Fallback
                if side == 'short':
                    return entry_price * (1 + self.stop_loss_pct / 100)
                else:
                    return entry_price * (1 - self.stop_loss_pct / 100)

    def calculate_take_profit(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate take profit for SHORT positions."""
        if self.use_fixed_stops:
            # Fixed percentage targets
            if side == 'short':
                return entry_price * (1 - self.take_profit_pct / 100)  # Profit below entry
            else:
                return entry_price * (1 + self.take_profit_pct / 100)
        else:
            # ATR-based targets
            if row is not None and 'atr' in row:
                atr = row['atr']
                if side == 'short':
                    return entry_price - (atr * self.take_profit_atr_multiplier)  # Profit below
                else:
                    return entry_price + (atr * self.take_profit_atr_multiplier)
            else:
                # Fallback
                if side == 'short':
                    return entry_price * (1 - self.take_profit_pct / 100)
                else:
                    return entry_price * (1 + self.take_profit_pct / 100)

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
