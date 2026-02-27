"""
Database repository for CRUD operations.
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import Trade, Position, BotState, PerformanceMetrics, init_database, get_session

logger = logging.getLogger(__name__)


class Repository:
    """Database repository for all models."""

    def __init__(self, database_url: str = "sqlite:///./trading_bot.db"):
        """Initialize repository."""
        self.engine = init_database(database_url)
        self.session: Optional[Session] = None

    def get_session(self) -> Session:
        """Get or create database session."""
        if self.session is None:
            self.session = get_session(self.engine)
        return self.session

    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()
            self.session = None

    # Trade operations
    def create_trade(self, trade_data: dict) -> Trade:
        """Create new trade record."""
        session = self.get_session()
        trade = Trade(**trade_data)
        session.add(trade)
        session.commit()
        logger.info(f"Created trade: {trade.symbol} {trade.side}")
        return trade

    def update_trade(self, trade_id: int, updates: dict) -> Optional[Trade]:
        """Update trade record."""
        session = self.get_session()
        trade = session.query(Trade).filter_by(id=trade_id).first()
        if trade:
            for key, value in updates.items():
                setattr(trade, key, value)
            session.commit()
        return trade

    def get_all_trades(self) -> List[Trade]:
        """Get all trades."""
        session = self.get_session()
        return session.query(Trade).all()

    def get_open_trades(self) -> List[Trade]:
        """Get all open trades."""
        session = self.get_session()
        return session.query(Trade).filter_by(status="open").all()

    # Position operations
    def create_position(self, position_data: dict) -> Position:
        """Create new position."""
        session = self.get_session()
        position = Position(**position_data)
        session.add(position)
        session.commit()
        return position

    def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        session = self.get_session()
        return session.query(Position).filter_by(symbol=symbol, status="open").first()

    def get_all_open_positions(self) -> List[Position]:
        """Get all open positions."""
        session = self.get_session()
        return session.query(Position).filter_by(status="open").all()

    def delete_position(self, symbol: str) -> bool:
        """Delete position."""
        session = self.get_session()
        position = session.query(Position).filter_by(symbol=symbol).first()
        if position:
            session.delete(position)
            session.commit()
            return True
        return False

    # Bot state operations
    def save_state(self, key: str, value: str) -> None:
        """Save bot state."""
        session = self.get_session()
        state = session.query(BotState).filter_by(key=key).first()
        if state:
            state.value = value
            state.updated_at = datetime.utcnow()
        else:
            state = BotState(key=key, value=value)
            session.add(state)
        session.commit()

    def get_state(self, key: str) -> Optional[str]:
        """Get bot state."""
        session = self.get_session()
        state = session.query(BotState).filter_by(key=key).first()
        return state.value if state else None

    # Performance metrics
    def save_metrics(self, metrics_data: dict) -> PerformanceMetrics:
        """Save performance metrics."""
        session = self.get_session()
        metrics = PerformanceMetrics(**metrics_data)
        session.add(metrics)
        session.commit()
        return metrics

    def get_latest_metrics(self, days: int = 30) -> List[PerformanceMetrics]:
        """Get latest performance metrics."""
        session = self.get_session()
        return session.query(PerformanceMetrics).order_by(
            PerformanceMetrics.date.desc()
        ).limit(days).all()
