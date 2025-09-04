#!/usr/bin/env python3
"""
Weather Data Ingestion Script

This script ingests weather data from various sources into the database.
Supports JSON input from Met Office, Meteostat, NWS, and other weather APIs.
"""

import json
import sqlite3
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# Import data quality modules
try:
    from data_quality_pipeline import process_weather_data
    from data_validation import validate_weather_data
    DATA_QUALITY_AVAILABLE = True
except ImportError:
    logger.warning("Data quality modules not available. Running without validation/cleaning.")
    DATA_QUALITY_AVAILABLE = False

class WeatherDataIngester:
    """Handles ingestion of weather data from various sources into the database."""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self.ensure_db_exists()

    def ensure_db_exists(self):
        """Ensure the database file exists."""
        if not Path(self.db_path).exists():
            logger.error(f"Database not found at {self.db_path}. Please run setup_database.py first.")
            sys.exit(1)

    def connect_db(self):
        """Connect to the database."""
        return sqlite3.connect(self.db_path)

    def get_source_id(self, source_name: str, conn: sqlite3.Connection) -> int:
        """Get or create source ID for a weather source."""
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM weather_sources WHERE source_name = ?", (source_name,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            # Insert new source
            cursor.execute(
                "INSERT INTO weather_sources (source_name) VALUES (?)",
                (source_name,)
            )
            return cursor.lastrowid

    def normalize_met_office_data(self, data: Dict, location: str) -> List[Dict]:
        """Normalize Met Office weather data."""
        normalized_data = []

        if 'features' in data and len(data['features']) > 0:
            feature = data['features'][0]
            time_series = feature.get('properties', {}).get('timeSeries', [])

            for ts in time_series:
                normalized_data.append({
                    'location_name': location,
                    'latitude': None,  # Would need to be passed separately
                    'longitude': None,
                    'timestamp': ts.get('time'),
                    'temperature': ts.get('screenTemperature'),
                    'feels_like': ts.get('feelsLikeTemperature'),
                    'humidity': ts.get('screenRelativeHumidity'),
                    'wind_speed': ts.get('windSpeed10m'),
                    'wind_direction': ts.get('windDirectionFrom10m'),
                    'precipitation': ts.get('totalPrecipAmount'),
                    'pressure': ts.get('mslp'),
                    'visibility': ts.get('visibility'),
                    'weather_code': ts.get('significantWeatherCode'),
                    'raw_data': json.dumps(ts)
                })

        return normalized_data

    def normalize_meteostat_data(self, data: Dict, location: str) -> List[Dict]:
        """Normalize Meteostat weather data."""
        normalized_data = []

        # Assuming data is a pandas DataFrame-like structure
        if hasattr(data, 'iterrows'):
            for index, row in data.iterrows():
                normalized_data.append({
                    'location_name': location,
                    'latitude': None,
                    'longitude': None,
                    'timestamp': str(index),
                    'temperature': row.get('tavg'),
                    'temperature_min': row.get('tmin'),
                    'temperature_max': row.get('tmax'),
                    'humidity': row.get('rhum'),
                    'wind_speed': row.get('wspd'),
                    'wind_direction': row.get('wdir'),
                    'precipitation': row.get('prcp'),
                    'pressure': row.get('pres'),
                    'raw_data': json.dumps(row.to_dict())
                })

        return normalized_data

    def normalize_nws_data(self, data: Dict, location: str) -> List[Dict]:
        """Normalize NWS weather data."""
        normalized_data = []

        if 'properties' in data:
            periods = data['properties'].get('periods', [])

            for period in periods:
                normalized_data.append({
                    'location_name': location,
                    'latitude': None,
                    'longitude': None,
                    'timestamp': period.get('startTime'),
                    'temperature': period.get('temperature'),
                    'weather_description': period.get('detailedForecast'),
                    'wind_speed': self.parse_wind_speed(period.get('windSpeed', '')),
                    'wind_direction': period.get('windDirection'),
                    'precipitation': None,  # NWS doesn't provide direct precipitation
                    'raw_data': json.dumps(period)
                })

        return normalized_data

    def parse_wind_speed(self, wind_speed_str: str) -> Optional[float]:
        """Parse wind speed from NWS format (e.g., '10 mph' -> 10.0)."""
        if not wind_speed_str:
            return None
        try:
            # Extract numeric value
            import re
            match = re.search(r'(\d+)', wind_speed_str)
            return float(match.group(1)) if match else None
        except:
            return None

    def normalize_generic_weather_data(self, data: Dict, location: str, source: str) -> List[Dict]:
        """Normalize generic weather data structure."""
        logger.info(f"Normalizing data for source: {source}, data type: {type(data)}")

        # For now, use generic normalization for all sources to test
        # TODO: Implement specific normalization for each source
        normalized_data = []

        # If data is a list, process each item
        if isinstance(data, list):
            logger.info(f"Processing list with {len(data)} items")
            for item in data:
                if isinstance(item, dict):
                    normalized_data.append(self._normalize_weather_item(item, location))
        # If data is a single dict, process it directly
        elif isinstance(data, dict):
            logger.info("Processing single dict")
            normalized_data.append(self._normalize_weather_item(data, location))

        logger.info(f"Normalized {len(normalized_data)} records")
        return normalized_data

    def _normalize_weather_item(self, item: Dict, location: str) -> Dict:
        """Normalize a single weather data item."""
        return {
            'location_name': item.get('location_name', location),
            'latitude': item.get('latitude'),
            'longitude': item.get('longitude'),
            'timestamp': item.get('timestamp') or item.get('time'),
            'temperature': item.get('temperature') or item.get('temp'),
            'temperature_min': item.get('temperature_min') or item.get('temp_min'),
            'temperature_max': item.get('temperature_max') or item.get('temp_max'),
            'feels_like': item.get('feels_like'),
            'humidity': item.get('humidity'),
            'pressure': item.get('pressure'),
            'wind_speed': item.get('wind_speed'),
            'wind_direction': item.get('wind_direction'),
            'precipitation': item.get('precipitation'),
            'weather_code': item.get('weather_code'),
            'weather_description': item.get('weather_description') or item.get('condition'),
            'visibility': item.get('visibility'),
            'uv_index': item.get('uv_index'),
            'alerts': item.get('alerts') if isinstance(item.get('alerts'), str) else json.dumps(item.get('alerts', [])),
            'raw_data': item.get('raw_data') if isinstance(item.get('raw_data'), str) else json.dumps(item)
        }

    def insert_weather_data(self, data: List[Dict], source_name: str, conn: sqlite3.Connection) -> int:
        """Insert weather data into the database."""
        if not data:
            return 0

        cursor = conn.cursor()
        source_id = self.get_source_id(source_name, conn)

        insert_sql = """
        INSERT OR IGNORE INTO weather_data
        (source_id, location_name, latitude, longitude, timestamp, temperature,
         temperature_min, temperature_max, feels_like, humidity, pressure,
         wind_speed, wind_direction, precipitation, weather_code, weather_description,
         visibility, uv_index, alerts, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted_count = 0
        for record in data:
            try:
                cursor.execute(insert_sql, (
                    source_id,
                    record.get('location_name'),
                    record.get('latitude'),
                    record.get('longitude'),
                    record.get('timestamp'),
                    record.get('temperature'),
                    record.get('temperature_min'),
                    record.get('temperature_max'),
                    record.get('feels_like'),
                    record.get('humidity'),
                    record.get('pressure'),
                    record.get('wind_speed'),
                    record.get('wind_direction'),
                    record.get('precipitation'),
                    record.get('weather_code'),
                    record.get('weather_description'),
                    record.get('visibility'),
                    record.get('uv_index'),
                    record.get('alerts'),
                    record.get('raw_data')
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            except sqlite3.Error as e:
                logger.error(f"Error inserting weather record: {e}")

        return inserted_count

    def ingest_json_file(self, json_path: str, source: str, location: str, enable_quality_pipeline: bool = True) -> dict:
        """Ingest weather data from a JSON file with optional quality processing."""
        if not Path(json_path).exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        logger.info(f"Reading JSON file: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        normalized_data = self.normalize_generic_weather_data(data, location, source)

        logger.info(f"Normalized {len(normalized_data)} weather records")

        # Apply data quality pipeline if available and enabled
        quality_result = None
        if DATA_QUALITY_AVAILABLE and enable_quality_pipeline and normalized_data:
            logger.info("Applying data quality pipeline to weather data")
            try:
                quality_config = {
                    'fail_on_validation_error': False,
                    'fail_on_cleaning_error': False,
                    'generate_reports': True,
                    'quality_threshold': 70.0  # More lenient for initial processing
                }
                quality_result = process_weather_data(normalized_data, quality_config)

                if quality_result['success']:
                    logger.info(f"Quality pipeline completed. Score: {quality_result['quality_score']}%")
                    # Use cleaned data for database insertion
                    normalized_data = quality_result['cleaned_data']
                    logger.info(f"Using {len(normalized_data)} cleaned records for database insertion")
                else:
                    logger.warning(f"Quality pipeline failed: {quality_result.get('error', 'Unknown error')}")
                    logger.warning("Proceeding with original normalized data")

            except Exception as e:
                logger.error(f"Error in data quality pipeline: {e}")
                logger.warning("Proceeding with original normalized data")

        # Insert data into database
        conn = self.connect_db()
        try:
            inserted_count = self.insert_weather_data(normalized_data, source, conn)
            conn.commit()
            logger.info(f"Successfully inserted {inserted_count} new weather records")

            result = {
                'file': json_path,
                'source': source,
                'location': location,
                'total_records': len(normalized_data),
                'inserted': inserted_count,
                'duplicates': len(normalized_data) - inserted_count,
                'quality_processed': quality_result is not None,
                'quality_score': quality_result.get('quality_score') if quality_result else None
            }

            if quality_result:
                result.update({
                    'original_records': quality_result['original_records'],
                    'processed_records': quality_result['processed_records'],
                    'validation_errors': quality_result['validation_result'].get('invalid_records', 0),
                    'cleaning_steps': quality_result['cleaning_result'].get('cleaning_steps', [])
                })

            return result

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description="Ingest weather data from JSON files")
    parser.add_argument(
        "json_file",
        help="Path to JSON file containing weather data"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Weather data source (met_office, meteostat, nws, etc.)"
    )
    parser.add_argument(
        "--location",
        required=True,
        help="Location name for the weather data"
    )
    parser.add_argument(
        "--db-path",
        default="data/climatetrade.db",
        help="Path to the database file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--enable-quality-pipeline", "-q",
        action="store_true",
        default=True,
        help="Enable data quality pipeline (validation and cleaning)"
    )
    parser.add_argument(
        "--disable-quality-pipeline",
        action="store_true",
        help="Disable data quality pipeline"
    )
    parser.add_argument(
        "--quality-config",
        type=str,
        help="Path to JSON file with quality pipeline configuration"
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

    # Determine if quality pipeline should be enabled
    enable_quality = args.enable_quality_pipeline and not args.disable_quality_pipeline

    # Load quality configuration if provided
    quality_config = None
    if args.quality_config and Path(args.quality_config).exists():
        try:
            with open(args.quality_config, 'r') as f:
                quality_config = json.load(f)
            logger.info(f"Loaded quality configuration from {args.quality_config}")
        except Exception as e:
            logger.error(f"Error loading quality configuration: {e}")
            quality_config = None

    ingester = WeatherDataIngester(args.db_path)

    try:
        result = ingester.ingest_json_file(args.json_file, args.source, args.location,
                                         enable_quality_pipeline=enable_quality)
        print(f"Processed {result['file']}: {result['inserted']} inserted, {result['duplicates']} duplicates")
        print(f"Source: {result['source']}, Location: {result['location']}")
        if result.get('quality_processed'):
            print(f"Quality Score: {result.get('quality_score', 'N/A')}%")
            print(f"Validation Errors: {result.get('validation_errors', 0)}")
            if result.get('cleaning_steps'):
                print(f"Cleaning Steps: {', '.join(result['cleaning_steps'])}")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()