"""
Backtesting engine for testing trading strategies on historical data.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from ..strategies.base_strategy import BaseStrategy
from ..risk.position_sizer import PositionSizer
from ..risk.risk_manager import RiskManager
from ..config.settings import Settings
from ..config.constants import OrderSide, PositionStatus, ExitReason

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Event-driven backtesting engine for strategy evaluation.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        settings: Optional[Settings] = None
    ):
        """
        Initialize backtest engine.

        Args:
            strategy: Trading strategy to test
            initial_capital: Starting capital
            commission: Commission per trade (0.001 = 0.1%)
            slippage: Slippage per trade (0.0005 = 0.05%)
            settings: Application settings
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.settings = settings or Settings()

        # Initialize components
        self.position_sizer = PositionSizer(self.settings)
        self.risk_manager = RiskManager(self.settings)

        # Backtest state
        self.balance = initial_capital
        self.equity = initial_capital
        self.positions: Dict = {}
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []
        self.dates: List[datetime] = []

    def run(
        self,
        df: pd.DataFrame,
        symbol: str = "BTC/USDT"
    ) -> Dict:
        """
        Run backtest on historical data.

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading pair symbol

        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest on {len(df)} bars")
        logger.info(f"Initial capital: ${self.initial_capital:.2f}")

        # Prepare data with indicators and signals
        df = self.strategy.prepare_data(df)

        # Simulate trading bar by bar
        for idx, row in df.iterrows():
            self._process_bar(row, symbol)

        # Close any remaining positions
        if self.positions:
            last_row = df.iloc[-1]
            self._close_position(last_row, symbol, ExitReason.MANUAL)

        logger.info(f"Backtest complete. Final equity: ${self.equity:.2f}")

        # Calculate performance metrics
        results = self._calculate_results()

        return results

    def _process_bar(self, row: pd.Series, symbol: str) -> None:
        """
        Process a single bar of data.

        Args:
            row: Current bar data
            symbol: Trading symbol
        """
        current_price = row['close']
        current_time = row.name if hasattr(row, 'name') else datetime.now()

        # Update equity curve
        self._update_equity(current_price)
        self.equity_curve.append(self.equity)
        self.dates.append(current_time)

        # Check if we have an open position
        if symbol in self.positions:
            self._manage_position(row, symbol)
        else:
            self._check_entry(row, symbol)

    def _check_entry(self, row: pd.Series, symbol: str) -> None:
        """Check for entry signals and open position."""
        # Check if strategy generates entry signal
        if not self.strategy.should_enter(row):
            return

        # Validate signal
        if not self.strategy.validate_signal(row, row.get('signal', 0)):
            return

        current_price = row['close']

        # Calculate position size
        position_size = self.position_sizer.calculate_position_size(
            account_balance=self.balance,
            entry_price=current_price
        )

        # Validate position size
        if not self.position_sizer.validate_position_size(
            position_size, self.balance, symbol
        ):
            return

        # Calculate quantity
        quantity = position_size / current_price

        # Apply slippage
        entry_price = current_price * (1 + self.slippage)

        # Calculate costs
        cost = entry_price * quantity
        fees = cost * self.commission
        total_cost = cost + fees

        # Check if we have enough balance
        if total_cost > self.balance:
            logger.debug(f"Insufficient balance for trade: {total_cost:.2f} > {self.balance:.2f}")
            return

        # Calculate stop loss and take profit
        stop_loss = self.risk_manager.calculate_stop_loss(
            entry_price, OrderSide.BUY.value
        )
        take_profit = self.risk_manager.calculate_take_profit(
            entry_price, OrderSide.BUY.value
        )

        # Open position
        self.positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': row.name if hasattr(row, 'name') else datetime.now(),
            'fees_paid': fees,
            'highest_price': entry_price,
            'entry_reason': self.strategy.get_entry_reason(row)
        }

        self.balance -= total_cost

        logger.info(
            f"ENTRY: {symbol} at ${entry_price:.2f}, "
            f"qty={quantity:.6f}, SL=${stop_loss:.2f}, TP=${take_profit:.2f}"
        )

    def _manage_position(self, row: pd.Series, symbol: str) -> None:
        """Manage open position (check exit conditions)."""
        position = self.positions[symbol]
        current_price = row['close']

        # Update highest price for trailing stop
        position['highest_price'] = max(position['highest_price'], current_price)

        # Update trailing stop
        if self.settings.use_trailing_stop:
            position['stop_loss'] = self.risk_manager.update_trailing_stop(
                entry_price=position['entry_price'],
                current_price=current_price,
                current_stop=position['stop_loss'],
                side=OrderSide.BUY.value
            )

        # Check stop loss / take profit
        should_close, exit_reason = self.risk_manager.should_close_position(
            entry_price=position['entry_price'],
            current_price=current_price,
            stop_loss=position['stop_loss'],
            take_profit=position['take_profit'],
            side=OrderSide.BUY.value
        )

        if should_close:
            self._close_position(row, symbol, exit_reason)
            return

        # Check strategy exit signal
        if self.strategy.should_exit(row, position):
            self._close_position(row, symbol, ExitReason.SIGNAL)

    def _close_position(
        self,
        row: pd.Series,
        symbol: str,
        exit_reason: ExitReason
    ) -> None:
        """Close an open position."""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        current_price = row['close']

        # Apply slippage
        exit_price = current_price * (1 - self.slippage)

        # Calculate P&L
        quantity = position['quantity']
        proceeds = exit_price * quantity
        fees = proceeds * self.commission
        net_proceeds = proceeds - fees

        # Calculate profit/loss
        cost = position['entry_price'] * quantity
        pnl = net_proceeds - cost
        pnl_percent = (pnl / cost) * 100

        # Update balance
        self.balance += net_proceeds

        # Record trade
        trade = {
            'symbol': symbol,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': quantity,
            'entry_time': position['entry_time'],
            'exit_time': row.name if hasattr(row, 'name') else datetime.now(),
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'fees': position['fees_paid'] + fees,
            'exit_reason': exit_reason.value,
            'entry_reason': position.get('entry_reason', 'Unknown')
        }
        self.trades.append(trade)

        # Update daily P&L for risk manager
        self.risk_manager.update_daily_pnl(pnl)

        logger.info(
            f"EXIT: {symbol} at ${exit_price:.2f}, "
            f"P&L=${pnl:.2f} ({pnl_percent:+.2f}%), reason={exit_reason.value}"
        )

        # Remove position
        del self.positions[symbol]

    def _update_equity(self, current_price: float) -> None:
        """Update total equity including unrealized P&L."""
        unrealized_pnl = 0.0

        for symbol, position in self.positions.items():
            position_value = current_price * position['quantity']
            cost = position['entry_price'] * position['quantity']
            unrealized_pnl += (position_value - cost)

        self.equity = self.balance + unrealized_pnl

    def _calculate_results(self) -> Dict:
        """Calculate backtest performance metrics."""
        if not self.trades:
            logger.warning("No trades executed during backtest")
            return self._empty_results()

        # Convert trades to DataFrame
        trades_df = pd.DataFrame(self.trades)

        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]

        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = trades_df['pnl'].sum()
        total_return = ((self.equity - self.initial_capital) / self.initial_capital) * 100

        # Average win/loss
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0

        # Profit factor
        gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Calculate equity curve metrics
        equity_array = np.array(self.equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]

        # Sharpe ratio (assuming 252 trading days)
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        # Maximum drawdown
        cumulative = equity_array
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        results = {
            'initial_capital': self.initial_capital,
            'final_equity': self.equity,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'dates': self.dates,
        }

        return results

    def _empty_results(self) -> Dict:
        """Return empty results when no trades executed."""
        return {
            'initial_capital': self.initial_capital,
            'final_equity': self.equity,
            'total_return': 0.0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trades': [],
            'equity_curve': self.equity_curve,
            'dates': self.dates,
        }
