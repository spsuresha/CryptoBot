"""
Telegram bot for sending trading alerts and notifications.
"""
import logging
from typing import Optional
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError

from ..config.settings import Settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram bot."""

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize Telegram notifier.

        Args:
            settings: Application settings
        """
        self.settings = settings or Settings()
        self.bot: Optional[Bot] = None
        self.enabled = False

        # Initialize bot if credentials are available
        if self.settings.telegram_bot_token and self.settings.telegram_chat_id:
            try:
                self.bot = Bot(token=self.settings.telegram_bot_token)
                self.enabled = self.settings.telegram_alerts
                logger.info("Telegram bot initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            logger.warning("Telegram credentials not configured")

    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Send a message via Telegram.

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)

        Returns:
            True if message sent successfully
        """
        if not self.enabled or not self.bot:
            logger.debug(f"Telegram disabled, skipping message: {message[:50]}...")
            return False

        try:
            # Run async send in event loop
            asyncio.run(self._send_async(message, parse_mode))
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def _send_async(self, message: str, parse_mode: str) -> None:
        """Send message asynchronously."""
        await self.bot.send_message(
            chat_id=self.settings.telegram_chat_id,
            text=message,
            parse_mode=parse_mode
        )

    def send_trade_alert(
        self,
        action: str,
        symbol: str,
        price: float,
        quantity: float,
        pnl: Optional[float] = None,
        reason: str = ""
    ) -> bool:
        """
        Send trade execution alert.

        Args:
            action: 'BUY' or 'SELL'
            symbol: Trading pair
            price: Execution price
            quantity: Trade quantity
            pnl: Profit/loss (for exits)
            reason: Trade reason

        Returns:
            True if sent successfully
        """
        if not self.settings.alert_on_trade:
            return False

        emoji = "🟢" if action == "BUY" else "🔴"
        message = f"{emoji} *{action} {symbol}*\n"
        message += f"Price: `${price:.2f}`\n"
        message += f"Quantity: `{quantity:.6f}`\n"

        if pnl is not None:
            pnl_emoji = "💰" if pnl > 0 else "📉"
            message += f"{pnl_emoji} P&L: `${pnl:+.2f}`\n"

        if reason:
            message += f"Reason: _{reason}_\n"

        message += f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        return self.send_message(message)

    def send_error_alert(self, error_msg: str, context: str = "") -> bool:
        """
        Send error alert.

        Args:
            error_msg: Error message
            context: Additional context

        Returns:
            True if sent successfully
        """
        if not self.settings.alert_on_error:
            return False

        message = f"⚠️ *ERROR ALERT*\n\n"
        message += f"Error: `{error_msg}`\n"

        if context:
            message += f"Context: _{context}_\n"

        message += f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        return self.send_message(message)

    def send_daily_summary(
        self,
        trades_today: int,
        pnl_today: float,
        win_rate: float,
        current_positions: int,
        equity: float
    ) -> bool:
        """
        Send daily performance summary.

        Args:
            trades_today: Number of trades
            pnl_today: Total P&L
            win_rate: Win rate percentage
            current_positions: Open positions
            equity: Current equity

        Returns:
            True if sent successfully
        """
        if not self.settings.alert_on_daily_summary:
            return False

        pnl_emoji = "💰" if pnl_today > 0 else "📉" if pnl_today < 0 else "➖"

        message = f"📊 *Daily Trading Summary*\n\n"
        message += f"Date: `{datetime.now().strftime('%Y-%m-%d')}`\n"
        message += f"Trades: `{trades_today}`\n"
        message += f"{pnl_emoji} P&L: `${pnl_today:+.2f}`\n"
        message += f"Win Rate: `{win_rate:.1f}%`\n"
        message += f"Open Positions: `{current_positions}`\n"
        message += f"Total Equity: `${equity:,.2f}`"

        return self.send_message(message)

    def send_bot_start(self, mode: str) -> bool:
        """
        Send bot start notification.

        Args:
            mode: Trading mode (paper/live)

        Returns:
            True if sent successfully
        """
        emoji = "🚀"
        message = f"{emoji} *Trading Bot Started*\n\n"
        message += f"Mode: `{mode.upper()}`\n"
        message += f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        return self.send_message(message)

    def send_bot_stop(self, reason: str = "Manual stop") -> bool:
        """
        Send bot stop notification.

        Args:
            reason: Stop reason

        Returns:
            True if sent successfully
        """
        emoji = "🛑"
        message = f"{emoji} *Trading Bot Stopped*\n\n"
        message += f"Reason: _{reason}_\n"
        message += f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        return self.send_message(message)

    def send_risk_alert(self, alert_type: str, message_text: str) -> bool:
        """
        Send risk management alert.

        Args:
            alert_type: Type of risk alert
            message_text: Alert message

        Returns:
            True if sent successfully
        """
        emoji = "⚡"
        message = f"{emoji} *Risk Alert: {alert_type}*\n\n"
        message += f"{message_text}\n"
        message += f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        return self.send_message(message)

    def test_connection(self) -> bool:
        """
        Test Telegram connection.

        Returns:
            True if connection successful
        """
        if not self.enabled or not self.bot:
            logger.error("Telegram bot not enabled")
            return False

        try:
            test_msg = f"✅ Telegram bot connection test successful!\n"
            test_msg += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self.send_message(test_msg)
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
