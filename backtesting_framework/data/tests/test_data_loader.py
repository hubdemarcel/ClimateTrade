#!/usr/bin/env python3
"""
Unit Tests for Backtesting Data Loader

Comprehensive unit tests for the data loading functionality,
including market data loading, weather data loading, and data alignment.
"""

import pytest
import pandas as pd
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from ..data_loader import (
    BacktestingDataLoader,
    MarketData,
    WeatherData
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Create test tables and data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create polymarket_data table
    cursor.execute('''
        CREATE TABLE polymarket_data (
            timestamp TEXT,
            market_id TEXT,
            outcome_name TEXT,
            probability REAL,
            volume REAL,
            event_title TEXT,
            scraped_at TEXT
        )
    ''')

    # Create weather_data table
    cursor.execute('''
        CREATE TABLE weather_data (
            timestamp TEXT,
            location_name TEXT,
            latitude REAL,
            longitude REAL,
            temperature REAL,
            temperature_min REAL,
            temperature_max REAL,
            humidity REAL,
            wind_speed REAL,
            precipitation REAL,
            pressure REAL,
            weather_code INTEGER,
            weather_description TEXT,
            source_id INTEGER
        )
    ''')

    # Create weather_sources table
    cursor.execute('''
        CREATE TABLE weather_sources (
            id INTEGER PRIMARY KEY,
            source_name TEXT
        )
    ''')

    # Insert test data
    cursor.execute("INSERT INTO weather_sources (source_name) VALUES ('openweather')")

    # Insert market data
    market_data = [
        ('2024-01-01T10:00:00Z', 'market1', 'Yes', 0.6, 1000.0, 'Will it rain?', '2024-01-01T10:30:00Z'),
        ('2024-01-01T11:00:00Z', 'market1', 'No', 0.4, 800.0, 'Will it rain?', '2024-01-01T11:30:00Z'),
        ('2024-01-02T10:00:00Z', 'market2', 'Yes', 0.7, 1200.0, 'Will it snow?', '2024-01-02T10:30:00Z'),
    ]
    cursor.executemany("INSERT INTO polymarket_data VALUES (?, ?, ?, ?, ?, ?, ?)", market_data)

    # Insert weather data
    weather_data = [
        ('2024-01-01T10:00:00Z', 'London', 51.5074, -0.1278, 15.5, 12.0, 18.0, 75.0, 10.0, 0.0, 1013.0, 800, 'Clear sky', 1),
        ('2024-01-01T11:00:00Z', 'London', 51.5074, -0.1278, 16.0, 13.0, 19.0, 70.0, 12.0, 0.0, 1012.0, 801, 'Few clouds', 1),
        ('2024-01-02T10:00:00Z', 'Paris', 48.8566, 2.3522, 10.0, 8.0, 12.0, 85.0, 5.0, 2.0, 1015.0, 500, 'Light rain', 1),
    ]
    cursor.executemany("INSERT INTO weather_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", weather_data)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)


class TestBacktestingDataLoader:
    """Test cases for BacktestingDataLoader"""

    def test_initialization_valid_db(self, temp_db):
        """Test initialization with valid database"""
        loader = BacktestingDataLoader(temp_db)
        assert loader.db_path == temp_db

    def test_initialization_invalid_db(self):
        """Test initialization with invalid database path"""
        with pytest.raises(ConnectionError):
            BacktestingDataLoader("nonexistent.db")

    def test_initialization_missing_tables(self, tmp_path):
        """Test initialization with missing required tables"""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()

        with pytest.raises(ValueError, match="Missing required tables"):
            BacktestingDataLoader(str(db_path))

    def test_load_market_data_all(self, temp_db):
        """Test loading all market data"""
        loader = BacktestingDataLoader(temp_db)
        df = loader.load_market_data()

        assert len(df) == 3
        assert list(df.columns) == ['timestamp', 'market_id', 'outcome_name', 'probability', 'volume', 'event_title', 'scraped_at']
        assert df['market_id'].nunique() == 2
        assert df['probability'].min() >= 0.0
        assert df['probability'].max() <= 1.0

    def test_load_market_data_filtered_by_ids(self, temp_db):
        """Test loading market data filtered by market IDs"""
        loader = BacktestingDataLoader(temp_db)
        df = loader.load_market_data(market_ids=['market1'])

        assert len(df) == 2
        assert all(df['market_id'] == 'market1')

    def test_load_market_data_filtered_by_date_range(self, temp_db):
        """Test loading market data filtered by date range"""
        loader = BacktestingDataLoader(temp_db)
        start_date = datetime(2024, 1, 1, 10, 30)
        end_date = datetime(2024, 1, 1, 23, 59)

        df = loader.load_market_data(start_date=start_date, end_date=end_date)

        assert len(df) == 2  # Should exclude the 2024-01-02 data
        assert all(pd.to_datetime(df['timestamp']) >= start_date)
        assert all(pd.to_datetime(df['timestamp']) <= end_date)

    def test_load_weather_data_all(self, temp_db):
        """Test loading all weather data"""
        loader = BacktestingDataLoader(temp_db)
        df = loader.load_weather_data()

        assert len(df) == 3
        expected_columns = ['timestamp', 'location_name', 'latitude', 'longitude', 'temperature',
                          'temperature_min', 'temperature_max', 'humidity', 'wind_speed',
                          'precipitation', 'pressure', 'weather_code', 'weather_description', 'source_name']
        assert list(df.columns) == expected_columns
        assert df['location_name'].nunique() == 2

    def test_load_weather_data_filtered_by_locations(self, temp_db):
        """Test loading weather data filtered by locations"""
        loader = BacktestingDataLoader(temp_db)
        df = loader.load_weather_data(locations=['London'])

        assert len(df) == 2
        assert all(df['location_name'] == 'London')

    def test_load_weather_data_filtered_by_sources(self, temp_db):
        """Test loading weather data filtered by sources"""
        loader = BacktestingDataLoader(temp_db)
        df = loader.load_weather_data(sources=['openweather'])

        assert len(df) == 3
        assert all(df['source_name'] == 'openweather')

    def test_load_weather_data_filtered_by_date_range(self, temp_db):
        """Test loading weather data filtered by date range"""
        loader = BacktestingDataLoader(temp_db)
        start_date = datetime(2024, 1, 1, 10, 30)
        end_date = datetime(2024, 1, 1, 23, 59)

        df = loader.load_weather_data(start_date=start_date, end_date=end_date)

        assert len(df) == 2
        assert all(pd.to_datetime(df['timestamp']) >= start_date)
        assert all(pd.to_datetime(df['timestamp']) <= end_date)

    def test_get_market_outcomes(self, temp_db):
        """Test getting market outcomes"""
        loader = BacktestingDataLoader(temp_db)
        outcomes = loader.get_market_outcomes('market1')

        assert len(outcomes) == 2
        assert 'Yes' in outcomes
        assert 'No' in outcomes

    def test_get_available_markets(self, temp_db):
        """Test getting available markets metadata"""
        loader = BacktestingDataLoader(temp_db)
        markets = loader.get_available_markets()

        assert len(markets) == 2
        market_ids = [m['market_id'] for m in markets]
        assert 'market1' in market_ids
        assert 'market2' in market_ids

        for market in markets:
            assert 'market_id' in market
            assert 'event_title' in market
            assert 'data_points' in market
            assert 'start_date' in market
            assert 'end_date' in market
            assert 'avg_volume' in market

    def test_get_available_locations(self, temp_db):
        """Test getting available locations metadata"""
        loader = BacktestingDataLoader(temp_db)
        locations = loader.get_available_locations()

        assert len(locations) == 2
        location_names = [l['location_name'] for l in locations]
        assert 'London' in location_names
        assert 'Paris' in location_names

        for location in locations:
            assert 'location_name' in location
            assert 'source_name' in location
            assert 'data_points' in location
            assert 'start_date' in location
            assert 'end_date' in location
            assert 'avg_temperature' in location

    def test_align_data_timeline_hourly(self, temp_db):
        """Test data alignment to hourly frequency"""
        loader = BacktestingDataLoader(temp_db)

        # Create test data with different timestamps
        market_df = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 10, 30), datetime(2024, 1, 1, 11)],
            'market_id': ['m1', 'm1', 'm1'],
            'probability': [0.5, 0.6, 0.7],
            'volume': [100, 200, 300],
            'outcome_name': ['Yes', 'Yes', 'Yes'],
            'event_title': ['Test', 'Test', 'Test']
        })

        weather_df = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 11)],
            'location_name': ['London', 'London'],
            'temperature': [15.0, 16.0],
            'humidity': [70.0, 75.0],
            'wind_speed': [10.0, 12.0],
            'pressure': [1013.0, 1012.0],
            'source_name': ['test', 'test']
        })

        aligned_market, aligned_weather = loader.align_data_timeline(market_df, weather_df, 'H')

        assert len(aligned_market) == 2  # Two hourly periods
        assert len(aligned_weather) == 2
        assert aligned_market.index.name == 'timestamp'
        assert aligned_weather.index.name == 'timestamp'

    def test_align_data_timeline_daily(self, temp_db):
        """Test data alignment to daily frequency"""
        loader = BacktestingDataLoader(temp_db)

        market_df = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 2, 10)],
            'market_id': ['m1', 'm1'],
            'probability': [0.5, 0.6],
            'volume': [100, 200],
            'outcome_name': ['Yes', 'Yes'],
            'event_title': ['Test', 'Test']
        })

        weather_df = pd.DataFrame({
            'timestamp': [datetime(2024, 1, 1, 10), datetime(2024, 1, 2, 10)],
            'location_name': ['London', 'London'],
            'temperature': [15.0, 16.0],
            'humidity': [70.0, 75.0],
            'wind_speed': [10.0, 12.0],
            'pressure': [1013.0, 1012.0],
            'source_name': ['test', 'test']
        })

        aligned_market, aligned_weather = loader.align_data_timeline(market_df, weather_df, 'D')

        assert len(aligned_market) == 2  # Two daily periods
        assert len(aligned_weather) == 2


class TestDataClasses:
    """Test cases for data classes"""

    def test_market_data_creation(self):
        """Test MarketData dataclass creation"""
        timestamp = datetime(2024, 1, 1, 10, 0)
        market_data = MarketData(
            timestamp=timestamp,
            market_id='market1',
            outcome_name='Yes',
            probability=0.6,
            volume=1000.0,
            event_title='Test Event'
        )

        assert market_data.timestamp == timestamp
        assert market_data.market_id == 'market1'
        assert market_data.outcome_name == 'Yes'
        assert market_data.probability == 0.6
        assert market_data.volume == 1000.0
        assert market_data.event_title == 'Test Event'

    def test_weather_data_creation(self):
        """Test WeatherData dataclass creation"""
        timestamp = datetime(2024, 1, 1, 10, 0)
        weather_data = WeatherData(
            timestamp=timestamp,
            location_name='London',
            temperature=15.5,
            temperature_min=12.0,
            temperature_max=18.0,
            humidity=75.0,
            wind_speed=10.0,
            precipitation=0.0,
            pressure=1013.0,
            weather_code=800
        )

        assert weather_data.timestamp == timestamp
        assert weather_data.location_name == 'London'
        assert weather_data.temperature == 15.5
        assert weather_data.humidity == 75.0
        assert weather_data.weather_code == 800


if __name__ == '__main__':
    pytest.main([__file__])