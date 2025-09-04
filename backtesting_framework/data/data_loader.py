#!/usr/bin/env python3
"""
Data Loader for Backtesting Framework

Handles loading and preprocessing of historical weather and market data
from the ClimateTrade database for backtesting purposes.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Container for market data"""
    timestamp: datetime
    market_id: str
    outcome_name: str
    probability: float
    volume: float
    event_title: str


@dataclass
class WeatherData:
    """Container for weather data"""
    timestamp: datetime
    location_name: str
    temperature: Optional[float]
    temperature_min: Optional[float]
    temperature_max: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    precipitation: Optional[float]
    pressure: Optional[float]
    weather_code: Optional[int]


class BacktestingDataLoader:
    """Loads and preprocesses data for backtesting"""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self._validate_db_connection()

    def _validate_db_connection(self):
        """Validate database connection"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                required_tables = ['polymarket_data', 'weather_data']
                missing_tables = [t for t in required_tables if t not in tables]
                if missing_tables:
                    raise ValueError(f"Missing required tables: {missing_tables}")
        except sqlite3.Error as e:
            raise ConnectionError(f"Database connection failed: {e}")

    def load_market_data(self,
                        market_ids: Optional[List[str]] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load market data for backtesting

        Args:
            market_ids: List of market IDs to load (None for all)
            start_date: Start date for data range
            end_date: End date for data range

        Returns:
            DataFrame with market data
        """
        query = """
        SELECT
            timestamp,
            market_id,
            outcome_name,
            probability,
            volume,
            event_title,
            scraped_at
        FROM polymarket_data
        WHERE 1=1
        """

        params = []

        if market_ids:
            placeholders = ','.join('?' * len(market_ids))
            query += f" AND market_id IN ({placeholders})"
            params.extend(market_ids)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp ASC"

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['scraped_at'] = pd.to_datetime(df['scraped_at'])

        # Handle missing values
        df['probability'] = df['probability'].fillna(0.5)  # Default to 50%
        df['volume'] = df['volume'].fillna(0.0)

        logger.info(f"Loaded {len(df)} market data records")
        return df

    def load_weather_data(self,
                         locations: Optional[List[str]] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         sources: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load weather data for backtesting

        Args:
            locations: List of location names to load (None for all)
            start_date: Start date for data range
            end_date: End date for data range
            sources: List of weather sources to include

        Returns:
            DataFrame with weather data
        """
        query = """
        SELECT
            w.timestamp,
            w.location_name,
            w.latitude,
            w.longitude,
            w.temperature,
            w.temperature_min,
            w.temperature_max,
            w.humidity,
            w.wind_speed,
            w.precipitation,
            w.pressure,
            w.weather_code,
            w.weather_description,
            s.source_name
        FROM weather_data w
        JOIN weather_sources s ON w.source_id = s.id
        WHERE 1=1
        """

        params = []

        if locations:
            placeholders = ','.join('?' * len(locations))
            query += f" AND w.location_name IN ({placeholders})"
            params.extend(locations)

        if sources:
            placeholders = ','.join('?' * len(sources))
            query += f" AND s.source_name IN ({placeholders})"
            params.extend(sources)

        if start_date:
            query += " AND w.timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND w.timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY w.timestamp ASC"

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Fill missing numeric values with forward/backward fill
        numeric_cols = ['temperature', 'temperature_min', 'temperature_max',
                       'humidity', 'wind_speed', 'precipitation', 'pressure']
        df[numeric_cols] = df[numeric_cols].fillna(method='ffill').fillna(method='bfill')

        logger.info(f"Loaded {len(df)} weather data records")
        return df

    def get_market_outcomes(self, market_id: str) -> List[str]:
        """Get all outcome names for a specific market"""
        query = "SELECT DISTINCT outcome_name FROM polymarket_data WHERE market_id = ?"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (market_id,))
            outcomes = [row[0] for row in cursor.fetchall()]

        return outcomes

    def get_available_markets(self) -> List[Dict[str, Any]]:
        """Get list of available markets with metadata"""
        query = """
        SELECT
            market_id,
            event_title,
            COUNT(*) as data_points,
            MIN(timestamp) as start_date,
            MAX(timestamp) as end_date,
            AVG(volume) as avg_volume
        FROM polymarket_data
        GROUP BY market_id, event_title
        ORDER BY data_points DESC
        """

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)

        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])

        return df.to_dict('records')

    def get_available_locations(self) -> List[Dict[str, Any]]:
        """Get list of available weather locations with metadata"""
        query = """
        SELECT
            location_name,
            source_name,
            COUNT(*) as data_points,
            MIN(timestamp) as start_date,
            MAX(timestamp) as end_date,
            AVG(temperature) as avg_temperature
        FROM weather_data w
        JOIN weather_sources s ON w.source_id = s.id
        GROUP BY location_name, source_name
        ORDER BY data_points DESC
        """

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)

        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])

        return df.to_dict('records')

    def align_data_timeline(self,
                           market_df: pd.DataFrame,
                           weather_df: pd.DataFrame,
                           freq: str = 'H') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Align market and weather data to the same time frequency

        Args:
            market_df: Market data DataFrame
            weather_df: Weather data DataFrame
            freq: Frequency for alignment ('H' for hourly, 'D' for daily)

        Returns:
            Tuple of aligned (market_df, weather_df)
        """
        # Set timestamp as index
        market_df = market_df.set_index('timestamp')
        weather_df = weather_df.set_index('timestamp')

        # Resample to desired frequency
        market_resampled = market_df.groupby('market_id').resample(freq).agg({
            'probability': 'mean',
            'volume': 'sum',
            'outcome_name': 'first',
            'event_title': 'first'
        }).dropna()

        weather_resampled = weather_df.groupby('location_name').resample(freq).agg({
            'temperature': 'mean',
            'temperature_min': 'min',
            'temperature_max': 'max',
            'humidity': 'mean',
            'wind_speed': 'mean',
            'precipitation': 'sum',
            'pressure': 'mean',
            'weather_code': 'first',
            'source_name': 'first'
        }).dropna()

        # Reset index
        market_resampled = market_resampled.reset_index()
        weather_resampled = weather_resampled.reset_index()

        logger.info(f"Aligned data to {freq} frequency: {len(market_resampled)} market, {len(weather_resampled)} weather records")

        return market_resampled, weather_resampled