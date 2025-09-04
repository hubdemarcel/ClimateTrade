#!/usr/bin/env python3
"""
Shared test fixtures and data generators for ClimaTrade project tests.

This module provides common test fixtures, mock objects, and data generators
that can be used across all test modules in the project.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock

# Import project modules for fixtures
try:
    from backtesting_framework.core.backtesting_engine import (
        BacktestConfig, BacktestResult, BacktestingDataLoader
    )
    from backtesting_framework.strategies.base_strategy import (
        TradingSignal, Position, BaseWeatherStrategy
    )
    from backtesting_framework.data.data_loader import MarketData, WeatherData
except ImportError:
    # Handle case where modules aren't available during testing
    BacktestConfig = Mock
    BacktestResult = Mock
    BacktestingDataLoader = Mock
    TradingSignal = Mock
    Position = Mock
    BaseWeatherStrategy = Mock
    MarketData = Mock
    WeatherData = Mock


@pytest.fixture(scope="session")
def random_seed():
    """Set random seed for reproducible tests"""
    np.random.seed(42)
    return 42


@pytest.fixture
def sample_backtest_config():
    """Standard backtest configuration for testing"""
    return BacktestConfig(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        initial_capital=10000.0,
        commission_per_trade=0.001,
        max_position_size=0.1,
        max_positions=10,
        data_frequency='H',
        enable_parallel=False,
        risk_free_rate=0.02
    )


@pytest.fixture
def sample_market_data():
    """Generate sample market data for testing"""
    timestamps = pd.date_range('2024-01-01', '2024-01-02', freq='H')

    data = []
    for ts in timestamps:
        # Generate realistic market data
        base_price = 0.5 + 0.1 * np.sin(ts.timestamp() / 86400)  # Daily cycle
        noise = np.random.normal(0, 0.05)  # Random noise

        data.extend([
            {
                'timestamp': ts,
                'market_id': 'market1',
                'outcome_name': 'Yes',
                'probability': np.clip(base_price + noise, 0.01, 0.99),
                'volume': np.random.lognormal(8, 1),  # Log-normal volume
                'event_title': 'Will it rain tomorrow?',
                'scraped_at': ts + timedelta(minutes=np.random.uniform(0, 30))
            },
            {
                'timestamp': ts,
                'market_id': 'market1',
                'outcome_name': 'No',
                'probability': np.clip(1 - (base_price + noise), 0.01, 0.99),
                'volume': np.random.lognormal(8, 1),
                'event_title': 'Will it rain tomorrow?',
                'scraped_at': ts + timedelta(minutes=np.random.uniform(0, 30))
            }
        ])

    return pd.DataFrame(data)


@pytest.fixture
def sample_weather_data():
    """Generate sample weather data for testing"""
    timestamps = pd.date_range('2024-01-01', '2024-01-02', freq='H')

    data = []
    for i, ts in enumerate(timestamps):
        # Generate realistic weather patterns
        temp_base = 15 + 5 * np.sin(2 * np.pi * (i / 24))  # Daily temperature cycle
        humidity_base = 70 + 20 * np.sin(2 * np.pi * (i / 24 - 0.25))  # Phase-shifted

        data.append({
            'timestamp': ts,
            'location_name': 'London',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'temperature': temp_base + np.random.normal(0, 2),
            'temperature_min': temp_base - 5 + np.random.normal(0, 1),
            'temperature_max': temp_base + 5 + np.random.normal(0, 1),
            'humidity': np.clip(humidity_base + np.random.normal(0, 5), 0, 100),
            'wind_speed': np.random.exponential(5),  # Exponential distribution
            'precipitation': np.random.exponential(0.1),  # Mostly zero with occasional rain
            'pressure': 1013 + np.random.normal(0, 10),
            'weather_code': np.random.choice([800, 801, 802, 500, 300]),  # Common weather codes
            'weather_description': 'Generated weather',
            'source_name': 'test_source'
        })

    return pd.DataFrame(data)


@pytest.fixture
def sample_trading_signals():
    """Generate sample trading signals"""
    signals = []
    timestamps = pd.date_range('2024-01-01 10:00', '2024-01-01 15:00', freq='H')

    for i, ts in enumerate(timestamps):
        signals.append(TradingSignal(
            timestamp=ts,
            market_id='market1',
            outcome_name='Yes' if i % 2 == 0 else 'No',
            signal_type='BUY',
            confidence=0.6 + 0.3 * np.random.random(),
            quantity=1.0,
            price=0.5 + 0.1 * np.random.random(),
            reasoning=f'Signal {i+1}: Test reasoning'
        ))

    return signals


@pytest.fixture
def sample_positions():
    """Generate sample trading positions"""
    positions = []

    for i in range(3):
        entry_time = datetime(2024, 1, 1, 10 + i, 0)
        exit_time = entry_time + timedelta(hours=2) if i < 2 else None

        positions.append(Position(
            market_id='market1',
            outcome_name='Yes',
            quantity=1.0,
            entry_price=0.5 + 0.1 * np.random.random(),
            entry_time=entry_time,
            current_price=0.55 + 0.1 * np.random.random() if exit_time else None,
            exit_price=0.55 + 0.1 * np.random.random() if exit_time else None,
            exit_time=exit_time,
            pnl=0.05 + 0.1 * np.random.random() if exit_time else 0.0,
            status='CLOSED' if exit_time else 'OPEN'
        ))

    return positions


@pytest.fixture
def mock_data_loader(sample_market_data, sample_weather_data):
    """Mock data loader with sample data"""
    loader = Mock(spec=BacktestingDataLoader)
    loader.load_market_data.return_value = sample_market_data
    loader.load_weather_data.return_value = sample_weather_data
    loader.align_data_timeline.return_value = (sample_market_data, sample_weather_data)
    return loader


@pytest.fixture
def mock_strategy(sample_trading_signals, sample_positions):
    """Mock trading strategy"""
    strategy = Mock(spec=BaseWeatherStrategy)
    strategy.name = "MockStrategy"
    strategy.generate_signals.return_value = sample_trading_signals
    strategy.update_positions.return_value = sample_positions
    return strategy


@pytest.fixture
def mock_polymarket_client():
    """Mock Polymarket API client"""
    client = Mock()
    client.get_all_markets.return_value = [
        Mock(active=True, clob_token_ids='["100", "200"]', id='market1'),
        Mock(active=True, clob_token_ids='["300", "400"]', id='market2')
    ]
    client.credentials = Mock(
        api_key="test_key",
        api_secret="test_secret",
        api_passphrase="test_passphrase"
    )
    return client


@pytest.fixture
def large_market_dataset():
    """Generate large market dataset for performance testing"""
    np.random.seed(42)  # For reproducible results

    timestamps = pd.date_range('2024-01-01', '2024-12-31', freq='H')
    markets = [f'market{i}' for i in range(10)]
    outcomes = ['Yes', 'No']

    data = []
    for ts in timestamps:
        for market in markets:
            for outcome in outcomes:
                data.append({
                    'timestamp': ts,
                    'market_id': market,
                    'outcome_name': outcome,
                    'probability': np.clip(0.5 + 0.2 * np.random.normal(), 0.01, 0.99),
                    'volume': np.random.lognormal(6, 1),
                    'event_title': f'Event for {market}',
                    'scraped_at': ts + timedelta(minutes=np.random.uniform(0, 60))
                })

    return pd.DataFrame(data)


@pytest.fixture
def large_weather_dataset():
    """Generate large weather dataset for performance testing"""
    np.random.seed(42)

    timestamps = pd.date_range('2024-01-01', '2024-12-31', freq='H')
    locations = [f'City_{i}' for i in range(20)]

    data = []
    for ts in timestamps:
        for location in locations:
            lat, lon = 40 + np.random.normal(0, 5), -74 + np.random.normal(0, 5)

            data.append({
                'timestamp': ts,
                'location_name': location,
                'latitude': lat,
                'longitude': lon,
                'temperature': 15 + 10 * np.sin(2 * np.pi * ts.dayofyear / 365) + np.random.normal(0, 5),
                'temperature_min': 10 + 10 * np.sin(2 * np.pi * ts.dayofyear / 365) + np.random.normal(0, 3),
                'temperature_max': 20 + 10 * np.sin(2 * np.pi * ts.dayofyear / 365) + np.random.normal(0, 3),
                'humidity': np.clip(60 + 20 * np.random.normal(), 0, 100),
                'wind_speed': np.random.exponential(8),
                'precipitation': np.random.exponential(0.2),
                'pressure': 1013 + np.random.normal(0, 15),
                'weather_code': np.random.choice([800, 801, 802, 803, 500, 501, 300, 200]),
                'weather_description': 'Generated weather data',
                'source_name': 'synthetic'
            })

    return pd.DataFrame(data)


@pytest.fixture
def backtesting_scenarios():
    """Generate various backtesting scenarios"""
    scenarios = {
        'bull_market': {
            'trend': 'upward',
            'volatility': 'low',
            'description': 'Bull market with steady gains'
        },
        'bear_market': {
            'trend': 'downward',
            'volatility': 'medium',
            'description': 'Bear market with declining prices'
        },
        'volatile_market': {
            'trend': 'sideways',
            'volatility': 'high',
            'description': 'Highly volatile sideways market'
        },
        'crash_scenario': {
            'trend': 'crash',
            'volatility': 'extreme',
            'description': 'Market crash scenario'
        }
    }

    return scenarios


@pytest.fixture
def weather_scenarios():
    """Generate various weather scenarios for testing"""
    scenarios = {
        'normal_weather': {
            'temperature': 15.0,
            'humidity': 60.0,
            'precipitation': 0.0,
            'wind_speed': 5.0,
            'description': 'Normal weather conditions'
        },
        'extreme_heat': {
            'temperature': 35.0,
            'humidity': 80.0,
            'precipitation': 0.0,
            'wind_speed': 3.0,
            'description': 'Extreme heat wave'
        },
        'heavy_rain': {
            'temperature': 12.0,
            'humidity': 95.0,
            'precipitation': 10.0,
            'wind_speed': 15.0,
            'description': 'Heavy rainfall event'
        },
        'storm_conditions': {
            'temperature': 8.0,
            'humidity': 90.0,
            'precipitation': 25.0,
            'wind_speed': 25.0,
            'description': 'Storm conditions'
        }
    }

    return scenarios


@pytest.fixture
def api_response_mocks():
    """Mock API responses for various services"""
    mocks = {
        'polymarket_markets': {
            'status_code': 200,
            'json': lambda: [
                {
                    'id': 'market1',
                    'question': 'Will it rain tomorrow?',
                    'active': True,
                    'clobTokenIds': ['100', '200'],
                    'outcomes': ['Yes', 'No']
                }
            ]
        },
        'polymarket_prices': {
            'status_code': 200,
            'json': lambda: {
                '100': {'price': '0.6', 'size': '100'},
                '200': {'price': '0.4', 'size': '100'}
            }
        },
        'meteostat_weather': {
            'status_code': 200,
            'json': lambda: [
                {
                    'time': '2024-01-01T12:00:00Z',
                    'temperature': 15.5,
                    'humidity': 75.0,
                    'precipitation': 0.0
                }
            ]
        },
        'weather_gov_forecast': {
            'status_code': 200,
            'json': lambda: {
                'properties': {
                    'periods': [
                        {
                            'startTime': '2024-01-01T12:00:00Z',
                            'endTime': '2024-01-01T18:00:00Z',
                            'temperature': 15,
                            'probabilityOfPrecipitation': {'value': 20}
                        }
                    ]
                }
            }
        }
    }

    return mocks


@pytest.fixture
def error_scenarios():
    """Generate error scenarios for testing"""
    scenarios = {
        'network_timeout': {
            'exception': TimeoutError("Connection timed out"),
            'description': 'Network timeout error'
        },
        'api_rate_limit': {
            'exception': Exception("Rate limit exceeded"),
            'status_code': 429,
            'description': 'API rate limit exceeded'
        },
        'invalid_credentials': {
            'exception': Exception("Invalid API credentials"),
            'status_code': 401,
            'description': 'Invalid API credentials'
        },
        'data_not_found': {
            'exception': Exception("Data not found"),
            'status_code': 404,
            'description': 'Requested data not found'
        }
    }

    return scenarios


# Utility functions for data generation

def generate_market_data_points(
    start_date: datetime,
    end_date: datetime,
    markets: List[str] = None,
    frequency: str = 'H'
) -> pd.DataFrame:
    """Generate market data points for testing"""
    if markets is None:
        markets = ['market1', 'market2']

    timestamps = pd.date_range(start_date, end_date, freq=frequency)

    data = []
    for ts in timestamps:
        for market in markets:
            for outcome in ['Yes', 'No']:
                data.append({
                    'timestamp': ts,
                    'market_id': market,
                    'outcome_name': outcome,
                    'probability': np.clip(0.5 + 0.2 * np.random.normal(), 0.01, 0.99),
                    'volume': np.random.lognormal(6, 1),
                    'event_title': f'Event for {market}',
                    'scraped_at': ts + timedelta(minutes=np.random.uniform(0, 30))
                })

    return pd.DataFrame(data)


def generate_weather_data_points(
    start_date: datetime,
    end_date: datetime,
    locations: List[str] = None,
    frequency: str = 'H'
) -> pd.DataFrame:
    """Generate weather data points for testing"""
    if locations is None:
        locations = ['London', 'Paris', 'Berlin']

    timestamps = pd.date_range(start_date, end_date, freq=frequency)

    data = []
    for ts in timestamps:
        for location in locations:
            lat_lon = {
                'London': (51.5074, -0.1278),
                'Paris': (48.8566, 2.3522),
                'Berlin': (52.5200, 13.4050)
            }.get(location, (40.0, -74.0))

            data.append({
                'timestamp': ts,
                'location_name': location,
                'latitude': lat_lon[0],
                'longitude': lat_lon[1],
                'temperature': 15 + 10 * np.sin(2 * np.pi * ts.dayofyear / 365) + np.random.normal(0, 3),
                'humidity': np.clip(60 + 20 * np.random.normal(), 0, 100),
                'wind_speed': np.random.exponential(5),
                'precipitation': np.random.exponential(0.1),
                'pressure': 1013 + np.random.normal(0, 10),
                'weather_code': 800,
                'source_name': 'generated'
            })

    return pd.DataFrame(data)


def generate_backtest_result(
    strategy_name: str = "TestStrategy",
    total_return: float = 0.15,
    win_rate: float = 0.65
) -> BacktestResult:
    """Generate a sample backtest result"""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    return BacktestResult(
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        total_return=total_return,
        annualized_return=total_return * 12,  # Rough approximation
        volatility=0.25,
        sharpe_ratio=1.2,
        max_drawdown=0.1,
        win_rate=win_rate,
        total_trades=20,
        positions=[],
        signals=[],
        equity_curve=[],
        metrics={}
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark API tests
        if "api" in str(item.fspath) or "client" in str(item.fspath):
            item.add_marker(pytest.mark.api)

        # Mark performance tests
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)