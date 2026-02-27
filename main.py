"""
Main entry point for the cryptocurrency trading bot.
Provides CLI commands for backtesting, paper trading, and live trading.
"""
import argparse
import sys
import logging
from datetime import datetime

# Setup logging first
from src.monitoring.logger import setup_logging
from src.config.settings import Settings

# Initialize settings and logging
settings = Settings()
setup_logging(settings)

logger = logging.getLogger(__name__)


def backtest_command(args):
    """Run backtesting on historical data."""
    logger.info("=" * 60)
    logger.info("BACKTESTING MODE")
    logger.info("=" * 60)
    logger.info(f"Pair: {args.pair}")
    logger.info(f"Start: {args.start}")
    logger.info(f"End: {args.end}")
    logger.info(f"Timeframe: {args.timeframe}")

    try:
        from src.exchange.connector import ExchangeConnector
        from src.exchange.data_fetcher import DataFetcher
        from src.strategies.ma_crossover import MACrossoverStrategy
        from src.backtesting.backtest_engine import BacktestEngine
        from src.backtesting.performance import PerformanceMetrics
        from src.backtesting.visualizer import Visualizer

        # Initialize components
        connector = ExchangeConnector(settings)
        connector.connect()

        data_fetcher = DataFetcher(connector, settings)

        # Fetch historical data
        logger.info("Fetching historical data...")
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")

        df = data_fetcher.fetch_ohlcv_dataframe(
            symbol=args.pair,
            timeframe=args.timeframe,
            since=start_date,
            until=end_date
        )

        logger.info(f"Loaded {len(df)} candles")

        # Initialize strategy
        strategy = MACrossoverStrategy(settings.strategy_params)

        # Initialize backtest engine
        logger.info("Running backtest...")
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=settings.initial_capital,
            commission=settings.commission,
            slippage=settings.slippage,
            settings=settings
        )

        # Run backtest
        results = backtest.run(df, symbol=args.pair)

        # Calculate detailed metrics
        metrics = PerformanceMetrics.calculate_all_metrics(results)

        # Print performance summary
        PerformanceMetrics.print_summary(metrics)

        # Generate charts
        if metrics['total_trades'] > 0:
            logger.info("Generating performance charts...")
            visualizer = Visualizer()
            visualizer.create_all_charts(metrics, symbol=args.pair)
            logger.info(f"Charts saved to ./reports/")

        logger.info("\nBacktest completed successfully!")

    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        return 1

    return 0


def paper_command(args):
    """Run bot in paper trading mode."""
    logger.info("=" * 60)
    logger.info("PAPER TRADING MODE")
    logger.info("=" * 60)
    logger.info(f"Pair: {args.pair}")
    logger.info(f"Timeframe: {args.timeframe}")
    logger.info("\nPaper trading mode simulates trades without real money.")
    logger.info("Press Ctrl+C to stop the bot gracefully.\n")

    try:
        from src.exchange.connector import ExchangeConnector
        from src.exchange.data_fetcher import DataFetcher
        from src.strategies.ma_crossover import MACrossoverStrategy
        from src.risk.portfolio import Portfolio
        import time

        # Initialize components
        connector = ExchangeConnector(settings)
        connector.connect()

        data_fetcher = DataFetcher(connector, settings)
        strategy = MACrossoverStrategy(settings.strategy_params)
        portfolio = Portfolio(initial_balance=settings.initial_capital)

        logger.info(f"Initial balance: ${portfolio.balance:.2f}")
        logger.info("Monitoring market for signals...\n")

        while True:
            try:
                # Fetch latest data
                df = data_fetcher.fetch_latest_candles(
                    symbol=args.pair,
                    timeframe=args.timeframe,
                    count=settings.lookback_periods
                )

                # Prepare data
                df = strategy.prepare_data(df)

                # Get latest signal
                latest = df.iloc[-1]
                signal = latest['signal']

                if signal == 1 and not portfolio.has_position(args.pair):
                    logger.info(f"BUY SIGNAL at {latest['close']:.2f}")
                    logger.info(f"Reason: {strategy.get_entry_reason(latest)}")

                elif signal == -1 and portfolio.has_position(args.pair):
                    logger.info(f"SELL SIGNAL at {latest['close']:.2f}")
                    logger.info(f"Reason: {strategy.get_exit_reason(latest)}")

                # Update status
                summary = portfolio.get_portfolio_summary()
                logger.info(
                    f"Balance: ${summary['balance']:.2f} | "
                    f"Positions: {summary['open_positions']} | "
                    f"PnL: {summary['pnl_percent']:.2f}%"
                )

                # Sleep
                time.sleep(settings.update_interval_seconds)

            except KeyboardInterrupt:
                logger.info("\nShutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)

        logger.info("Paper trading stopped.")

    except Exception as e:
        logger.error(f"Paper trading failed: {e}", exc_info=True)
        return 1

    return 0


def live_command(args):
    """Run bot in live trading mode (with confirmation)."""
    logger.warning("=" * 60)
    logger.warning("LIVE TRADING MODE - REAL MONEY AT RISK!")
    logger.warning("=" * 60)

    # Safety confirmation
    print("\n⚠️  WARNING: You are about to start LIVE trading with REAL money!")
    print(f"Exchange: {settings.exchange_name}")
    print(f"Testnet: {settings.exchange_testnet}")
    print(f"Pair: {args.pair}")
    print(f"Timeframe: {args.timeframe}\n")

    confirmation = input("Type 'START LIVE TRADING' to confirm (case-sensitive): ")

    if confirmation != "START LIVE TRADING":
        logger.info("Live trading cancelled by user.")
        return 0

    logger.info("Starting live trading...")
    logger.info("Note: Full live trading implementation is under development.")
    logger.info("Please use paper trading mode for testing.")

    return 0


def analyze_command(args):
    """Analyze trading performance."""
    logger.info("=" * 60)
    logger.info("PERFORMANCE ANALYSIS")
    logger.info("=" * 60)

    try:
        from src.database.repository import Repository

        repo = Repository(settings.database_url)

        # Get trades
        trades = repo.get_all_trades()

        if not trades:
            logger.info("No trades found in database.")
            return 0

        logger.info(f"Total trades: {len(trades)}")

        # Calculate metrics
        closed_trades = [t for t in trades if t.status == "closed"]
        winning_trades = [t for t in closed_trades if t.pnl > 0]

        if closed_trades:
            total_pnl = sum(t.pnl for t in closed_trades)
            win_rate = (len(winning_trades) / len(closed_trades)) * 100

            logger.info(f"Closed trades: {len(closed_trades)}")
            logger.info(f"Winning trades: {len(winning_trades)}")
            logger.info(f"Win rate: {win_rate:.1f}%")
            logger.info(f"Total PnL: ${total_pnl:.2f}")

        repo.close()

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1

    return 0


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Cryptocurrency Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py backtest --pair BTCUSDT --start 2024-01-01 --end 2024-12-31
  python main.py paper --pair BTCUSDT --timeframe 5m
  python main.py live --pair BTCUSDT
  python main.py analyze --days 30
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Run backtesting")
    backtest_parser.add_argument("--pair", default="BTC/USDT", help="Trading pair")
    backtest_parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    backtest_parser.add_argument("--end", default="2024-12-31", help="End date (YYYY-MM-DD)")
    backtest_parser.add_argument("--timeframe", default="1h", help="Timeframe")

    # Paper trading command
    paper_parser = subparsers.add_parser("paper", help="Run paper trading")
    paper_parser.add_argument("--pair", default="BTC/USDT", help="Trading pair")
    paper_parser.add_argument("--timeframe", default="5m", help="Timeframe")

    # Live trading command
    live_parser = subparsers.add_parser("live", help="Run live trading")
    live_parser.add_argument("--pair", default="BTC/USDT", help="Trading pair")
    live_parser.add_argument("--timeframe", default="5m", help="Timeframe")

    # Analysis command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze performance")
    analyze_parser.add_argument("--days", type=int, default=30, help="Days to analyze")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "backtest":
        return backtest_command(args)
    elif args.command == "paper":
        return paper_command(args)
    elif args.command == "live":
        return live_command(args)
    elif args.command == "analyze":
        return analyze_command(args)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
