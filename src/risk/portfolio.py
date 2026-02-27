"""
Portfolio tracker for managing positions and calculating metrics.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trading position."""
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    unrealized_pnl: float = 0.0
    highest_price: float = field(default=0.0)
    lowest_price: float = field(default=float('inf'))

    def update_pnl(self, current_price: float) -> None:
        """Update unrealized PnL."""
        if self.side == "buy":
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity

        # Track price extremes
        self.highest_price = max(self.highest_price, current_price)
        self.lowest_price = min(self.lowest_price, current_price)

    def get_pnl_percent(self) -> float:
        """Get PnL as percentage of entry value."""
        entry_value = self.entry_price * self.quantity
        if entry_value == 0:
            return 0.0
        return (self.unrealized_pnl / entry_value) * 100


class Portfolio:
    """
    Track and manage trading portfolio.
    """

    def __init__(self, initial_balance: float = 10000.0):
        """Initialize portfolio."""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.equity = initial_balance

    def add_position(self, position: Position) -> None:
        """Add a new position."""
        self.positions[position.symbol] = position
        logger.info(
            f"Added position: {position.symbol} {position.side} "
            f"{position.quantity} @ {position.entry_price}"
        )

    def remove_position(self, symbol: str) -> Optional[Position]:
        """Remove and return a position."""
        position = self.positions.pop(symbol, None)
        if position:
            logger.info(f"Removed position: {symbol}")
        return position

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if has position in symbol."""
        return symbol in self.positions

    def update_position_prices(self, prices: Dict[str, float]) -> None:
        """Update all positions with current prices."""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_pnl(prices[symbol])

    def calculate_total_equity(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio equity."""
        self.update_position_prices(prices)

        total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )

        self.equity = self.balance + total_unrealized_pnl
        return self.equity

    def get_open_positions_count(self) -> int:
        """Get number of open positions."""
        return len(self.positions)

    def get_total_exposure(self) -> float:
        """Calculate total exposure (sum of position values)."""
        return sum(
            pos.entry_price * pos.quantity
            for pos in self.positions.values()
        )

    def get_exposure_by_symbol(self, symbol: str) -> float:
        """Get exposure for a specific symbol."""
        position = self.get_position(symbol)
        if position:
            return position.entry_price * position.quantity
        return 0.0

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary statistics."""
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())

        return {
            "initial_balance": self.initial_balance,
            "balance": self.balance,
            "equity": self.equity,
            "unrealized_pnl": total_unrealized,
            "open_positions": len(self.positions),
            "total_exposure": self.get_total_exposure(),
            "pnl_percent": ((self.equity - self.initial_balance) / self.initial_balance) * 100
        }

    def update_balance(self, amount: float) -> None:
        """Update balance (add realized PnL)."""
        self.balance += amount
        logger.debug(f"Balance updated: {self.balance:.2f} (change: {amount:+.2f})")
