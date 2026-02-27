"""
Performance metrics calculator for backtesting results.
"""
import numpy as np
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Calculate comprehensive performance metrics."""

    @staticmethod
    def calculate_all_metrics(results: Dict) -> Dict:
        """
        Calculate comprehensive performance metrics from backtest results.

        Args:
            results: Backtest results dictionary

        Returns:
            Dictionary with detailed metrics
        """
        trades = results.get('trades', [])
        equity_curve = results.get('equity_curve', [])

        if not trades:
            return results

        trades_df = pd.DataFrame(trades)

        # Additional metrics
        metrics = {
            **results,
            'total_fees': trades_df['fees'].sum(),
            'largest_win': trades_df['pnl'].max(),
            'largest_loss': trades_df['pnl'].min(),
            'avg_trade_duration': PerformanceMetrics._calculate_avg_duration(trades_df),
            'expectancy': PerformanceMetrics._calculate_expectancy(trades_df),
            'recovery_factor': PerformanceMetrics._calculate_recovery_factor(results),
            'sortino_ratio': PerformanceMetrics._calculate_sortino_ratio(equity_curve),
            'calmar_ratio': PerformanceMetrics._calculate_calmar_ratio(results),
        }

        return metrics

    @staticmethod
    def _calculate_avg_duration(trades_df: pd.DataFrame) -> float:
        """Calculate average trade duration in hours."""
        if 'entry_time' in trades_df.columns and 'exit_time' in trades_df.columns:
            try:
                trades_df['duration'] = (
                    pd.to_datetime(trades_df['exit_time']) -
                    pd.to_datetime(trades_df['entry_time'])
                ).dt.total_seconds() / 3600
                return trades_df['duration'].mean()
            except:
                return 0.0
        return 0.0

    @staticmethod
    def _calculate_expectancy(trades_df: pd.DataFrame) -> float:
        """Calculate expectancy (average profit per trade)."""
        if len(trades_df) == 0:
            return 0.0

        winning = trades_df[trades_df['pnl'] > 0]
        losing = trades_df[trades_df['pnl'] <= 0]

        if len(losing) == 0:
            return winning['pnl'].mean() if len(winning) > 0 else 0.0

        win_rate = len(winning) / len(trades_df)
        avg_win = winning['pnl'].mean() if len(winning) > 0 else 0
        avg_loss = abs(losing['pnl'].mean()) if len(losing) > 0 else 0

        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        return expectancy

    @staticmethod
    def _calculate_recovery_factor(results: Dict) -> float:
        """Calculate recovery factor (net profit / max drawdown)."""
        total_pnl = results.get('total_pnl', 0)
        max_drawdown = abs(results.get('max_drawdown', 0))

        if max_drawdown == 0:
            return float('inf') if total_pnl > 0 else 0.0

        return total_pnl / max_drawdown

    @staticmethod
    def _calculate_sortino_ratio(equity_curve: List[float]) -> float:
        """
        Calculate Sortino ratio (focuses on downside deviation).
        """
        if len(equity_curve) < 2:
            return 0.0

        equity_array = np.array(equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]

        if len(returns) == 0:
            return 0.0

        # Only consider negative returns for downside deviation
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return float('inf') if returns.mean() > 0 else 0.0

        downside_std = downside_returns.std()

        if downside_std == 0:
            return float('inf') if returns.mean() > 0 else 0.0

        sortino = (returns.mean() / downside_std) * np.sqrt(252)
        return sortino

    @staticmethod
    def _calculate_calmar_ratio(results: Dict) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).
        """
        total_return = results.get('total_return', 0)
        max_drawdown = abs(results.get('max_drawdown', 0))

        if max_drawdown == 0:
            return float('inf') if total_return > 0 else 0.0

        return total_return / max_drawdown

    @staticmethod
    def print_summary(metrics: Dict) -> None:
        """Print performance summary to console."""
        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("=" * 60)

        print(f"\n💰 Capital & Returns:")
        print(f"  Initial Capital:    ${metrics['initial_capital']:,.2f}")
        print(f"  Final Equity:       ${metrics['final_equity']:,.2f}")
        print(f"  Total Return:       {metrics['total_return']:+.2f}%")
        print(f"  Total P&L:          ${metrics['total_pnl']:+,.2f}")

        print(f"\n📊 Trade Statistics:")
        print(f"  Total Trades:       {metrics['total_trades']}")
        print(f"  Winning Trades:     {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)")
        print(f"  Losing Trades:      {metrics['losing_trades']}")
        print(f"  Average Win:        ${metrics['avg_win']:,.2f}")
        print(f"  Average Loss:       ${metrics['avg_loss']:,.2f}")
        print(f"  Largest Win:        ${metrics.get('largest_win', 0):,.2f}")
        print(f"  Largest Loss:       ${metrics.get('largest_loss', 0):,.2f}")

        print(f"\n📈 Performance Metrics:")
        pf = metrics['profit_factor']
        pf_str = f"{pf:.2f}" if pf != float('inf') else "∞"
        print(f"  Profit Factor:      {pf_str}")
        print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio:      {metrics.get('sortino_ratio', 0):.2f}")
        print(f"  Max Drawdown:       {metrics['max_drawdown']:.2f}%")
        print(f"  Calmar Ratio:       {metrics.get('calmar_ratio', 0):.2f}")
        print(f"  Recovery Factor:    {metrics.get('recovery_factor', 0):.2f}")

        print(f"\n💸 Costs:")
        print(f"  Total Fees:         ${metrics.get('total_fees', 0):,.2f}")
        print(f"  Expectancy:         ${metrics.get('expectancy', 0):,.2f} per trade")

        if metrics.get('avg_trade_duration'):
            print(f"\n⏱️  Average Trade Duration: {metrics['avg_trade_duration']:.1f} hours")

        print("\n" + "=" * 60 + "\n")
