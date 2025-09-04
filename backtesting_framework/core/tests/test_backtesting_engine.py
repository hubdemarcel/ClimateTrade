#!/usr/bin/env python3
"""
Unit Tests for Backtesting Engine Core

Comprehensive unit tests for the backtesting engine functionality,
including data loading, strategy execution, position management, and results calculation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List

from ..backtesting_engine import (
    BacktestingEngine,
    BacktestConfig,
    BacktestResult,
    BacktestingDataLoader,
    BaseWeatherStrategy,
    TradingSignal,
    Position,
    PerformanceMetrics,
    RiskMetrics
)


@pytest.fixture
def sample_config():
    """Sample backtest configuration"""
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
    """Sample market data for testing"""
    timestamps = pd.date_range('2024-01-01', '2024-01-02', freq='H')
    data = []
    for ts in timestamps:
        data.extend([
            {
                'timestamp': ts,
                'market_id': 'market1',
                'outcome_name': 'Yes',
                'probability': 0.6,
                'volume': 1000.0,
                'event_title': 'Will it rain tomorrow?'
            },
            {
                'timestamp': ts,
                'market_id': 'market1',
                'outcome_name': 'No',
                'probability': 0.4,
                'volume': 800.0,
                'event_title': 'Will it rain tomorrow?'
            }
        ])
    return pd.DataFrame(data)


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    timestamps = pd.date_range('2024-01-01', '2024-01-02', freq='H')
    data = []
    for ts in timestamps:
        data.append({
            'timestamp': ts,
            'location_name': 'London',
            'temperature': 15.5,
            'humidity': 75.0,
            'wind_speed': 10.0,
            'pressure': 1013.0
        })
    return pd.DataFrame(data)


@pytest.fixture
def mock_data_loader(sample_market_data, sample_weather_data):
    """Mock data loader"""
    loader = Mock(spec=BacktestingDataLoader)
    loader.load_market_data.return_value = sample_market_data
    loader.load_weather_data.return_value = sample_weather_data
    loader.align_data_timeline.return_value = (sample_market_data, sample_weather_data)
    return loader


@pytest.fixture
def mock_strategy():
    """Mock trading strategy"""
    strategy = Mock(spec=BaseWeatherStrategy)
    strategy.name = "TestStrategy"
    strategy.generate_signals.return_value = [
        TradingSignal(
            timestamp=datetime(2024, 1, 1, 12, 0),
            market_id='market1',
            outcome_name='Yes',
            signal_type='BUY',
            confidence=0.8,
            quantity=1.0
        )
    ]
    strategy.update_positions.return_value = [
        Position(
            market_id='market1',
            outcome_name='Yes',
            quantity=1.0,
            entry_price=0.6,
            entry_time=datetime(2024, 1, 1, 12, 0),
            status='OPEN'
        )
    ]
    return strategy


@pytest.fixture
def mock_performance_metrics():
    """Mock performance metrics"""
    return Mock(spec=PerformanceMetrics)


@pytest.fixture
def mock_risk_metrics():
    """Mock risk metrics"""
    return Mock(spec=RiskMetrics)


class TestBacktestingEngine:
    """Test cases for BacktestingEngine"""

    def test_initialization(self, sample_config, mock_data_loader, mock_performance_metrics, mock_risk_metrics):
        """Test engine initialization"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics', return_value=mock_performance_metrics), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics', return_value=mock_risk_metrics):

            engine = BacktestingEngine(sample_config)

            assert engine.config == sample_config
            assert engine.data_loader == mock_data_loader
            assert engine.performance_metrics == mock_performance_metrics
            assert engine.risk_metrics == mock_risk_metrics

    def test_run_backtest_success(self, sample_config, mock_data_loader, mock_strategy):
        """Test successful backtest execution"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)

            result = engine.run_backtest(mock_strategy)

            assert isinstance(result, BacktestResult)
            assert result.strategy_name == "TestStrategy"
            assert result.start_date == sample_config.start_date
            assert result.end_date == sample_config.end_date
            assert result.total_return >= 0
            assert result.total_trades >= 0
            assert len(result.positions) >= 0
            assert len(result.signals) >= 0

    def test_run_backtest_insufficient_data(self, sample_config):
        """Test backtest with insufficient data"""
        mock_loader = Mock(spec=BacktestingDataLoader)
        mock_loader.load_market_data.return_value = pd.DataFrame()
        mock_loader.load_weather_data.return_value = pd.DataFrame()

        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)
            strategy = Mock(spec=BaseWeatherStrategy)
            strategy.name = "TestStrategy"

            with pytest.raises(ValueError, match="Insufficient data"):
                engine.run_backtest(strategy)

    def test_run_multiple_strategies_sequential(self, sample_config, mock_data_loader, mock_strategy):
        """Test running multiple strategies sequentially"""
        strategies = [mock_strategy, mock_strategy]

        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)
            results = engine.run_multiple_strategies(strategies)

            assert len(results) == 2
            assert all(isinstance(r, BacktestResult) for r in results)

    def test_run_multiple_strategies_parallel(self, sample_config, mock_data_loader, mock_strategy):
        """Test running multiple strategies in parallel"""
        config = BacktestConfig(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            enable_parallel=True
        )
        strategies = [mock_strategy, mock_strategy]

        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(config)
            results = engine.run_multiple_strategies(strategies)

            assert len(results) == 2
            assert all(isinstance(r, BacktestResult) for r in results)

    def test_create_simulation_timeline(self, sample_config, mock_data_loader):
        """Test simulation timeline creation"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)

            market_data = pd.DataFrame({
                'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 11)]
            })
            weather_data = pd.DataFrame({
                'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 12)]
            })

            timeline = engine._create_simulation_timeline(market_data, weather_data)

            assert len(timeline) == 3  # 10, 11, 12
            assert timeline[0] == datetime(2024, 1, 1, 10)
            assert timeline[1] == datetime(2024, 1, 1, 11)
            assert timeline[2] == datetime(2024, 1, 1, 12)

    def test_calculate_results(self, sample_config, mock_data_loader, mock_strategy):
        """Test results calculation"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)

            positions = [
                Position(
                    market_id='market1',
                    outcome_name='Yes',
                    quantity=1.0,
                    entry_price=0.5,
                    entry_time=datetime(2024, 1, 1),
                    exit_price=0.6,
                    exit_time=datetime(2024, 1, 15),
                    pnl=0.1,
                    status='CLOSED'
                )
            ]
            signals = [
                TradingSignal(
                    timestamp=datetime(2024, 1, 1),
                    market_id='market1',
                    outcome_name='Yes',
                    signal_type='BUY',
                    confidence=0.8
                )
            ]
            equity_curve = [
                (datetime(2024, 1, 1), 10000.0),
                (datetime(2024, 1, 15), 10010.0)
            ]

            result = engine._calculate_results(mock_strategy, positions, signals, equity_curve)

            assert isinstance(result, BacktestResult)
            assert result.total_return == 0.001  # 10/10000
            assert result.total_trades == 1
            assert result.win_rate == 1.0
            assert len(result.positions) == 1
            assert len(result.signals) == 1

    def test_calculate_sortino_ratio(self, sample_config, mock_data_loader):
        """Test Sortino ratio calculation"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)

            # Test with positive returns
            returns = pd.Series([0.01, 0.02, -0.01, 0.015])
            sortino = engine._calculate_sortino_ratio(returns, 0.02)
            assert isinstance(sortino, float)

            # Test with no downside returns
            returns_no_downside = pd.Series([0.01, 0.02, 0.015])
            sortino_inf = engine._calculate_sortino_ratio(returns_no_downside, 0.02)
            assert sortino_inf == float('inf')

    def test_validate_backtest_data(self, sample_config, mock_data_loader, sample_market_data, sample_weather_data):
        """Test data validation"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)

            validation = engine.validate_backtest_data(sample_market_data, sample_weather_data)

            assert 'market_data_points' in validation
            assert 'weather_data_points' in validation
            assert 'data_quality_score' in validation
            assert validation['data_quality_score'] >= 0.0
            assert validation['data_quality_score'] <= 1.0

    def test_check_data_gaps(self, sample_config, mock_data_loader):
        """Test data gap detection"""
        with patch('backtesting_framework.core.backtesting_engine.BacktestingDataLoader', return_value=mock_data_loader), \
             patch('backtesting_framework.core.backtesting_engine.PerformanceMetrics'), \
             patch('backtesting_framework.core.backtesting_engine.RiskMetrics'):

            engine = BacktestingEngine(sample_config)

            # Test with gaps
            df = pd.DataFrame({
                'timestamp': [
                    datetime(2024, 1, 1, 10),
                    datetime(2024, 1, 1, 11),
                    datetime(2024, 1, 1, 14)  # 3-hour gap
                ],
                'value': [1, 2, 3]
            })

            gaps = engine._check_data_gaps(df, 'timestamp')
            assert len(gaps) == 1
            assert gaps[0][0] == datetime(2024, 1, 1, 11)
            assert gaps[0][1] == datetime(2024, 1, 1, 14)

            # Test with no gaps
            df_no_gaps = pd.DataFrame({
                'timestamp': [
                    datetime(2024, 1, 1, 10),
                    datetime(2024, 1, 1, 11),
                    datetime(2024, 1, 1, 12)
                ],
                'value': [1, 2, 3]
            })

            gaps_none = engine._check_data_gaps(df_no_gaps, 'timestamp')
            assert len(gaps_none) == 0


class TestBacktestConfig:
    """Test cases for BacktestConfig"""

    def test_config_initialization(self):
        """Test configuration initialization with defaults"""
        config = BacktestConfig(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )

        assert config.start_date == datetime(2024, 1, 1)
        assert config.end_date == datetime(2024, 1, 31)
        assert config.initial_capital == 10000.0
        assert config.commission_per_trade == 0.001
        assert config.max_position_size == 0.1
        assert config.max_positions == 10
        assert config.data_frequency == 'H'
        assert config.enable_parallel == False
        assert config.risk_free_rate == 0.02


class TestBacktestResult:
    """Test cases for BacktestResult"""

    def test_result_initialization(self):
        """Test result initialization"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        result = BacktestResult(
            strategy_name="TestStrategy",
            start_date=start_date,
            end_date=end_date,
            total_return=0.15,
            annualized_return=0.18,
            volatility=0.25,
            sharpe_ratio=1.2,
            max_drawdown=0.1,
            win_rate=0.65,
            total_trades=20
        )

        assert result.strategy_name == "TestStrategy"
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert result.total_return == 0.15
        assert result.annualized_return == 0.18
        assert result.volatility == 0.25
        assert result.sharpe_ratio == 1.2
        assert result.max_drawdown == 0.1
        assert result.win_rate == 0.65
        assert result.total_trades == 20
        assert result.positions == []
        assert result.signals == []
        assert result.equity_curve == []
        assert result.metrics == {}


if __name__ == '__main__':
    pytest.main([__file__])