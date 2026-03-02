"""
Test Telegram Bot Connection
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.monitoring.telegram_bot import TelegramNotifier

print("=" * 60)
print("TELEGRAM BOT CONNECTION TEST")
print("=" * 60)
print()

try:
    # Initialize settings
    settings = Settings()

    print(f"Bot Token: {settings.telegram_bot_token[:20]}..." if settings.telegram_bot_token else "Not configured")
    print(f"Chat ID: {settings.telegram_chat_id}")
    print(f"Telegram Alerts: {settings.telegram_alerts}")
    print()

    # Initialize Telegram notifier
    notifier = TelegramNotifier(settings)

    if not notifier.enabled:
        print("❌ Telegram bot not enabled")
        print()
        print("To enable:")
        print("1. Set TELEGRAM_BOT_TOKEN in .env")
        print("2. Set TELEGRAM_CHAT_ID in .env")
        print("3. Ensure telegram_alerts: true in config.yaml")
        sys.exit(1)

    print("✓ Telegram bot initialized")
    print()

    # Test connection
    print("Sending test message...")
    if notifier.test_connection():
        print("✅ SUCCESS! Check your Telegram for the test message")
        print()

        # Send sample trade alert
        print("Sending sample trade alert...")
        notifier.send_trade_alert(
            action="BUY",
            symbol="BTC/USDT",
            price=65000.00,
            quantity=0.01,
            reason="Test trade - bot is working!"
        )

        print("✅ Sample trade alert sent!")
        print()
        print("=" * 60)
        print("TELEGRAM SETUP COMPLETE!")
        print("=" * 60)
        print()
        print("You will now receive alerts for:")
        print("  🟢 Trade entries (BUY signals)")
        print("  🔴 Trade exits (SELL signals with P&L)")
        print("  ⚠️  Errors and warnings")
        print("  📊 Daily summaries")
        print("  🚀 Bot start/stop events")

    else:
        print("❌ FAILED! Check your credentials")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
