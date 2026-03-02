"""
Futures Momentum Strategy - Short-term scalping/momentum trading
Designed for BTC/USDT futures with high volatility and quick moves
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class FuturesMomentumStrategy(BaseStrategy):
    """
    Momentum-based strategy for futures trading.

    Uses:
    - EMA crossovers for trend direction
    - RSI for momentum confirmation
    - ATR for volatility filtering (only trade in high volatility)
    - Volume confirmation
    - Tight stops and quick profits for scalping

    Can go both LONG and SHORT (futures trading)
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__()

        # EMA parameters
        self.ema_fast = parameters.get('ema_fast', 9)
        self.ema_slow = parameters.get('ema_slow', 21)
        self.ema_trend = parameters.get('ema_trend', 50)

        # RSI parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_bullish = parameters.get('rsi_bullish', 55)  # Above = bullish momentum
        self.rsi_bearish = parameters.get('rsi_bearish', 45)  # Below = bearish momentum

        # ATR (volatility) parameters
        self.atr_period = parameters.get('atr_period', 14)
        self.min_atr_multiplier = parameters.get('min_atr_multiplier', 1.0)  # Minimum volatility required

        # Volume parameters
        self.volume_ma_period = parameters.get('volume_ma_period', 20)
        self.min_volume_ratio = parameters.get('min_volume_ratio', 1.2)  # Volume must be 1.2x average

        # Risk management
        self.stop_loss_atr_multiplier = parameters.get('stop_loss_atr_multiplier', 2.0)
        self.take_profit_atr_multiplier = parameters.get('take_profit_atr_multiplier', 3.0)

        # Alternative: fixed percentage stops
        self.use_fixed_stops = parameters.get('use_fixed_stops', False)
        self.stop_loss_pct = parameters.get('stop_loss_pct', 1.5)
        self.take_profit_pct = parameters.get('take_profit_pct', 3.0)

        # Filters
        self.require_trend_alignment = parameters.get('require_trend_alignment', True)
        self.require_volume_confirmation = parameters.get('require_volume_confirmation', True)
        self.require_volatility_filter = parameters.get('require_volatility_filter', True)

        logger.info(f"Initialized FuturesMomentumStrategy")
        logger.info(f"EMAs: {self.ema_fast}/{self.ema_slow}/{self.ema_trend}")
        logger.info(f"RSI: {self.rsi_period} (Bull>{self.rsi_bullish}, Bear<{self.rsi_bearish})")
        logger.info(f"Stops: {self.stop_loss_atr_multiplier}x ATR SL, {self.take_profit_atr_multiplier}x ATR TP")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()

        # EMAs
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        df['ema_trend'] = df['close'].ewm(span=self.ema_trend, adjust=False).mean()

        # EMA crossover signals
        df['ema_cross'] = 0
        df.loc[df['ema_fast'] > df['ema_slow'], 'ema_cross'] = 1   # Bullish
        df.loc[df['ema_fast'] < df['ema_slow'], 'ema_cross'] = -1  # Bearish

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # ATR for volatility and dynamic stops
        df['atr'] = self._calculate_atr(df, self.atr_period)

        # ATR as percentage of price (for filtering)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        # Volume indicators
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Momentum indicators
        df['price_momentum'] = df['close'].pct_change(5) * 100  # 5-period momentum

        # Trend strength
        df['trend_strength'] = ((df['close'] - df['ema_trend']) / df['ema_trend']) * 100

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on momentum and breakouts."""
        df = df.copy()
        df['signal'] = 0

        # === LONG CONDITIONS ===
        long_ema_cross = (df['ema_cross'] == 1) & (df['ema_cross'].shift(1) != 1)  # Fresh bullish cross
        long_rsi = df['rsi'] > self.rsi_bullish  # Bullish momentum
        long_volume = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True
        long_volatility = df['atr_pct'] > self.min_atr_multiplier if self.require_volatility_filter else True
        long_trend = df['close'] > df['ema_trend'] if self.require_trend_alignment else True

        long_condition = long_ema_cross & long_rsi & long_volume & long_volatility & long_trend

        # === SHORT CONDITIONS ===
        short_ema_cross = (df['ema_cross'] == -1) & (df['ema_cross'].shift(1) != -1)  # Fresh bearish cross
        short_rsi = df['rsi'] < self.rsi_bearish  # Bearish momentum
        short_volume = df['volume_ratio'] > self.min_volume_ratio if self.require_volume_confirmation else True
        short_volatility = df['atr_pct'] > self.min_atr_multiplier if self.require_volatility_filter else True
        short_trend = df['close'] < df['ema_trend'] if self.require_trend_alignment else True

        short_condition = short_ema_cross & short_rsi & short_volume & short_volatility & short_trend

        # Assign signals
        df.loc[long_condition, 'signal'] = 1   # LONG
        df.loc[short_condition, 'signal'] = -1  # SHORT

        return df

    def should_enter(self, row: pd.Series) -> bool:
        """Check if should enter a position."""
        return row['signal'] != 0

    def should_exit(self, row: pd.Series, position) -> bool:
        """Check if should exit current position."""
        if position is None:
            return False

        # Exit on opposite signal
        if position.get('side') == 'long' and row['signal'] == -1:
            return True
        if position.get('side') == 'short' and row['signal'] == 1:
            return True

        return False

    def calculate_stop_loss(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate stop loss based on ATR or fixed percentage."""
        if self.use_fixed_stops:
            # Fixed percentage stops
            if side == 'long':
                return entry_price * (1 - self.stop_loss_pct / 100)
            else:
                return entry_price * (1 + self.stop_loss_pct / 100)
        else:
            # ATR-based stops
            if row is not None and 'atr' in row:
                atr = row['atr']
                if side == 'long':
                    return entry_price - (atr * self.stop_loss_atr_multiplier)
                else:
                    return entry_price + (atr * self.stop_loss_atr_multiplier)
            else:
                # Fallback to fixed if ATR not available
                if side == 'long':
                    return entry_price * (1 - self.stop_loss_pct / 100)
                else:
                    return entry_price * (1 + self.stop_loss_pct / 100)

    def calculate_take_profit(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate take profit based on ATR or fixed percentage."""
        if self.use_fixed_stops:
            # Fixed percentage targets
            if side == 'long':
                return entry_price * (1 + self.take_profit_pct / 100)
            else:
                return entry_price * (1 - self.take_profit_pct / 100)
        else:
            # ATR-based targets
            if row is not None and 'atr' in row:
                atr = row['atr']
                if side == 'long':
                    return entry_price + (atr * self.take_profit_atr_multiplier)
                else:
                    return entry_price - (atr * self.take_profit_atr_multiplier)
            else:
                # Fallback to fixed if ATR not available
                if side == 'long':
                    return entry_price * (1 + self.take_profit_pct / 100)
                else:
                    return entry_price * (1 - self.take_profit_pct / 100)

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
