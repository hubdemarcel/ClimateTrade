#!/usr/bin/env python3
"""
Unit Tests for Data Quality Module

This module contains comprehensive unit tests for the data validation,
cleaning, and quality pipeline functionality.
"""

import unittest
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from data_validation import (
    PolymarketDataValidator,
    WeatherDataValidator,
    validate_polymarket_data,
    validate_weather_data
)

from data_cleaning import (
    MissingValueHandler,
    OutlierDetector,
    DataNormalizer,
    PolymarketDataCleaner,
    WeatherDataCleaner,
    clean_polymarket_data,
    clean_weather_data
)

from data_quality_pipeline import (
    DataQualityPipeline,
    DataSource,
    process_polymarket_data,
    process_weather_data
)


class TestPolymarketDataValidator(unittest.TestCase):
    """Test cases for Polymarket data validation."""

    def setUp(self):
        self.validator = PolymarketDataValidator()

    def test_valid_polymarket_record(self):
        """Test validation of a valid Polymarket record."""
        valid_record = {
            'event_title': 'Will it rain in London tomorrow?',
            'market_id': '0x1234567890abcdef',
            'outcome_name': 'Yes',
            'probability': 0.65,
            'volume': 10000.50,
            'timestamp': '2025-09-04T12:00:00Z',
            'scraped_at': '2025-09-04T12:30:00Z'
        }

        is_valid = self.validator.validate_record(valid_record)
        self.assertTrue(is_valid)
        self.assertEqual(len(self.validator.validation_errors), 0)

    def test_invalid_polymarket_record_missing_fields(self):
        """Test validation of Polymarket record with missing required fields."""
        invalid_record = {
            'event_title': 'Will it rain in London tomorrow?',
            # Missing market_id, outcome_name, timestamp, scraped_at
            'probability': 0.65,
            'volume': 10000.50
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertFalse(is_valid)
        self.assertGreater(len(self.validator.validation_errors), 0)

    def test_invalid_probability_range(self):
        """Test validation of Polymarket record with invalid probability."""
        invalid_record = {
            'event_title': 'Will it rain in London tomorrow?',
            'market_id': '0x1234567890abcdef',
            'outcome_name': 'Yes',
            'probability': 1.5,  # Invalid: should be between 0 and 1
            'volume': 10000.50,
            'timestamp': '2025-09-04T12:00:00Z',
            'scraped_at': '2025-09-04T12:30:00Z'
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertTrue(is_valid)  # Should still be valid, just with warnings
        self.assertGreater(len(self.validator.validation_warnings), 0)

    def test_invalid_timestamp_format(self):
        """Test validation of Polymarket record with invalid timestamp."""
        invalid_record = {
            'event_title': 'Will it rain in London tomorrow?',
            'market_id': '0x1234567890abcdef',
            'outcome_name': 'Yes',
            'probability': 0.65,
            'volume': 10000.50,
            'timestamp': 'invalid-timestamp',
            'scraped_at': '2025-09-04T12:30:00Z'
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertFalse(is_valid)
        self.assertGreater(len(self.validator.validation_errors), 0)

    def test_batch_validation(self):
        """Test batch validation of multiple Polymarket records."""
        records = [
            {
                'event_title': 'Will it rain in London tomorrow?',
                'market_id': '0x1234567890abcdef',
                'outcome_name': 'Yes',
                'probability': 0.65,
                'volume': 10000.50,
                'timestamp': '2025-09-04T12:00:00Z',
                'scraped_at': '2025-09-04T12:30:00Z'
            },
            {
                'event_title': 'Will temperature exceed 20C?',
                'market_id': '0xabcdef1234567890',
                'outcome_name': 'No',
                'probability': 0.45,
                'volume': None,  # Missing volume
                'timestamp': '2025-09-04T12:00:00Z',
                'scraped_at': '2025-09-04T12:30:00Z'
            }
        ]

        result = self.validator.validate_batch(records)
        self.assertEqual(result['total_records'], 2)
        self.assertEqual(result['valid_records'], 2)  # Both should be valid (warnings don't fail)
        self.assertEqual(result['invalid_records'], 0)


class TestWeatherDataValidator(unittest.TestCase):
    """Test cases for weather data validation."""

    def setUp(self):
        self.validator = WeatherDataValidator()

    def test_valid_weather_record(self):
        """Test validation of a valid weather record."""
        valid_record = {
            'location_name': 'London, UK',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'timestamp': '2025-09-04T12:00:00Z',
            'temperature': 18.5,
            'humidity': 72,
            'wind_speed': 8.5,
            'pressure': 1013.2
        }

        is_valid = self.validator.validate_record(valid_record)
        self.assertTrue(is_valid)
        self.assertEqual(len(self.validator.validation_errors), 0)

    def test_invalid_weather_record_missing_fields(self):
        """Test validation of weather record with missing required fields."""
        invalid_record = {
            'latitude': 51.5074,
            'longitude': -0.1278,
            # Missing location_name and timestamp
            'temperature': 18.5,
            'humidity': 72
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertFalse(is_valid)
        self.assertGreater(len(self.validator.validation_errors), 0)

    def test_invalid_coordinate_range(self):
        """Test validation of weather record with invalid coordinates."""
        invalid_record = {
            'location_name': 'London, UK',
            'latitude': 91.0,  # Invalid: should be between -90 and 90
            'longitude': -0.1278,
            'timestamp': '2025-09-04T12:00:00Z',
            'temperature': 18.5,
            'humidity': 72
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertTrue(is_valid)  # Should still be valid, just with warnings
        self.assertGreater(len(self.validator.validation_warnings), 0)

    def test_invalid_temperature_range(self):
        """Test validation of weather record with unrealistic temperature."""
        invalid_record = {
            'location_name': 'London, UK',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'timestamp': '2025-09-04T12:00:00Z',
            'temperature': -200.0,  # Unrealistic temperature
            'humidity': 72
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertTrue(is_valid)  # Should still be valid, just with warnings
        self.assertGreater(len(self.validator.validation_warnings), 0)

    def test_temperature_consistency_check(self):
        """Test validation of temperature min/max consistency."""
        invalid_record = {
            'location_name': 'London, UK',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'timestamp': '2025-09-04T12:00:00Z',
            'temperature': 15.0,
            'temperature_min': 20.0,  # Min > max
            'temperature_max': 10.0,
            'humidity': 72
        }

        is_valid = self.validator.validate_record(invalid_record)
        self.assertFalse(is_valid)
        self.assertGreater(len(self.validator.validation_errors), 0)


class TestMissingValueHandler(unittest.TestCase):
    """Test cases for missing value handling."""

    def setUp(self):
        self.handler = MissingValueHandler()

    def test_drop_missing_strategy(self):
        """Test drop missing values strategy."""
        data = [
            {'name': 'Alice', 'age': 25, 'city': 'London'},
            {'name': 'Bob', 'age': None, 'city': 'Paris'},
            {'name': 'Charlie', 'age': 30, 'city': None}
        ]

        result = self.handler.handle_missing_values(data, 'drop', ['age', 'city'])
        self.assertEqual(len(result), 1)  # Only Alice's record should remain
        self.assertEqual(result[0]['name'], 'Alice')

    def test_mean_fill_strategy(self):
        """Test mean fill strategy."""
        data = [
            {'name': 'Alice', 'score': 85},
            {'name': 'Bob', 'score': None},
            {'name': 'Charlie', 'score': 95}
        ]

        result = self.handler.handle_missing_values(data, 'mean', ['score'])
        self.assertEqual(len(result), 3)
        # Bob's score should be filled with mean (90.0)
        bob_record = next(r for r in result if r['name'] == 'Bob')
        self.assertEqual(bob_record['score'], 90.0)

    def test_forward_fill_strategy(self):
        """Test forward fill strategy."""
        data = [
            {'time': 1, 'value': 10},
            {'time': 2, 'value': None},
            {'time': 3, 'value': None},
            {'time': 4, 'value': 20}
        ]

        result = self.handler.handle_missing_values(data, 'forward_fill', ['value'])
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1]['value'], 10)  # Forward filled
        self.assertEqual(result[2]['value'], 10)  # Forward filled
        self.assertEqual(result[3]['value'], 20)  # Original value


class TestOutlierDetector(unittest.TestCase):
    """Test cases for outlier detection."""

    def setUp(self):
        self.detector = OutlierDetector()

    def test_iqr_outlier_detection(self):
        """Test IQR-based outlier detection."""
        data = [
            {'id': 1, 'value': 10},
            {'id': 2, 'value': 12},
            {'id': 3, 'value': 11},
            {'id': 4, 'value': 13},
            {'id': 5, 'value': 100}  # Outlier
        ]

        result = self.detector.detect_outliers(data, 'iqr', ['value'])
        self.assertEqual(result['total_outliers'], 1)
        self.assertEqual(len(result['outliers']), 1)
        self.assertEqual(result['outliers'][0]['index'], 4)

    def test_zscore_outlier_detection(self):
        """Test Z-score-based outlier detection."""
        data = [
            {'id': 1, 'value': 10},
            {'id': 2, 'value': 11},
            {'id': 3, 'value': 10},
            {'id': 4, 'value': 12},
            {'id': 5, 'value': 50}  # Outlier
        ]

        result = self.detector.detect_outliers(data, 'zscore', ['value'], threshold=2.0)
        self.assertGreater(result['total_outliers'], 0)


class TestDataNormalizer(unittest.TestCase):
    """Test cases for data normalization."""

    def setUp(self):
        self.normalizer = DataNormalizer()

    def test_timestamp_normalization(self):
        """Test timestamp normalization."""
        data = [
            {'id': 1, 'timestamp': '2025-09-04 12:00:00'},
            {'id': 2, 'timestamp': '2025-09-04T13:30:00Z'},
            {'id': 3, 'timestamp': '2025/09/04 14:00:00'}
        ]

        result = self.normalizer.normalize_timestamps(data)
        self.assertEqual(len(result), 3)
        # All timestamps should be in ISO format
        for record in result:
            self.assertTrue(record['timestamp'].endswith('Z') or '+' in record['timestamp'])

    def test_numeric_normalization(self):
        """Test numeric field normalization."""
        data = [
            {'id': 1, 'temperature': '18.5', 'humidity': 72},
            {'id': 2, 'temperature': 19.2, 'humidity': '68%'},
            {'id': 3, 'temperature': '20.0 C', 'humidity': 75}
        ]

        result = self.normalizer.normalize_numeric_fields(data, ['temperature', 'humidity'])
        self.assertEqual(len(result), 3)
        for record in result:
            self.assertIsInstance(record['temperature'], float)
            self.assertIsInstance(record['humidity'], (int, float))

    def test_coordinate_normalization(self):
        """Test coordinate normalization."""
        data = [
            {'location': 'London', 'lat': 51.5074, 'lon': -0.1278},
            {'location': 'Paris', 'lat': 48.8566, 'lon': 2.3522}
        ]

        result = self.normalizer.normalize_coordinates(data)
        self.assertEqual(len(result), 2)
        # Coordinates should be rounded to 6 decimal places
        self.assertEqual(result[0]['lat'], 51.5074)
        self.assertEqual(result[0]['lon'], -0.1278)


class TestDataQualityPipeline(unittest.TestCase):
    """Test cases for the data quality pipeline."""

    def setUp(self):
        self.polymarket_data = [
            {
                'event_title': 'Will it rain in London tomorrow?',
                'market_id': '0x1234567890abcdef',
                'outcome_name': 'Yes',
                'probability': 0.65,
                'volume': 10000.50,
                'timestamp': '2025-09-04T12:00:00Z',
                'scraped_at': '2025-09-04T12:30:00Z'
            }
        ]

        self.weather_data = [
            {
                'location_name': 'London, UK',
                'latitude': 51.5074,
                'longitude': -0.1278,
                'timestamp': '2025-09-04T12:00:00Z',
                'temperature': 18.5,
                'humidity': 72,
                'wind_speed': 8.5,
                'pressure': 1013.2
            }
        ]

    @patch('data_quality_pipeline.process_polymarket_data')
    def test_polymarket_pipeline_processing(self, mock_process):
        """Test Polymarket data quality pipeline processing."""
        mock_process.return_value = {
            'success': True,
            'quality_score': 95.0,
            'processed_records': 1,
            'cleaned_data': self.polymarket_data
        }

        result = process_polymarket_data(self.polymarket_data)
        self.assertTrue(result['success'])
        self.assertEqual(result['quality_score'], 95.0)

    @patch('data_quality_pipeline.process_weather_data')
    def test_weather_pipeline_processing(self, mock_process):
        """Test weather data quality pipeline processing."""
        mock_process.return_value = {
            'success': True,
            'quality_score': 92.0,
            'processed_records': 1,
            'cleaned_data': self.weather_data
        }

        result = process_weather_data(self.weather_data)
        self.assertTrue(result['success'])
        self.assertEqual(result['quality_score'], 92.0)

    def test_pipeline_creation(self):
        """Test pipeline creation for different data sources."""
        poly_pipeline = DataQualityPipeline(DataSource.POLYMARKET)
        self.assertEqual(poly_pipeline.source, DataSource.POLYMARKET)

        weather_pipeline = DataQualityPipeline(DataSource.WEATHER)
        self.assertEqual(weather_pipeline.source, DataSource.WEATHER)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def test_validate_polymarket_data_function(self):
        """Test the validate_polymarket_data convenience function."""
        data = [
            {
                'event_title': 'Test Event',
                'market_id': '0x123',
                'outcome_name': 'Yes',
                'probability': 0.5,
                'timestamp': '2025-09-04T12:00:00Z',
                'scraped_at': '2025-09-04T12:30:00Z'
            }
        ]

        result = validate_polymarket_data(data)
        self.assertIn('total_records', result)
        self.assertIn('valid_records', result)
        self.assertIn('invalid_records', result)

    def test_validate_weather_data_function(self):
        """Test the validate_weather_data convenience function."""
        data = [
            {
                'location_name': 'Test Location',
                'timestamp': '2025-09-04T12:00:00Z',
                'temperature': 20.0
            }
        ]

        result = validate_weather_data(data)
        self.assertIn('total_records', result)
        self.assertIn('valid_records', result)
        self.assertIn('invalid_records', result)

    def test_clean_polymarket_data_function(self):
        """Test the clean_polymarket_data convenience function."""
        data = [
            {
                'event_title': 'Test Event',
                'market_id': '0x123',
                'outcome_name': 'Yes',
                'probability': 0.5,
                'volume': None,  # Missing value
                'timestamp': '2025-09-04T12:00:00Z',
                'scraped_at': '2025-09-04T12:30:00Z'
            }
        ]

        result = clean_polymarket_data(data)
        self.assertIn('cleaned_data', result)
        self.assertIn('original_count', result)
        self.assertIn('cleaned_count', result)

    def test_clean_weather_data_function(self):
        """Test the clean_weather_data convenience function."""
        data = [
            {
                'location_name': 'Test Location',
                'timestamp': '2025-09-04T12:00:00Z',
                'temperature': 20.0,
                'humidity': None  # Missing value
            }
        ]

        result = clean_weather_data(data)
        self.assertIn('cleaned_data', result)
        self.assertIn('original_count', result)
        self.assertIn('cleaned_count', result)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)

    # Run the tests
    unittest.main(verbosity=2)