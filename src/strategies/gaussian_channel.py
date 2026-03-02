"""
Gaussian Channel Strategy - Mean-reversion using Gaussian-weighted bands
Based on the Gaussian Channel indicator concept with smooth price filtering
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class GaussianChannelStrategy(BaseStrategy):
    """
    Gaussian Channel Strategy - Buy at lower band, sell at upper band.

    Uses Gaussian (normal distribution) weighting to create smooth moving average
    and volatility bands. More responsive than simple MA but smoother than EMA.

    Entry signals:
    - BUY: Price touches or crosses below lower Gaussian band
    - SELL: Price touches or crosses above upper Gaussian band

    Exit signals:
    - Stop loss and take profit based on percentage or ATR
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__()

        # Gaussian Channel parameters
        self.period = parameters.get('period', 20)  # Window for Gaussian calculation
        self.poles = parameters.get('poles', 4)  # Number of poles (smoothness)
        self.mult = parameters.get('mult', 2.0)  # Band multiplier (like BB std dev)

        # Alternative: Use standard deviation bands
        self.use_std_bands = parameters.get('use_std_bands', True)
        self.std_mult = parameters.get('std_mult', 2.0)

        # Entry confirmation
        self.require_close_outside = parameters.get('require_close_outside', True)
        self.entry_buffer_pct = parameters.get('entry_buffer_pct', 0.5)  # % inside band to trigger

        # Risk management
        self.stop_loss_pct = parameters.get('stop_loss_pct', 10.0)
        self.take_profit_pct = parameters.get('take_profit_pct', 20.0)
        self.use_atr_stops = parameters.get('use_atr_stops', False)
        self.atr_period = parameters.get('atr_period', 14)
        self.atr_stop_multiplier = parameters.get('atr_stop_multiplier', 2.0)
        self.atr_target_multiplier = parameters.get('atr_target_multiplier', 4.0)

        # Additional filters
        self.use_rsi_filter = parameters.get('use_rsi_filter', False)
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_oversold = parameters.get('rsi_oversold', 30)
        self.rsi_overbought = parameters.get('rsi_overbought', 70)

        logger.info(f"Initialized GaussianChannelStrategy")
        logger.info(f"Period: {self.period}, Poles: {self.poles}, Multiplier: {self.mult}")
        logger.info(f"Stops: {self.stop_loss_pct}% SL, {self.take_profit_pct}% TP")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Gaussian Channel and supporting indicators."""
        df = df.copy()

        # Calculate Gaussian-weighted moving average
        df = self._calculate_gaussian_channel(df)

        # Optional: ATR for dynamic stops
        if self.use_atr_stops:
            df['atr'] = self._calculate_atr(df, self.atr_period)

        # Optional: RSI filter
        if self.use_rsi_filter:
            df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Calculate band penetration percentage
        df['band_position'] = ((df['close'] - df['gc_lower']) /
                               (df['gc_upper'] - df['gc_lower']) * 100)

        return df

    def _calculate_gaussian_channel(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Gaussian Channel using weighted moving average.

        The Gaussian Channel uses normal distribution weighting to smooth price.
        This is more advanced than simple MA but less reactive than EMA.
        """
        close = df['close'].values

        # Create Gaussian weights
        weights = self._gaussian_weights(self.period, self.poles)

        # Calculate Gaussian-weighted moving average
        gc_middle = np.convolve(close, weights, mode='same')

        # Handle edge cases (beginning of series)
        for i in range(min(len(weights), len(gc_middle))):
            if i == 0:
                gc_middle[i] = close[i]
            else:
                gc_middle[i] = np.average(close[:i+1], weights=weights[-i-1:])

        df['gc_middle'] = gc_middle

        if self.use_std_bands:
            # Use standard deviation bands (simpler, more reliable)
            rolling_std = df['close'].rolling(window=self.period).std()
            df['gc_upper'] = df['gc_middle'] + (rolling_std * self.std_mult)
            df['gc_lower'] = df['gc_middle'] - (rolling_std * self.std_mult)
        else:
            # Use Gaussian-weighted standard deviation
            deviations = np.abs(close - gc_middle)
            gc_std = np.convolve(deviations, weights, mode='same')

            # Handle edge cases
            for i in range(min(len(weights), len(gc_std))):
                if i == 0:
                    gc_std[i] = 0
                else:
                    gc_std[i] = np.average(deviations[:i+1], weights=weights[-i-1:])

            df['gc_upper'] = gc_middle + (gc_std * self.mult)
            df['gc_lower'] = gc_middle - (gc_std * self.mult)

        return df

    def _gaussian_weights(self, period: int, poles: int) -> np.ndarray:
        """
        Generate Gaussian weights for smoothing.

        Args:
            period: Window size
            poles: Number of poles (higher = smoother, slower)

        Returns:
            Array of normalized weights
        """
        # Standard deviation based on period and poles
        sigma = period / (2.0 * poles)

        # Create centered array
        x = np.arange(-period, period + 1)

        # Gaussian distribution formula: exp(-(x^2) / (2 * sigma^2))
        weights = np.exp(-(x ** 2) / (2 * sigma ** 2))

        # Normalize so sum = 1
        weights = weights / weights.sum()

        return weights

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on Gaussian Channel bands."""
        df = df.copy()
        df['signal'] = 0

        # Buy when price touches lower band
        if self.require_close_outside:
            # Require close below lower band
            buy_condition = df['close'] <= df['gc_lower'] * (1 + self.entry_buffer_pct / 100)
        else:
            # Just require touching lower band
            buy_condition = df['low'] <= df['gc_lower'] * (1 + self.entry_buffer_pct / 100)

        # Sell when price touches upper band
        if self.require_close_outside:
            # Require close above upper band
            sell_condition = df['close'] >= df['gc_upper'] * (1 - self.entry_buffer_pct / 100)
        else:
            # Just require touching upper band
            sell_condition = df['high'] >= df['gc_upper'] * (1 - self.entry_buffer_pct / 100)

        # Optional RSI filter
        if self.use_rsi_filter:
            buy_condition = buy_condition & (df['rsi'] < self.rsi_oversold)
            sell_condition = sell_condition & (df['rsi'] > self.rsi_overbought)

        # Detect transitions (new signals)
        buy_transition = buy_condition & ~buy_condition.shift(1).fillna(False)
        sell_transition = sell_condition & ~sell_condition.shift(1).fillna(False)

        df.loc[buy_transition, 'signal'] = 1
        df.loc[sell_transition, 'signal'] = -1

        return df

    def should_enter(self, row: pd.Series) -> bool:
        """Check if should enter a position."""
        return row['signal'] != 0

    def should_exit(self, row: pd.Series, position) -> bool:
        """Check if should exit current position."""
        if position is None:
            return False

        # Rely on stop loss and take profit
        return False

    def calculate_stop_loss(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate stop loss."""
        if self.use_atr_stops and row is not None and 'atr' in row:
            atr = row['atr']
            if side == 'long':
                return entry_price - (atr * self.atr_stop_multiplier)
            else:
                return entry_price + (atr * self.atr_stop_multiplier)
        else:
            # Fixed percentage stop
            if side == 'long':
                return entry_price * (1 - self.stop_loss_pct / 100)
            else:
                return entry_price * (1 + self.stop_loss_pct / 100)

    def calculate_take_profit(self, entry_price: float, side: str, row: pd.Series = None) -> float:
        """Calculate take profit."""
        if self.use_atr_stops and row is not None and 'atr' in row:
            atr = row['atr']
            if side == 'long':
                return entry_price + (atr * self.atr_target_multiplier)
            else:
                return entry_price - (atr * self.atr_target_multiplier)
        else:
            # Fixed percentage target
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
