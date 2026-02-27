"""
Visualization tools for backtest results.
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (12, 8)


class Visualizer:
    """Create charts and visualizations for backtest results."""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def create_all_charts(
        self,
        results: Dict,
        symbol: str = "BTC/USDT",
        save: bool = True
    ) -> None:
        """
        Create all visualization charts.

        Args:
            results: Backtest results dictionary
            symbol: Trading pair symbol
            save: Whether to save charts to files
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        # Create equity curve
        self.plot_equity_curve(
            results,
            save=save,
            filename=f"equity_curve_{timestamp}.png"
        )

        # Create drawdown chart
        self.plot_drawdown(
            results,
            save=save,
            filename=f"drawdown_{timestamp}.png"
        )

        # Create trade distribution
        if results['trades']:
            self.plot_trade_distribution(
                results,
                save=save,
                filename=f"trade_dist_{timestamp}.png"
            )

            # Create monthly returns heatmap
            self.plot_monthly_returns(
                results,
                save=save,
                filename=f"monthly_returns_{timestamp}.png"
            )

        logger.info(f"Charts saved to {self.output_dir}")

    def plot_equity_curve(
        self,
        results: Dict,
        save: bool = True,
        filename: str = "equity_curve.png"
    ) -> None:
        """Plot equity curve over time."""
        fig, ax = plt.subplots(figsize=(14, 7))

        equity = results['equity_curve']
        dates = results['dates']

        # Plot equity curve
        ax.plot(dates, equity, linewidth=2, label='Portfolio Value', color='#2E86AB')

        # Add initial capital line
        ax.axhline(
            y=results['initial_capital'],
            color='gray',
            linestyle='--',
            linewidth=1,
            label='Initial Capital'
        )

        # Formatting
        ax.set_title('Equity Curve', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        if len(dates) > 0:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45)

        plt.tight_layout()

        if save:
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved equity curve to {filepath}")

        plt.close()

    def plot_drawdown(
        self,
        results: Dict,
        save: bool = True,
        filename: str = "drawdown.png"
    ) -> None:
        """Plot drawdown chart."""
        fig, ax = plt.subplots(figsize=(14, 7))

        equity = np.array(results['equity_curve'])
        dates = results['dates']

        # Calculate drawdown
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100

        # Plot drawdown
        ax.fill_between(
            dates,
            drawdown,
            0,
            alpha=0.3,
            color='red',
            label='Drawdown'
        )
        ax.plot(dates, drawdown, color='darkred', linewidth=1.5)

        # Formatting
        ax.set_title('Drawdown Over Time', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        if len(dates) > 0:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45)

        # Add max drawdown annotation
        max_dd_idx = np.argmin(drawdown)
        max_dd_value = drawdown[max_dd_idx]
        ax.annotate(
            f'Max DD: {max_dd_value:.2f}%',
            xy=(dates[max_dd_idx], max_dd_value),
            xytext=(10, -20),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )

        plt.tight_layout()

        if save:
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved drawdown chart to {filepath}")

        plt.close()

    def plot_trade_distribution(
        self,
        results: Dict,
        save: bool = True,
        filename: str = "trade_distribution.png"
    ) -> None:
        """Plot distribution of trade P&L."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        trades_df = pd.DataFrame(results['trades'])

        # Histogram of P&L
        ax1.hist(
            trades_df['pnl'],
            bins=30,
            color='skyblue',
            edgecolor='black',
            alpha=0.7
        )
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.set_title('P&L Distribution', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Profit/Loss ($)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.grid(True, alpha=0.3)

        # Win/Loss pie chart
        wins = len(trades_df[trades_df['pnl'] > 0])
        losses = len(trades_df[trades_df['pnl'] <= 0])

        colors = ['#2ecc71', '#e74c3c']
        ax2.pie(
            [wins, losses],
            labels=['Wins', 'Losses'],
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        ax2.set_title('Win/Loss Ratio', fontsize=14, fontweight='bold')

        plt.tight_layout()

        if save:
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved trade distribution to {filepath}")

        plt.close()

    def plot_monthly_returns(
        self,
        results: Dict,
        save: bool = True,
        filename: str = "monthly_returns.png"
    ) -> None:
        """Plot monthly returns heatmap."""
        trades_df = pd.DataFrame(results['trades'])

        if 'exit_time' not in trades_df.columns:
            logger.warning("Cannot create monthly returns without exit_time")
            return

        try:
            # Convert to datetime
            trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])

            # Extract year and month
            trades_df['year'] = trades_df['exit_time'].dt.year
            trades_df['month'] = trades_df['exit_time'].dt.month

            # Group by year and month
            monthly_pnl = trades_df.groupby(['year', 'month'])['pnl'].sum().reset_index()

            # Pivot for heatmap
            pivot_table = monthly_pnl.pivot(
                index='year',
                columns='month',
                values='pnl'
            )

            # Create heatmap
            fig, ax = plt.subplots(figsize=(12, 6))

            sns.heatmap(
                pivot_table,
                annot=True,
                fmt='.0f',
                cmap='RdYlGn',
                center=0,
                cbar_kws={'label': 'P&L ($)'},
                ax=ax
            )

            ax.set_title('Monthly Returns', fontsize=14, fontweight='bold')
            ax.set_xlabel('Month', fontsize=11)
            ax.set_ylabel('Year', fontsize=11)

            # Set month names
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            ax.set_xticklabels(month_names)

            plt.tight_layout()

            if save:
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                logger.info(f"Saved monthly returns to {filepath}")

            plt.close()

        except Exception as e:
            logger.error(f"Error creating monthly returns chart: {e}")

    def create_report_html(
        self,
        results: Dict,
        metrics: Dict,
        symbol: str = "BTC/USDT"
    ) -> str:
        """
        Create HTML report with all metrics and charts.

        Args:
            results: Backtest results
            metrics: Performance metrics
            symbol: Trading pair

        Returns:
            Path to HTML file
        """
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        html_file = self.output_dir / f"backtest_report_{timestamp}.html"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report - {symbol}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }}
                h1 {{ color: #2E86AB; }}
                h2 {{ color: #333; border-bottom: 2px solid #2E86AB; padding-bottom: 10px; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .metric-label {{ font-weight: bold; color: #666; }}
                .metric-value {{ font-size: 1.2em; color: #2E86AB; }}
                .positive {{ color: #2ecc71; }}
                .negative {{ color: #e74c3c; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #2E86AB; color: white; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Backtest Report: {symbol}</h1>
                <p><strong>Generated:</strong> {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

                <h2>Performance Summary</h2>
                <div class="metric">
                    <span class="metric-label">Initial Capital:</span>
                    <span class="metric-value">${metrics['initial_capital']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Final Equity:</span>
                    <span class="metric-value">${metrics['final_equity']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Return:</span>
                    <span class="metric-value {'positive' if metrics['total_return'] > 0 else 'negative'}">
                        {metrics['total_return']:+.2f}%
                    </span>
                </div>

                <h2>Trade Statistics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Trades</td><td>{metrics['total_trades']}</td></tr>
                    <tr><td>Winning Trades</td><td>{metrics['winning_trades']} ({metrics['win_rate']:.1f}%)</td></tr>
                    <tr><td>Losing Trades</td><td>{metrics['losing_trades']}</td></tr>
                    <tr><td>Average Win</td><td>${metrics['avg_win']:,.2f}</td></tr>
                    <tr><td>Average Loss</td><td>${metrics['avg_loss']:,.2f}</td></tr>
                    <tr><td>Profit Factor</td><td>{metrics['profit_factor']:.2f}</td></tr>
                </table>

                <h2>Risk Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Sharpe Ratio</td><td>{metrics['sharpe_ratio']:.2f}</td></tr>
                    <tr><td>Sortino Ratio</td><td>{metrics.get('sortino_ratio', 0):.2f}</td></tr>
                    <tr><td>Max Drawdown</td><td>{metrics['max_drawdown']:.2f}%</td></tr>
                    <tr><td>Calmar Ratio</td><td>{metrics.get('calmar_ratio', 0):.2f}</td></tr>
                </table>

                <h2>Charts</h2>
                <h3>Equity Curve</h3>
                <img src="equity_curve_{timestamp}.png" alt="Equity Curve">

                <h3>Drawdown</h3>
                <img src="drawdown_{timestamp}.png" alt="Drawdown">

                <h3>Trade Distribution</h3>
                <img src="trade_dist_{timestamp}.png" alt="Trade Distribution">
            </div>
        </body>
        </html>
        """

        with open(html_file, 'w') as f:
            f.write(html_content)

        logger.info(f"Created HTML report: {html_file}")
        return str(html_file)
