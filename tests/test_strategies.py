"""
Unit tests for trading strategies.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategies.ma_crossover import MACrossoverStrategy
from src.strategies.indicators import (
    calculate_sma,
    calculate_rsi,
    calculate_macd,
    detect_ma_crossover
)
from src.config.constants import SignalType


class TestMAStrategy:
    """Test Moving Average Crossover Strategy."""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')

        # Create trending data for MA crossover
        prices = np.linspace(100, 150, 100) + np.random.randn(100) * 2

        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': prices,
            'high': prices + 1,
            'low': prices - 1,
            'close': prices,
            'volume': np.random.randint(1000, 5000, 100)
        }, index=dates)

        return df

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        params = {
            'fast_period': 10,
            'slow_period': 30
        }
        strategy = MACrossoverStrategy(params)

        assert strategy.fast_period == 10
        assert strategy.slow_period == 30

    def test_calculate_indicators(self, sample_data):
        """Test indicator calculation."""
        strategy = MACrossoverStrategy({
            'fast_period': 10,
            'slow_period': 30
        })

        df = strategy.calculate_indicators(sample_data)

        assert 'fast_ma' in df.columns
        assert 'slow_ma' in df.columns
        assert not df['fast_ma'].isna().all()
        assert not df['slow_ma'].isna().all()

    def test_generate_signals(self, sample_data):
        """Test signal generation."""
        strategy = MACrossoverStrategy({
            'fast_period': 5,
            'slow_period': 10
        })

        df = strategy.prepare_data(sample_data)

        assert 'signal' in df.columns
        assert df['signal'].isin([-1, 0, 1]).all()

    def test_signal_validation(self, sample_data):
        """Test signal validation."""
        strategy = MACrossoverStrategy({
            'fast_period': 5,
            'slow_period': 10
        })

        df = strategy.prepare_data(sample_data)
        row = df.iloc[-1]

        # Should validate if all required data is present
        is_valid = strategy.validate_signal(row, SignalType.BUY)
        assert isinstance(is_valid, bool)

    def test_rsi_filter(self, sample_data):
        """Test RSI filter."""
        strategy = MACrossoverStrategy({
            'fast_period': 5,
            'slow_period': 10,
            'use_rsi_filter': True,
            'rsi_period': 14,
            'rsi_overbought': 70
        })

        df = strategy.prepare_data(sample_data)

        assert 'rsi' in df.columns


class TestIndicators:
    """Test technical indicators."""

    @pytest.fixture
    def sample_prices(self):
        """Create sample price series."""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
        df = pd.DataFrame({
            'close': np.linspace(100, 110, 50) + np.random.randn(50),
            'high': np.linspace(101, 111, 50),
            'low': np.linspace(99, 109, 50),
            'volume': np.random.randint(1000, 5000, 50)
        }, index=dates)
        return df

    def test_sma_calculation(self, sample_prices):
        """Test SMA calculation."""
        sma = calculate_sma(sample_prices, period=10)

        assert len(sma) == len(sample_prices)
        assert not sma.isna().all()
        # First 9 values should be NaN
        assert sma.iloc[:9].isna().all()

    def test_rsi_calculation(self, sample_prices):
        """Test RSI calculation."""
        rsi = calculate_rsi(sample_prices, period=14)

        assert len(rsi) == len(sample_prices)
        # RSI should be between 0 and 100
        assert (rsi.dropna() >= 0).all()
        assert (rsi.dropna() <= 100).all()

    def test_macd_calculation(self, sample_prices):
        """Test MACD calculation."""
        macd, signal, hist = calculate_macd(sample_prices)

        assert len(macd) == len(sample_prices)
        assert len(signal) == len(sample_prices)
        assert len(hist) == len(sample_prices)

    def test_ma_crossover_detection(self):
        """Test MA crossover detection."""
        # Create synthetic data with clear crossover
        fast_ma = pd.Series([95, 96, 97, 98, 99, 101, 102, 103])
        slow_ma = pd.Series([100, 100, 100, 100, 100, 100, 100, 100])

        signals = detect_ma_crossover(fast_ma, slow_ma)

        # Should detect bullish crossover around index 5
        assert 1 in signals.values


def test_strategy_entry_exit_logic():
    """Test strategy entry and exit logic."""
    strategy = MACrossoverStrategy({'fast_period': 5, 'slow_period': 10})

    # Create sample row with buy signal
    row = pd.Series({
        'signal': 1,
        'close': 100,
        'fast_ma': 101,
        'slow_ma': 99
    })

    assert strategy.should_enter(row) == True

    # Create sample row with sell signal
    row['signal'] = -1
    assert strategy.should_exit(row, None) == True
