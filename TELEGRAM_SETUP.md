# Telegram Alerts Setup Guide

Get instant notifications on your phone when your bot executes trades!

## What You'll Receive

✅ **Trade Alerts:**
- 🟢 BUY signals with entry price and quantity
- 🔴 SELL signals with exit price and P&L
- 💰 Profit/loss for each trade

✅ **Status Notifications:**
- 🚀 Bot start/stop events
- ⚠️ Error alerts
- 📊 Daily performance summaries

✅ **Risk Alerts:**
- Stop loss triggers
- Daily loss limit warnings
- Position size alerts

---

## Quick Setup (5 minutes)

### Step 1: Create Your Telegram Bot

1. Open **Telegram** app
2. Search for **@BotFather**
3. Start a chat and send: `/newbot`
4. Choose a **name** for your bot (e.g., "My Trading Bot")
5. Choose a **username** (must end with "bot", e.g., "mytrading_bot")
6. **Copy the Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Start a chat with it
3. It will send you your **Chat ID** (a number like: `123456789`)
4. **Copy this number**

### Step 3: Configure Your Bot

**Option A - Automated Setup:**

```bash
cd /c/temp/Crypto_Bot
chmod +x setup_telegram.sh
./setup_telegram.sh
```

**Option B - Manual Setup:**

Edit `.env` file and replace:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

With your actual credentials:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### Step 4: Test Connection

```bash
cd /c/temp/Crypto_Bot
source venv311/Scripts/activate
python test_telegram.py
```

You should receive a test message on Telegram!

### Step 5: Restart Your Bot

```bash
cd /c/temp/Crypto_Bot
./stop_paper_trading.sh
./start_paper_trading.sh
```

---

## Example Alerts

### Trade Entry Alert
```
🟢 BUY BTC/USDT
Price: $62,450.00
Quantity: 0.01600
Reason: RSI oversold (28.4), near lower BB
Time: 2026-03-02 14:30:00
```

### Trade Exit Alert
```
🔴 SELL BTC/USDT
Price: $71,817.50
Quantity: 0.01600
💰 P&L: +$149.88
Reason: Take profit target reached (+15%)
Time: 2026-03-03 08:15:00
```

### Daily Summary
```
📊 Daily Trading Summary

Date: 2026-03-02
Trades: 2
💰 P&L: +$285.50
Win Rate: 100.0%
Open Positions: 0
Total Equity: $10,285.50
```

---

## Troubleshooting

### "Telegram credentials not configured"
- Make sure you updated `.env` with real values (not placeholders)
- Check that there are no extra spaces around the values
- Restart the bot after updating .env

### "Failed to send message"
- Verify your Bot Token is correct
- Verify your Chat ID is correct
- Make sure you started a chat with your bot (send `/start` to it)
- Check your internet connection

### "Bot not enabled"
- Ensure `telegram_alerts: true` in `config.yaml` (already set ✓)
- Check that both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set in `.env`

### Not receiving alerts
1. Send `/start` to your bot on Telegram
2. Run `python test_telegram.py` to verify connection
3. Check bot logs: `tail -f paper_trading_6h.log | grep -i telegram`

---

## Privacy & Security

✅ **Your credentials are safe:**
- Bot token is stored locally in `.env` (not committed to git)
- Only you can message your bot
- Messages are sent directly to your Chat ID
- No data is shared with third parties

✅ **Bot permissions:**
- Your bot can only send messages to you
- It cannot read other people's messages
- It has no access to your Telegram contacts

---

## Advanced Configuration

In `config.yaml`, you can customize alert types:

```yaml
monitoring:
  telegram_alerts: true
  alert_on_trade: true          # Trade entry/exit alerts
  alert_on_error: true           # Error alerts
  alert_on_daily_summary: true   # Daily performance summary
  alert_on_bot_events: true      # Bot start/stop
```

---

## Next Steps

Once Telegram is configured:

1. ✅ Test connection: `python test_telegram.py`
2. ✅ Restart bot: `./stop_paper_trading.sh && ./start_paper_trading.sh`
3. ✅ Wait for first trade alert!
4. 📱 Keep Telegram notifications enabled on your phone

You'll be notified instantly when your bot finds a trading opportunity!
