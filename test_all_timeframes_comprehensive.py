"""
Comprehensive Timeframe Testing - Find the optimal timeframe
Tests: 1h, 2h, 3h, 6h, 8h, 12h
Goal: Find best timeframe for dual direction trading
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.exchange.connector import ExchangeConnector
from src.exchange.data_fetcher import DataFetcher
from src.strategies.dual_direction import DualDirectionStrategy
from src.backtesting.backtest_engine import BacktestEngine

print("=" * 100)
print("COMPREHENSIVE TIMEFRAME ANALYSIS")
print("=" * 100)
print("Testing: 1h, 2h, 3h, 6h, 8h, 12h")
print("Finding optimal timeframe for dual direction trading")
print("=" * 100)

settings = Settings()
connector = ExchangeConnector(settings)
connector.connect()
data_fetcher = DataFetcher(connector)

# Timeframes to test with appropriate data periods
timeframes_config = {
    '1h': 180,   # 180 days
    '2h': 270,   # 270 days
    '3h': 365,   # 365 days
    '6h': 545,   # 545 days (1.5 years)
    '8h': 730,   # 730 days (2 years)
    '12h': 730,  # 730 days (2 years)
}

all_results = []

for timeframe, days in timeframes_config.items():
    print(f"\n{'=' * 100}")
    print(f"TESTING TIMEFRAME: {timeframe}")
    print(f"{'=' * 100}\n")

    print(f"Fetching {timeframe} data ({days} days)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    try:
        df = data_fetcher.fetch_ohlcv_dataframe(
            symbol='BTC/USDT',
            timeframe=timeframe,
            since=start_date,
            until=end_date
        )
        print(f"Loaded {len(df)} candles\n")
    except Exception as e:
        print(f"Error fetching {timeframe} data: {e}")
        continue

    if len(df) < 100:
        print(f"Not enough data for {timeframe}")
        continue

    # Configurations optimized per timeframe
    configs = []

    # Adjust parameters based on timeframe
    if timeframe in ['1h', '2h']:
        # Shorter timeframes - tighter stops
        configs.append((f"{timeframe} Balanced", {
            'long_rsi_oversold': 30, 'long_rsi_extreme': 20, 'long_stoch_oversold': 20,
            'long_stop_loss_pct': 4.0, 'long_take_profit_pct': 8.0,
            'short_rsi_overbought': 70, 'short_stop_loss_pct': 2.5, 'short_take_profit_pct': 5.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

        configs.append((f"{timeframe} Conservative", {
            'long_rsi_oversold': 25, 'long_rsi_extreme': 20, 'long_stoch_oversold': 15,
            'long_stop_loss_pct': 5.0, 'long_take_profit_pct': 10.0,
            'short_rsi_overbought': 75, 'short_stop_loss_pct': 3.0, 'short_take_profit_pct': 6.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

        configs.append((f"{timeframe} Aggressive", {
            'long_rsi_oversold': 35, 'long_rsi_extreme': 25, 'long_stoch_oversold': 25,
            'long_stop_loss_pct': 3.0, 'long_take_profit_pct': 6.0,
            'short_rsi_overbought': 65, 'short_stop_loss_pct': 2.0, 'short_take_profit_pct': 4.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

    elif timeframe in ['3h', '4h', '6h']:
        # Medium timeframes - balanced
        configs.append((f"{timeframe} Balanced", {
            'long_rsi_oversold': 30, 'long_rsi_extreme': 20, 'long_stoch_oversold': 20,
            'long_stop_loss_pct': 6.0, 'long_take_profit_pct': 15.0,
            'short_rsi_overbought': 70, 'short_stop_loss_pct': 3.0, 'short_take_profit_pct': 6.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

        configs.append((f"{timeframe} Conservative", {
            'long_rsi_oversold': 25, 'long_rsi_extreme': 20, 'long_stoch_oversold': 15,
            'long_stop_loss_pct': 8.0, 'long_take_profit_pct': 20.0,
            'short_rsi_overbought': 75, 'short_stop_loss_pct': 3.5, 'short_take_profit_pct': 7.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

        configs.append((f"{timeframe} Aggressive", {
            'long_rsi_oversold': 35, 'long_rsi_extreme': 25, 'long_stoch_oversold': 25,
            'long_stop_loss_pct': 5.0, 'long_take_profit_pct': 12.0,
            'short_rsi_overbought': 65, 'short_stop_loss_pct': 2.5, 'short_take_profit_pct': 5.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

    else:  # 8h, 12h
        # Longer timeframes - wider stops
        configs.append((f"{timeframe} Balanced", {
            'long_rsi_oversold': 30, 'long_rsi_extreme': 20, 'long_stoch_oversold': 20,
            'long_stop_loss_pct': 8.0, 'long_take_profit_pct': 20.0,
            'short_rsi_overbought': 70, 'short_stop_loss_pct': 4.0, 'short_take_profit_pct': 8.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

        configs.append((f"{timeframe} Conservative", {
            'long_rsi_oversold': 25, 'long_rsi_extreme': 20, 'long_stoch_oversold': 15,
            'long_stop_loss_pct': 10.0, 'long_take_profit_pct': 25.0,
            'short_rsi_overbought': 75, 'short_stop_loss_pct': 5.0, 'short_take_profit_pct': 10.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

        configs.append((f"{timeframe} Aggressive", {
            'long_rsi_oversold': 35, 'long_rsi_extreme': 25, 'long_stoch_oversold': 25,
            'long_stop_loss_pct': 6.0, 'long_take_profit_pct': 15.0,
            'short_rsi_overbought': 65, 'short_stop_loss_pct': 3.0, 'short_take_profit_pct': 6.0,
            'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': True,
        }))

    # Add LONG-only and SHORT-only for comparison
    configs.append((f"{timeframe} LONG Only", {
        'long_rsi_oversold': 30, 'long_rsi_extreme': 20, 'long_stoch_oversold': 20,
        'long_stop_loss_pct': 6.0, 'long_take_profit_pct': 15.0,
        'short_rsi_overbought': 70, 'short_stop_loss_pct': 3.0, 'short_take_profit_pct': 6.0,
        'require_volume_confirmation': True, 'enable_longs': True, 'enable_shorts': False,
    }))

    configs.append((f"{timeframe} SHORT Only", {
        'long_rsi_oversold': 30, 'long_rsi_extreme': 20, 'long_stoch_oversold': 20,
        'long_stop_loss_pct': 6.0, 'long_take_profit_pct': 15.0,
        'short_rsi_overbought': 70, 'short_stop_loss_pct': 3.0, 'short_take_profit_pct': 6.0,
        'require_volume_confirmation': True, 'enable_longs': False, 'enable_shorts': True,
    }))

    print(f"Testing {len(configs)} configurations...\n")
    print(f"{'Configuration':<35} {'Trades':<8} {'Win%':<8} {'Return%':<10} {'P.F.':<8} {'DD%':<8}")
    print("-" * 95)

    best_for_timeframe = None
    best_return = -999

    for name, params in configs:
        try:
            strategy = DualDirectionStrategy(parameters=params)
            backtest = BacktestEngine(
                strategy=strategy,
                initial_capital=10000.0,
                commission=0.0004,
                slippage=0.001
            )

            result = backtest.run(df.copy(), symbol='BTC/USDT')

            trades = result['total_trades']
            if trades < 10:
                continue

            win_rate = result['win_rate']
            total_return = result['total_return']
            profit_factor = result['profit_factor']
            max_dd = abs(result['max_drawdown'])

            marker = ""
            if profit_factor >= 2.0 and total_return > 15:
                marker = " *** EXCELLENT!"
            elif profit_factor >= 1.7 and total_return > 10:
                marker = " ** VERY GOOD"
            elif profit_factor >= 1.5 and total_return > 5:
                marker = " * GOOD"
            elif profit_factor >= 1.3 and total_return > 2:
                marker = " + PROFIT"

            print(f"{name:<35} {trades:<8d} {win_rate:<8.1f} {total_return:<10.2f} {profit_factor:<8.2f} {max_dd:<8.1f}{marker}")

            if total_return > best_return:
                best_return = total_return
                best_for_timeframe = {
                    'name': name,
                    'timeframe': timeframe,
                    'params': params,
                    'trades': trades,
                    'win_rate': win_rate,
                    'return': total_return,
                    'profit_factor': profit_factor,
                    'max_dd': max_dd,
                    'avg_win': result['avg_win'],
                    'avg_loss': result['avg_loss'],
                    'sharpe': result['sharpe_ratio'],
                }

        except Exception as e:
            print(f"{name:<35} ERROR: {str(e)[:40]}")
            continue

    if best_for_timeframe:
        all_results.append(best_for_timeframe)
        print(f"\nBest for {timeframe}: {best_for_timeframe['name']} - {best_for_timeframe['return']:.2f}% return")

# Final comparison
print("\n" + "=" * 100)
print("TIMEFRAME COMPARISON - BEST CONFIGURATION FOR EACH")
print("=" * 100)

if all_results:
    # Sort by return
    all_results.sort(key=lambda x: x['return'], reverse=True)

    print(f"\n{'Rank':<6} {'Timeframe':<12} {'Configuration':<35} {'Return%':<10} {'P.F.':<8} {'Trades':<8}")
    print("-" * 95)

    for idx, r in enumerate(all_results, 1):
        marker = ""
        if r['return'] > 10:
            marker = " ✓✓✓"
        elif r['return'] > 5:
            marker = " ✓✓"
        elif r['return'] > 2:
            marker = " ✓"
        print(f"{idx:<6} {r['timeframe']:<12} {r['name']:<35} {r['return']:<10.2f} {r['profit_factor']:<8.2f} {r['trades']:<8d}{marker}")

    # Best overall
    best = all_results[0]

    print("\n" + "=" * 100)
    print("🏆 WINNER: BEST TIMEFRAME & CONFIGURATION")
    print("=" * 100)

    print(f"\nTimeframe: {best['timeframe']}")
    print(f"Configuration: {best['name']}")
    print("\nPerformance:")
    print(f"  Total Return: {best['return']:.2f}%")
    print(f"  Profit Factor: {best['profit_factor']:.2f}")
    print(f"  Win Rate: {best['win_rate']:.1f}%")
    print(f"  Total Trades: {best['trades']}")
    print(f"  Max Drawdown: {best['max_dd']:.1f}%")
    print(f"  Sharpe Ratio: {best['sharpe']:.2f}")

    if best['avg_loss'] != 0:
        rr = abs(best['avg_win'] / best['avg_loss'])
        print(f"  Risk/Reward: 1:{rr:.2f}")

    print(f"  Average Win: {best['avg_win']:.2f}%")
    print(f"  Average Loss: {best['avg_loss']:.2f}%")

    # Top 3 comparison
    print("\n" + "=" * 100)
    print("TOP 3 TIMEFRAMES")
    print("=" * 100)

    print(f"\n{'Rank':<6} {'Timeframe':<12} {'Return%':<12} {'P.F.':<8} {'Win%':<8} {'Drawdown%':<12}")
    print("-" * 70)

    for idx, r in enumerate(all_results[:3], 1):
        print(f"{idx:<6} {r['timeframe']:<12} {r['return']:<12.2f} {r['profit_factor']:<8.2f} {r['win_rate']:<8.1f} {r['max_dd']:<12.1f}")

    # Save best config
    if best['return'] > 5 and best['profit_factor'] >= 1.5:
        config_filename = f"config_dual_direction_{best['timeframe']}_optimized.yaml"

        config_content = f"""# Dual Direction Strategy - {best['timeframe'].upper()} OPTIMIZED
# Best performing configuration found through comprehensive testing
# Performance: {best['return']:.2f}% return, {best['win_rate']:.1f}% win rate, P.F. {best['profit_factor']:.2f}

exchange:
  name: binance
  testnet: true
  futures: true
  rate_limit_delay: 0.1

strategy:
  name: dual_direction
  parameters:
"""
        for key, value in best['params'].items():
            config_content += f"    {key}: {value}\n"

        config_content += f"""
risk:
  risk_per_trade_percent: 1.0
  max_position_size_percent: 20.0
  max_concurrent_positions: 1
  max_trades_per_day: 10
  daily_loss_limit_percent: 5.0
  max_consecutive_losses: 3
  max_drawdown_percent: {min(30, best['max_dd'] * 1.5):.1f}

trading:
  pairs:
    - BTC/USDT
  default_timeframe: {best['timeframe']}
  use_futures: true
  leverage: 1
  use_limit_orders: false

backtesting:
  initial_capital: 10000.0
  commission: 0.0004
  slippage: 0.001

monitoring:
  telegram_alerts: true
  log_level: INFO

# PERFORMANCE ({best['timeframe']} timeframe):
#   Return: {best['return']:.2f}%
#   Profit Factor: {best['profit_factor']:.2f}
#   Win Rate: {best['win_rate']:.1f}%
#   Max Drawdown: {best['max_dd']:.1f}%
#   Total Trades: {best['trades']}
"""

        with open(config_filename, 'w', encoding='utf-8') as f:
            f.write(config_content)

        print(f"\n✓ Configuration saved: {config_filename}")

        print("\n" + "=" * 100)
        print("READY FOR PAPER TRADING")
        print("=" * 100)
        print(f"""
Start paper trading with the winning configuration:
  python main.py paper --pair BTC/USDT --timeframe {best['timeframe']}

Or validate on different periods:
  python main.py backtest --pair BTC/USDT --timeframe {best['timeframe']} --start 2022-01-01 --end 2022-12-31
  python main.py backtest --pair BTC/USDT --timeframe {best['timeframe']} --start 2023-01-01 --end 2023-12-31
        """)

    # Create summary comparison
    print("\n" + "=" * 100)
    print("TIMEFRAME CHARACTERISTICS")
    print("=" * 100)

    print("\nFast Timeframes (1h-2h):")
    fast_tf = [r for r in all_results if r['timeframe'] in ['1h', '2h']]
    if fast_tf:
        for r in fast_tf:
            print(f"  {r['timeframe']}: {r['return']:.2f}% return, {r['trades']} trades")

    print("\nMedium Timeframes (3h-6h):")
    medium_tf = [r for r in all_results if r['timeframe'] in ['3h', '4h', '6h']]
    if medium_tf:
        for r in medium_tf:
            print(f"  {r['timeframe']}: {r['return']:.2f}% return, {r['trades']} trades")

    print("\nSlow Timeframes (8h-12h):")
    slow_tf = [r for r in all_results if r['timeframe'] in ['8h', '12h']]
    if slow_tf:
        for r in slow_tf:
            print(f"  {r['timeframe']}: {r['return']:.2f}% return, {r['trades']} trades")

else:
    print("\n! No profitable configurations found")

print("\n" + "=" * 100)
print("COMPREHENSIVE TIMEFRAME ANALYSIS COMPLETE")
print("=" * 100)
