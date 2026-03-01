"""
Diagnostic script to see what's happening with signals.
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

print("=" * 80)
print("STRATEGY DIAGNOSTIC")
print("=" * 80)

# Load settings and fetch data
settings = Settings()
connector = ExchangeConnector(settings)
connector.connect()
data_fetcher = DataFetcher(connector)

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

# Create strategy
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

# Prepare data with indicators
print("\nCalculating indicators...")
df = strategy.prepare_data(df)

print("\nChecking signals...")
buy_signals = df[df['signal'] == 1]
sell_signals = df[df['signal'] == -1]

print(f"BUY signals: {len(buy_signals)}")
print(f"SELL signals: {len(sell_signals)}")
print(f"Total candles: {len(df)}")

# Check conditions
print("\n" + "=" * 80)
print("CONDITION ANALYSIS")
print("=" * 80)

# Check how many candles meet each condition
if len(buy_signals) > 0:
    print("\nChecking BUY conditions on all data:")
    print(f"Price > Trend EMA: {df['uptrend'].sum()} candles ({df['uptrend'].sum()/len(df)*100:.1f}%)")
    print(f"ADX > 25: {df['strong_trend'].sum()} candles ({df['strong_trend'].sum()/len(df)*100:.1f}%)")
    print(f"RSI 40-60: {df['rsi_good'].sum()} candles ({df['rsi_good'].sum()/len(df)*100:.1f}%)")
    print(f"MACD bullish: {df['macd_bull'].sum()} candles ({df['macd_bull'].sum()/len(df)*100:.1f}%)")
    print(f"Above BB mid: {df['above_bb_mid'].sum()} candles ({df['above_bb_mid'].sum()/len(df)*100:.1f}%)")
    print(f"Momentum: {df['momentum'].sum()} candles ({df['momentum'].sum()/len(df)*100:.1f}%)")

    # Check ALL conditions together
    all_conditions = (
        df['uptrend'] &
        df['strong_trend'] &
        df['rsi_good'] &
        df['macd_bull'] &
        df['above_bb_mid'] &
        df['momentum']
    )
    print(f"\nALL conditions met: {all_conditions.sum()} candles ({all_conditions.sum()/len(df)*100:.1f}%)")
    print(f"BUY signals generated: {len(buy_signals)}")

    if all_conditions.sum() != len(buy_signals):
        print(f"\n⚠️  MISMATCH! Expected {all_conditions.sum()} BUY signals, got {len(buy_signals)}")
    else:
        print(f"\n✅ Correct! Signal generation working properly")

# Show first few BUY signals
if len(buy_signals) > 0:
    print("\n" + "=" * 80)
    print("FIRST 5 BUY SIGNALS")
    print("=" * 80)
    for idx, row in buy_signals.head(5).iterrows():
        print(f"\nDate: {row['timestamp']}")
        print(f"  Price: ${row['close']:.2f}")
        print(f"  Trend EMA: ${row['trend_ema']:.2f} (above: {row['uptrend']})")
        print(f"  ADX: {row['adx']:.1f} (>25: {row['strong_trend']})")
        print(f"  RSI: {row['rsi']:.1f} (40-60: {row['rsi_good']})")
        print(f"  MACD: {row['macd']:.2f} vs Signal: {row['macd_signal']:.2f} (bull: {row['macd_bull']})")
        print(f"  BB Middle: ${row['bb_middle']:.2f} (above: {row['above_bb_mid']})")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
