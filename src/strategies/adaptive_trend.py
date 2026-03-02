"""
Adaptive Trend-Following Strategy
Optimized for trending markets with dynamic risk management.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class AdaptiveTrendStrategy(BaseStrategy):
    """
    Trend-following strategy that adapts to market conditions.

    Features:
    - Multiple timeframe confirmation
    - Dynamic stop-loss using ATR
    - Momentum filters
    - Trend strength validation
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """Initialize the adaptive trend strategy."""
        super().__init__(parameters)

        # Moving average parameters
        self.fast_ma = self.parameters.get('fast_ma', 10)
        self.slow_ma = self.parameters.get('slow_ma', 30)
        self.trend_ma = self.parameters.get('trend_ma', 100)

        # Momentum parameters
        self.rsi_period = self.parameters.get('rsi_period', 14)
        self.rsi_overbought = self.parameters.get('rsi_overbought', 70)
        self.rsi_oversold = self.parameters.get('rsi_oversold', 30)

        # ADX for trend strength
        self.adx_period = self.parameters.get('adx_period', 14)
        self.adx_threshold = self.parameters.get('adx_threshold', 25)

        # Risk management
        self.atr_period = self.parameters.get('atr_period', 14)
        self.atr_stop_multiplier = self.parameters.get('atr_stop_multiplier', 2.0)
        self.atr_target_multiplier = self.parameters.get('atr_target_multiplier', 3.0)

        # Fixed stop/target fallback
        self.stop_loss_pct = self.parameters.get('stop_loss_pct', 2.0)
        self.take_profit_pct = self.parameters.get('take_profit_pct', 4.0)

        logger.info("Initialized AdaptiveTrendStrategy")
        logger.info(f"Fast MA: {self.fast_ma}, Slow MA: {self.slow_ma}, Trend MA: {self.trend_ma}")
        logger.info(f"ADX threshold: {self.adx_threshold}")
        logger.info(f"ATR stops: {self.atr_stop_multiplier}x / {self.atr_target_multiplier}x")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators and add them to the dataframe."""
        df = df.copy()

        # Moving averages
        df['fast_ma'] = df['close'].ewm(span=self.fast_ma, adjust=False).mean()
        df['slow_ma'] = df['close'].ewm(span=self.slow_ma, adjust=False).mean()
        df['trend_ma'] = df['close'].rolling(window=self.trend_ma).mean()

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # ATR for dynamic stops
        df['atr'] = self._calculate_atr(df, self.atr_period)

        # ADX for trend strength
        df = self._calculate_adx(df, self.adx_period)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on indicators."""
        df = self._generate_signals(df)
        return df

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
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def _calculate_adx(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        """Calculate ADX (Average Directional Index) for trend strength."""
        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate smoothed +DI and -DI
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        df['adx'] = adx
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di

        return df

    def _generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on trend and momentum."""

        # Trend conditions
        df['uptrend'] = df['fast_ma'] > df['slow_ma']
        df['downtrend'] = df['fast_ma'] < df['slow_ma']
        df['above_trend_ma'] = df['close'] > df['trend_ma']
        df['below_trend_ma'] = df['close'] < df['trend_ma']

        # Trend strength
        df['strong_trend'] = df['adx'] > self.adx_threshold

        # MA crossover
        df['ma_cross_up'] = (df['fast_ma'] > df['slow_ma']) & (df['fast_ma'].shift(1) <= df['slow_ma'].shift(1))
        df['ma_cross_down'] = (df['fast_ma'] < df['slow_ma']) & (df['fast_ma'].shift(1) >= df['slow_ma'].shift(1))

        # RSI filters (not overbought/oversold in extreme)
        df['rsi_not_overbought'] = df['rsi'] < self.rsi_overbought
        df['rsi_not_oversold'] = df['rsi'] > self.rsi_oversold

        # LONG entry: MA cross up + above trend MA + strong trend + RSI not overbought
        long_entry = (
            df['ma_cross_up'] &
            df['above_trend_ma'] &
            df['strong_trend'] &
            df['rsi_not_overbought']
        )

        # SHORT entry: MA cross down + below trend MA + strong trend + RSI not oversold
        short_entry = (
            df['ma_cross_down'] &
            df['below_trend_ma'] &
            df['strong_trend'] &
            df['rsi_not_oversold']
        )

        # Exit conditions
        # LONG exit: MA cross down or RSI overbought
        long_exit = df['ma_cross_down'] | (df['rsi'] > self.rsi_overbought)

        # SHORT exit: MA cross up or RSI oversold
        short_exit = df['ma_cross_up'] | (df['rsi'] < self.rsi_oversold)

        # Assign signals
        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        df['exit_long'] = long_exit
        df['exit_short'] = short_exit

        # Calculate dynamic stops based on ATR
        df['atr_stop_long'] = df['close'] - (df['atr'] * self.atr_stop_multiplier)
        df['atr_target_long'] = df['close'] + (df['atr'] * self.atr_target_multiplier)
        df['atr_stop_short'] = df['close'] + (df['atr'] * self.atr_stop_multiplier)
        df['atr_target_short'] = df['close'] - (df['atr'] * self.atr_target_multiplier)

        return df

    def should_enter_long(self, row: pd.Series) -> bool:
        """Check if should enter long position."""
        return row['signal'] == 1

    def should_enter_short(self, row: pd.Series) -> bool:
        """Check if should enter short position."""
        return row['signal'] == -1

    def should_exit_long(self, row: pd.Series, entry_price: float) -> bool:
        """Check if should exit long position."""
        return row['exit_long']

    def should_exit_short(self, row: pd.Series, entry_price: float) -> bool:
        """Check if should exit short position."""
        return row['exit_short']

    def get_stop_loss(self, row: pd.Series, side: str) -> float:
        """Get stop loss price based on ATR or fixed percentage."""
        if side == 'long':
            # Use ATR-based stop if available, otherwise percentage
            if pd.notna(row.get('atr_stop_long')):
                return row['atr_stop_long']
            else:
                return row['close'] * (1 - self.stop_loss_pct / 100)
        else:  # short
            if pd.notna(row.get('atr_stop_short')):
                return row['atr_stop_short']
            else:
                return row['close'] * (1 + self.stop_loss_pct / 100)

    def get_take_profit(self, row: pd.Series, side: str) -> float:
        """Get take profit price based on ATR or fixed percentage."""
        if side == 'long':
            # Use ATR-based target if available, otherwise percentage
            if pd.notna(row.get('atr_target_long')):
                return row['atr_target_long']
            else:
                return row['close'] * (1 + self.take_profit_pct / 100)
        else:  # short
            if pd.notna(row.get('atr_target_short')):
                return row['atr_target_short']
            else:
                return row['close'] * (1 - self.take_profit_pct / 100)

    def get_entry_reason(self, row: pd.Series) -> str:
        """Get reason for entry."""
        if row['signal'] == 1:
            return f"LONG: MA crossover + trend strength (ADX: {row['adx']:.1f})"
        elif row['signal'] == -1:
            return f"SHORT: MA crossover + trend strength (ADX: {row['adx']:.1f})"
        return "No signal"

    def get_exit_reason(self, row: pd.Series) -> str:
        """Get reason for exit."""
        if row.get('exit_long', False):
            return "EXIT LONG: Trend reversal or RSI overbought"
        elif row.get('exit_short', False):
            return "EXIT SHORT: Trend reversal or RSI oversold"
        return "No exit signal"
