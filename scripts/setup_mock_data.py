#!/usr/bin/env python3
"""
Setup mock data for ClimateTrade database
Creates sample weather data and sources for testing the frontend
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import random

def setup_database():
    """Set up the database with schema and mock data"""
    db_path = Path("../data/climatetrade.db")

    # Create database directory if it doesn't exist
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = Path("../database/schema.sql")
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema (split by semicolon and filter out empty statements)
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except sqlite3.Error as e:
                    print(f"Warning: {e} (statement: {statement[:50]}...)")

    conn.commit()

    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM weather_sources")
    if cursor.fetchone()[0] == 0:
        print("Adding mock weather sources...")
        add_mock_sources(cursor)

    cursor.execute("SELECT COUNT(*) FROM weather_data")
    if cursor.fetchone()[0] == 0:
        print("Adding mock weather data...")
        add_mock_weather_data(cursor)

    conn.commit()
    conn.close()
    print("Database setup complete!")

def add_mock_sources(cursor):
    """Add mock weather sources"""
    sources = [
        ('met_office', 'UK Met Office Weather DataHub', 'https://www.metoffice.gov.uk/', 1, 1000, 'json', 1, datetime.now().isoformat(), datetime.now().isoformat()),
        ('meteostat', 'Meteostat Historical Weather Data', 'https://meteostat.net/', 1, 2000, 'json', 1, datetime.now().isoformat(), datetime.now().isoformat()),
        ('nws', 'US National Weather Service', 'https://api.weather.gov', 0, 1000, 'json', 1, datetime.now().isoformat(), datetime.now().isoformat()),
        ('weather2geo', 'Weather2Geo API', 'https://api.weather2geo.com', 1, 1000, 'json', 0, datetime.now().isoformat(), datetime.now().isoformat()),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO weather_sources
        (source_name, description, api_endpoint, api_key_required, rate_limit_per_hour, data_format, active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sources)

def add_mock_weather_data(cursor):
    """Add mock weather data for the last 24 hours"""
    # Get source IDs
    cursor.execute("SELECT id, source_name FROM weather_sources")
    sources_raw = cursor.fetchall()
    sources = {name: id for id, name in sources_raw}  # Reverse the mapping
    print(f"DEBUG: Sources mapping: {sources}")

    locations = ['London', 'New York']
    base_time = datetime.now() - timedelta(hours=24)

    weather_data = []

    for hour in range(24):
        timestamp = (base_time + timedelta(hours=hour)).isoformat()

        for location in locations:
            for source_name, source_id in sources.items():
                # Skip inactive sources
                if source_name == 'weather2geo':
                    continue

                # Generate realistic weather data with source-specific variations
                base_temp = 20 if location == 'London' else 25

                # Add source-specific temperature variations
                if source_name == 'met_office':
                    temp_offset = random.uniform(-1, 1)  # Most accurate
                elif source_name == 'nws':
                    temp_offset = random.uniform(-2, 2)  # Good accuracy
                elif source_name == 'meteostat':
                    temp_offset = random.uniform(-1.5, 1.5)  # Historical data
                else:
                    temp_offset = random.uniform(-3, 3)  # More variation

                temperature = round(base_temp + temp_offset, 1)

                # Convert to Fahrenheit for display
                temperature_f = round((temperature * 9/5) + 32, 1)

                humidity = random.randint(40, 80)
                wind_speed = round(random.uniform(5, 15), 1)
                precipitation = round(random.uniform(0, 2), 1)

                weather_descriptions = ['Clear sky', 'Partly cloudy', 'Overcast', 'Light rain', 'Moderate rain']
                weather_desc = random.choice(weather_descriptions)

                # Source-specific quality scores
                if source_name == 'met_office':
                    quality_score = random.uniform(0.9, 1.0)  # High quality
                elif source_name == 'nws':
                    quality_score = random.uniform(0.85, 0.98)  # Very good
                elif source_name == 'meteostat':
                    quality_score = random.uniform(0.8, 0.95)  # Good
                else:
                    quality_score = random.uniform(0.7, 0.9)  # Decent

                weather_data.append((
                    source_id, location, None, None, timestamp,
                    temperature_f, None, None, None,  # temperature fields
                    humidity, None,  # pressure
                    wind_speed, random.randint(0, 359),  # wind direction
                    precipitation, random.randint(1, 5),  # weather code
                    weather_desc, None, None,  # visibility, uv
                    json.dumps({'mock': True, 'source': source_name}),  # alerts
                    json.dumps({  # raw data
                        'temperature': temperature,
                        'humidity': humidity,
                        'wind_speed': wind_speed,
                        'description': weather_desc,
                        'source': source_name
                    }),
                    quality_score,
                    datetime.now().isoformat()
                ))

    cursor.executemany("""
        INSERT OR IGNORE INTO weather_data
        (source_id, location_name, latitude, longitude, timestamp,
         temperature, temperature_min, temperature_max, feels_like,
         humidity, pressure, wind_speed, wind_direction, precipitation,
         weather_code, weather_description, visibility, uv_index, alerts,
         raw_data, data_quality_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, weather_data)

    print(f"Added {len(weather_data)} mock weather records from {len([s for s in sources.keys() if s != 'weather2geo'])} sources")

if __name__ == "__main__":
    print("Setting up ClimateTrade database with mock data...")
    setup_database()
    print("Setup complete! You can now refresh your browser at http://localhost:8080")