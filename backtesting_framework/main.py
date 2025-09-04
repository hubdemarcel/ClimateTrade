#!/usr/bin/env python3
"""
ClimateTrade Backtesting Framework - Main Runner

This script demonstrates how to use the comprehensive backtesting framework
for weather-based trading strategies on Polymarket.
"""

import argparse
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.backtesting_engine import BacktestingEngine, BacktestConfig, BacktestResult
from data.data_loader import BacktestingDataLoader
from strategies.weather_strategies import (
    TemperatureThresholdStrategy,
    PrecipitationStrategy,
    WindSpeedStrategy,
    WeatherPatternStrategy,
    SeasonalWeatherStrategy
)
from optimization.strategy_optimizer import StrategyOptimizer, ParameterSpace
from metrics.performance_metrics import PerformanceMetrics
from risk.risk_metrics import RiskMetrics
from utils.reporting import BacktestReporter

# Import centralized logging
try:
    # Add project root to path for utils
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logging import setup_logging, get_logger
    # Setup centralized logging
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging if centralized system not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backtesting.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)


def create_sample_config() -> BacktestConfig:
    """Create a sample backtest configuration"""
    return BacktestConfig(
        start_date=datetime.now() - timedelta(days=90),
        end_date=datetime.now(),
        initial_capital=10000.0,
        commission_per_trade=0.001,
        max_position_size=0.1,
        max_positions=5,
        data_frequency='H',
        enable_parallel=False
    )


def run_single_strategy_backtest(strategy_name: str,
                                market_ids: Optional[List[str]] = None,
                                locations: Optional[List[str]] = None) -> BacktestResult:
    """
    Run a backtest for a single strategy

    Args:
        strategy_name: Name of the strategy to run
        market_ids: Optional list of market IDs to test
        locations: Optional list of weather locations to use

    Returns:
        BacktestResult object
    """
    logger.info(f"Running backtest for strategy: {strategy_name}")

    # Create configuration
    config = create_sample_config()

    # Initialize components
    engine = BacktestingEngine(config)
    data_loader = BacktestingDataLoader()

    # Create strategy instance
    strategy_classes = {
        'temperature': TemperatureThresholdStrategy,
        'precipitation': PrecipitationStrategy,
        'wind': WindSpeedStrategy,
        'pattern': WeatherPatternStrategy,
        'seasonal': SeasonalWeatherStrategy
    }

    if strategy_name not in strategy_classes:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    strategy = strategy_classes[strategy_name]()

    # Run backtest
    result = engine.run_backtest(strategy, market_ids, locations)

    logger.info(f"Backtest completed. Total return: {result.total_return:.2%}")
    return result


def run_multiple_strategies_backtest(strategy_names: List[str],
                                   market_ids: Optional[List[str]] = None,
                                   locations: Optional[List[str]] = None) -> List[BacktestResult]:
    """
    Run backtests for multiple strategies

    Args:
        strategy_names: List of strategy names to run
        market_ids: Optional list of market IDs to test
        locations: Optional list of weather locations to use

    Returns:
        List of BacktestResult objects
    """
    logger.info(f"Running backtests for {len(strategy_names)} strategies")

    config = create_sample_config()
    engine = BacktestingEngine(config)

    strategies = []
    strategy_classes = {
        'temperature': TemperatureThresholdStrategy,
        'precipitation': PrecipitationStrategy,
        'wind': WindSpeedStrategy,
        'pattern': WeatherPatternStrategy,
        'seasonal': SeasonalWeatherStrategy
    }

    for name in strategy_names:
        if name in strategy_classes:
            strategies.append(strategy_classes[name]())

    if not strategies:
        raise ValueError("No valid strategies specified")

    results = engine.run_multiple_strategies(strategies, market_ids, locations)

    # Sort results by Sharpe ratio
    results.sort(key=lambda x: x.sharpe_ratio, reverse=True)

    logger.info("Multi-strategy backtest completed")
    return results


def optimize_strategy(strategy_name: str,
                     optimization_method: str = 'random_search',
                     max_evaluations: int = 50) -> Dict[str, Any]:
    """
    Optimize strategy parameters

    Args:
        strategy_name: Name of strategy to optimize
        optimization_method: Optimization method ('grid_search', 'random_search', 'bayesian', 'evolutionary')
        max_evaluations: Maximum number of parameter evaluations

    Returns:
        Dictionary with optimization results
    """
    logger.info(f"Optimizing strategy: {strategy_name} using {optimization_method}")

    config = create_sample_config()
    engine = BacktestingEngine(config)
    optimizer = StrategyOptimizer(engine)

    strategy_classes = {
        'temperature': TemperatureThresholdStrategy,
        'precipitation': PrecipitationStrategy,
        'wind': WindSpeedStrategy,
        'pattern': WeatherPatternStrategy,
        'seasonal': SeasonalWeatherStrategy
    }

    if strategy_name not in strategy_classes:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    strategy_class = strategy_classes[strategy_name]

    # Define parameter spaces for optimization
    parameter_spaces = get_parameter_spaces(strategy_name)

    # Run optimization
    optimization_result = optimizer.optimize_strategy(
        strategy_class=strategy_class,
        parameter_spaces=parameter_spaces,
        optimization_method=optimization_method,
        max_evaluations=max_evaluations
    )

    logger.info(f"Optimization completed. Best score: {optimization_result.best_score:.4f}")

    return {
        'best_parameters': optimization_result.best_parameters,
        'best_score': optimization_result.best_score,
        'optimization_method': optimization_result.optimization_method,
        'total_evaluations': len(optimization_result.optimization_history),
        'history': optimization_result.optimization_history
    }


def get_parameter_spaces(strategy_name: str) -> Dict[str, ParameterSpace]:
    """Get parameter spaces for strategy optimization"""
    if strategy_name == 'temperature':
        return {
            'hot_threshold': ParameterSpace(
                name='hot_threshold',
                param_type='continuous',
                min_value=20.0,
                max_value=40.0
            ),
            'cold_threshold': ParameterSpace(
                name='cold_threshold',
                param_type='continuous',
                min_value=-10.0,
                max_value=10.0
            ),
            'signal_strength_threshold': ParameterSpace(
                name='signal_strength_threshold',
                param_type='continuous',
                min_value=0.5,
                max_value=0.9
            )
        }
    elif strategy_name == 'precipitation':
        return {
            'rain_threshold': ParameterSpace(
                name='rain_threshold',
                param_type='continuous',
                min_value=5.0,
                max_value=50.0
            ),
            'drought_threshold': ParameterSpace(
                name='drought_threshold',
                param_type='continuous',
                min_value=0.0,
                max_value=1.0
            ),
            'signal_strength_threshold': ParameterSpace(
                name='signal_strength_threshold',
                param_type='continuous',
                min_value=0.6,
                max_value=0.9
            )
        }
    elif strategy_name == 'wind':
        return {
            'high_wind_threshold': ParameterSpace(
                name='high_wind_threshold',
                param_type='continuous',
                min_value=10.0,
                max_value=30.0
            ),
            'low_wind_threshold': ParameterSpace(
                name='low_wind_threshold',
                param_type='continuous',
                min_value=1.0,
                max_value=5.0
            ),
            'signal_strength_threshold': ParameterSpace(
                name='signal_strength_threshold',
                param_type='continuous',
                min_value=0.6,
                max_value=0.9
            )
        }
    else:
        # Default parameter space
        return {
            'signal_strength_threshold': ParameterSpace(
                name='signal_strength_threshold',
                param_type='continuous',
                min_value=0.5,
                max_value=0.9
            )
        }


def generate_comprehensive_report(results: List[BacktestResult],
                                output_file: str = 'backtest_report.html') -> None:
    """
    Generate a comprehensive HTML report

    Args:
        results: List of backtest results
        output_file: Output file path
    """
    logger.info(f"Generating comprehensive report: {output_file}")

    reporter = BacktestReporter()

    # Generate HTML report
    html_content = reporter.generate_html_report(results)

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"Report saved to {output_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="ClimateTrade Backtesting Framework")
    parser.add_argument(
        'command',
        choices=['single', 'multi', 'optimize', 'report'],
        help='Command to execute'
    )
    parser.add_argument(
        '--strategy', '-s',
        nargs='+',
        help='Strategy name(s) to use'
    )
    parser.add_argument(
        '--markets', '-m',
        nargs='+',
        help='Market IDs to test'
    )
    parser.add_argument(
        '--locations', '-l',
        nargs='+',
        help='Weather locations to use'
    )
    parser.add_argument(
        '--optimization-method', '-o',
        choices=['grid_search', 'random_search', 'bayesian', 'evolutionary'],
        default='random_search',
        help='Optimization method'
    )
    parser.add_argument(
        '--max-evaluations', '-e',
        type=int,
        default=50,
        help='Maximum optimization evaluations'
    )
    parser.add_argument(
        '--output', '-f',
        default='backtest_report.html',
        help='Output file for reports'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        # Update logging level for verbose output
        try:
            from utils.logging import update_logging_config, LogConfig
            config = LogConfig(level='DEBUG', console_level='DEBUG')
            update_logging_config(config)
        except ImportError:
            logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.command == 'single':
            if not args.strategy or len(args.strategy) != 1:
                raise ValueError("Single strategy mode requires exactly one strategy")

            result = run_single_strategy_backtest(
                args.strategy[0],
                args.markets,
                args.locations
            )

            # Print summary
            print(f"\nBacktest Results for {args.strategy[0]}:")
            print(f"Total Return: {result.total_return:.2%}")
            print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"Max Drawdown: {result.max_drawdown:.2%}")
            print(f"Win Rate: {result.win_rate:.2%}")
            print(f"Total Trades: {result.total_trades}")

        elif args.command == 'multi':
            if not args.strategy:
                raise ValueError("Multi strategy mode requires at least one strategy")

            results = run_multiple_strategies_backtest(
                args.strategy,
                args.markets,
                args.locations
            )

            # Print summary for each strategy
            print("\nMulti-Strategy Backtest Results:")
            print("-" * 60)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.strategy_name}")
                print(".2%"                   ".2f"                   ".2%"                   ".2%"                   f"   Trades: {result.total_trades}")
                print()

        elif args.command == 'optimize':
            if not args.strategy or len(args.strategy) != 1:
                raise ValueError("Optimize mode requires exactly one strategy")

            optimization_result = optimize_strategy(
                args.strategy[0],
                args.optimization_method,
                args.max_evaluations
            )

            # Print optimization results
            print(f"\nOptimization Results for {args.strategy[0]}:")
            print(f"Method: {optimization_result['optimization_method']}")
            print(f"Best Score: {optimization_result['best_score']:.4f}")
            print(f"Total Evaluations: {optimization_result['total_evaluations']}")
            print(f"Best Parameters: {json.dumps(optimization_result['best_parameters'], indent=2)}")

        elif args.command == 'report':
            # Load results from previous runs (this would need to be implemented)
            print("Report generation not yet implemented for saved results")
            print("Use single/multi commands to generate new results")

    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())