"""
Technical indicators for trading strategies.
Uses pandas-ta library for indicator calculations.
"""
import pandas as pd
import pandas_ta as ta
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def calculate_sma(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    """
    Calculate Simple Moving Average.

    Args:
        df: DataFrame with price data
        period: Moving average period
        column: Column to calculate SMA on

    Returns:
        Series with SMA values
    """
    return ta.sma(df[column], length=period)


def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    """
    Calculate Exponential Moving Average.

    Args:
        df: DataFrame with price data
        period: Moving average period
        column: Column to calculate EMA on

    Returns:
        Series with EMA values
    """
    return ta.ema(df[column], length=period)


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    Calculate Relative Strength Index.

    Args:
        df: DataFrame with price data
        period: RSI period (default: 14)
        column: Column to calculate RSI on

    Returns:
        Series with RSI values (0-100)
    """
    return ta.rsi(df[column], length=period)


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    column: str = 'close'
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        df: DataFrame with price data
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)
        column: Column to calculate MACD on

    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    macd_result = ta.macd(df[column], fast=fast, slow=slow, signal=signal)

    if macd_result is None or macd_result.empty:
        return pd.Series(), pd.Series(), pd.Series()

    macd_line = macd_result[f'MACD_{fast}_{slow}_{signal}']
    signal_line = macd_result[f'MACDs_{fast}_{slow}_{signal}']
    histogram = macd_result[f'MACDh_{fast}_{slow}_{signal}']

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std: float = 2.0,
    column: str = 'close'
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Args:
        df: DataFrame with price data
        period: Moving average period (default: 20)
        std: Standard deviation multiplier (default: 2.0)
        column: Column to calculate bands on

    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    bb_result = ta.bbands(df[column], length=period, std=std)

    if bb_result is None or bb_result.empty:
        return pd.Series(), pd.Series(), pd.Series()

    upper = bb_result[f'BBU_{period}_{std}']
    middle = bb_result[f'BBM_{period}_{std}']
    lower = bb_result[f'BBL_{period}_{std}']

    return upper, middle, lower


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (volatility indicator).

    Args:
        df: DataFrame with OHLC data
        period: ATR period (default: 14)

    Returns:
        Series with ATR values
    """
    return ta.atr(df['high'], df['low'], df['close'], length=period)


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (trend strength).

    Args:
        df: DataFrame with OHLC data
        period: ADX period (default: 14)

    Returns:
        Series with ADX values (0-100)
    """
    adx_result = ta.adx(df['high'], df['low'], df['close'], length=period)

    if adx_result is None or adx_result.empty:
        return pd.Series()

    return adx_result[f'ADX_{period}']


def calculate_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
    smooth: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.

    Args:
        df: DataFrame with OHLC data
        k_period: %K period (default: 14)
        d_period: %D period (default: 3)
        smooth: Smoothing period (default: 3)

    Returns:
        Tuple of (%K line, %D line)
    """
    stoch_result = ta.stoch(
        df['high'],
        df['low'],
        df['close'],
        k=k_period,
        d=d_period,
        smooth_k=smooth
    )

    if stoch_result is None or stoch_result.empty:
        return pd.Series(), pd.Series()

    k_line = stoch_result[f'STOCHk_{k_period}_{d_period}_{smooth}']
    d_line = stoch_result[f'STOCHd_{k_period}_{d_period}_{smooth}']

    return k_line, d_line


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    Calculate On-Balance Volume.

    Args:
        df: DataFrame with close and volume data

    Returns:
        Series with OBV values
    """
    return ta.obv(df['close'], df['volume'])


def detect_ma_crossover(
    fast_ma: pd.Series,
    slow_ma: pd.Series
) -> pd.Series:
    """
    Detect moving average crossover signals.

    Args:
        fast_ma: Fast moving average series
        slow_ma: Slow moving average series

    Returns:
        Series with values: 1 (bullish crossover), -1 (bearish crossover), 0 (no crossover)
    """
    # Current: fast > slow
    above = fast_ma > slow_ma

    # Previous: fast <= slow (shifted by 1)
    was_below = fast_ma.shift(1) <= slow_ma.shift(1)

    # Bullish crossover: was below, now above
    bullish = above & was_below

    # Bearish crossover: was above, now below
    bearish = ~above & ~was_below.shift(-1)

    # Create signal series
    signals = pd.Series(0, index=fast_ma.index)
    signals[bullish] = 1
    signals[bearish] = -1

    return signals


def add_all_indicators(
    df: pd.DataFrame,
    ma_periods: list = [10, 30, 50, 200],
    rsi_period: int = 14,
    macd_params: dict = None,
    bb_params: dict = None,
    atr_period: int = 14
) -> pd.DataFrame:
    """
    Add multiple common indicators to DataFrame.

    Args:
        df: DataFrame with OHLCV data
        ma_periods: List of MA periods to calculate
        rsi_period: RSI period
        macd_params: MACD parameters dict (fast, slow, signal)
        bb_params: Bollinger Bands parameters dict (period, std)
        atr_period: ATR period

    Returns:
        DataFrame with all indicators added
    """
    df = df.copy()

    # Moving averages
    for period in ma_periods:
        df[f'sma_{period}'] = calculate_sma(df, period)
        df[f'ema_{period}'] = calculate_ema(df, period)

    # RSI
    df['rsi'] = calculate_rsi(df, rsi_period)

    # MACD
    if macd_params is None:
        macd_params = {'fast': 12, 'slow': 26, 'signal': 9}

    macd, macd_signal, macd_hist = calculate_macd(
        df,
        fast=macd_params['fast'],
        slow=macd_params['slow'],
        signal=macd_params['signal']
    )
    df['macd'] = macd
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_hist

    # Bollinger Bands
    if bb_params is None:
        bb_params = {'period': 20, 'std': 2.0}

    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
        df,
        period=bb_params['period'],
        std=bb_params['std']
    )
    df['bb_upper'] = bb_upper
    df['bb_middle'] = bb_middle
    df['bb_lower'] = bb_lower

    # ATR (volatility)
    df['atr'] = calculate_atr(df, atr_period)

    logger.debug(f"Added indicators to DataFrame with {len(df)} rows")

    return df


def is_overbought(rsi: float, threshold: float = 70) -> bool:
    """Check if RSI indicates overbought condition."""
    return rsi > threshold


def is_oversold(rsi: float, threshold: float = 30) -> bool:
    """Check if RSI indicates oversold condition."""
    return rsi < threshold


def is_bullish_macd(macd: float, signal: float) -> bool:
    """Check if MACD indicates bullish momentum."""
    return macd > signal


def is_bearish_macd(macd: float, signal: float) -> bool:
    """Check if MACD indicates bearish momentum."""
    return macd < signal
