"""
Position sizing calculator based on risk management rules.
"""
import logging
from typing import Optional
from decimal import Decimal

from ..config.settings import Settings
from ..config.constants import PositionSizingMethod

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Calculate position sizes based on risk management parameters.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize position sizer.

        Args:
            settings: Application settings
        """
        self.settings = settings or Settings()

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        risk_percent: Optional[float] = None,
        volatility: Optional[float] = None,
    ) -> float:
        """
        Calculate position size based on configured method.

        Args:
            account_balance: Total account balance
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price (optional, for volatility sizing)
            risk_percent: Risk percentage (optional, uses config default)
            volatility: ATR or volatility measure (optional, for volatility sizing)

        Returns:
            Position size in quote currency
        """
        if account_balance <= 0:
            logger.warning("Account balance is zero or negative")
            return 0.0

        if entry_price <= 0:
            logger.warning("Entry price must be positive")
            return 0.0

        # Get risk percentage
        if risk_percent is None:
            risk_percent = self.settings.max_position_size_percent

        # Calculate based on method
        method = self.settings.position_sizing_method

        if method == PositionSizingMethod.FIXED.value:
            return self._calculate_fixed_size(account_balance, risk_percent)

        elif method == PositionSizingMethod.VOLATILITY.value:
            return self._calculate_volatility_based_size(
                account_balance,
                entry_price,
                stop_loss_price,
                risk_percent,
                volatility
            )

        else:
            logger.warning(f"Unknown sizing method: {method}, using fixed")
            return self._calculate_fixed_size(account_balance, risk_percent)

    def _calculate_fixed_size(
        self,
        account_balance: float,
        risk_percent: float
    ) -> float:
        """
        Calculate fixed percentage position size.

        Args:
            account_balance: Total account balance
            risk_percent: Percentage of account to risk

        Returns:
            Position size
        """
        position_size = account_balance * (risk_percent / 100.0)

        logger.debug(
            f"Fixed position size: {position_size:.2f} "
            f"({risk_percent}% of {account_balance:.2f})"
        )

        return position_size

    def _calculate_volatility_based_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: Optional[float],
        risk_percent: float,
        volatility: Optional[float]
    ) -> float:
        """
        Calculate position size based on volatility (ATR-based).

        Uses the formula:
        Position Size = (Account Balance * Risk %) / (Entry Price - Stop Loss Price)

        Args:
            account_balance: Total account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_percent: Risk percentage
            volatility: ATR or volatility measure

        Returns:
            Position size
        """
        if stop_loss_price is None or stop_loss_price <= 0:
            # Fallback to fixed sizing if no stop loss
            logger.debug("No stop loss provided, using fixed sizing")
            return self._calculate_fixed_size(account_balance, risk_percent)

        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit == 0:
            logger.warning("Risk per unit is zero, using fixed sizing")
            return self._calculate_fixed_size(account_balance, risk_percent)

        # Calculate position size
        risk_amount = account_balance * (risk_percent / 100.0)
        position_size = risk_amount / risk_per_unit

        logger.debug(
            f"Volatility-based position size: {position_size:.2f} "
            f"(risk per unit: {risk_per_unit:.2f})"
        )

        return position_size

    def calculate_quantity(
        self,
        position_size: float,
        entry_price: float,
        min_quantity: float = 0.0,
        quantity_precision: int = 8
    ) -> float:
        """
        Convert position size to quantity of asset.

        Args:
            position_size: Position size in quote currency
            entry_price: Entry price
            min_quantity: Minimum quantity allowed by exchange
            quantity_precision: Number of decimal places for quantity

        Returns:
            Quantity to trade
        """
        if entry_price <= 0:
            return 0.0

        quantity = position_size / entry_price

        # Round to precision
        quantity = round(quantity, quantity_precision)

        # Ensure minimum quantity
        if quantity < min_quantity:
            logger.warning(
                f"Calculated quantity {quantity} below minimum {min_quantity}"
            )
            return 0.0

        return quantity

    def validate_position_size(
        self,
        position_size: float,
        account_balance: float,
        symbol: str
    ) -> bool:
        """
        Validate if position size is within acceptable limits.

        Args:
            position_size: Position size to validate
            account_balance: Account balance
            symbol: Trading symbol

        Returns:
            True if position size is valid
        """
        if position_size <= 0:
            logger.warning(f"Position size must be positive: {position_size}")
            return False

        # Check maximum position size
        max_size = account_balance * (self.settings.max_position_size_percent / 100.0)
        if position_size > max_size:
            logger.warning(
                f"Position size {position_size:.2f} exceeds maximum {max_size:.2f}"
            )
            return False

        # Check minimum notional value (e.g., $10)
        min_notional = 10.0
        if position_size < min_notional:
            logger.warning(
                f"Position size {position_size:.2f} below minimum notional {min_notional}"
            )
            return False

        return True
