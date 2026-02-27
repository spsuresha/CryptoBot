"""
Trade execution engine for live and paper trading.
"""
import logging
from typing import Dict, Optional
from datetime import datetime

from ..exchange.connector import ExchangeConnector
from ..config.settings import Settings
from ..config.constants import OrderSide, OrderType, TradingMode
from ..monitoring.telegram_bot import TelegramNotifier

logger = logging.getLogger(__name__)


class TradeExecutor:
    """Execute trades on exchange or simulate for paper trading."""

    def __init__(
        self,
        connector: ExchangeConnector,
        settings: Optional[Settings] = None,
        notifier: Optional[TelegramNotifier] = None
    ):
        """
        Initialize trade executor.

        Args:
            connector: Exchange connector
            settings: Application settings
            notifier: Telegram notifier
        """
        self.connector = connector
        self.settings = settings or Settings()
        self.notifier = notifier
        self.paper_orders: Dict = {}  # For paper trading simulation

    def execute_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reason: str = ""
    ) -> Optional[Dict]:
        """
        Execute a market order.

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order quantity
            reason: Trade reason

        Returns:
            Order information or None if failed
        """
        # Validate inputs
        if quantity <= 0:
            logger.error(f"Invalid quantity: {quantity}")
            return None

        # Check if paper trading or dry run
        if self.settings.is_paper_mode():
            return self._simulate_order(symbol, side, quantity, reason)

        if self.settings.is_dry_run_mode():
            return self._log_dry_run_order(symbol, side, quantity, reason)

        # Execute real order
        return self._execute_real_order(symbol, side, quantity, reason)

    def _execute_real_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reason: str
    ) -> Optional[Dict]:
        """Execute real order on exchange."""
        try:
            logger.info(f"Executing {side} order: {quantity} {symbol}")

            # Create market order
            order = self.connector.create_order(
                symbol=symbol,
                order_type=OrderType.MARKET.value,
                side=side,
                amount=quantity
            )

            logger.info(f"Order executed: {order.get('id')}")

            # Send Telegram notification
            if self.notifier:
                self.notifier.send_trade_alert(
                    action=side.upper(),
                    symbol=symbol,
                    price=order.get('price', 0),
                    quantity=quantity,
                    reason=reason
                )

            return order

        except Exception as e:
            logger.error(f"Failed to execute order: {e}")

            if self.notifier:
                self.notifier.send_error_alert(
                    error_msg=str(e),
                    context=f"Order execution: {side} {quantity} {symbol}"
                )

            return None

    def _simulate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reason: str
    ) -> Dict:
        """Simulate order for paper trading."""
        # Get current market price
        ticker = self.connector.fetch_ticker(symbol)
        current_price = ticker['last']

        # Simulate order execution with slippage
        slippage_factor = 1.001 if side == 'buy' else 0.999
        execution_price = current_price * slippage_factor

        order_id = f"paper_{datetime.now().timestamp()}"

        order = {
            'id': order_id,
            'symbol': symbol,
            'type': OrderType.MARKET.value,
            'side': side,
            'amount': quantity,
            'price': execution_price,
            'cost': execution_price * quantity,
            'status': 'closed',
            'timestamp': datetime.now().timestamp(),
            'datetime': datetime.now().isoformat(),
            'fee': {
                'cost': execution_price * quantity * self.settings.commission,
                'currency': 'USDT'
            }
        }

        self.paper_orders[order_id] = order

        logger.info(
            f"PAPER TRADE: {side.upper()} {quantity} {symbol} @ ${execution_price:.2f}"
        )

        # Send notification
        if self.notifier:
            self.notifier.send_trade_alert(
                action=side.upper(),
                symbol=symbol,
                price=execution_price,
                quantity=quantity,
                reason=reason
            )

        return order

    def _log_dry_run_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reason: str
    ) -> Dict:
        """Log order for dry run mode."""
        logger.info(
            f"DRY RUN: Would {side.upper()} {quantity} {symbol} - Reason: {reason}"
        )

        return {
            'id': 'dry_run',
            'symbol': symbol,
            'side': side,
            'amount': quantity,
            'status': 'simulated'
        }

    def execute_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        reason: str = ""
    ) -> Optional[Dict]:
        """
        Execute a limit order.

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Limit price
            reason: Trade reason

        Returns:
            Order information or None if failed
        """
        if self.settings.is_paper_mode() or self.settings.is_dry_run_mode():
            logger.info(f"Limit orders not fully supported in paper/dry-run mode")
            return self._simulate_order(symbol, side, quantity, reason)

        try:
            logger.info(f"Executing {side} limit order: {quantity} {symbol} @ ${price}")

            order = self.connector.create_order(
                symbol=symbol,
                order_type=OrderType.LIMIT.value,
                side=side,
                amount=quantity,
                price=price
            )

            logger.info(f"Limit order placed: {order.get('id')}")
            return order

        except Exception as e:
            logger.error(f"Failed to execute limit order: {e}")
            return None

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair

        Returns:
            True if cancelled successfully
        """
        if self.settings.is_paper_mode():
            if order_id in self.paper_orders:
                del self.paper_orders[order_id]
                logger.info(f"PAPER TRADE: Cancelled order {order_id}")
                return True
            return False

        try:
            result = self.connector.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        current_balance: float
    ) -> tuple[bool, str]:
        """
        Validate order before execution.

        Args:
            symbol: Trading pair
            side: Order side
            quantity: Order quantity
            current_balance: Current account balance

        Returns:
            (is_valid, reason)
        """
        # Check quantity
        if quantity <= 0:
            return False, "Invalid quantity"

        # Get current price
        try:
            ticker = self.connector.fetch_ticker(symbol)
            current_price = ticker['last']
        except Exception as e:
            return False, f"Failed to fetch price: {e}"

        # Check if enough balance
        if side == 'buy':
            required_balance = current_price * quantity * 1.01  # +1% buffer
            if required_balance > current_balance:
                return False, f"Insufficient balance: need ${required_balance:.2f}, have ${current_balance:.2f}"

        # Check minimum notional
        min_notional = 10.0  # $10 minimum
        order_value = current_price * quantity
        if order_value < min_notional:
            return False, f"Order value ${order_value:.2f} below minimum ${min_notional}"

        return True, "Order validated"

    def get_paper_orders(self) -> Dict:
        """Get all paper trading orders."""
        return self.paper_orders.copy()
