"""
Quick test script for Conservative Trend Strategy.
This bypasses config files to test the strategy directly.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.exchange.connector import ExchangeConnector
from src.exchange.data_fetcher import DataFetcher
from src.strategies.conservative_trend import ConservativeTrendStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.performance import PerformanceMetrics

print("=" * 80)
print("TESTING CONSERVATIVE TREND STRATEGY")
print("=" * 80)
print("Target: 70%+ win rate, <30% max drawdown")
print("=" * 80)

# Load settings
settings = Settings()

# Connect to exchange
print("\nConnecting to exchange...")
connector = ExchangeConnector(settings)
connector.connect()
data_fetcher = DataFetcher(connector)

# Fetch data
print("Fetching BTC/USDT data for 2024...")
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

df = data_fetcher.fetch_ohlcv_dataframe(
    symbol='BTC/USDT',
    timeframe='1h',
    since=start_date,
    until=end_date
)

print(f"Loaded {len(df)} candles")

# Create Conservative Trend strategy with optimized parameters
print("\nInitializing Conservative Trend Strategy...")
strategy = ConservativeTrendStrategy(parameters={
    'trend_period': 50,
    'fast_ema': 8,
    'slow_ema': 21,
    'exit_ema': 20,
    'rsi_period': 14,
    'rsi_min': 40,
    'rsi_max': 60,
    'rsi_exit': 70,
    'adx_period': 14,
    'adx_threshold': 25,
    'bb_period': 20,
    'bb_std': 2.0,
    'atr_period': 14,
    'atr_stop_mult': 2.0,
    'atr_target_mult': 3.0,
})

# Run backtest
print("Running backtest...")
backtest = BacktestEngine(
    strategy=strategy,
    initial_capital=1000.0,
    commission=0.001,
    slippage=0.0005
)

results = backtest.run(df, symbol='BTC/USDT')

# Calculate metrics
metrics = PerformanceMetrics.calculate_all_metrics(results)

# Print results
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)
PerformanceMetrics.print_summary(metrics)

# Check if targets met
print("\n" + "=" * 80)
print("TARGET ANALYSIS")
print("=" * 80)

win_rate = metrics.get('win_rate', 0)
max_dd = abs(metrics.get('max_drawdown', 0))

print(f"Win Rate Target: 70%+")
print(f"Actual Win Rate: {win_rate:.1f}%")
if win_rate >= 70:
    print("✅ TARGET MET!")
else:
    print(f"❌ Target missed by {70 - win_rate:.1f}%")

print(f"\nMax Drawdown Target: <30%")
print(f"Actual Max Drawdown: {max_dd:.1f}%")
if max_dd < 30:
    print("✅ TARGET MET!")
else:
    print(f"❌ Target exceeded by {max_dd - 30:.1f}%")

print("\n" + "=" * 80)
if win_rate >= 70 and max_dd < 30:
    print("🎯 BOTH TARGETS ACHIEVED!")
elif win_rate >= 65:
    print("⚠️  Close to target - try optimization")
else:
    print("❌ Need parameter optimization")
print("=" * 80)
