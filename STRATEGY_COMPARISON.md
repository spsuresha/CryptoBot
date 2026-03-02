# Trading Strategy Comparison - All Timeframes

## Summary Table

| Timeframe | Best Strategy | Direction | Return % | Profit Factor | Win Rate | Config File |
|-----------|--------------|-----------|----------|---------------|----------|-------------|
| **15m** | Bearish Short | SHORT only | +1.34% | **1.77** ✓ | 42.9% | config_best_15m.yaml |
| **4h** | Dual Direction | LONG + SHORT | **+13.90%** ✓ | **1.63** ✓ | 37.7% | config_dual_direction_optimized.yaml |
| **1d** | Buy Low Sell High | LONG only | **+8.93%** ✓ | **1.69** ✓ | ~50% | config_buy_low_sell_high_optimized.yaml |

## Detailed Analysis

### 15-Minute Timeframe

**Best Strategy: SHORT-ONLY (Bearish Short)**

```yaml
Performance:
  Return: +1.34%
  Profit Factor: 1.77 (TARGET MET ✓)
  Win Rate: 42.9%
  Risk/Reward: 1:2.36
  Trades: 14 in 60 days
  Max Drawdown: 20.8%
```

**Why SHORT-only?**
- LONG signals: -26.30% (fail badly on 15m)
- SHORT signals: +1.34% (work well)
- Dual direction: -7.57% (LONG losses wipe out SHORT gains)

**How it works:**
- Enters SHORT when price hits upper Bollinger Band
- RSI > 70 (overbought)
- Shows reversal candlestick pattern
- Volume confirmation required
- Exit: 2% stop loss, 4% take profit

**Use when:**
- You want short-term trading (15 minute candles)
- You expect overbought reversals
- You're comfortable with SHORT-only positions

**Config:** `config_best_15m.yaml` or `config_dual_direction_15m.yaml`

---

### 4-Hour Timeframe

**Best Strategy: DUAL DIRECTION (LONG + SHORT)**

```yaml
Performance:
  Return: +13.90%
  Profit Factor: 1.63 (TARGET MET ✓)
  Win Rate: 37.7%
  Risk/Reward: 1:2.70
  Trades: 77 in 365 days
  Max Drawdown: 26.3%
```

**Why Dual Direction?**
- LONG signals: +9.66% (good)
- SHORT signals: -0.14% (break-even)
- **Dual direction: +13.90% (44% better than LONG-only!)**

**How it works:**
- **LONG**: Enters when RSI < 25, Stochastic < 15, near lower BB
  - Targets: 8% stop loss, 25% take profit
- **SHORT**: Enters when RSI > 75, near upper BB with reversal
  - Targets: 2% stop loss, 4% take profit
- Never holds both directions simultaneously

**Use when:**
- You want medium-term trading (4 hour candles)
- You want to capture both up and down moves
- Current market: ranging or uncertain direction

**Config:** `config_dual_direction_optimized.yaml`

---

### Daily (1d) Timeframe

**Best Strategy: BUY LOW SELL HIGH (LONG-only)**

```yaml
Performance:
  Return: +8.93%
  Profit Factor: 1.69 (TARGET MET ✓)
  Win Rate: ~50%
  Risk/Reward: 1:3
  Trades: ~20-30 per year
  Max Drawdown: ~22%
```

**Why LONG-only?**
- Crypto trends up long-term
- Daily timeframe captures major moves
- Buying dips works consistently
- SHORT signals less reliable on daily

**How it works:**
- Enters LONG when RSI < 30 AND Stochastic < 20
- Must be near lower Bollinger Band
- Requires 2 of 3 indicators to align
- Targets: 10% stop loss, 30% take profit

**Use when:**
- You want swing trading (hold 1-7 days)
- You prefer buying dips in uptrending market
- You want fewer but higher quality trades

**Config:** `config_buy_low_sell_high_optimized.yaml`

---

## Recommendations by Goal

### Goal: Highest Returns
**Winner: 4h Dual Direction (+13.90%)**
- Best overall performance
- Trades both directions
- 44% better than next best strategy

### Goal: Best Risk/Reward
**Winner: 4h Dual Direction (1:2.70)**
- Wins are 2.7x larger than losses
- Asymmetric stops optimize each direction

### Goal: Highest Win Rate
**Winner: 1d Buy Low Sell High (~50%)**
- Wins half the trades
- But still profitable overall
- More psychologically comfortable

### Goal: Highest Profit Factor
**Winner: 15m SHORT-only (1.77)**
- Makes $1.77 for every $1 lost
- But lowest absolute returns (+1.34%)

### Goal: Least Drawdown
**Winner: 15m SHORT-only (20.8%)**
- Tight stops limit losses
- But fewer opportunities

### Goal: Most Trades (Active Trading)
**Winner: 15m SHORT-only (14+ per 60 days)**
- More frequent signals
- But commission impact significant

### Goal: Fewer Trades (Swing Trading)
**Winner: 1d Buy Low Sell High (~20-30 per year)**
- High quality setups only
- Less time monitoring

---

## How to Choose

### I want SHORT-TERM trading (intraday)
→ Use **15m SHORT-only** (config_best_15m.yaml)
- Check charts every hour
- Quick entries and exits
- +1.34%, P.F. 1.77

### I want MEDIUM-TERM trading (swing)
→ Use **4h Dual Direction** (config_dual_direction_optimized.yaml)
- Check charts 2-3 times per day
- Hold positions 1-3 days
- +13.90%, P.F. 1.63

### I want LONG-TERM trading (position)
→ Use **1d Buy Low Sell High** (config_buy_low_sell_high_optimized.yaml)
- Check charts once per day
- Hold positions 3-10 days
- +8.93%, P.F. 1.69

### I want to trade BOTH directions
→ Use **4h Dual Direction** (config_dual_direction_optimized.yaml)
- Only 4h works for dual direction
- 15m and 1d favor single direction

### I want HIGHEST returns
→ Use **4h Dual Direction** (13.90%)

### I want SAFEST option (lowest risk)
→ Use **1d Buy Low Sell High** (well-tested, stable)

---

## Next Steps

1. **Validate Your Choice**
   ```bash
   # Test on 2022 (bear market)
   python main.py backtest --pair BTC/USDT --timeframe <YOUR_TF> --start 2022-01-01 --end 2022-12-31
   
   # Test on 2023 (bull market)
   python main.py backtest --pair BTC/USDT --timeframe <YOUR_TF> --start 2023-01-01 --end 2023-12-31
   ```

2. **Paper Trade** (1-2 weeks)
   ```bash
   python main.py paper --pair BTC/USDT --timeframe <YOUR_TF>
   ```

3. **Compare Paper Trading with Backtest**
   - Similar return? Strategy is robust ✓
   - Very different? May be overfit to recent data ✗

4. **If Successful, Consider Live Trading**
   - Start with small position sizes (0.5% risk per trade)
   - Monitor for 1 month
   - Gradually increase if performing well

---

## Configuration Files

All configuration files are ready to use:

- `config_best_15m.yaml` - 15m SHORT-only
- `config_dual_direction_15m.yaml` - 15m Dual (shorts only mode)
- `config_dual_direction_optimized.yaml` - 4h Dual (LONG+SHORT)
- `config_buy_low_sell_high_optimized.yaml` - 1d LONG-only

Simply copy the one you want to use as `config.yaml`:

```bash
cp config_dual_direction_optimized.yaml config.yaml
python main.py paper --pair BTC/USDT --timeframe 4h
```
