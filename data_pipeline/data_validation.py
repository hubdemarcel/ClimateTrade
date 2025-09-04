#!/usr/bin/env python3
"""
Data Validation Module

This module provides comprehensive data validation functions for Polymarket and weather data.
Validates data integrity, formats, ranges, and consistency across different data sources.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import re
import json

logger = logging.getLogger(__name__)

class DataValidator:
    """Base class for data validation with common validation methods."""

    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []

    def reset_errors(self):
        """Reset validation errors and warnings."""
        self.validation_errors = []
        self.validation_warnings = []

    def add_error(self, field: str, message: str, value: Any = None):
        """Add a validation error."""
        error_msg = f"Field '{field}': {message}"
        if value is not None:
            error_msg += f" (value: {value})"
        self.validation_errors.append(error_msg)
        logger.error(error_msg)

    def add_warning(self, field: str, message: str, value: Any = None):
        """Add a validation warning."""
        warning_msg = f"Field '{field}': {message}"
        if value is not None:
            warning_msg += f" (value: {value})"
        self.validation_warnings.append(warning_msg)
        logger.warning(warning_msg)

    def validate_required_fields(self, data: Dict, required_fields: List[str]) -> bool:
        """Validate that all required fields are present and not empty."""
        valid = True
        for field in required_fields:
            if field not in data:
                self.add_error(field, "Required field is missing")
                valid = False
            elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                self.add_error(field, "Required field is empty or null")
                valid = False
        return valid

    def validate_data_types(self, data: Dict, type_requirements: Dict[str, type]) -> bool:
        """Validate data types for specified fields."""
        valid = True
        for field, expected_type in type_requirements.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    try:
                        # Try to convert if possible
                        if expected_type == int and isinstance(data[field], str):
                            int(data[field])
                        elif expected_type == float and isinstance(data[field], str):
                            float(data[field])
                        elif expected_type == bool and isinstance(data[field], str):
                            data[field].lower() in ['true', 'false', '1', '0']
                        else:
                            self.add_error(field, f"Invalid data type, expected {expected_type.__name__}")
                            valid = False
                    except (ValueError, TypeError):
                        self.add_error(field, f"Invalid data type, expected {expected_type.__name__}")
                        valid = False
        return valid

    def validate_numeric_range(self, data: Dict, range_requirements: Dict[str, Tuple[Optional[float], Optional[float]]]) -> bool:
        """Validate numeric fields are within acceptable ranges."""
        valid = True
        for field, (min_val, max_val) in range_requirements.items():
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if min_val is not None and value < min_val:
                        self.add_warning(field, f"Value below minimum threshold {min_val}", value)
                    if max_val is not None and value > max_val:
                        self.add_warning(field, f"Value above maximum threshold {max_val}", value)
                except (ValueError, TypeError):
                    self.add_error(field, "Invalid numeric value")
                    valid = False
        return valid

    def validate_timestamp_format(self, timestamp_str: str, field_name: str) -> bool:
        """Validate timestamp format and convert to ISO format if needed."""
        if not timestamp_str:
            return False

        # Common timestamp formats to try
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',  # ISO 8601 UTC
            '%Y-%m-%dT%H:%M:%S%z', # ISO 8601 with timezone
            '%Y-%m-%d %H:%M:%S',   # Standard format
            '%Y-%m-%dT%H:%M:%S',   # ISO without timezone
            '%Y-%m-%d',            # Date only
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                # Ensure timezone awareness
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return True
            except ValueError:
                continue

        self.add_error(field_name, f"Invalid timestamp format: {timestamp_str}")
        return False

    def get_validation_summary(self) -> Dict:
        """Get summary of validation results."""
        return {
            'errors': len(self.validation_errors),
            'warnings': len(self.validation_warnings),
            'error_messages': self.validation_errors.copy(),
            'warning_messages': self.validation_warnings.copy(),
            'is_valid': len(self.validation_errors) == 0
        }


class PolymarketDataValidator(DataValidator):
    """Validator for Polymarket data."""

    def __init__(self):
        super().__init__()
        self.required_fields = [
            'event_title', 'market_id', 'outcome_name', 'timestamp', 'scraped_at'
        ]

        self.type_requirements = {
            'probability': (int, float),
            'volume': (int, float)
        }

        self.range_requirements = {
            'probability': (0.0, 1.0),  # Probability should be between 0 and 1
            'volume': (0.0, None)       # Volume should be non-negative
        }

    def validate_record(self, record: Dict) -> bool:
        """Validate a single Polymarket record."""
        self.reset_errors()

        # Validate required fields
        if not self.validate_required_fields(record, self.required_fields):
            return False

        # Validate data types
        if not self.validate_data_types(record, self.type_requirements):
            return False

        # Validate numeric ranges
        if not self.validate_numeric_range(record, self.range_requirements):
            pass  # Warnings don't fail validation

        # Validate timestamps
        if not self.validate_timestamp_format(record.get('timestamp', ''), 'timestamp'):
            return False

        if not self.validate_timestamp_format(record.get('scraped_at', ''), 'scraped_at'):
            return False

        # Validate market_id format (should be alphanumeric with possible hyphens)
        market_id = record.get('market_id', '')
        if not re.match(r'^[a-zA-Z0-9\-]+$', market_id):
            self.add_error('market_id', f"Invalid market ID format: {market_id}")

        # Validate scraped_at is not in the future
        try:
            scraped_dt = datetime.fromisoformat(record['scraped_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if scraped_dt > now:
                self.add_warning('scraped_at', "Scraped timestamp is in the future", record['scraped_at'])
        except (ValueError, AttributeError):
            pass  # Already validated format above

        return len(self.validation_errors) == 0

    def validate_batch(self, records: List[Dict]) -> Dict:
        """Validate a batch of Polymarket records."""
        results = []
        total_valid = 0

        for i, record in enumerate(records):
            is_valid = self.validate_record(record)
            results.append({
                'index': i,
                'is_valid': is_valid,
                'errors': self.validation_errors.copy(),
                'warnings': self.validation_warnings.copy()
            })
            if is_valid:
                total_valid += 1

        return {
            'total_records': len(records),
            'valid_records': total_valid,
            'invalid_records': len(records) - total_valid,
            'results': results
        }


class WeatherDataValidator(DataValidator):
    """Validator for weather data."""

    def __init__(self):
        super().__init__()
        self.required_fields = [
            'location_name', 'timestamp'
        ]

        self.type_requirements = {
            'latitude': (int, float),
            'longitude': (int, float),
            'temperature': (int, float),
            'temperature_min': (int, float),
            'temperature_max': (int, float),
            'feels_like': (int, float),
            'humidity': (int, float),
            'pressure': (int, float),
            'wind_speed': (int, float),
            'wind_direction': (int, float),
            'precipitation': (int, float),
            'visibility': (int, float),
            'uv_index': (int, float),
            'weather_code': (int, str)
        }

        # Realistic ranges for weather data
        self.range_requirements = {
            'latitude': (-90.0, 90.0),
            'longitude': (-180.0, 180.0),
            'temperature': (-100.0, 60.0),  # Celsius
            'temperature_min': (-100.0, 60.0),
            'temperature_max': (-100.0, 60.0),
            'feels_like': (-100.0, 60.0),
            'humidity': (0.0, 100.0),  # Percentage
            'pressure': (800.0, 1200.0),  # hPa
            'wind_speed': (0.0, 150.0),  # m/s or mph
            'wind_direction': (0.0, 360.0),  # Degrees
            'precipitation': (0.0, 500.0),  # mm
            'visibility': (0.0, 100000.0),  # meters
            'uv_index': (0.0, 15.0)
        }

    def validate_record(self, record: Dict) -> bool:
        """Validate a single weather record."""
        self.reset_errors()

        # Validate required fields
        if not self.validate_required_fields(record, self.required_fields):
            return False

        # Validate data types
        if not self.validate_data_types(record, self.type_requirements):
            return False

        # Validate numeric ranges
        if not self.validate_numeric_range(record, self.range_requirements):
            pass  # Warnings don't fail validation

        # Validate timestamp
        if not self.validate_timestamp_format(record.get('timestamp', ''), 'timestamp'):
            return False

        # Validate location coordinates consistency
        latitude = record.get('latitude')
        longitude = record.get('longitude')
        if latitude is not None and longitude is not None:
            # Check if coordinates are realistic (not 0,0 which often indicates missing data)
            if latitude == 0.0 and longitude == 0.0:
                self.add_warning('coordinates', "Coordinates are (0,0) which may indicate missing location data")

        # Validate temperature relationships
        temp = record.get('temperature')
        temp_min = record.get('temperature_min')
        temp_max = record.get('temperature_max')

        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            self.add_error('temperature_range', f"Min temperature ({temp_min}) > max temperature ({temp_max})")

        if temp is not None:
            if temp_min is not None and temp < temp_min:
                self.add_warning('temperature', f"Temperature ({temp}) < min temperature ({temp_min})")
            if temp_max is not None and temp > temp_max:
                self.add_warning('temperature', f"Temperature ({temp}) > max temperature ({temp_max})")

        # Validate wind direction if wind speed is present
        wind_speed = record.get('wind_speed')
        wind_direction = record.get('wind_direction')

        if wind_speed is not None and wind_speed > 0 and wind_direction is None:
            self.add_warning('wind_direction', "Wind direction missing when wind speed is present")

        # Validate weather code format
        weather_code = record.get('weather_code')
        if weather_code is not None:
            if isinstance(weather_code, str):
                # Try to convert to int
                try:
                    int(weather_code)
                except ValueError:
                    self.add_warning('weather_code', f"Non-numeric weather code: {weather_code}")

        # Validate raw_data is valid JSON if present
        raw_data = record.get('raw_data')
        if raw_data and isinstance(raw_data, str):
            try:
                json.loads(raw_data)
            except json.JSONDecodeError:
                self.add_warning('raw_data', "Invalid JSON in raw_data field")

        return len(self.validation_errors) == 0

    def validate_batch(self, records: List[Dict]) -> Dict:
        """Validate a batch of weather records."""
        results = []
        total_valid = 0

        for i, record in enumerate(records):
            is_valid = self.validate_record(record)
            results.append({
                'index': i,
                'is_valid': is_valid,
                'errors': self.validation_errors.copy(),
                'warnings': self.validation_warnings.copy()
            })
            if is_valid:
                total_valid += 1

        return {
            'total_records': len(records),
            'valid_records': total_valid,
            'invalid_records': len(records) - total_valid,
            'results': results
        }


def validate_polymarket_data(records: List[Dict]) -> Dict:
    """Convenience function to validate Polymarket data."""
    validator = PolymarketDataValidator()
    return validator.validate_batch(records)


def validate_weather_data(records: List[Dict]) -> Dict:
    """Convenience function to validate weather data."""
    validator = WeatherDataValidator()
    return validator.validate_batch(records)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test Polymarket validation
    polymarket_sample = {
        'event_title': 'Will it rain in London tomorrow?',
        'market_id': '0x1234567890abcdef',
        'outcome_name': 'Yes',
        'probability': 0.65,
        'volume': 10000.50,
        'timestamp': '2025-09-04T12:00:00Z',
        'scraped_at': '2025-09-04T12:30:00Z'
    }

    poly_validator = PolymarketDataValidator()
    is_valid = poly_validator.validate_record(polymarket_sample)
    print(f"Polymarket record valid: {is_valid}")
    print(f"Validation summary: {poly_validator.get_validation_summary()}")

    # Test weather validation
    weather_sample = {
        'location_name': 'London, UK',
        'latitude': 51.5074,
        'longitude': -0.1278,
        'timestamp': '2025-09-04T12:00:00Z',
        'temperature': 18.5,
        'humidity': 72,
        'wind_speed': 8.5,
        'pressure': 1013.2
    }

    weather_validator = WeatherDataValidator()
    is_valid = weather_validator.validate_record(weather_sample)
    print(f"Weather record valid: {is_valid}")
    print(f"Validation summary: {weather_validator.get_validation_summary()}")