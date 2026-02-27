"""
Position manager for tracking and managing open positions.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..database.repository import Repository
from ..risk.portfolio import Position
from ..config.constants import PositionStatus, ExitReason

logger = logging.getLogger(__name__)


class PositionManager:
    """Manage open trading positions."""

    def __init__(self, repository: Optional[Repository] = None):
        """
        Initialize position manager.

        Args:
            repository: Database repository
        """
        self.repository = repository or Repository()
        self.positions: Dict[str, Position] = {}
        self._load_positions_from_db()

    def _load_positions_from_db(self) -> None:
        """Load open positions from database."""
        try:
            db_positions = self.repository.get_all_open_positions()
            for db_pos in db_positions:
                position = Position(
                    symbol=db_pos.symbol,
                    side=db_pos.side,
                    entry_price=db_pos.entry_price,
                    quantity=db_pos.quantity,
                    entry_time=db_pos.entry_time,
                    stop_loss=db_pos.stop_loss,
                    take_profit=db_pos.take_profit,
                    unrealized_pnl=db_pos.unrealized_pnl
                )
                self.positions[db_pos.symbol] = position

            logger.info(f"Loaded {len(self.positions)} positions from database")
        except Exception as e:
            logger.error(f"Failed to load positions from database: {e}")

    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        entry_reason: str = ""
    ) -> Position:
        """
        Open a new position.

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            entry_price: Entry price
            quantity: Position quantity
            stop_loss: Stop loss price
            take_profit: Take profit price
            entry_reason: Reason for entry

        Returns:
            Position object
        """
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.positions[symbol] = position

        # Save to database
        try:
            self.repository.create_position({
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'quantity': quantity,
                'entry_time': position.entry_time,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'status': PositionStatus.OPEN.value
            })

            # Also create trade record
            self.repository.create_trade({
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'quantity': quantity,
                'entry_time': position.entry_time,
                'status': PositionStatus.OPEN.value,
                'notes': entry_reason
            })

            logger.info(f"Opened position: {symbol} {side} {quantity} @ ${entry_price}")

        except Exception as e:
            logger.error(f"Failed to save position to database: {e}")

        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: ExitReason,
        fees: float = 0.0
    ) -> Optional[Position]:
        """
        Close an open position.

        Args:
            symbol: Trading pair
            exit_price: Exit price
            exit_reason: Reason for exit
            fees: Transaction fees

        Returns:
            Closed position or None
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot close position: {symbol} not found")
            return None

        position = self.positions[symbol]

        # Calculate final P&L
        position.update_pnl(exit_price)
        exit_time = datetime.now()

        # Calculate P&L
        if position.side == 'buy':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity

        pnl -= fees
        pnl_percent = (pnl / (position.entry_price * position.quantity)) * 100

        # Update database
        try:
            # Remove from positions table
            self.repository.delete_position(symbol)

            # Update trade record
            open_trades = self.repository.get_open_trades()
            for trade in open_trades:
                if trade.symbol == symbol:
                    self.repository.update_trade(trade.id, {
                        'exit_price': exit_price,
                        'exit_time': exit_time,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                        'fees': fees,
                        'status': PositionStatus.CLOSED.value,
                        'exit_reason': exit_reason.value
                    })
                    break

            logger.info(
                f"Closed position: {symbol} @ ${exit_price}, "
                f"P&L: ${pnl:+.2f} ({pnl_percent:+.2f}%)"
            )

        except Exception as e:
            logger.error(f"Failed to update database on position close: {e}")

        # Remove from active positions
        return self.positions.pop(symbol)

    def update_position_prices(self, prices: Dict[str, float]) -> None:
        """
        Update all positions with current prices.

        Args:
            prices: Dictionary of symbol -> current price
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_pnl(prices[symbol])

                # Update in database
                try:
                    db_position = self.repository.get_position_by_symbol(symbol)
                    if db_position:
                        self.repository.update_trade(db_position.id, {
                            'unrealized_pnl': position.unrealized_pnl
                        })
                except Exception as e:
                    logger.error(f"Failed to update position in database: {e}")

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if has position in symbol."""
        return symbol in self.positions

    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        return list(self.positions.values())

    def get_positions_count(self) -> int:
        """Get number of open positions."""
        return len(self.positions)

    def get_total_exposure(self) -> float:
        """Calculate total exposure across all positions."""
        return sum(
            pos.entry_price * pos.quantity
            for pos in self.positions.values()
        )

    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def update_stop_loss(self, symbol: str, new_stop_loss: float) -> bool:
        """
        Update stop loss for a position.

        Args:
            symbol: Trading pair
            new_stop_loss: New stop loss price

        Returns:
            True if updated successfully
        """
        if symbol not in self.positions:
            return False

        self.positions[symbol].stop_loss = new_stop_loss

        # Update database
        try:
            db_position = self.repository.get_position_by_symbol(symbol)
            if db_position:
                self.repository.update_trade(db_position.id, {
                    'stop_loss': new_stop_loss
                })

            logger.debug(f"Updated stop loss for {symbol}: ${new_stop_loss:.2f}")
            return True

        except Exception as e:
            logger.error(f"Failed to update stop loss in database: {e}")
            return False

    def get_position_summary(self) -> Dict:
        """Get summary of all positions."""
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())

        return {
            'open_positions': len(self.positions),
            'total_exposure': self.get_total_exposure(),
            'unrealized_pnl': total_unrealized,
            'positions': [
                {
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'entry_price': pos.entry_price,
                    'quantity': pos.quantity,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'pnl_percent': pos.get_pnl_percent()
                }
                for pos in self.positions.values()
            ]
        }

    def close(self) -> None:
        """Close position manager and cleanup."""
        self.repository.close()
