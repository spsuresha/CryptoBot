"""
Simple Scalping Strategy - Optimized for 60% win rate on 1-minute.

Simpler version with fewer filters for more trading opportunities.
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional

from .base_strategy import BaseStrategy
from .indicators import (
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_ema,
)
from ..config.constants import SignalType

logger = logging.getLogger(__name__)


class SimpleScalpingStrategy(BaseStrategy):
    """
    Simple scalping strategy with RSI + Bollinger Bands.

    Entry (LONG):
    - RSI < 30 (oversold)
    - Price at or below lower Bollinger Band

    Entry (SHORT):
    - RSI > 70 (overbought)
    - Price at or above upper Bollinger Band

    Exit:
    - RSI returns to 50 (neutral)
    - OR Price returns to middle BB
    - OR Stop loss / Take profit hit

    Target: 60%+ win rate, 1.5:1 risk/reward
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        super().__init__("Simple Scalping")

        if parameters is None:
            parameters = {}

        # RSI parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_oversold = parameters.get('rsi_oversold', 30)
        self.rsi_overbought = parameters.get('rsi_overbought', 70)
        self.rsi_exit = parameters.get('rsi_exit', 50)

        # Bollinger Bands
        self.bb_period = parameters.get('bb_period', 20)
        self.bb_std = parameters.get('bb_std', 2.0)

        # Risk management
        self.stop_loss_pct = parameters.get('stop_loss_pct', 0.5)  # 0.5%
        self.take_profit_pct = parameters.get('take_profit_pct', 0.75)  # 0.75% (1.5:1 R/R)

        logger.info(f"Initialized {self.name}")
        logger.info(f"RSI: {self.rsi_oversold}/{self.rsi_overbought}, Exit: {self.rsi_exit}")
        logger.info(f"Risk: {self.stop_loss_pct}% / {self.take_profit_pct}%")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators."""
        df = df.copy()

        # RSI
        df['rsi'] = calculate_rsi(df, self.rsi_period)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
            df, self.bb_period, self.bb_std
        )
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals."""
        df = df.copy()
        df['signal'] = SignalType.HOLD.value

        # LONG entry conditions
        df['long_rsi'] = df['rsi'] < self.rsi_oversold
        df['long_bb'] = df['close'] <= df['bb_lower'] * 1.005  # Within 0.5% of lower BB

        long_entry = df['long_rsi'] & df['long_bb']

        # Detect new entries (transition from False to True)
        long_entry_prev = long_entry.shift(1).fillna(False)
        long_signal = long_entry & ~long_entry_prev

        # SHORT entry conditions
        df['short_rsi'] = df['rsi'] > self.rsi_overbought
        df['short_bb'] = df['close'] >= df['bb_upper'] * 0.995  # Within 0.5% of upper BB

        short_entry = df['short_rsi'] & df['short_bb']

        # Detect new entries
        short_entry_prev = short_entry.shift(1).fillna(False)
        short_signal = short_entry & ~short_entry_prev

        # EXIT conditions (for both long and short)
        df['rsi_neutral'] = (df['rsi'] >= self.rsi_exit - 5) & (df['rsi'] <= self.rsi_exit + 5)
        df['at_bb_middle'] = (df['close'] >= df['bb_middle'] * 0.998) & (df['close'] <= df['bb_middle'] * 1.002)

        exit_condition = df['rsi_neutral'] | df['at_bb_middle']

        # Detect exit transitions
        exit_prev = exit_condition.shift(1).fillna(False)
        exit_signal = exit_condition & ~exit_prev

        # Set signals
        df.loc[long_signal, 'signal'] = SignalType.BUY.value
        df.loc[short_signal, 'signal'] = -2  # SHORT entry
        df.loc[exit_signal, 'signal'] = SignalType.SELL.value  # Exit (both long and short)

        # Calculate stops and targets
        df['stop_loss'] = df['close'] * (1 - self.stop_loss_pct / 100)
        df['take_profit'] = df['close'] * (1 + self.take_profit_pct / 100)

        # For shorts (inverted)
        df['stop_loss_short'] = df['close'] * (1 + self.stop_loss_pct / 100)
        df['take_profit_short'] = df['close'] * (1 - self.take_profit_pct / 100)

        return df

    def should_enter_long(self, row: pd.Series) -> bool:
        return row['signal'] == SignalType.BUY.value

    def should_exit_long(self, row: pd.Series, entry_price: float) -> bool:
        # Signal-based exit
        if row['signal'] == SignalType.SELL.value:
            return True

        # Stop loss
        if row['close'] <= row['stop_loss']:
            return True

        # Take profit
        if row['close'] >= row['take_profit']:
            return True

        return False

    def get_position_size(self, row: pd.Series, capital: float, risk_per_trade: float = 0.01) -> float:
        """Calculate position size (1% risk)."""
        risk_amount = capital * risk_per_trade
        stop_distance_pct = self.stop_loss_pct / 100
        position_size = (risk_amount / stop_distance_pct) / row['close']

        # Limit to 5% of capital
        max_position = capital * 0.05
        position_size = min(position_size, max_position / row['close'])

        return position_size

    def get_stop_loss(self, row: pd.Series, entry_price: float) -> Optional[float]:
        return row['stop_loss']

    def get_take_profit(self, row: pd.Series, entry_price: float) -> Optional[float]:
        return row['take_profit']
