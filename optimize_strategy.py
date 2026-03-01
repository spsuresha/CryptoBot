"""
Strategy Parameter Optimization using Grid Search.
Tests different parameter combinations to find optimal settings.
"""
import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
from itertools import product
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.exchange.connector import ExchangeConnector
from src.exchange.data_fetcher import DataFetcher
from src.strategies.ma_crossover import MACrossoverStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.performance import PerformanceMetrics

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """Grid search optimizer for strategy parameters."""

    def __init__(
        self,
        initial_capital: float = 1000.0,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.results: List[Dict] = []

    def generate_parameter_grid(
        self,
        fast_periods: List[int] = None,
        slow_periods: List[int] = None,
        rsi_overbought: List[int] = None,
        rsi_oversold: List[int] = None,
        use_rsi_filter: List[bool] = None,
        use_macd_filter: List[bool] = None
    ) -> List[Dict]:
        """
        Generate all parameter combinations for grid search.

        Args:
            fast_periods: List of fast MA periods to test
            slow_periods: List of slow MA periods to test
            rsi_overbought: List of RSI overbought thresholds
            rsi_oversold: List of RSI oversold thresholds
            use_rsi_filter: Whether to use RSI filter
            use_macd_filter: Whether to use MACD filter

        Returns:
            List of parameter dictionaries
        """
        # Default parameter ranges
        if fast_periods is None:
            fast_periods = [5, 10, 15, 20]
        if slow_periods is None:
            slow_periods = [20, 30, 40, 50]
        if rsi_overbought is None:
            rsi_overbought = [65, 70, 75]
        if rsi_oversold is None:
            rsi_oversold = [25, 30, 35]
        if use_rsi_filter is None:
            use_rsi_filter = [True, False]
        if use_macd_filter is None:
            use_macd_filter = [True, False]

        # Generate all combinations
        param_grid = []
        for fast, slow, rsi_ob, rsi_os, use_rsi, use_macd in product(
            fast_periods, slow_periods, rsi_overbought, rsi_oversold,
            use_rsi_filter, use_macd_filter
        ):
            # Skip invalid combinations (fast must be less than slow)
            if fast >= slow:
                continue

            param_grid.append({
                'fast_period': fast,
                'slow_period': slow,
                'rsi_overbought': rsi_ob,
                'rsi_oversold': rsi_os,
                'use_rsi_filter': use_rsi,
                'use_macd_filter': use_macd
            })

        return param_grid

    def run_backtest_with_params(
        self,
        df: pd.DataFrame,
        params: Dict,
        symbol: str
    ) -> Dict:
        """
        Run backtest with specific parameters.

        Args:
            df: Historical price data
            params: Strategy parameters
            symbol: Trading pair symbol

        Returns:
            Results dictionary with metrics
        """
        # Create strategy with parameters (as dict with rsi_period added)
        strategy_params = params.copy()
        strategy_params['rsi_period'] = 14
        strategy = MACrossoverStrategy(parameters=strategy_params)

        # Run backtest
        backtest = BacktestEngine(
            strategy=strategy,
            initial_capital=self.initial_capital,
            commission=self.commission,
            slippage=self.slippage
        )

        results = backtest.run(df.copy(), symbol=symbol)
        metrics = PerformanceMetrics.calculate_all_metrics(results)

        # Add parameters to results
        result = {
            'params': params,
            'total_return': metrics.get('total_return', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'win_rate': metrics.get('win_rate', 0),
            'profit_factor': metrics.get('profit_factor', 0),
            'num_trades': metrics.get('num_trades', 0),
            'avg_trade': metrics.get('avg_trade', 0),
            'final_capital': metrics.get('final_capital', self.initial_capital),
            'sortino_ratio': metrics.get('sortino_ratio', 0),
            'calmar_ratio': metrics.get('calmar_ratio', 0)
        }

        return result

    def optimize(
        self,
        df: pd.DataFrame,
        symbol: str,
        param_grid: List[Dict] = None,
        ranking_metric: str = 'sharpe_ratio',
        min_trades: int = 10
    ) -> pd.DataFrame:
        """
        Run grid search optimization.

        Args:
            df: Historical price data
            symbol: Trading pair symbol
            param_grid: Parameter combinations to test (None = use default)
            ranking_metric: Metric to rank results by
            min_trades: Minimum number of trades required

        Returns:
            DataFrame with all results sorted by ranking metric
        """
        if param_grid is None:
            param_grid = self.generate_parameter_grid()

        logger.info(f"Starting grid search with {len(param_grid)} parameter combinations")
        logger.info(f"Ranking by: {ranking_metric}")
        logger.info(f"Minimum trades: {min_trades}")

        # Run backtests for all parameter combinations
        self.results = []
        for i, params in enumerate(param_grid, 1):
            try:
                logger.info(f"Testing combination {i}/{len(param_grid)}: {params}")
                result = self.run_backtest_with_params(df, params, symbol)
                self.results.append(result)

                # Print progress every 10 combinations
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(param_grid)} completed")

            except Exception as e:
                logger.error(f"Error testing parameters {params}: {e}")
                continue

        # Convert to DataFrame for easy analysis
        results_df = pd.DataFrame(self.results)

        # Check if we have any results
        if len(results_df) == 0:
            logger.error("All parameter combinations failed. No results to analyze.")
            return pd.DataFrame()

        # Filter by minimum trades
        results_df = results_df[results_df['num_trades'] >= min_trades]

        if len(results_df) == 0:
            logger.warning("No parameter combinations met the minimum trades requirement")
            return pd.DataFrame()

        # Sort by ranking metric (descending for most metrics)
        ascending = ranking_metric in ['max_drawdown']  # Lower is better for drawdown
        results_df = results_df.sort_values(by=ranking_metric, ascending=ascending)

        logger.info(f"Optimization complete! Tested {len(param_grid)} combinations")
        logger.info(f"Valid results (>= {min_trades} trades): {len(results_df)}")

        return results_df

    def print_top_results(self, results_df: pd.DataFrame, top_n: int = 10):
        """Print top N results in readable format."""
        print("\n" + "=" * 100)
        print(f"TOP {top_n} PARAMETER COMBINATIONS")
        print("=" * 100)

        for i, (idx, row) in enumerate(results_df.head(top_n).iterrows(), 1):
            params = row['params']
            print(f"\nRank #{i}")
            print("-" * 100)
            print(f"Parameters:")
            print(f"  Fast MA: {params['fast_period']}, Slow MA: {params['slow_period']}")
            print(f"  RSI Overbought: {params['rsi_overbought']}, RSI Oversold: {params['rsi_oversold']}")
            print(f"  RSI Filter: {params['use_rsi_filter']}, MACD Filter: {params['use_macd_filter']}")
            print(f"\nPerformance:")
            print(f"  Total Return: {row['total_return']:.2f}%")
            print(f"  Sharpe Ratio: {row['sharpe_ratio']:.2f}")
            print(f"  Sortino Ratio: {row['sortino_ratio']:.2f}")
            print(f"  Calmar Ratio: {row['calmar_ratio']:.2f}")
            print(f"  Max Drawdown: {row['max_drawdown']:.2f}%")
            print(f"  Win Rate: {row['win_rate']:.2f}%")
            print(f"  Profit Factor: {row['profit_factor']:.2f}")
            print(f"  Number of Trades: {row['num_trades']}")
            print(f"  Average Trade: {row['avg_trade']:.2f}%")
            print(f"  Final Capital: ${row['final_capital']:.2f}")

        print("\n" + "=" * 100)

    def save_results(self, results_df: pd.DataFrame, filename: str = None):
        """Save optimization results to CSV and JSON files."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'optimization_results_{timestamp}'

        # Save to CSV
        csv_path = f'reports/{filename}.csv'
        os.makedirs('reports', exist_ok=True)
        results_df.to_csv(csv_path, index=False)
        logger.info(f"Results saved to {csv_path}")

        # Save top 10 to JSON for easy config update
        top_10 = results_df.head(10).to_dict('records')
        json_path = f'reports/{filename}_top10.json'
        with open(json_path, 'w') as f:
            json.dump(top_10, f, indent=2, default=str)
        logger.info(f"Top 10 results saved to {json_path}")

        return csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description='Optimize trading strategy parameters')
    parser.add_argument('--pair', type=str, default='BTC/USDT', help='Trading pair')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe')
    parser.add_argument('--initial-capital', type=float, default=1000.0, help='Initial capital')
    parser.add_argument('--ranking', type=str, default='sharpe_ratio',
                        choices=['sharpe_ratio', 'total_return', 'sortino_ratio', 'calmar_ratio', 'profit_factor'],
                        help='Metric to rank results by')
    parser.add_argument('--min-trades', type=int, default=10, help='Minimum number of trades')
    parser.add_argument('--fast-periods', type=str, default='5,10,15,20',
                        help='Comma-separated fast MA periods')
    parser.add_argument('--slow-periods', type=str, default='20,30,40,50',
                        help='Comma-separated slow MA periods')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: Test fewer combinations')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 100)
    print("STRATEGY PARAMETER OPTIMIZATION")
    print("=" * 100)
    print(f"Pair: {args.pair}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Initial Capital: ${args.initial_capital}")
    print(f"Ranking Metric: {args.ranking}")
    print(f"Minimum Trades: {args.min_trades}")
    print("=" * 100)

    # Load settings and fetch data
    settings = Settings()
    connector = ExchangeConnector(settings)
    connector.connect()
    data_fetcher = DataFetcher(connector)

    logger.info("Fetching historical data...")

    # Parse dates
    start_dt = datetime.strptime(args.start, '%Y-%m-%d')
    end_dt = datetime.strptime(args.end, '%Y-%m-%d')

    df = data_fetcher.fetch_ohlcv_dataframe(
        symbol=args.pair,
        timeframe=args.timeframe,
        since=start_dt,
        until=end_dt
    )
    logger.info(f"Loaded {len(df)} candles")

    # Parse parameter ranges
    fast_periods = [int(x) for x in args.fast_periods.split(',')]
    slow_periods = [int(x) for x in args.slow_periods.split(',')]

    # Quick mode: fewer combinations
    if args.quick:
        fast_periods = [10, 15]
        slow_periods = [30, 40]
        rsi_overbought = [70]
        rsi_oversold = [30]
        use_rsi = [True]
        use_macd = [True]
        logger.info("Quick mode: Testing limited parameter combinations")
    else:
        rsi_overbought = [65, 70, 75]
        rsi_oversold = [25, 30, 35]
        use_rsi = [True, False]
        use_macd = [True, False]

    # Create optimizer
    optimizer = StrategyOptimizer(
        initial_capital=args.initial_capital,
        commission=settings.commission,
        slippage=settings.slippage
    )

    # Generate parameter grid
    param_grid = optimizer.generate_parameter_grid(
        fast_periods=fast_periods,
        slow_periods=slow_periods,
        rsi_overbought=rsi_overbought,
        rsi_oversold=rsi_oversold,
        use_rsi_filter=use_rsi,
        use_macd_filter=use_macd
    )

    logger.info(f"Generated {len(param_grid)} parameter combinations to test")

    # Run optimization
    results_df = optimizer.optimize(
        df=df,
        symbol=args.pair,
        param_grid=param_grid,
        ranking_metric=args.ranking,
        min_trades=args.min_trades
    )

    if len(results_df) == 0:
        print("\nNo valid results found. Try:")
        print("  - Longer time period")
        print("  - Lower min_trades threshold")
        print("  - Different parameter ranges")
        return

    # Print top results
    optimizer.print_top_results(results_df, top_n=10)

    # Save results
    csv_path, json_path = optimizer.save_results(results_df)

    # Print best parameters for config.yaml
    best = results_df.iloc[0]
    best_params = best['params']

    print("\n" + "=" * 100)
    print("RECOMMENDED CONFIG.YAML SETTINGS")
    print("=" * 100)
    print("strategy:")
    print("  name: ma_crossover")
    print("  parameters:")
    print(f"    fast_period: {best_params['fast_period']}")
    print(f"    slow_period: {best_params['slow_period']}")
    print(f"    use_rsi_filter: {str(best_params['use_rsi_filter']).lower()}")
    print("    rsi_period: 14")
    print(f"    rsi_overbought: {best_params['rsi_overbought']}")
    print(f"    rsi_oversold: {best_params['rsi_oversold']}")
    print(f"    use_macd_filter: {str(best_params['use_macd_filter']).lower()}")
    print("=" * 100)

    print(f"\nFull results saved to: {csv_path}")
    print(f"Top 10 results saved to: {json_path}")


if __name__ == '__main__':
    main()
