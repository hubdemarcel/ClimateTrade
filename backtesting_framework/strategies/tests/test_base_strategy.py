#!/usr/bin/env python3
"""
Unit Tests for Base Strategy Framework

Comprehensive unit tests for the base strategy classes,
including signal generation, position management, and strategy metrics.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ..base_strategy import (
    BaseWeatherStrategy,
    WeatherThresholdStrategy,
    TradingSignal,
    Position
)


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return pd.DataFrame({
        'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 11)],
        'market_id': ['market1', 'market1'],
        'outcome_name': ['Yes', 'No'],
        'probability': [0.6, 0.4],
        'volume': [1000.0, 800.0],
        'event_title': ['Will it rain?', 'Will it rain?']
    })


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return pd.DataFrame({
        'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 11)],
        'location_name': ['London', 'London'],
        'temperature': [25.5, 26.0],  # Above threshold
        'humidity': [85.0, 90.0],     # Above threshold
        'wind_speed': [10.0, 12.0],
        'pressure': [1013.0, 1012.0]
    })


@pytest.fixture
def sample_positions():
    """Sample positions for testing"""
    return [
        Position(
            market_id='market1',
            outcome_name='Yes',
            quantity=1.0,
            entry_price=0.5,
            entry_time=datetime(2024, 1, 1, 9),
            current_price=0.6,
            status='OPEN'
        ),
        Position(
            market_id='market1',
            outcome_name='No',
            quantity=1.0,
            entry_price=0.4,
            entry_time=datetime(2024, 1, 1, 9),
            exit_price=0.3,
            exit_time=datetime(2024, 1, 1, 10),
            pnl=-0.1,
            status='CLOSED'
        )
    ]


class TestTradingSignal:
    """Test cases for TradingSignal dataclass"""

    def test_signal_creation(self):
        """Test signal creation with all parameters"""
        timestamp = datetime(2024, 1, 1, 10, 0)
        signal = TradingSignal(
            timestamp=timestamp,
            market_id='market1',
            outcome_name='Yes',
            signal_type='BUY',
            confidence=0.8,
            quantity=1.0,
            price=0.6,
            reasoning='Test signal'
        )

        assert signal.timestamp == timestamp
        assert signal.market_id == 'market1'
        assert signal.outcome_name == 'Yes'
        assert signal.signal_type == 'BUY'
        assert signal.confidence == 0.8
        assert signal.quantity == 1.0
        assert signal.price == 0.6
        assert signal.reasoning == 'Test signal'

    def test_signal_creation_minimal(self):
        """Test signal creation with minimal parameters"""
        timestamp = datetime(2024, 1, 1, 10, 0)
        signal = TradingSignal(
            timestamp=timestamp,
            market_id='market1',
            outcome_name='Yes',
            signal_type='BUY',
            confidence=0.8
        )

        assert signal.timestamp == timestamp
        assert signal.market_id == 'market1'
        assert signal.outcome_name == 'Yes'
        assert signal.signal_type == 'BUY'
        assert signal.confidence == 0.8
        assert signal.quantity is None
        assert signal.price is None
        assert signal.reasoning is None


class TestPosition:
    """Test cases for Position dataclass"""

    def test_position_creation(self):
        """Test position creation with all parameters"""
        entry_time = datetime(2024, 1, 1, 10, 0)
        exit_time = datetime(2024, 1, 1, 11, 0)

        position = Position(
            market_id='market1',
            outcome_name='Yes',
            quantity=1.0,
            entry_price=0.5,
            entry_time=entry_time,
            current_price=0.6,
            exit_price=0.6,
            exit_time=exit_time,
            pnl=0.1,
            status='CLOSED'
        )

        assert position.market_id == 'market1'
        assert position.outcome_name == 'Yes'
        assert position.quantity == 1.0
        assert position.entry_price == 0.5
        assert position.entry_time == entry_time
        assert position.current_price == 0.6
        assert position.exit_price == 0.6
        assert position.exit_time == exit_time
        assert position.pnl == 0.1
        assert position.status == 'CLOSED'

    def test_position_creation_minimal(self):
        """Test position creation with minimal parameters"""
        entry_time = datetime(2024, 1, 1, 10, 0)

        position = Position(
            market_id='market1',
            outcome_name='Yes',
            quantity=1.0,
            entry_price=0.5,
            entry_time=entry_time
        )

        assert position.market_id == 'market1'
        assert position.outcome_name == 'Yes'
        assert position.quantity == 1.0
        assert position.entry_price == 0.5
        assert position.entry_time == entry_time
        assert position.current_price is None
        assert position.exit_price is None
        assert position.exit_time is None
        assert position.pnl == 0.0
        assert position.status == 'OPEN'


class TestBaseWeatherStrategy:
    """Test cases for BaseWeatherStrategy"""

    def test_strategy_initialization(self):
        """Test strategy initialization"""
        strategy = BaseWeatherStrategy("TestStrategy", {"param1": "value1"})

        assert strategy.name == "TestStrategy"
        assert strategy.parameters == {"param1": "value1"}
        assert strategy.positions == []
        assert strategy.signals_history == []

    def test_generate_signals_abstract(self):
        """Test that generate_signals raises NotImplementedError"""
        strategy = BaseWeatherStrategy("TestStrategy")

        with pytest.raises(NotImplementedError):
            strategy.generate_signals(pd.DataFrame(), pd.DataFrame(), [])

    def test_update_positions_buy_signal(self, sample_market_data):
        """Test position update with BUY signal"""
        strategy = BaseWeatherStrategy("TestStrategy")

        signal = TradingSignal(
            timestamp=datetime(2024, 1, 1, 10),
            market_id='market1',
            outcome_name='Yes',
            signal_type='BUY',
            confidence=0.8,
            quantity=1.0
        )

        positions = strategy.update_positions([signal], sample_market_data)

        assert len(positions) == 1
        assert positions[0].market_id == 'market1'
        assert positions[0].outcome_name == 'Yes'
        assert positions[0].quantity == 1.0
        assert positions[0].entry_price == 0.6  # From market data
        assert positions[0].status == 'OPEN'
        assert len(strategy.signals_history) == 1

    def test_update_positions_sell_signal(self, sample_market_data):
        """Test position update with SELL signal"""
        strategy = BaseWeatherStrategy("TestStrategy")

        # First create a position
        buy_signal = TradingSignal(
            timestamp=datetime(2024, 1, 1, 9),
            market_id='market1',
            outcome_name='Yes',
            signal_type='BUY',
            confidence=0.8,
            quantity=1.0
        )
        strategy.update_positions([buy_signal], sample_market_data)

        # Now sell
        sell_signal = TradingSignal(
            timestamp=datetime(2024, 1, 1, 10),
            market_id='market1',
            outcome_name='Yes',
            signal_type='SELL',
            confidence=0.8
        )
        positions = strategy.update_positions([sell_signal], sample_market_data)

        assert len(positions) == 1
        assert positions[0].status == 'CLOSED'
        assert positions[0].exit_price == 0.6
        assert positions[0].pnl == 0.0  # Same entry and exit price

    def test_get_open_positions(self, sample_positions):
        """Test getting open positions"""
        strategy = BaseWeatherStrategy("TestStrategy")
        strategy.positions = sample_positions

        open_positions = strategy.get_open_positions()
        assert len(open_positions) == 1
        assert open_positions[0].status == 'OPEN'

    def test_get_closed_positions(self, sample_positions):
        """Test getting closed positions"""
        strategy = BaseWeatherStrategy("TestStrategy")
        strategy.positions = sample_positions

        closed_positions = strategy.get_closed_positions()
        assert len(closed_positions) == 1
        assert closed_positions[0].status == 'CLOSED'

    def test_get_total_pnl(self, sample_positions):
        """Test calculating total P&L"""
        strategy = BaseWeatherStrategy("TestStrategy")
        strategy.positions = sample_positions

        total_pnl = strategy.get_total_pnl()
        assert total_pnl == -0.1  # Only the closed position

    def test_get_strategy_metrics_no_trades(self):
        """Test strategy metrics with no trades"""
        strategy = BaseWeatherStrategy("TestStrategy")

        metrics = strategy.get_strategy_metrics()
        assert metrics['total_pnl'] == 0.0
        assert metrics['total_trades'] == 0
        assert metrics['win_rate'] == 0.0
        assert metrics['open_positions'] == 0

    def test_get_strategy_metrics_with_trades(self, sample_positions):
        """Test strategy metrics with trades"""
        strategy = BaseWeatherStrategy("TestStrategy")
        strategy.positions = sample_positions

        metrics = strategy.get_strategy_metrics()
        assert metrics['total_pnl'] == -0.1
        assert metrics['total_trades'] == 1
        assert metrics['win_rate'] == 0.0  # Losing trade
        assert metrics['avg_loss'] == -0.1
        assert metrics['open_positions'] == 1


class TestWeatherThresholdStrategy:
    """Test cases for WeatherThresholdStrategy"""

    def test_strategy_initialization(self):
        """Test WeatherThresholdStrategy initialization"""
        strategy = WeatherThresholdStrategy(
            name="ThresholdStrategy",
            parameters={
                "temperature_threshold": 30.0,
                "humidity_threshold": 90.0,
                "signal_strength_threshold": 0.8
            }
        )

        assert strategy.name == "ThresholdStrategy"
        assert strategy.temperature_threshold == 30.0
        assert strategy.humidity_threshold == 90.0
        assert strategy.signal_strength_threshold == 0.8

    def test_strategy_initialization_defaults(self):
        """Test WeatherThresholdStrategy initialization with defaults"""
        strategy = WeatherThresholdStrategy()

        assert strategy.name == "WeatherThresholdStrategy"
        assert strategy.temperature_threshold == 25.0
        assert strategy.humidity_threshold == 80.0
        assert strategy.signal_strength_threshold == 0.7

    def test_generate_signals_temperature_threshold(self, sample_market_data, sample_weather_data):
        """Test signal generation based on temperature threshold"""
        strategy = WeatherThresholdStrategy(temperature_threshold=20.0)  # Below current temp

        signals = strategy.generate_signals(sample_market_data, sample_weather_data, [])

        assert len(signals) == 2  # One for each weather data point
        for signal in signals:
            assert signal.signal_type == 'BUY'
            assert signal.market_id == 'market1'
            assert signal.outcome_name == 'Yes'
            assert signal.confidence > 0.5  # High confidence due to temp difference

    def test_generate_signals_humidity_threshold(self, sample_market_data, sample_weather_data):
        """Test signal generation based on humidity threshold"""
        strategy = WeatherThresholdStrategy(humidity_threshold=70.0)  # Below current humidity

        signals = strategy.generate_signals(sample_market_data, sample_weather_data, [])

        assert len(signals) == 2
        for signal in signals:
            assert signal.signal_type == 'BUY'
            assert 'humidity' in signal.reasoning.lower()

    def test_generate_signals_below_threshold(self, sample_market_data):
        """Test signal generation when conditions are below thresholds"""
        strategy = WeatherThresholdStrategy(
            temperature_threshold=30.0,  # Above current temp
            humidity_threshold=95.0     # Above current humidity
        )

        weather_data = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 10)],
            'location_name': ['London'],
            'temperature': [20.0],  # Below threshold
            'humidity': [70.0]      # Below threshold
        })

        signals = strategy.generate_signals(sample_market_data, weather_data, [])

        assert len(signals) == 0  # No signals should be generated

    def test_generate_signals_low_confidence(self, sample_market_data):
        """Test signal generation with low confidence"""
        strategy = WeatherThresholdStrategy(
            temperature_threshold=25.0,  # Just below current temp
            signal_strength_threshold=0.9  # High threshold
        )

        weather_data = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 10)],
            'location_name': ['London'],
            'temperature': [25.1],  # Just above threshold
            'humidity': [75.0]
        })

        signals = strategy.generate_signals(sample_market_data, weather_data, [])

        assert len(signals) == 0  # Confidence too low

    def test_create_temperature_signal(self, sample_market_data):
        """Test temperature signal creation"""
        strategy = WeatherThresholdStrategy(temperature_threshold=20.0)

        weather_row = pd.Series({
            'timestamp': datetime(2024, 1, 1, 10),
            'location_name': 'London',
            'temperature': 25.5
        })

        signal = strategy._create_temperature_signal(weather_row, sample_market_data, 'HIGH_TEMP')

        assert signal is not None
        assert signal.signal_type == 'BUY'
        assert signal.confidence > 0.5
        assert 'Temperature' in signal.reasoning

    def test_create_humidity_signal(self, sample_market_data):
        """Test humidity signal creation"""
        strategy = WeatherThresholdStrategy(humidity_threshold=70.0)

        weather_row = pd.Series({
            'timestamp': datetime(2024, 1, 1, 10),
            'location_name': 'London',
            'humidity': 85.0
        })

        signal = strategy._create_humidity_signal(weather_row, sample_market_data, 'HIGH_HUMIDITY')

        assert signal is not None
        assert signal.signal_type == 'BUY'
        assert signal.confidence > 0.5
        assert 'Humidity' in signal.reasoning

    def test_signal_creation_no_market_data(self):
        """Test signal creation with no relevant market data"""
        strategy = WeatherThresholdStrategy()

        weather_row = pd.Series({
            'timestamp': datetime(2024, 1, 1, 10),
            'location_name': 'London',
            'temperature': 30.0
        })

        # Empty market data
        market_data = pd.DataFrame()

        signal = strategy._create_temperature_signal(weather_row, market_data, 'HIGH_TEMP')
        assert signal is None


if __name__ == '__main__':
    pytest.main([__file__])