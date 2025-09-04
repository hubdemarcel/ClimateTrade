#!/usr/bin/env python3
"""
Data Cleaning Module

This module provides comprehensive data cleaning utilities for Polymarket and weather data.
Handles missing values, normalization, outlier detection, and data consistency.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timezone
from statistics import mean, median, stdev
import re
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class DataCleaner:
    """Base class for data cleaning operations."""

    def __init__(self):
        self.cleaning_stats = defaultdict(int)

    def reset_stats(self):
        """Reset cleaning statistics."""
        self.cleaning_stats = defaultdict(int)

    def log_cleaning_action(self, action: str, field: str = None):
        """Log a cleaning action."""
        key = f"{action}_{field}" if field else action
        self.cleaning_stats[key] += 1
        logger.debug(f"Cleaning action: {action}" + (f" on field {field}" if field else ""))

    def get_cleaning_summary(self) -> Dict:
        """Get summary of cleaning operations performed."""
        return dict(self.cleaning_stats)


class MissingValueHandler:
    """Handles missing values in data."""

    def __init__(self):
        self.strategies = {
            'drop': self._drop_missing,
            'mean': self._fill_with_mean,
            'median': self._fill_with_median,
            'mode': self._fill_with_mode,
            'forward_fill': self._forward_fill,
            'backward_fill': self._backward_fill,
            'interpolate': self._interpolate,
            'constant': self._fill_with_constant
        }

    def handle_missing_values(self, data: List[Dict], strategy: str = 'drop',
                            fields: List[str] = None, **kwargs) -> List[Dict]:
        """Apply missing value handling strategy to data."""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}")

        return self.strategies[strategy](data, fields or [], **kwargs)

    def _drop_missing(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Drop records with missing values in specified fields."""
        cleaned_data = []
        for record in data:
            has_missing = any(record.get(field) is None or
                            (isinstance(record.get(field), str) and not record.get(field).strip())
                            for field in fields)
            if not has_missing:
                cleaned_data.append(record)
        return cleaned_data

    def _fill_with_mean(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Fill missing values with mean of the field."""
        # Calculate means for each field
        field_means = {}
        for field in fields:
            values = [r[field] for r in data if r.get(field) is not None and
                     isinstance(r[field], (int, float))]
            if values:
                field_means[field] = mean(values)

        # Fill missing values
        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in fields:
                if cleaned_record.get(field) is None or \
                   (isinstance(cleaned_record.get(field), str) and not cleaned_record.get(field).strip()):
                    if field in field_means:
                        cleaned_record[field] = field_means[field]
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def _fill_with_median(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Fill missing values with median of the field."""
        field_medians = {}
        for field in fields:
            values = [r[field] for r in data if r.get(field) is not None and
                     isinstance(r[field], (int, float))]
            if values:
                field_medians[field] = median(values)

        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in fields:
                if cleaned_record.get(field) is None or \
                   (isinstance(cleaned_record.get(field), str) and not cleaned_record.get(field).strip()):
                    if field in field_medians:
                        cleaned_record[field] = field_medians[field]
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def _fill_with_mode(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Fill missing values with mode (most frequent value) of the field."""
        field_modes = {}
        for field in fields:
            values = [r[field] for r in data if r.get(field) is not None]
            if values:
                # Find most common value
                from collections import Counter
                field_modes[field] = Counter(values).most_common(1)[0][0]

        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in fields:
                if cleaned_record.get(field) is None or \
                   (isinstance(cleaned_record.get(field), str) and not cleaned_record.get(field).strip()):
                    if field in field_modes:
                        cleaned_record[field] = field_modes[field]
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def _forward_fill(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Forward fill missing values (use last known value)."""
        last_values = {}
        cleaned_data = []

        for record in data:
            cleaned_record = record.copy()
            for field in fields:
                if cleaned_record.get(field) is None or \
                   (isinstance(cleaned_record.get(field), str) and not cleaned_record.get(field).strip()):
                    if field in last_values:
                        cleaned_record[field] = last_values[field]
                else:
                    last_values[field] = cleaned_record[field]
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def _backward_fill(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Backward fill missing values (use next known value)."""
        # Reverse the data, forward fill, then reverse back
        reversed_data = list(reversed(data))
        forward_filled = self._forward_fill(reversed_data, fields)
        return list(reversed(forward_filled))

    def _interpolate(self, data: List[Dict], fields: List[str], **kwargs) -> List[Dict]:
        """Interpolate missing values using linear interpolation."""
        # This is a simplified version - for time series data, more sophisticated
        # interpolation methods would be needed
        return self._fill_with_mean(data, fields)

    def _fill_with_constant(self, data: List[Dict], fields: List[str], constant: Any = 0) -> List[Dict]:
        """Fill missing values with a constant value."""
        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in fields:
                if cleaned_record.get(field) is None or \
                   (isinstance(cleaned_record.get(field), str) and not cleaned_record.get(field).strip()):
                    cleaned_record[field] = constant
            cleaned_data.append(cleaned_record)

        return cleaned_data


class OutlierDetector:
    """Detects and handles outliers in data."""

    def __init__(self):
        self.methods = {
            'iqr': self._iqr_method,
            'zscore': self._zscore_method,
            'isolation_forest': self._isolation_forest_method,
            'percentile': self._percentile_method
        }

    def detect_outliers(self, data: List[Dict], method: str = 'iqr',
                       fields: List[str] = None, **kwargs) -> Dict:
        """Detect outliers using specified method."""
        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}")

        return self.methods[method](data, fields or [], **kwargs)

    def _iqr_method(self, data: List[Dict], fields: List[str], multiplier: float = 1.5) -> Dict:
        """Detect outliers using Interquartile Range (IQR) method."""
        outliers = []
        bounds = {}

        for field in fields:
            values = [r[field] for r in data if r.get(field) is not None and
                     isinstance(r[field], (int, float))]

            if len(values) < 4:  # Need at least 4 values for quartiles
                continue

            values.sort()
            q1 = values[len(values) // 4]
            q3 = values[3 * len(values) // 4]
            iqr = q3 - q1

            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr

            bounds[field] = {'lower': lower_bound, 'upper': upper_bound}

            # Find outliers
            for i, record in enumerate(data):
                value = record.get(field)
                if value is not None and isinstance(value, (int, float)):
                    if value < lower_bound or value > upper_bound:
                        outliers.append({
                            'index': i,
                            'field': field,
                            'value': value,
                            'bounds': (lower_bound, upper_bound)
                        })

        return {
            'outliers': outliers,
            'bounds': bounds,
            'method': 'iqr',
            'total_outliers': len(outliers)
        }

    def _zscore_method(self, data: List[Dict], fields: List[str], threshold: float = 3.0) -> Dict:
        """Detect outliers using Z-score method."""
        outliers = []
        stats = {}

        for field in fields:
            values = [r[field] for r in data if r.get(field) is not None and
                     isinstance(r[field], (int, float))]

            if len(values) < 2:  # Need at least 2 values for standard deviation
                continue

            mean_val = mean(values)
            std_val = stdev(values)

            stats[field] = {'mean': mean_val, 'std': std_val}

            # Find outliers
            for i, record in enumerate(data):
                value = record.get(field)
                if value is not None and isinstance(value, (int, float)) and std_val > 0:
                    z_score = abs((value - mean_val) / std_val)
                    if z_score > threshold:
                        outliers.append({
                            'index': i,
                            'field': field,
                            'value': value,
                            'z_score': z_score,
                            'threshold': threshold
                        })

        return {
            'outliers': outliers,
            'stats': stats,
            'method': 'zscore',
            'total_outliers': len(outliers)
        }

    def _isolation_forest_method(self, data: List[Dict], fields: List[str], **kwargs) -> Dict:
        """Detect outliers using Isolation Forest (placeholder for advanced implementation)."""
        # This would require scikit-learn, simplified version for now
        logger.warning("Isolation Forest method not fully implemented - using IQR as fallback")
        return self._iqr_method(data, fields, **kwargs)

    def _percentile_method(self, data: List[Dict], fields: List[str],
                          lower_percentile: float = 5.0, upper_percentile: float = 95.0) -> Dict:
        """Detect outliers using percentile method."""
        outliers = []
        bounds = {}

        for field in fields:
            values = [r[field] for r in data if r.get(field) is not None and
                     isinstance(r[field], (int, float))]

            if len(values) < 10:  # Need reasonable sample size
                continue

            values.sort()
            lower_idx = int(len(values) * lower_percentile / 100)
            upper_idx = int(len(values) * upper_percentile / 100)

            lower_bound = values[lower_idx]
            upper_bound = values[upper_idx]

            bounds[field] = {'lower': lower_bound, 'upper': upper_bound}

            # Find outliers
            for i, record in enumerate(data):
                value = record.get(field)
                if value is not None and isinstance(value, (int, float)):
                    if value < lower_bound or value > upper_bound:
                        outliers.append({
                            'index': i,
                            'field': field,
                            'value': value,
                            'bounds': (lower_bound, upper_bound)
                        })

        return {
            'outliers': outliers,
            'bounds': bounds,
            'method': 'percentile',
            'total_outliers': len(outliers)
        }


class DataNormalizer:
    """Normalizes data formats and values."""

    def __init__(self):
        pass

    def normalize_timestamps(self, data: List[Dict], timestamp_fields: List[str] = None) -> List[Dict]:
        """Normalize timestamp fields to ISO 8601 UTC format."""
        if timestamp_fields is None:
            timestamp_fields = ['timestamp', 'scraped_at', 'created_at']

        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in timestamp_fields:
                if field in cleaned_record and cleaned_record[field]:
                    try:
                        # Try to parse various timestamp formats
                        timestamp_str = str(cleaned_record[field])
                        dt = self._parse_timestamp(timestamp_str)
                        if dt:
                            cleaned_record[field] = dt.isoformat()
                    except Exception as e:
                        logger.warning(f"Could not normalize timestamp {cleaned_record[field]}: {e}")
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string into datetime object."""
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        return None

    def normalize_numeric_fields(self, data: List[Dict], numeric_fields: List[str] = None) -> List[Dict]:
        """Normalize numeric fields to proper types and handle invalid values."""
        if numeric_fields is None:
            numeric_fields = ['probability', 'volume', 'temperature', 'humidity',
                            'wind_speed', 'pressure', 'latitude', 'longitude']

        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in numeric_fields:
                if field in cleaned_record and cleaned_record[field] is not None:
                    try:
                        value = cleaned_record[field]
                        if isinstance(value, str):
                            # Remove common non-numeric characters
                            clean_value = re.sub(r'[^\d.-]', '', value.strip())
                            if clean_value:
                                cleaned_record[field] = float(clean_value)
                            else:
                                cleaned_record[field] = None
                        elif isinstance(value, (int, float)):
                            cleaned_record[field] = float(value)
                        else:
                            cleaned_record[field] = None
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {field} value {cleaned_record[field]} to numeric")
                        cleaned_record[field] = None
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def normalize_text_fields(self, data: List[Dict], text_fields: List[str] = None) -> List[Dict]:
        """Normalize text fields (trim whitespace, handle encoding issues)."""
        if text_fields is None:
            text_fields = ['event_title', 'event_url', 'market_id', 'outcome_name',
                         'location_name', 'weather_description']

        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for field in text_fields:
                if field in cleaned_record and cleaned_record[field]:
                    try:
                        if isinstance(cleaned_record[field], str):
                            # Trim whitespace and normalize
                            cleaned_record[field] = cleaned_record[field].strip()
                        else:
                            cleaned_record[field] = str(cleaned_record[field]).strip()
                    except Exception as e:
                        logger.warning(f"Could not normalize text field {field}: {e}")
                        cleaned_record[field] = ""
            cleaned_data.append(cleaned_record)

        return cleaned_data

    def normalize_coordinates(self, data: List[Dict]) -> List[Dict]:
        """Normalize latitude and longitude coordinates."""
        cleaned_data = []
        for record in data:
            cleaned_record = record.copy()
            for coord_field in ['latitude', 'longitude']:
                if coord_field in cleaned_record and cleaned_record[coord_field] is not None:
                    try:
                        value = float(cleaned_record[coord_field])
                        # Ensure coordinates are within valid ranges
                        if coord_field == 'latitude':
                            value = max(-90.0, min(90.0, value))
                        elif coord_field == 'longitude':
                            value = max(-180.0, min(180.0, value))
                        cleaned_record[coord_field] = round(value, 6)  # Round to 6 decimal places
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid coordinate value for {coord_field}: {cleaned_record[coord_field]}")
                        cleaned_record[coord_field] = None
            cleaned_data.append(cleaned_record)

        return cleaned_data


class PolymarketDataCleaner(DataCleaner):
    """Data cleaner specifically for Polymarket data."""

    def __init__(self):
        super().__init__()
        self.missing_handler = MissingValueHandler()
        self.outlier_detector = OutlierDetector()
        self.normalizer = DataNormalizer()

    def clean_data(self, data: List[Dict], config: Dict = None) -> Dict:
        """Clean Polymarket data with comprehensive cleaning pipeline."""
        if config is None:
            config = self._get_default_config()

        cleaned_data = data.copy()
        cleaning_steps = []

        # Step 1: Normalize data formats
        logger.info("Normalizing Polymarket data formats")
        cleaned_data = self.normalizer.normalize_timestamps(cleaned_data)
        cleaned_data = self.normalizer.normalize_numeric_fields(cleaned_data)
        cleaned_data = self.normalizer.normalize_text_fields(cleaned_data)
        cleaning_steps.append("format_normalization")

        # Step 2: Handle missing values
        if config.get('handle_missing', True):
            strategy = config.get('missing_strategy', 'drop')
            fields = config.get('missing_fields', ['probability', 'volume'])
            logger.info(f"Handling missing values using {strategy} strategy")
            cleaned_data = self.missing_handler.handle_missing_values(
                cleaned_data, strategy, fields
            )
            cleaning_steps.append(f"missing_values_{strategy}")

        # Step 3: Detect outliers
        if config.get('detect_outliers', True):
            method = config.get('outlier_method', 'iqr')
            fields = config.get('outlier_fields', ['probability', 'volume'])
            logger.info(f"Detecting outliers using {method} method")
            outlier_results = self.outlier_detector.detect_outliers(
                cleaned_data, method, fields
            )
            cleaning_steps.append(f"outlier_detection_{method}")

            # Optionally remove outliers
            if config.get('remove_outliers', False):
                outlier_indices = {o['index'] for o in outlier_results['outliers']}
                cleaned_data = [r for i, r in enumerate(cleaned_data) if i not in outlier_indices]
                cleaning_steps.append("outlier_removal")

        return {
            'cleaned_data': cleaned_data,
            'original_count': len(data),
            'cleaned_count': len(cleaned_data),
            'cleaning_steps': cleaning_steps,
            'config': config
        }

    def _get_default_config(self) -> Dict:
        """Get default cleaning configuration for Polymarket data."""
        return {
            'handle_missing': True,
            'missing_strategy': 'mean',
            'missing_fields': ['probability', 'volume'],
            'detect_outliers': True,
            'outlier_method': 'iqr',
            'outlier_fields': ['probability', 'volume'],
            'remove_outliers': False  # Only detect by default
        }


class WeatherDataCleaner(DataCleaner):
    """Data cleaner specifically for weather data."""

    def __init__(self):
        super().__init__()
        self.missing_handler = MissingValueHandler()
        self.outlier_detector = OutlierDetector()
        self.normalizer = DataNormalizer()

    def clean_data(self, data: List[Dict], config: Dict = None) -> Dict:
        """Clean weather data with comprehensive cleaning pipeline."""
        if config is None:
            config = self._get_default_config()

        cleaned_data = data.copy()
        cleaning_steps = []

        # Step 1: Normalize data formats
        logger.info("Normalizing weather data formats")
        cleaned_data = self.normalizer.normalize_timestamps(cleaned_data)
        cleaned_data = self.normalizer.normalize_numeric_fields(cleaned_data)
        cleaned_data = self.normalizer.normalize_text_fields(cleaned_data)
        cleaned_data = self.normalizer.normalize_coordinates(cleaned_data)
        cleaning_steps.append("format_normalization")

        # Step 2: Handle missing values
        if config.get('handle_missing', True):
            strategy = config.get('missing_strategy', 'interpolate')
            fields = config.get('missing_fields', ['temperature', 'humidity', 'wind_speed'])
            logger.info(f"Handling missing values using {strategy} strategy")
            cleaned_data = self.missing_handler.handle_missing_values(
                cleaned_data, strategy, fields
            )
            cleaning_steps.append(f"missing_values_{strategy}")

        # Step 3: Detect outliers
        if config.get('detect_outliers', True):
            method = config.get('outlier_method', 'zscore')
            fields = config.get('outlier_fields', ['temperature', 'humidity', 'pressure', 'wind_speed'])
            logger.info(f"Detecting outliers using {method} method")
            outlier_results = self.outlier_detector.detect_outliers(
                cleaned_data, method, fields
            )
            cleaning_steps.append(f"outlier_detection_{method}")

            # Optionally remove outliers
            if config.get('remove_outliers', False):
                outlier_indices = {o['index'] for o in outlier_results['outliers']}
                cleaned_data = [r for i, r in enumerate(cleaned_data) if i not in outlier_indices]
                cleaning_steps.append("outlier_removal")

        return {
            'cleaned_data': cleaned_data,
            'original_count': len(data),
            'cleaned_count': len(cleaned_data),
            'cleaning_steps': cleaning_steps,
            'config': config
        }

    def _get_default_config(self) -> Dict:
        """Get default cleaning configuration for weather data."""
        return {
            'handle_missing': True,
            'missing_strategy': 'interpolate',
            'missing_fields': ['temperature', 'humidity', 'wind_speed', 'pressure'],
            'detect_outliers': True,
            'outlier_method': 'zscore',
            'outlier_fields': ['temperature', 'humidity', 'pressure', 'wind_speed'],
            'remove_outliers': False  # Only detect by default
        }


# Convenience functions
def clean_polymarket_data(data: List[Dict], config: Dict = None) -> Dict:
    """Convenience function to clean Polymarket data."""
    cleaner = PolymarketDataCleaner()
    return cleaner.clean_data(data, config)


def clean_weather_data(data: List[Dict], config: Dict = None) -> Dict:
    """Convenience function to clean weather data."""
    cleaner = WeatherDataCleaner()
    return cleaner.clean_data(data, config)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test Polymarket cleaning
    polymarket_sample = [
        {
            'event_title': 'Will it rain in London tomorrow?',
            'market_id': '0x1234567890abcdef',
            'outcome_name': 'Yes',
            'probability': 0.65,
            'volume': None,  # Missing value
            'timestamp': '2025-09-04T12:00:00Z',
            'scraped_at': '2025-09-04T12:30:00Z'
        },
        {
            'event_title': 'Will temperature exceed 20C?',
            'market_id': '0xabcdef1234567890',
            'outcome_name': 'No',
            'probability': 0.45,
            'volume': 5000.0,
            'timestamp': '2025-09-04T12:00:00Z',
            'scraped_at': '2025-09-04T12:30:00Z'
        }
    ]

    result = clean_polymarket_data(polymarket_sample)
    print(f"Polymarket cleaning: {result['original_count']} -> {result['cleaned_count']} records")
    print(f"Cleaning steps: {result['cleaning_steps']}")

    # Test weather cleaning
    weather_sample = [
        {
            'location_name': 'London, UK',
            'latitude': 51.5074,
            'longitude': -0.1278,
            'timestamp': '2025-09-04T12:00:00Z',
            'temperature': 18.5,
            'humidity': None,  # Missing value
            'wind_speed': 8.5,
            'pressure': 1013.2
        }
    ]

    result = clean_weather_data(weather_sample)
    print(f"Weather cleaning: {result['original_count']} -> {result['cleaned_count']} records")
    print(f"Cleaning steps: {result['cleaning_steps']}")