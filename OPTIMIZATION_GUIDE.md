# Strategy Optimization Guide

## Overview

The optimization script uses **grid search** to find the best trading strategy parameters by testing different combinations on historical data.

## Quick Start

```bash
# Basic optimization (tests ~200 combinations)
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31

# Quick test (tests ~8 combinations)
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --quick

# Optimize for different metric
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --ranking total_return

# Custom parameter ranges
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 \
    --fast-periods 5,10,15 --slow-periods 25,30,35,40
```

---

## Parameters Being Optimized

### Moving Average Periods
- **Fast MA**: 5, 10, 15, 20 (default)
- **Slow MA**: 20, 30, 40, 50 (default)

### RSI Thresholds
- **Overbought**: 65, 70, 75 (default)
- **Oversold**: 25, 30, 35 (default)

### Strategy Filters
- **RSI Filter**: On/Off
- **MACD Filter**: On/Off

---

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--pair` | Trading pair | BTC/USDT |
| `--start` | Start date (YYYY-MM-DD) | Required |
| `--end` | End date (YYYY-MM-DD) | Required |
| `--timeframe` | Timeframe (1m, 5m, 15m, 1h, 4h, 1d) | 1h |
| `--initial-capital` | Starting capital | 1000 |
| `--ranking` | Metric to rank by | sharpe_ratio |
| `--min-trades` | Minimum trades required | 10 |
| `--fast-periods` | Fast MA periods (comma-separated) | 5,10,15,20 |
| `--slow-periods` | Slow MA periods (comma-separated) | 20,30,40,50 |
| `--quick` | Quick mode (fewer combinations) | False |

---

## Ranking Metrics

Choose which metric to optimize for with `--ranking`:

- **`sharpe_ratio`** (default) - Risk-adjusted returns (best for consistent performance)
- **`total_return`** - Maximum profit (ignores risk)
- **`sortino_ratio`** - Downside risk-adjusted returns
- **`calmar_ratio`** - Return vs max drawdown
- **`profit_factor`** - Ratio of gross profit to gross loss

---

## Examples

### 1. Find Best Sharpe Ratio (Default)

```bash
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31
```

**Best for:** Consistent risk-adjusted returns

### 2. Maximize Total Returns

```bash
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --ranking total_return
```

**Best for:** Maximum profit (may have higher risk)

### 3. Minimize Downside Risk

```bash
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --ranking sortino_ratio
```

**Best for:** Conservative trading with lower drawdowns

### 4. Quick Test (Fast)

```bash
python optimize_strategy.py --start 2024-06-01 --end 2024-12-31 --quick
```

**Tests only 8 combinations** - Good for quick testing

### 5. Optimize for Different Pair

```bash
python optimize_strategy.py --pair ETH/USDT --start 2024-01-01 --end 2024-12-31
```

### 6. Custom Parameter Ranges

```bash
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 \
    --fast-periods 8,12,16 \
    --slow-periods 26,30,34,38 \
    --min-trades 15
```

### 7. Optimize 5-Minute Timeframe

```bash
python optimize_strategy.py --start 2024-06-01 --end 2024-12-31 --timeframe 5m
```

---

## Understanding Results

### Output Format

```
TOP 10 PARAMETER COMBINATIONS
================================================================================

Rank #1
--------------------------------------------------------------------------------
Parameters:
  Fast MA: 10, Slow MA: 30
  RSI Overbought: 70, RSI Oversold: 30
  RSI Filter: True, MACD Filter: True

Performance:
  Total Return: 45.23%
  Sharpe Ratio: 1.85
  Sortino Ratio: 2.34
  Calmar Ratio: 1.52
  Max Drawdown: -8.45%
  Win Rate: 62.5%
  Profit Factor: 2.15
  Number of Trades: 48
  Average Trade: 0.94%
  Final Capital: $1452.30
```

### Key Metrics Explained

**Total Return**: Overall profit percentage
- Higher is better
- Example: 45% = turned $1000 into $1450

**Sharpe Ratio**: Risk-adjusted returns
- Above 1.0 = Good
- Above 2.0 = Excellent
- Above 3.0 = Outstanding

**Sortino Ratio**: Like Sharpe, but only penalizes downside volatility
- Higher is better
- More relevant than Sharpe for trading

**Max Drawdown**: Largest peak-to-trough decline
- Lower (closer to 0) is better
- -10% is acceptable, -20% is risky

**Win Rate**: Percentage of profitable trades
- 50%+ is decent
- 60%+ is good
- 70%+ is excellent

**Profit Factor**: Gross profit / Gross loss
- Above 1.0 = Profitable
- Above 1.5 = Good
- Above 2.0 = Excellent

**Number of Trades**: Total trades executed
- Too few (< 10) = May be overfit
- 20-100 = Good sample size
- Too many (> 500) = High transaction costs

---

## Output Files

Results are saved to `reports/` directory:

### 1. CSV File
`optimization_results_YYYYMMDD_HHMMSS.csv`

Contains all tested combinations with full metrics. Open in Excel for analysis.

**Columns:**
- All parameter combinations
- All performance metrics
- Easy to filter and sort

### 2. JSON File
`optimization_results_YYYYMMDD_HHMMSS_top10.json`

Top 10 results in JSON format.

**Use case:** Import best parameters into your config

---

## Applying Results

### Option 1: Update config.yaml

The script prints recommended settings:

```yaml
strategy:
  name: ma_crossover
  parameters:
    fast_period: 10
    slow_period: 30
    use_rsi_filter: true
    rsi_period: 14
    rsi_overbought: 70
    rsi_oversold: 30
    use_macd_filter: true
```

Copy this into your `config.yaml` file.

### Option 2: Verify with Backtest

```bash
# Test the best parameters found
python main.py backtest --pair BTC/USDT --start 2024-01-01 --end 2024-12-31
```

### Option 3: Out-of-Sample Testing

**Important:** Don't just use the optimized parameters blindly!

```bash
# Optimize on first 6 months
python optimize_strategy.py --start 2024-01-01 --end 2024-06-30

# Test on second 6 months (out-of-sample)
python main.py backtest --pair BTC/USDT --start 2024-07-01 --end 2024-12-31
```

**If performance is similar**, parameters are likely robust.
**If performance drops significantly**, parameters may be overfit.

---

## Best Practices

### 1. Use Enough Data

❌ **Bad:** 1 month of data
✅ **Good:** 6-12 months of data
✅ **Better:** Multiple years + different market conditions

```bash
# At least 6 months
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31
```

### 2. Walk-Forward Optimization

Test on multiple periods:

```bash
# Optimize on 2023
python optimize_strategy.py --start 2023-01-01 --end 2023-12-31

# Validate on 2024
python main.py backtest --pair BTC/USDT --start 2024-01-01 --end 2024-12-31
```

### 3. Different Market Conditions

Test on:
- Bull markets
- Bear markets
- Sideways markets

```bash
# Bull market (e.g., Q1 2024)
python optimize_strategy.py --start 2024-01-01 --end 2024-03-31

# Bear market (e.g., Q2 2024)
python optimize_strategy.py --start 2024-04-01 --end 2024-06-30
```

### 4. Minimum Trades

Don't trust parameters with too few trades:

```bash
# Require at least 20 trades
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --min-trades 20
```

### 5. Multiple Pairs

Optimize for each pair separately:

```bash
# BTC/USDT
python optimize_strategy.py --pair BTC/USDT --start 2024-01-01 --end 2024-12-31

# ETH/USDT
python optimize_strategy.py --pair ETH/USDT --start 2024-01-01 --end 2024-12-31
```

### 6. Multiple Timeframes

```bash
# 1-hour timeframe
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --timeframe 1h

# 4-hour timeframe
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --timeframe 4h
```

---

## Performance Tips

### Quick Mode for Testing

```bash
# Fast test (< 1 minute)
python optimize_strategy.py --start 2024-06-01 --end 2024-12-31 --quick
```

Tests only 8 combinations instead of 200+

### Reduce Parameter Ranges

```bash
# Test fewer values
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 \
    --fast-periods 10,15 \
    --slow-periods 30,40
```

### Shorter Time Period

```bash
# 3 months instead of 12
python optimize_strategy.py --start 2024-09-01 --end 2024-12-31
```

---

## Common Issues

### Issue: "No valid results found"

**Cause:** Not enough trades generated

**Solutions:**
```bash
# Lower minimum trades
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --min-trades 5

# Use longer time period
python optimize_strategy.py --start 2023-01-01 --end 2024-12-31

# Use shorter timeframe (more frequent trades)
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --timeframe 15m
```

### Issue: Too Slow

**Solutions:**
```bash
# Use quick mode
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --quick

# Shorter period
python optimize_strategy.py --start 2024-09-01 --end 2024-12-31

# Fewer parameters
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 \
    --fast-periods 10 --slow-periods 30
```

### Issue: All Results Similar

**Cause:** Parameters don't matter much for this market

**Solutions:**
- Try different time period
- Try different pair
- Try different timeframe
- Consider strategy may not work well for this asset

---

## Avoiding Overfitting

### Warning Signs

❌ **Overfit:**
- Perfect results (90%+ win rate, 5+ Sharpe)
- Very specific parameters (e.g., RSI=73 vs RSI=72 huge difference)
- Works great in-sample, terrible out-of-sample

✅ **Robust:**
- Good but not perfect results (60-70% win rate, 1.5-3 Sharpe)
- Similar performance across multiple periods
- Nearby parameters give similar results

### How to Avoid

1. **Use out-of-sample testing**
   ```bash
   # Train on 2023
   python optimize_strategy.py --start 2023-01-01 --end 2023-12-31

   # Test on 2024
   python main.py backtest --start 2024-01-01 --end 2024-12-31
   ```

2. **Check parameter sensitivity**
   - If Fast=10 gives Sharpe=2.5 and Fast=11 gives Sharpe=0.5, it's overfit
   - Robust parameters should have gradual changes

3. **Minimum sample size**
   - At least 30 trades
   - At least 6 months of data

4. **Multiple market conditions**
   - Bull, bear, and sideways markets
   - Different volatility regimes

---

## Advanced: Custom Optimization

Want to optimize different parameters? Edit `optimize_strategy.py`:

```python
# Around line 35, modify generate_parameter_grid():
if fast_periods is None:
    fast_periods = [7, 14, 21]  # Your custom values
```

---

## Next Steps After Optimization

1. ✅ Run optimization
2. ✅ Review top 10 results
3. ✅ Update config.yaml with best parameters
4. ✅ Run full backtest to verify
5. ✅ Test on out-of-sample data
6. ✅ Paper trade for 1-2 weeks
7. ✅ Go live with small position size

---

## Quick Reference

```bash
# Standard optimization
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31

# Quick test
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --quick

# Maximize returns
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --ranking total_return

# Minimize risk
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 --ranking sortino_ratio

# Different pair
python optimize_strategy.py --pair ETH/USDT --start 2024-01-01 --end 2024-12-31

# Custom parameters
python optimize_strategy.py --start 2024-01-01 --end 2024-12-31 \
    --fast-periods 5,10,15 --slow-periods 20,30,40 --min-trades 15
```

---

**Happy Optimizing!** 🎯

Remember: Past performance doesn't guarantee future results. Always paper trade before going live!
