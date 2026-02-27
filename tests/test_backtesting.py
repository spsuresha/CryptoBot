"""
Unit tests for backtesting engine.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.performance import PerformanceMetrics
from src.strategies.ma_crossover import MACrossoverStrategy


class TestBacktestEngine:
    """Test backtesting engine."""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data with trend."""
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')

        # Create uptrend then downtrend
        trend_up = np.linspace(100, 150, 100)
        trend_down = np.linspace(150, 120, 100)
        prices = np.concatenate([trend_up, trend_down])
        prices += np.random.randn(200) * 2

        df = pd.DataFrame({
            'timestamp': [int(d.timestamp() * 1000) for d in dates],
            'open': prices,
            'high': prices + 2,
            'low': prices - 2,
            'close': prices,
            'volume': np.random.randint(1000, 5000, 200)
        }, index=dates)

        return df

    @pytest.fixture
    def strategy(self):
        """Create strategy instance."""
        return MACrossoverStrategy({
            'fast_period': 5,
            'slow_period': 20
        })

    def test_backtest_initialization(self, strategy):
        """Test backtest initialization."""
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=10000,
            commission=0.001,
            slippage=0.0005
        )

        assert backtest.initial_capital == 10000
        assert backtest.balance == 10000
        assert backtest.commission == 0.001

    def test_run_backtest(self, strategy, sample_data):
        """Test running full backtest."""
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=10000
        )

        results = backtest.run(sample_data, symbol="BTC/USDT")

        assert 'initial_capital' in results
        assert 'final_equity' in results
        assert 'total_trades' in results
        assert 'equity_curve' in results

    def test_backtest_trades(self, strategy, sample_data):
        """Test that backtest generates trades."""
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=10000
        )

        results = backtest.run(sample_data)

        # Should have executed some trades
        assert len(results['trades']) > 0

    def test_backtest_metrics(self, strategy, sample_data):
        """Test backtest metrics calculation."""
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=10000
        )

        results = backtest.run(sample_data)

        assert 'win_rate' in results
        assert 'sharpe_ratio' in results
        assert 'max_drawdown' in results
        assert results['win_rate'] >= 0
        assert results['win_rate'] <= 100

    def test_commission_calculation(self, strategy, sample_data):
        """Test that commissions are calculated correctly."""
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=10000,
            commission=0.01  # 1% commission
        )

        results = backtest.run(sample_data)

        if results['trades']:
            # Check that trades have fees
            first_trade = results['trades'][0]
            assert 'fees' in first_trade
            assert first_trade['fees'] > 0

    def test_equity_curve(self, strategy, sample_data):
        """Test equity curve generation."""
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=10000
        )

        results = backtest.run(sample_data)

        equity_curve = results['equity_curve']

        # Equity curve should have same length as data
        assert len(equity_curve) == len(sample_data)

        # First equity should be initial capital
        assert equity_curve[0] == pytest.approx(10000, rel=0.01)


class TestPerformanceMetrics:
    """Test performance metrics calculations."""

    @pytest.fixture
    def sample_results(self):
        """Create sample backtest results."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')

        return {
            'initial_capital': 10000,
            'final_equity': 11000,
            'total_return': 10.0,
            'total_pnl': 1000,
            'total_trades': 10,
            'winning_trades': 6,
            'losing_trades': 4,
            'win_rate': 60.0,
            'avg_win': 200,
            'avg_loss': -100,
            'profit_factor': 1.5,
            'sharpe_ratio': 1.2,
            'max_drawdown': -5.0,
            'trades': [
                {
                    'pnl': 100,
                    'fees': 10,
                    'entry_time': dates[i],
                    'exit_time': dates[i+1]
                }
                for i in range(10)
            ],
            'equity_curve': np.linspace(10000, 11000, 100).tolist(),
            'dates': dates.tolist()
        }

    def test_calculate_all_metrics(self, sample_results):
        """Test comprehensive metrics calculation."""
        metrics = PerformanceMetrics.calculate_all_metrics(sample_results)

        assert 'total_fees' in metrics
        assert 'largest_win' in metrics
        assert 'expectancy' in metrics
        assert 'recovery_factor' in metrics

    def test_expectancy_calculation(self):
        """Test expectancy calculation."""
        trades_data = [
            {'pnl': 100},
            {'pnl': 200},
            {'pnl': -50},
            {'pnl': -30}
        ]
        trades_df = pd.DataFrame(trades_data)

        expectancy = PerformanceMetrics._calculate_expectancy(trades_df)

        # (2 wins * 150 avg) - (2 losses * 40 avg) / 4 = 55
        assert expectancy > 0

    def test_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        equity_curve = [10000, 10100, 10050, 10200, 10150, 10300]

        sortino = PerformanceMetrics._calculate_sortino_ratio(equity_curve)

        assert isinstance(sortino, float)

    def test_empty_results(self):
        """Test metrics with no trades."""
        results = {
            'initial_capital': 10000,
            'final_equity': 10000,
            'trades': [],
            'equity_curve': [10000],
            'dates': []
        }

        metrics = PerformanceMetrics.calculate_all_metrics(results)

        # Should not crash and return valid structure
        assert metrics is not None


def test_realistic_backtest_scenario():
    """Test a realistic backtesting scenario."""
    # Create realistic price data
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='1H')

    # Simulate price with trend and noise
    trend = np.linspace(40000, 45000, 1000)
    noise = np.random.randn(1000) * 500
    prices = trend + noise

    df = pd.DataFrame({
        'timestamp': [int(d.timestamp() * 1000) for d in dates],
        'open': prices,
        'high': prices + np.abs(np.random.randn(1000) * 100),
        'low': prices - np.abs(np.random.randn(1000) * 100),
        'close': prices,
        'volume': np.random.randint(100, 1000, 1000)
    }, index=dates)

    # Create strategy
    strategy = MACrossoverStrategy({
        'fast_period': 10,
        'slow_period': 30,
        'use_rsi_filter': True
    })

    # Run backtest
    backtest = BacktestEngine(
        strategy=strategy,
        initial_capital=10000,
        commission=0.001,
        slippage=0.0005
    )

    results = backtest.run(df, symbol="BTC/USDT")

    # Verify realistic results
    assert results['total_trades'] > 0
    assert results['final_equity'] > 0
    assert -100 <= results['total_return'] <= 1000  # Reasonable range
    assert -100 <= results['max_drawdown'] <= 0
