"""
Conservative Trend Following Strategy.

Designed for high win rate (target 70%+) with controlled drawdown (<30%).

Features:
- Multiple confirmation indicators
- Strict trend filtering
- Conservative entry/exit rules
- Volatility-based stop losses
- Quick profit taking
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional

from .base_strategy import BaseStrategy
from .indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_adx,
)
from ..config.constants import SignalType

logger = logging.getLogger(__name__)


class ConservativeTrendStrategy(BaseStrategy):
    """
    Conservative trend following strategy with multiple confirmations.

    Entry Rules (ALL must be true for BUY):
    1. Price > 50 EMA (uptrend)
    2. ADX > 25 (strong trend)
    3. RSI between 40-60 (not overbought)
    4. MACD > Signal (bullish momentum)
    5. Price > BB Middle (above average)
    6. Short EMA > Long EMA (momentum)

    Exit Rules (ANY triggers SELL):
    1. Price < 20 EMA (fast exit)
    2. RSI > 70 (overbought)
    3. MACD < Signal (momentum shift)
    4. Stop loss: 2 ATR below entry
    5. Take profit: 3 ATR above entry
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize Conservative Trend Strategy.

        Parameters:
            trend_period: Long-term trend EMA (default: 50)
            fast_ema: Fast EMA for momentum (default: 8)
            slow_ema: Slow EMA for momentum (default: 21)
            exit_ema: Exit EMA (default: 20)
            rsi_period: RSI period (default: 14)
            rsi_min: Minimum RSI for entry (default: 40)
            rsi_max: Maximum RSI for entry (default: 60)
            rsi_exit: RSI exit threshold (default: 70)
            adx_period: ADX period (default: 14)
            adx_threshold: Minimum ADX for entry (default: 25)
            bb_period: Bollinger Bands period (default: 20)
            bb_std: BB standard deviation (default: 2.0)
            atr_period: ATR period (default: 14)
            atr_stop_mult: ATR multiplier for stop loss (default: 2.0)
            atr_target_mult: ATR multiplier for take profit (default: 3.0)
        """
        super().__init__("Conservative Trend")

        if parameters is None:
            parameters = {}

        # Trend parameters
        self.trend_period = parameters.get('trend_period', 50)
        self.fast_ema = parameters.get('fast_ema', 8)
        self.slow_ema = parameters.get('slow_ema', 21)
        self.exit_ema = parameters.get('exit_ema', 20)

        # RSI parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_min = parameters.get('rsi_min', 40)
        self.rsi_max = parameters.get('rsi_max', 60)
        self.rsi_exit = parameters.get('rsi_exit', 70)

        # ADX parameters
        self.adx_period = parameters.get('adx_period', 14)
        self.adx_threshold = parameters.get('adx_threshold', 25)

        # Bollinger Bands parameters
        self.bb_period = parameters.get('bb_period', 20)
        self.bb_std = parameters.get('bb_std', 2.0)

        # ATR parameters
        self.atr_period = parameters.get('atr_period', 14)
        self.atr_stop_mult = parameters.get('atr_stop_mult', 2.0)
        self.atr_target_mult = parameters.get('atr_target_mult', 3.0)

        logger.info(f"Initialized {self.name}")
        logger.info(f"Trend EMA: {self.trend_period}, Fast/Slow EMA: {self.fast_ema}/{self.slow_ema}")
        logger.info(f"RSI Range: {self.rsi_min}-{self.rsi_max}, Exit: {self.rsi_exit}")
        logger.info(f"ADX Threshold: {self.adx_threshold}")
        logger.info(f"ATR Stop/Target: {self.atr_stop_mult}/{self.atr_target_mult}")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators."""
        df = df.copy()

        # Moving averages
        df['trend_ema'] = calculate_ema(df, self.trend_period)
        df['fast_ema'] = calculate_ema(df, self.fast_ema)
        df['slow_ema'] = calculate_ema(df, self.slow_ema)
        df['exit_ema'] = calculate_ema(df, self.exit_ema)

        # RSI
        df['rsi'] = calculate_rsi(df, self.rsi_period)

        # MACD
        macd, signal, hist = calculate_macd(df, fast=12, slow=26, signal=9)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist

        # ADX
        df['adx'] = calculate_adx(df, self.adx_period)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
            df, self.bb_period, self.bb_std
        )
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower

        # ATR for stops
        df['atr'] = calculate_atr(df, self.atr_period)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals with multiple confirmations."""
        df = df.copy()
        df['signal'] = SignalType.HOLD.value

        # Calculate all conditions for BUY
        df['uptrend'] = df['close'] > df['trend_ema']
        df['strong_trend'] = df['adx'] > self.adx_threshold
        df['rsi_good'] = (df['rsi'] >= self.rsi_min) & (df['rsi'] <= self.rsi_max)
        df['macd_bull'] = df['macd'] > df['macd_signal']
        df['above_bb_mid'] = df['close'] > df['bb_middle']
        df['momentum'] = df['fast_ema'] > df['slow_ema']

        # BUY: ALL conditions must be TRUE
        buy_signal = (
            df['uptrend'] &
            df['strong_trend'] &
            df['rsi_good'] &
            df['macd_bull'] &
            df['above_bb_mid'] &
            df['momentum']
        )

        # Calculate conditions for SELL
        df['fast_exit'] = df['close'] < df['exit_ema']
        df['rsi_high'] = df['rsi'] > self.rsi_exit
        df['macd_bear'] = df['macd'] < df['macd_signal']

        # SELL: ANY condition triggers exit
        sell_signal = (
            df['fast_exit'] |
            df['rsi_high'] |
            df['macd_bear']
        )

        # Set signals
        df.loc[buy_signal, 'signal'] = SignalType.BUY.value
        df.loc[sell_signal, 'signal'] = SignalType.SELL.value

        # Calculate dynamic stop loss and take profit
        df['stop_loss'] = df['close'] - (df['atr'] * self.atr_stop_mult)
        df['take_profit'] = df['close'] + (df['atr'] * self.atr_target_mult)

        return df

    def should_enter_long(self, row: pd.Series) -> bool:
        """Check if should enter long position."""
        return row['signal'] == SignalType.BUY.value

    def should_exit_long(self, row: pd.Series, entry_price: float) -> bool:
        """Check if should exit long position."""
        # Check signal-based exit
        if row['signal'] == SignalType.SELL.value:
            return True

        # Check stop loss
        if row['close'] <= row['stop_loss']:
            return True

        # Check take profit
        if row['close'] >= row['take_profit']:
            return True

        return False

    def get_position_size(self, row: pd.Series, capital: float, risk_per_trade: float = 0.02) -> float:
        """
        Calculate position size based on ATR volatility.

        Args:
            row: Current bar data
            capital: Available capital
            risk_per_trade: Risk per trade as fraction (default: 2%)

        Returns:
            Position size in base currency
        """
        # Risk amount in dollars
        risk_amount = capital * risk_per_trade

        # Stop loss distance in dollars
        stop_distance = row['atr'] * self.atr_stop_mult

        # Position size = Risk amount / Stop distance
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
            # Limit to max 10% of capital
            max_position = capital * 0.10
            position_size = min(position_size, max_position / row['close'])
        else:
            position_size = 0

        return position_size

    def get_stop_loss(self, row: pd.Series, entry_price: float) -> Optional[float]:
        """Get stop loss price."""
        return row['stop_loss']

    def get_take_profit(self, row: pd.Series, entry_price: float) -> Optional[float]:
        """Get take profit price."""
        return row['take_profit']
