"""
SQLAlchemy database models for trading bot.
"""
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Trade(Base):
    """Trade history model."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime)
    pnl = Column(Float, default=0.0)
    pnl_percent = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    strategy = Column(String(50))
    status = Column(String(20), default="open")  # 'open' or 'closed'
    exit_reason = Column(String(50))
    notes = Column(Text)

    def __repr__(self):
        return f"<Trade {self.symbol} {self.side} {self.quantity} @ {self.entry_price}>"


class Position(Base):
    """Open positions model."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True)
    side = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    status = Column(String(20), default="open")

    def __repr__(self):
        return f"<Position {self.symbol} {self.side} {self.quantity}>"


class BotState(Base):
    """Bot state for persistence."""
    __tablename__ = "bot_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BotState {self.key}={self.value}>"


class PerformanceMetrics(Base):
    """Daily performance metrics."""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    num_trades = Column(Integer, default=0)
    equity = Column(Float)

    def __repr__(self):
        return f"<PerformanceMetrics {self.date} PnL={self.total_pnl}>"


def init_database(database_url: str = "sqlite:///./trading_bot.db"):
    """
    Initialize database and create tables.

    Args:
        database_url: Database connection URL
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get database session."""
    Session = sessionmaker(bind=engine)
    return Session()
