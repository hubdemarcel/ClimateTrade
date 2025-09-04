#!/usr/bin/env python3
"""
Example Usage of ClimateTrade Backtesting Framework

This script demonstrates how to use the backtesting framework
to test weather-based trading strategies on Polymarket data.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the backtesting framework to Python path
sys.path.insert(0, os.path.dirname(__file__))

from core.backtesting_engine import BacktestingEngine, BacktestConfig
from strategies.weather_strategies import (
    TemperatureThresholdStrategy,
    PrecipitationStrategy,
    WindSpeedStrategy,
    WeatherPatternStrategy
)
from optimization.strategy_optimizer import StrategyOptimizer, ParameterSpace
from utils.reporting import BacktestReporter


def example_single_strategy():
    """Example: Run a single strategy backtest"""
    print("=== Single Strategy Backtest Example ===")

    # Create backtest configuration
    config = BacktestConfig(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        initial_capital=10000.0,
        commission_per_trade=0.001,
        max_position_size=0.1,
        max_positions=3,
        data_frequency='H'
    )

    # Initialize components
    engine = BacktestingEngine(config)

    # Create and run temperature strategy
    strategy = TemperatureThresholdStrategy(parameters={
        'hot_threshold': 25.0,
        'cold_threshold': 5.0,
        'signal_strength_threshold': 0.7
    })

    try:
        result = engine.run_backtest(strategy)

        print("Backtest Results:")
        print(".2%"        print(".2f"        print(".2%"        print(".2%"        print(f"Total Trades: {result.total_trades}")

        return result

    except Exception as e:
        print(f"Backtest failed: {e}")
        return None


def example_multiple_strategies():
    """Example: Compare multiple strategies"""
    print("\n=== Multiple Strategies Comparison Example ===")

    config = BacktestConfig(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        initial_capital=10000.0
    )

    engine = BacktestingEngine(config)

    strategies = [
        TemperatureThresholdStrategy(name="Temp Strategy"),
        PrecipitationStrategy(name="Rain Strategy"),
        WindSpeedStrategy(name="Wind Strategy")
    ]

    results = []
    for strategy in strategies:
        try:
            result = engine.run_backtest(strategy)
            results.append(result)
            print(".2%"        except Exception as e:
            print(f"Strategy {strategy.name} failed: {e}")

    # Sort by Sharpe ratio
    results.sort(key=lambda x: x.sharpe_ratio, reverse=True)

    print("\nStrategy Comparison (sorted by Sharpe ratio):")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.strategy_name}: Sharpe={result.sharpe_ratio:.2f}, Return={result.total_return:.2%}")

    return results


def example_strategy_optimization():
    """Example: Optimize strategy parameters"""
    print("\n=== Strategy Optimization Example ===")

    config = BacktestConfig(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )

    engine = BacktestingEngine(config)
    optimizer = StrategyOptimizer(engine)

    # Define parameter spaces for temperature strategy
    parameter_spaces = {
        'hot_threshold': ParameterSpace(
            name='hot_threshold',
            param_type='continuous',
            min_value=20.0,
            max_value=35.0
        ),
        'cold_threshold': ParameterSpace(
            name='cold_threshold',
            param_type='continuous',
            min_value=-5.0,
            max_value=10.0
        ),
        'signal_strength_threshold': ParameterSpace(
            name='signal_strength_threshold',
            param_type='continuous',
            min_value=0.5,
            max_value=0.9
        )
    }

    try:
        # Run optimization
        optimization_result = optimizer.optimize_strategy(
            strategy_class=TemperatureThresholdStrategy,
            parameter_spaces=parameter_spaces,
            optimization_method='random_search',
            max_evaluations=20  # Small number for demo
        )

        print("Optimization Results:")
        print(f"Best Parameters: {optimization_result.best_parameters}")
        print(".4f"        print(f"Total Evaluations: {len(optimization_result.optimization_history)}")

        return optimization_result

    except Exception as e:
        print(f"Optimization failed: {e}")
        return None


def example_advanced_strategy():
    """Example: Use advanced weather pattern strategy"""
    print("\n=== Advanced Weather Pattern Strategy Example ===")

    config = BacktestConfig(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        initial_capital=10000.0
    )

    engine = BacktestingEngine(config)

    # Advanced strategy with custom parameters
    strategy = WeatherPatternStrategy(parameters={
        'pattern_lookback': 72,  # 3 days
        'correlation_threshold': 0.6,
        'signal_strength_threshold': 0.75
    })

    try:
        result = engine.run_backtest(strategy)

        print("Advanced Strategy Results:")
        print(".2%"        print(".2f"        print(".2%"        print(f"Total Trades: {result.total_trades}")

        # Show some additional metrics
        if result.metrics:
            print(f"Profit Factor: {result.metrics.get('profit_factor', 'N/A')}")
            print(f"Expectancy: {result.metrics.get('expectancy', 'N/A')}")

        return result

    except Exception as e:
        print(f"Advanced strategy backtest failed: {e}")
        return None


def example_generate_report(results):
    """Example: Generate HTML report"""
    print("\n=== Report Generation Example ===")

    if not results:
        print("No results to report")
        return

    try:
        reporter = BacktestReporter()

        # Filter out None results
        valid_results = [r for r in results if r is not None]

        if valid_results:
            html_content = reporter.generate_html_report(valid_results)

            # Save report
            report_file = "backtest_example_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"Report saved to: {report_file}")
            print("Open the HTML file in a web browser to view the detailed report.")
        else:
            print("No valid results to report")

    except Exception as e:
        print(f"Report generation failed: {e}")


def main():
    """Main example function"""
    print("ClimateTrade Backtesting Framework - Examples")
    print("=" * 50)

    results = []

    # Run examples
    try:
        # Single strategy
        result1 = example_single_strategy()
        results.append(result1)

        # Multiple strategies
        multi_results = example_multiple_strategies()
        results.extend(multi_results)

        # Strategy optimization
        opt_result = example_strategy_optimization()
        if opt_result:
            # Create a mock BacktestResult from optimization
            # (In practice, you'd run the optimized strategy)
            pass

        # Advanced strategy
        result2 = example_advanced_strategy()
        results.append(result2)

        # Generate report
        example_generate_report(results)

    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"Examples failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNext steps:")
    print("1. Review the generated HTML report")
    print("2. Modify strategy parameters in the examples")
    print("3. Create your own custom strategies")
    print("4. Use the command-line interface: python main.py --help")


if __name__ == "__main__":
    main()