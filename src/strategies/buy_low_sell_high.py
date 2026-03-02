"""
Buy Low Sell High Strategy - Cycle-based trading
Identifies oversold conditions to buy and overbought conditions to sell
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class BuyLowSellHighStrategy(BaseStrategy):
    """
    Strategy focused on buying at cycle lows and selling at cycle highs.

    Uses multiple approaches:
    - RSI extremes for overbought/oversold
    - Bollinger Bands for deviation from mean
    - Price distance from moving average
    - Stochastic oscillator for momentum extremes
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        super().__init__()

        # Strategy type
        self.strategy_type = parameters.get('strategy_type', 'rsi_extreme')

        # RSI parameters
        self.rsi_period = parameters.get('rsi_period', 14)
        self.rsi_oversold = parameters.get('rsi_oversold', 30)
        self.rsi_overbought = parameters.get('rsi_overbought', 70)

        # Bollinger Band parameters
        self.bb_period = parameters.get('bb_period', 20)
        self.bb_std = parameters.get('bb_std', 2.0)

        # Moving Average parameters
        self.ma_period = parameters.get('ma_period', 50)
        self.ma_deviation_pct = parameters.get('ma_deviation_pct', 10.0)

        # Stochastic parameters
        self.stoch_k_period = parameters.get('stoch_k_period', 14)
        self.stoch_d_period = parameters.get('stoch_d_period', 3)
        self.stoch_oversold = parameters.get('stoch_oversold', 20)
        self.stoch_overbought = parameters.get('stoch_overbought', 80)

        # Risk management
        self.stop_loss_pct = parameters.get('stop_loss_pct', 10.0)
        self.take_profit_pct = parameters.get('take_profit_pct', 20.0)

        # Optional: Use ATR for dynamic stops
        self.use_atr_stops = parameters.get('use_atr_stops', False)
        self.atr_period = parameters.get('atr_period', 14)
        self.atr_stop_multiplier = parameters.get('atr_stop_multiplier', 2.0)
        self.atr_target_multiplier = parameters.get('atr_target_multiplier', 4.0)

        # Confirmation filters
        self.require_volume_confirmation = parameters.get('require_volume_confirmation', False)
        self.volume_ma_period = parameters.get('volume_ma_period', 20)

        logger.info(f"Initialized BuyLowSellHighStrategy - Type: {self.strategy_type}")
        logger.info(f"RSI: {self.rsi_period} ({self.rsi_oversold}/{self.rsi_overbought})")
        logger.info(f"BB: {self.bb_period} periods, {self.bb_std} std dev")
        logger.info(f"Stops: {self.stop_loss_pct}% SL, {self.take_profit_pct}% TP")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle'] * 100

        # Price position within bands (0 = lower band, 100 = upper band)
        df['bb_position'] = ((df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower']) * 100)

        # Moving Average and deviation
        df['ma'] = df['close'].rolling(window=self.ma_period).mean()
        df['price_ma_deviation'] = ((df['close'] - df['ma']) / df['ma'] * 100)

        # Stochastic Oscillator
        df = self._calculate_stochastic(df, self.stoch_k_period, self.stoch_d_period)

        # ATR for dynamic stops
        if self.use_atr_stops:
            df['atr'] = self._calculate_atr(df, self.atr_period)

        # Volume indicators
        if self.require_volume_confirmation:
            df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Rate of Change (momentum)
        df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on strategy type."""
        df = df.copy()
        df['signal'] = 0

        if self.strategy_type == 'rsi_extreme':
            df = self._rsi_extreme_signals(df)
        elif self.strategy_type == 'bollinger_bounce':
            df = self._bollinger_bounce_signals(df)
        elif self.strategy_type == 'ma_deviation':
            df = self._ma_deviation_signals(df)
        elif self.strategy_type == 'stochastic_extreme':
            df = self._stochastic_extreme_signals(df)
        elif self.strategy_type == 'combo_conservative':
            df = self._combo_conservative_signals(df)
        elif self.strategy_type == 'combo_aggressive':
            df = self._combo_aggressive_signals(df)
        else:
            df = self._rsi_extreme_signals(df)

        return df

    def _rsi_extreme_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Buy when RSI oversold, sell when RSI overbought."""
        # Buy conditions
        buy_condition = df['rsi'] < self.rsi_oversold

        # Sell conditions
        sell_condition = df['rsi'] > self.rsi_overbought

        # Detect transitions
        buy_transition = buy_condition & ~buy_condition.shift(1).fillna(False)
        sell_transition = sell_condition & ~sell_condition.shift(1).fillna(False)

        df.loc[buy_transition, 'signal'] = 1
        df.loc[sell_transition, 'signal'] = -1

        return df

    def _bollinger_bounce_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Buy when price touches lower band, sell when touches upper band."""
        # Buy when price is at or below lower band
        buy_condition = df['close'] <= df['bb_lower'] * 1.01  # Within 1% of lower band

        # Sell when price is at or above upper band
        sell_condition = df['close'] >= df['bb_upper'] * 0.99  # Within 1% of upper band

        # Detect transitions
        buy_transition = buy_condition & ~buy_condition.shift(1).fillna(False)
        sell_transition = sell_condition & ~sell_condition.shift(1).fillna(False)

        df.loc[buy_transition, 'signal'] = 1
        df.loc[sell_transition, 'signal'] = -1

        return df

    def _ma_deviation_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Buy when price is far below MA, sell when far above."""
        # Buy when price is significantly below MA
        buy_condition = df['price_ma_deviation'] < -self.ma_deviation_pct

        # Sell when price is significantly above MA
        sell_condition = df['price_ma_deviation'] > self.ma_deviation_pct

        # Detect transitions
        buy_transition = buy_condition & ~buy_condition.shift(1).fillna(False)
        sell_transition = sell_condition & ~sell_condition.shift(1).fillna(False)

        df.loc[buy_transition, 'signal'] = 1
        df.loc[sell_transition, 'signal'] = -1

        return df

    def _stochastic_extreme_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Buy when stochastic oversold, sell when overbought."""
        # Buy when both K and D are oversold
        buy_condition = (df['stoch_k'] < self.stoch_oversold) & (df['stoch_d'] < self.stoch_oversold)

        # Sell when both K and D are overbought
        sell_condition = (df['stoch_k'] > self.stoch_overbought) & (df['stoch_d'] > self.stoch_overbought)

        # Detect transitions
        buy_transition = buy_condition & ~buy_condition.shift(1).fillna(False)
        sell_transition = sell_condition & ~sell_condition.shift(1).fillna(False)

        df.loc[buy_transition, 'signal'] = 1
        df.loc[sell_transition, 'signal'] = -1

        return df

    def _combo_conservative_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Combination: Require multiple indicators to confirm extremes."""
        # Buy when multiple indicators show oversold
        rsi_oversold = df['rsi'] < self.rsi_oversold
        bb_low = df['close'] <= df['bb_lower'] * 1.02
        stoch_oversold = df['stoch_k'] < self.stoch_oversold

        buy_condition = rsi_oversold & bb_low & stoch_oversold

        # Sell when multiple indicators show overbought
        rsi_overbought = df['rsi'] > self.rsi_overbought
        bb_high = df['close'] >= df['bb_upper'] * 0.98
        stoch_overbought = df['stoch_k'] > self.stoch_overbought

        sell_condition = rsi_overbought & bb_high & stoch_overbought

        # Detect transitions
        buy_transition = buy_condition & ~buy_condition.shift(1).fillna(False)
        sell_transition = sell_condition & ~sell_condition.shift(1).fillna(False)

        df.loc[buy_transition, 'signal'] = 1
        df.loc[sell_transition, 'signal'] = -1

        return df

    def _combo_aggressive_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Combination: Require at least 2 out of 3 indicators."""
        # Buy conditions
        rsi_oversold = df['rsi'] < self.rsi_oversold
        bb_low = df['close'] <= df['bb_lower'] * 1.02
        stoch_oversold = df['stoch_k'] < self.stoch_oversold

        buy_score = rsi_oversold.astype(int) + bb_low.astype(int) + stoch_oversold.astype(int)
        buy_condition = buy_score >= 2

        # Sell conditions
        rsi_overbought = df['rsi'] > self.rsi_overbought
        bb_high = df['close'] >= df['bb_upper'] * 0.98
        stoch_overbought = df['stoch_k'] > self.stoch_overbought

        sell_score = rsi_overbought.astype(int) + bb_high.astype(int) + stoch_overbought.astype(int)
        sell_condition = sell_score >= 2

        # Detect transitions
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

        # Rely on stop loss and take profit for exits
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

    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int, d_period: int) -> pd.DataFrame:
        """Calculate Stochastic Oscillator."""
        # %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()

        df['stoch_k'] = ((df['close'] - low_min) / (high_max - low_min) * 100)

        # %D = 3-period SMA of %K
        df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()

        return df
