"""
Risk management system with safety checks and limits.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..config.settings import Settings
from ..config.constants import ExitReason

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Enforce risk management rules and safety limits.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize risk manager."""
        self.settings = settings or Settings()
        self.daily_pnl = 0.0
        self.daily_pnl_date = datetime.now().date()
        self.circuit_breaker_active = False

    def can_open_position(
        self,
        current_positions: int,
        account_balance: float,
        proposed_position_size: float
    ) -> tuple[bool, str]:
        """
        Check if can open a new position.

        Returns:
            (can_open, reason)
        """
        # Check max concurrent positions
        if current_positions >= self.settings.max_concurrent_positions:
            return False, f"Max concurrent positions reached ({current_positions})"

        # Check daily loss limit
        if self._is_daily_loss_limit_exceeded():
            return False, "Daily loss limit exceeded"

        # Check circuit breaker
        if self.circuit_breaker_active:
            return False, "Circuit breaker active"

        # Check position size vs balance
        if proposed_position_size > account_balance:
            return False, "Insufficient balance"

        return True, "OK"

    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
        use_trailing: bool = True
    ) -> float:
        """Calculate stop loss price."""
        stop_pct = self.settings.stop_loss_percent / 100.0

        if side == "buy":
            return entry_price * (1 - stop_pct)
        else:
            return entry_price * (1 + stop_pct)

    def calculate_take_profit(
        self,
        entry_price: float,
        side: str
    ) -> float:
        """Calculate take profit price."""
        tp_pct = self.settings.take_profit_percent / 100.0

        if side == "buy":
            return entry_price * (1 + tp_pct)
        else:
            return entry_price * (1 - tp_pct)

    def update_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        current_stop: float,
        side: str
    ) -> float:
        """Update trailing stop loss."""
        if not self.settings.use_trailing_stop:
            return current_stop

        trail_pct = self.settings.trailing_stop_percent / 100.0

        if side == "buy":
            new_stop = current_price * (1 - trail_pct)
            return max(current_stop, new_stop)
        else:
            new_stop = current_price * (1 + trail_pct)
            return min(current_stop, new_stop)

    def should_close_position(
        self,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        side: str
    ) -> tuple[bool, Optional[ExitReason]]:
        """
        Check if position should be closed.

        Returns:
            (should_close, exit_reason)
        """
        if side == "buy":
            if current_price <= stop_loss:
                return True, ExitReason.STOP_LOSS
            if current_price >= take_profit:
                return True, ExitReason.TAKE_PROFIT
        else:
            if current_price >= stop_loss:
                return True, ExitReason.STOP_LOSS
            if current_price <= take_profit:
                return True, ExitReason.TAKE_PROFIT

        return False, None

    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily PnL tracker."""
        today = datetime.now().date()

        if today != self.daily_pnl_date:
            self.daily_pnl = 0.0
            self.daily_pnl_date = today

        self.daily_pnl += pnl

    def _is_daily_loss_limit_exceeded(self) -> bool:
        """Check if daily loss limit is exceeded."""
        return self.daily_pnl < -abs(self.settings.daily_loss_limit_percent)

    def check_circuit_breaker(self, price_change_percent: float) -> bool:
        """
        Check if circuit breaker should trigger.

        Args:
            price_change_percent: Price change in one candle

        Returns:
            True if circuit breaker triggered
        """
        if not self.settings.enable_circuit_breaker:
            return False

        threshold = self.settings.circuit_breaker_volatility_threshold

        if abs(price_change_percent) > threshold:
            self.circuit_breaker_active = True
            logger.warning(
                f"Circuit breaker triggered! Price change: {price_change_percent:.2f}%"
            )
            return True

        return False

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker."""
        self.circuit_breaker_active = False
        logger.info("Circuit breaker reset")
