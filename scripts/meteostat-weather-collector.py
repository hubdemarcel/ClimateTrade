#!/usr/bin/env python3
"""
Meteostat Weather Data Collection Script for ClimateTrade

This script collects current weather data for London and New York City using
the Meteostat Python library and stores it in the ClimateTrade database.

Usage:
    python meteostat-weather-collector.py --location london
    python meteostat-weather-collector.py --location nyc
    python meteostat-weather-collector.py --all
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path
import pandas as pd

# Add meteostat-python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'meteostat-python'))

try:
    from meteostat import Point, Hourly
except ImportError as e:
    print(f"Error importing meteostat: {e}")
    print("Please ensure meteostat-python is properly installed")
    sys.exit(1)

# Location coordinates
LOCATIONS = {
    'london': {
        'name': 'London, UK',
        'lat': 51.5074,
        'lon': -0.1278,
        'elevation': 25
    },
    'nyc': {
        'name': 'New York City, US',
        'lat': 40.7128,
        'lon': -74.0060,
        'elevation': 10
    }
}

class WeatherDataCollector:
    """Handles weather data collection and database insertion."""

    def __init__(self, db_path: str = "../data/climatetrade.db"):
        self.db_path = db_path
        self.ensure_db_exists()

    def celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius temperature to Fahrenheit."""
        if celsius is None:
            return None
        return round((celsius * 9/5) + 32, 1)

    def ensure_db_exists(self):
        """Ensure the database file exists."""
        if not Path(self.db_path).exists():
            print(f"Error: Database not found at {self.db_path}")
            print("Please run the database setup first:")
            print("python data_pipeline/setup_database.py")
            sys.exit(1)

    def get_meteostat_source_id(self) -> int:
        """Get the meteostat source ID from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id FROM weather_sources WHERE source_name = 'meteostat'")
            result = cursor.fetchone()
            if not result:
                print("Error: meteostat source not found in database")
                return None
            return result[0]
        finally:
            conn.close()

    def collect_weather_data(self, location_key: str) -> Optional[Dict]:
        """Collect current weather data for a location using Meteostat."""
        if location_key not in LOCATIONS:
            print(f"Error: Unknown location '{location_key}'")
            return None

        location = LOCATIONS[location_key]

        try:
            # Create Point for the location
            point = Point(location['lat'], location['lon'], location['elevation'])

            # Get current time and previous hour for recent data
            now = datetime.utcnow()
            start_time = now - timedelta(hours=1)
            end_time = now

            print(f"Collecting weather data for {location['name']}...")
            print(f"Time range: {start_time} to {end_time}")

            # Get hourly data
            data = Hourly(point, start_time, end_time)
            data = data.fetch()

            if data.empty:
                print(f"No data available for {location['name']}")
                return None

            # Get the most recent data point
            latest_data = data.iloc[-1]

            # Convert to dictionary and handle NaN values
            weather_dict = {}
            for col in data.columns:
                value = latest_data[col]
                if pd.isna(value):
                    weather_dict[col] = None
                else:
                    weather_dict[col] = value

            return {
                'location': location,
                'timestamp': latest_data.name.isoformat(),
                'data': weather_dict,
                'raw_data': json.dumps(weather_dict)
            }

        except Exception as e:
            print(f"Error collecting data for {location['name']}: {e}")
            return None

    def insert_weather_data(self, source_id: int, weather_data: Dict) -> bool:
        """Insert weather data into the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Prepare data for insertion
            location = weather_data['location']
            data = weather_data['data']

            # Convert temperatures from Celsius to Fahrenheit
            temp_celsius = data.get('temp')
            temp_fahrenheit = self.celsius_to_fahrenheit(temp_celsius) if temp_celsius is not None else None

            # Map meteostat fields to database fields (temperatures now in Fahrenheit)
            insert_data = {
                'source_id': source_id,
                'location_name': location['name'],
                'latitude': location['lat'],
                'longitude': location['lon'],
                'timestamp': weather_data['timestamp'],
                'temperature': temp_fahrenheit,
                'temperature_min': temp_fahrenheit,  # Using same temp for min/max since Meteostat provides single temp
                'temperature_max': temp_fahrenheit,
                'feels_like': None,  # Meteostat doesn't provide this
                'humidity': data.get('rhum'),
                'pressure': data.get('pres'),
                'wind_speed': data.get('wspd'),
                'wind_direction': data.get('wdir'),
                'precipitation': data.get('prcp'),
                'weather_code': None,  # Meteostat uses different codes
                'weather_description': None,
                'visibility': None,  # Meteostat doesn't provide this
                'uv_index': None,  # Meteostat doesn't provide this
                'alerts': None,
                'raw_data': weather_data['raw_data']
            }

            # Insert data
            columns = ', '.join(insert_data.keys())
            placeholders = ', '.join(['?' for _ in insert_data])
            values = list(insert_data.values())

            query = f"""
                INSERT OR REPLACE INTO weather_data
                ({columns})
                VALUES ({placeholders})
            """

            cursor.execute(query, values)
            conn.commit()

            print(f"Successfully inserted weather data for {location['name']}")
            return True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        except Exception as e:
            print(f"Error inserting data: {e}")
            return False
        finally:
            conn.close()

    def collect_and_store(self, location_key: str) -> bool:
        """Collect weather data and store it in the database."""
        # Get source ID
        source_id = self.get_meteostat_source_id()
        if not source_id:
            return False

        # Collect data
        weather_data = self.collect_weather_data(location_key)
        if not weather_data:
            return False

        # Store data
        return self.insert_weather_data(source_id, weather_data)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Collect weather data using Meteostat")
    parser.add_argument(
        "--db-path",
        default="../data/climatetrade.db",
        help="Path to the database file"
    )
    parser.add_argument(
        "--location",
        choices=['london', 'nyc'],
        help="Location to collect data for"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Collect data for all locations"
    )

    args = parser.parse_args()

    if not args.location and not args.all:
        parser.error("Must specify --location or --all")

    collector = WeatherDataCollector(args.db_path)

    success_count = 0
    total_count = 0

    if args.all:
        locations = ['london', 'nyc']
    else:
        locations = [args.location]

    for location in locations:
        total_count += 1
        if collector.collect_and_store(location):
            success_count += 1

    print(f"\nCompleted: {success_count}/{total_count} locations processed successfully")

    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)