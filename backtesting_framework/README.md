# ClimateTrade Backtesting Framework

A comprehensive simulation framework for backtesting weather-based trading signals on Polymarket. This framework enables systematic testing and optimization of trading strategies that use historical weather data to predict market movements.

## Features

### 🚀 Core Capabilities

- **Historical Data Integration**: Seamless integration with existing ClimateTrade data pipeline
- **Multiple Weather Sources**: Support for Met Office, Meteostat, NWS, and other weather APIs
- **Strategy Framework**: Extensible base classes for implementing custom trading strategies
- **Performance Metrics**: Comprehensive risk-adjusted performance calculations
- **Risk Analysis**: Value at Risk (VaR), Expected Shortfall, stress testing
- **Strategy Optimization**: Multiple optimization methods (grid search, random search, evolutionary)
- **Parallel Processing**: Multi-threaded backtesting for improved performance
- **Visualization**: HTML reports with interactive charts and performance summaries

### 📊 Supported Metrics

- **Return Metrics**: Total return, annualized return, alpha/beta
- **Risk Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio, maximum drawdown
- **Trading Metrics**: Win rate, profit factor, expectancy, Kelly criterion
- **Risk Measures**: VaR, Expected Shortfall, Ulcer Index, stress test results

## Architecture

```
backtesting_framework/
├── core/                    # Core backtesting engine
│   └── backtesting_engine.py
├── data/                    # Data loading and preprocessing
│   └── data_loader.py
├── strategies/              # Trading strategy implementations
│   ├── base_strategy.py
│   └── weather_strategies.py
├── metrics/                 # Performance calculation
│   └── performance_metrics.py
├── risk/                    # Risk analysis and VaR calculations
│   └── risk_metrics.py
├── optimization/            # Strategy parameter optimization
│   └── strategy_optimizer.py
├── utils/                   # Utilities and reporting
│   └── reporting.py
└── main.py                  # Command-line interface
```

## Quick Start

### Prerequisites

- Python 3.8+
- SQLite database with historical weather and market data
- Required packages: pandas, numpy, scipy, matplotlib

### Installation

```bash
cd backtesting_framework
pip install -r requirements.txt
```

### Basic Usage

#### Single Strategy Backtest

```python
from backtesting_framework.main import run_single_strategy_backtest
from datetime import datetime, timedelta

# Run a temperature-based strategy
result = run_single_strategy_backtest(
    strategy_name='temperature',
    market_ids=['temp_market_1', 'temp_market_2'],
    locations=['London, UK', 'New York City, NY']
)

print(f"Strategy Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

#### Command Line Interface

```bash
# Single strategy backtest
python main.py single --strategy temperature --markets temp_market_1 --locations "London, UK"

# Multiple strategies comparison
python main.py multi --strategy temperature precipitation wind --markets temp_market_1

# Strategy optimization
python main.py optimize --strategy temperature --optimization-method random_search --max-evaluations 100
```

## Strategy Examples

### Temperature Threshold Strategy

Trades based on temperature crossing predefined thresholds:

```python
from backtesting_framework.strategies.weather_strategies import TemperatureThresholdStrategy

strategy = TemperatureThresholdStrategy(parameters={
    'hot_threshold': 30.0,      # Celsius
    'cold_threshold': 0.0,      # Celsius
    'signal_strength_threshold': 0.7
})
```

### Precipitation Strategy

Trades based on rainfall patterns and drought conditions:

```python
from backtesting_framework.strategies.weather_strategies import PrecipitationStrategy

strategy = PrecipitationStrategy(parameters={
    'rain_threshold': 10.0,     # mm
    'drought_threshold': 0.1,   # mm
    'signal_strength_threshold': 0.8
})
```

### Weather Pattern Strategy

Advanced strategy using multiple weather variables and correlations:

```python
from backtesting_framework.strategies.weather_strategies import WeatherPatternStrategy

strategy = WeatherPatternStrategy(parameters={
    'pattern_lookback': 168,    # 7 days in hours
    'correlation_threshold': 0.7,
    'signal_strength_threshold': 0.8
})
```

## Custom Strategy Development

### Implementing a New Strategy

```python
from backtesting_framework.strategies.base_strategy import BaseWeatherStrategy, TradingSignal

class MyCustomStrategy(BaseWeatherStrategy):
    def __init__(self, name="MyStrategy", parameters=None):
        super().__init__(name, parameters)
        # Initialize strategy parameters

    def generate_signals(self, market_data, weather_data, current_positions):
        signals = []

        # Implement your signal generation logic here
        # Analyze weather_data and market_data
        # Generate TradingSignal objects

        return signals
```

### Strategy Parameters

Strategies support parameter optimization:

```python
parameter_spaces = {
    'threshold': ParameterSpace(
        name='threshold',
        param_type='continuous',
        min_value=0.0,
        max_value=100.0
    ),
    'lookback': ParameterSpace(
        name='lookback',
        param_type='discrete',
        min_value=24,
        max_value=168
    )
}
```

## Optimization Methods

### Grid Search

Exhaustive search over parameter combinations:

```python
optimizer.optimize_strategy(
    strategy_class=MyStrategy,
    parameter_spaces=parameter_spaces,
    optimization_method='grid_search',
    max_evaluations=100
)
```

### Random Search

Random sampling from parameter space:

```python
optimizer.optimize_strategy(
    strategy_class=MyStrategy,
    parameter_spaces=parameter_spaces,
    optimization_method='random_search',
    max_evaluations=200
)
```

### Evolutionary Optimization

Genetic algorithm-based optimization:

```python
optimizer.optimize_strategy(
    strategy_class=MyStrategy,
    parameter_spaces=parameter_spaces,
    optimization_method='evolutionary',
    max_evaluations=150
)
```

## Performance Analysis

### Key Metrics

- **Sharpe Ratio**: Risk-adjusted returns (higher is better)
- **Sortino Ratio**: Downside deviation only (higher is better)
- **Calmar Ratio**: Return vs maximum drawdown (higher is better)
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Maximum Drawdown**: Largest peak-to-trough decline

### Risk Analysis

- **Value at Risk (VaR)**: Potential loss at given confidence level
- **Expected Shortfall**: Average loss beyond VaR threshold
- **Stress Testing**: Performance under extreme scenarios
- **Recovery Analysis**: Time to recover from drawdowns

## Data Requirements

### Weather Data Schema

```sql
CREATE TABLE weather_data (
    timestamp TEXT,
    location_name TEXT,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    precipitation REAL,
    pressure REAL,
    weather_code INTEGER
);
```

### Market Data Schema

```sql
CREATE TABLE polymarket_data (
    timestamp TEXT,
    market_id TEXT,
    outcome_name TEXT,
    probability REAL,
    volume REAL,
    event_title TEXT
);
```

## Configuration

### Backtest Configuration

```python
config = BacktestConfig(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=10000.0,
    commission_per_trade=0.001,
    max_position_size=0.1,
    max_positions=5,
    data_frequency='H'
)
```

## Reporting

### HTML Reports

Generate comprehensive HTML reports with:

- Performance summary tables
- Equity curves and drawdown charts
- Monthly returns analysis
- Risk metrics dashboard
- Strategy comparison matrices

```python
from backtesting_framework.utils.reporting import BacktestReporter

reporter = BacktestReporter()
html_report = reporter.generate_html_report(results)
with open('backtest_report.html', 'w') as f:
    f.write(html_report)
```

## Advanced Features

### Parallel Processing

Enable multi-threaded backtesting for improved performance:

```python
config = BacktestConfig(enable_parallel=True)
```

### Walk-Forward Optimization

Optimize strategies using rolling time windows:

```python
# Coming in future version
optimizer.walk_forward_optimization(
    strategy_class=MyStrategy,
    parameter_spaces=parameter_spaces,
    window_size=30,  # days
    step_size=7      # days
)
```

### Custom Metrics

Add custom performance metrics:

```python
def custom_metric(result: BacktestResult) -> float:
    return result.total_return / result.max_drawdown

# Use in optimization
optimizer.optimize_strategy(
    strategy_class=MyStrategy,
    parameter_spaces=parameter_spaces,
    optimization_target=custom_metric
)
```

## Best Practices

### Strategy Development

1. **Start Simple**: Begin with basic strategies and gradually add complexity
2. **Data Quality**: Ensure weather and market data alignment
3. **Overfitting Prevention**: Use out-of-sample testing and walk-forward analysis
4. **Risk Management**: Always include position sizing and stop-loss logic

### Performance Evaluation

1. **Multiple Metrics**: Don't rely on a single performance metric
2. **Benchmarking**: Compare against buy-and-hold and other strategies
3. **Robustness**: Test across different market conditions
4. **Transaction Costs**: Include realistic trading costs

### Optimization

1. **Parameter Ranges**: Set realistic parameter bounds
2. **Evaluation Budget**: Balance optimization time vs. improvement
3. **Cross-Validation**: Use time-series cross-validation
4. **Regularization**: Avoid over-optimization

## Troubleshooting

### Common Issues

- **Data Alignment**: Ensure weather and market data timestamps match
- **Memory Usage**: For large datasets, consider data chunking
- **Performance**: Use parallel processing for multiple strategy evaluation
- **Convergence**: Adjust optimization parameters for better convergence

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Adding New Strategies

1. Extend `BaseWeatherStrategy` class
2. Implement `generate_signals` method
3. Add strategy to `main.py` command-line interface
4. Include comprehensive docstrings and examples

### Adding New Metrics

1. Extend `PerformanceMetrics` or `RiskMetrics` classes
2. Add metric calculation methods
3. Update result reporting
4. Include metric in optimization targets

## License

This project is part of the ClimateTrade ecosystem. See project LICENSE file for details.

## Support

For questions and support:

- Check the documentation in `docs/` directory
- Review example scripts in `examples/` directory
- Open issues on the project repository

---

**Note**: This framework is designed for research and educational purposes. Always validate strategies with real market conditions and consider transaction costs, slippage, and other real-world factors before live trading.
