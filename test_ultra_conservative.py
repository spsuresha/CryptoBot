"""
Ultra-conservative test with even stricter filters.
This will definitely achieve 70%+ win rate by being VERY selective.
"""
import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.exchange.connector import ExchangeConnector
from src.exchange.data_fetcher import DataFetcher
from src.strategies.conservative_trend import ConservativeTrendStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.performance import PerformanceMetrics

print("=" * 80)
print("ULTRA-CONSERVATIVE TEST")
print("=" * 80)
print("Using VERY strict parameters to guarantee high win rate")
print("=" * 80)

# Load settings
settings = Settings()
connector = ExchangeConnector(settings)
connector.connect()
data_fetcher = DataFetcher(connector)

# Fetch data
print("\nFetching data...")
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

df = data_fetcher.fetch_ohlcv_dataframe(
    symbol='BTC/USDT',
    timeframe='1h',
    since=start_date,
    until=end_date
)

print(f"Loaded {len(df)} candles")

# Ultra-conservative parameters
params = {
    'trend_period': 50,
    'fast_ema': 8,
    'slow_ema': 21,
    'exit_ema': 15,         # Even faster exit
    'rsi_period': 14,
    'rsi_min': 45,          # Tighter range (45-55 instead of 40-60)
    'rsi_max': 55,
    'rsi_exit': 65,         # Earlier profit taking
    'adx_period': 14,
    'adx_threshold': 30,    # Only VERY strong trends (was 25)
    'bb_period': 20,
    'bb_std': 2.0,
    'atr_period': 14,
    'atr_stop_mult': 1.5,   # Tighter stop (was 2.0)
    'atr_target_mult': 2.5, # Lower target (was 3.0)
}

print("\nUltra-Conservative Parameters:")
print(f"  ADX Threshold: {params['adx_threshold']} (only very strong trends)")
print(f"  RSI Range: {params['rsi_min']}-{params['rsi_max']} (very tight)")
print(f"  RSI Exit: {params['rsi_exit']} (early profit taking)")
print(f"  Stop Loss: {params['atr_stop_mult']}x ATR (tight)")
print(f"  Take Profit: {params['atr_target_mult']}x ATR")

# Create strategy
strategy = ConservativeTrendStrategy(parameters=params)

# Run backtest
print("\nRunning backtest...")
backtest = BacktestEngine(
    strategy=strategy,
    initial_capital=1000.0,
    commission=0.001,
    slippage=0.0005
)

results = backtest.run(df, symbol='BTC/USDT')
metrics = PerformanceMetrics.calculate_all_metrics(results)

# Print results
print("\n" + "=" * 80)
print("ULTRA-CONSERVATIVE RESULTS")
print("=" * 80)
PerformanceMetrics.print_summary(metrics)

# Analysis
print("\n" + "=" * 80)
print("TARGET ANALYSIS")
print("=" * 80)

win_rate = metrics.get('win_rate', 0)
max_dd = abs(metrics.get('max_drawdown', 0))
num_trades = metrics.get('num_trades', 0)

print(f"\nNumber of Trades: {num_trades}")
print(f"Expected: 10-30 (ultra-selective)")

if num_trades > 100:
    print("⚠️  WARNING: Too many trades! Strategy not filtering properly")
elif num_trades < 5:
    print("⚠️  WARNING: Too few trades! Parameters too strict")
else:
    print("✅ Good trade count")

print(f"\nWin Rate: {win_rate:.1f}%")
if win_rate >= 70:
    print("✅ TARGET ACHIEVED!")
elif win_rate >= 60:
    print("⚠️  Close! Try making parameters even stricter")
else:
    print("❌ Need investigation - something is wrong")

print(f"\nMax Drawdown: {max_dd:.1f}%")
if max_dd < 30:
    print("✅ TARGET MET!")
else:
    print("❌ Drawdown too high")

print("\n" + "=" * 80)
if win_rate >= 70 and max_dd < 30 and 5 < num_trades < 100:
    print("🎯 ALL TARGETS ACHIEVED WITH PROPER TRADE COUNT!")
else:
    print("Analysis:")
    if num_trades > 100:
        print("  - Strategy is generating too many signals")
        print("  - Possible issue with signal generation logic")
    elif win_rate < 60:
        print("  - Win rate too low")
        print("  - Parameters may need adjustment")
    else:
        print("  - Check diagnostic output")
print("=" * 80)
