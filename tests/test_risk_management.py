"""
Unit tests for risk management system.
"""
import pytest
from datetime import datetime

from src.risk.position_sizer import PositionSizer
from src.risk.risk_manager import RiskManager
from src.risk.portfolio import Portfolio, Position
from src.config.settings import Settings
from src.config.constants import ExitReason


class TestPositionSizer:
    """Test position sizing calculations."""

    @pytest.fixture
    def sizer(self):
        """Create position sizer instance."""
        settings = Settings()
        settings.max_position_size_percent = 10
        settings.position_sizing_method = 'fixed'
        return PositionSizer(settings)

    def test_fixed_position_size(self, sizer):
        """Test fixed percentage position sizing."""
        account_balance = 10000
        position_size = sizer.calculate_position_size(
            account_balance=account_balance,
            entry_price=100
        )

        # Should be 10% of account
        assert position_size == 1000

    def test_volatility_based_sizing(self):
        """Test volatility-based position sizing."""
        settings = Settings()
        settings.position_sizing_method = 'volatility'
        sizer = PositionSizer(settings)

        position_size = sizer._calculate_volatility_based_size(
            account_balance=10000,
            entry_price=100,
            stop_loss_price=95,
            risk_percent=2.0,
            volatility=None
        )

        # Risk $200 on a $5 stop = 40 shares
        assert position_size == pytest.approx(40, rel=0.1)

    def test_calculate_quantity(self, sizer):
        """Test quantity calculation."""
        position_size = 1000
        entry_price = 50

        quantity = sizer.calculate_quantity(
            position_size=position_size,
            entry_price=entry_price
        )

        assert quantity == 20

    def test_validate_position_size(self, sizer):
        """Test position size validation."""
        # Valid position size
        is_valid = sizer.validate_position_size(
            position_size=500,
            account_balance=10000,
            symbol="BTC/USDT"
        )
        assert is_valid == True

        # Too large position
        is_valid = sizer.validate_position_size(
            position_size=5000,
            account_balance=10000,
            symbol="BTC/USDT"
        )
        assert is_valid == False

        # Too small position
        is_valid = sizer.validate_position_size(
            position_size=5,
            account_balance=10000,
            symbol="BTC/USDT"
        )
        assert is_valid == False


class TestRiskManager:
    """Test risk management rules."""

    @pytest.fixture
    def risk_mgr(self):
        """Create risk manager instance."""
        settings = Settings()
        settings.stop_loss_percent = 2.0
        settings.take_profit_percent = 4.0
        settings.max_concurrent_positions = 3
        settings.daily_loss_limit_percent = 5.0
        return RiskManager(settings)

    def test_stop_loss_calculation(self, risk_mgr):
        """Test stop loss calculation."""
        entry_price = 100
        stop_loss = risk_mgr.calculate_stop_loss(entry_price, 'buy')

        # Should be 2% below entry
        assert stop_loss == pytest.approx(98, rel=0.01)

    def test_take_profit_calculation(self, risk_mgr):
        """Test take profit calculation."""
        entry_price = 100
        take_profit = risk_mgr.calculate_take_profit(entry_price, 'buy')

        # Should be 4% above entry
        assert take_profit == pytest.approx(104, rel=0.01)

    def test_position_close_conditions(self, risk_mgr):
        """Test position close conditions."""
        entry_price = 100
        stop_loss = 98
        take_profit = 104

        # Hit stop loss
        should_close, reason = risk_mgr.should_close_position(
            entry_price=entry_price,
            current_price=97,
            stop_loss=stop_loss,
            take_profit=take_profit,
            side='buy'
        )
        assert should_close == True
        assert reason == ExitReason.STOP_LOSS

        # Hit take profit
        should_close, reason = risk_mgr.should_close_position(
            entry_price=entry_price,
            current_price=105,
            stop_loss=stop_loss,
            take_profit=take_profit,
            side='buy'
        )
        assert should_close == True
        assert reason == ExitReason.TAKE_PROFIT

        # No exit condition
        should_close, reason = risk_mgr.should_close_position(
            entry_price=entry_price,
            current_price=101,
            stop_loss=stop_loss,
            take_profit=take_profit,
            side='buy'
        )
        assert should_close == False

    def test_can_open_position(self, risk_mgr):
        """Test position opening validation."""
        # Can open with available slots
        can_open, reason = risk_mgr.can_open_position(
            current_positions=2,
            account_balance=10000,
            proposed_position_size=1000
        )
        assert can_open == True

        # Cannot open - max positions reached
        can_open, reason = risk_mgr.can_open_position(
            current_positions=3,
            account_balance=10000,
            proposed_position_size=1000
        )
        assert can_open == False

    def test_trailing_stop_update(self, risk_mgr):
        """Test trailing stop loss update."""
        entry_price = 100
        current_stop = 98

        # Price moved up, should update stop
        new_stop = risk_mgr.update_trailing_stop(
            entry_price=entry_price,
            current_price=110,
            current_stop=current_stop,
            side='buy'
        )

        assert new_stop > current_stop

    def test_daily_loss_limit(self, risk_mgr):
        """Test daily loss limit enforcement."""
        # Update with large loss
        risk_mgr.update_daily_pnl(-600)

        can_open, reason = risk_mgr.can_open_position(
            current_positions=0,
            account_balance=10000,
            proposed_position_size=1000
        )

        assert can_open == False
        assert "Daily loss limit" in reason


class TestPortfolio:
    """Test portfolio management."""

    @pytest.fixture
    def portfolio(self):
        """Create portfolio instance."""
        return Portfolio(initial_balance=10000)

    def test_add_position(self, portfolio):
        """Test adding a position."""
        position = Position(
            symbol="BTC/USDT",
            side="buy",
            entry_price=100,
            quantity=10,
            entry_time=datetime.now(),
            stop_loss=98,
            take_profit=104
        )

        portfolio.add_position(position)

        assert portfolio.has_position("BTC/USDT")
        assert portfolio.get_positions_count() == 1

    def test_remove_position(self, portfolio):
        """Test removing a position."""
        position = Position(
            symbol="BTC/USDT",
            side="buy",
            entry_price=100,
            quantity=10,
            entry_time=datetime.now(),
            stop_loss=98,
            take_profit=104
        )

        portfolio.add_position(position)
        removed = portfolio.remove_position("BTC/USDT")

        assert removed is not None
        assert not portfolio.has_position("BTC/USDT")

    def test_update_position_pnl(self, portfolio):
        """Test updating position P&L."""
        position = Position(
            symbol="BTC/USDT",
            side="buy",
            entry_price=100,
            quantity=10,
            entry_time=datetime.now(),
            stop_loss=98,
            take_profit=104
        )

        portfolio.add_position(position)

        # Update with higher price
        portfolio.update_position_prices({"BTC/USDT": 110})

        pos = portfolio.get_position("BTC/USDT")
        assert pos.unrealized_pnl == 100  # (110-100) * 10

    def test_portfolio_equity(self, portfolio):
        """Test portfolio equity calculation."""
        position = Position(
            symbol="BTC/USDT",
            side="buy",
            entry_price=100,
            quantity=10,
            entry_time=datetime.now(),
            stop_loss=98,
            take_profit=104
        )

        portfolio.add_position(position)
        portfolio.balance = 9000  # After buying

        # Update with profit
        equity = portfolio.calculate_total_equity({"BTC/USDT": 110})

        # 9000 balance + 100 unrealized profit
        assert equity == 9100

    def test_get_summary(self, portfolio):
        """Test portfolio summary."""
        summary = portfolio.get_portfolio_summary()

        assert 'initial_balance' in summary
        assert 'balance' in summary
        assert 'equity' in summary
        assert 'open_positions' in summary
