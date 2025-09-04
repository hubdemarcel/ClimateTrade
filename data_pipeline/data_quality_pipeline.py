#!/usr/bin/env python3
"""
Data Quality Pipeline Module

This module provides an automated data quality pipeline that integrates validation,
cleaning, and quality assurance processes for Polymarket and weather data.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import json
import csv
from dataclasses import dataclass, asdict
from enum import Enum

from .data_validation import validate_polymarket_data, validate_weather_data
from .data_cleaning import clean_polymarket_data, clean_weather_data

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enumeration of supported data sources."""
    POLYMARKET = "polymarket"
    WEATHER = "weather"

class PipelineStage(Enum):
    """Enumeration of pipeline stages."""
    VALIDATION = "validation"
    CLEANING = "cleaning"
    QUALITY_CHECK = "quality_check"
    REPORTING = "reporting"

@dataclass
class DataQualityReport:
    """Data quality report structure."""
    source: str
    total_records: int
    valid_records: int
    invalid_records: int
    cleaned_records: int
    validation_errors: int
    validation_warnings: int
    cleaning_actions: Dict[str, int]
    processing_time: float
    timestamp: str
    pipeline_stages: List[str]
    quality_score: float  # 0-100 scale

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

class DataQualityPipeline:
    """Automated data quality pipeline for processing data through validation and cleaning stages."""

    def __init__(self, source: DataSource, config: Dict = None):
        self.source = source
        self.config = config or self._get_default_config()
        self.reports = []
        self.current_report = None

        # Initialize pipeline components
        self._setup_pipeline()

    def _setup_pipeline(self):
        """Setup pipeline components based on data source."""
        if self.source == DataSource.POLYMARKET:
            self.validator = lambda data: validate_polymarket_data(data)
            self.cleaner = lambda data, config: clean_polymarket_data(data, config)
        elif self.source == DataSource.WEATHER:
            self.validator = lambda data: validate_weather_data(data)
            self.cleaner = lambda data, config: clean_weather_data(data, config)
        else:
            raise ValueError(f"Unsupported data source: {self.source}")

    def _get_default_config(self) -> Dict:
        """Get default pipeline configuration."""
        base_config = {
            'fail_on_validation_error': False,
            'fail_on_cleaning_error': False,
            'generate_reports': True,
            'report_format': 'json',
            'log_level': 'INFO',
            'quality_threshold': 80.0,  # Minimum quality score to pass
        }

        if self.source == DataSource.POLYMARKET:
            base_config.update({
                'validation_config': {},
                'cleaning_config': {
                    'handle_missing': True,
                    'missing_strategy': 'mean',
                    'detect_outliers': True,
                    'remove_outliers': False
                }
            })
        elif self.source == DataSource.WEATHER:
            base_config.update({
                'validation_config': {},
                'cleaning_config': {
                    'handle_missing': True,
                    'missing_strategy': 'interpolate',
                    'detect_outliers': True,
                    'remove_outliers': False
                }
            })

        return base_config

    def process_data(self, data: List[Dict], metadata: Dict = None) -> Dict:
        """Process data through the complete quality pipeline."""
        start_time = datetime.now()
        pipeline_stages = []
        quality_score = 100.0

        try:
            logger.info(f"Starting data quality pipeline for {self.source.value}")
            logger.info(f"Processing {len(data)} records")

            # Stage 1: Validation
            logger.info("Stage 1: Data Validation")
            validation_result = self._run_validation(data)
            pipeline_stages.append(PipelineStage.VALIDATION.value)

            if validation_result['total_records'] > 0:
                validation_quality = (validation_result['valid_records'] / validation_result['total_records']) * 100
                quality_score = min(quality_score, validation_quality)

            # Check if we should fail on validation errors
            if self.config.get('fail_on_validation_error', False) and validation_result['invalid_records'] > 0:
                raise ValueError(f"Validation failed: {validation_result['invalid_records']} invalid records")

            # Stage 2: Cleaning
            logger.info("Stage 2: Data Cleaning")
            cleaning_result = self._run_cleaning(data, validation_result)
            pipeline_stages.append(PipelineStage.CLEANING.value)

            # Stage 3: Quality Check
            logger.info("Stage 3: Quality Assurance")
            quality_result = self._run_quality_check(cleaning_result)
            pipeline_stages.append(PipelineStage.QUALITY_CHECK.value)

            # Calculate final quality score
            if cleaning_result['original_count'] > 0:
                cleaning_efficiency = (cleaning_result['cleaned_count'] / cleaning_result['original_count']) * 100
                quality_score = min(quality_score, cleaning_efficiency)

            # Stage 4: Reporting
            if self.config.get('generate_reports', True):
                logger.info("Stage 4: Report Generation")
                report = self._generate_report(
                    data, validation_result, cleaning_result, quality_result,
                    start_time, pipeline_stages, quality_score
                )
                pipeline_stages.append(PipelineStage.REPORTING.value)
                self.reports.append(report)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                'success': True,
                'source': self.source.value,
                'original_records': len(data),
                'processed_records': cleaning_result['cleaned_count'],
                'quality_score': round(quality_score, 2),
                'processing_time': processing_time,
                'pipeline_stages': pipeline_stages,
                'validation_result': validation_result,
                'cleaning_result': cleaning_result,
                'quality_result': quality_result,
                'cleaned_data': cleaning_result['cleaned_data']
            }

            # Check quality threshold
            if quality_score < self.config.get('quality_threshold', 80.0):
                logger.warning(f"Quality score {quality_score} below threshold {self.config['quality_threshold']}")
                if self.config.get('fail_on_low_quality', False):
                    result['success'] = False
                    result['error'] = f"Quality score {quality_score} below threshold"

            logger.info(f"Pipeline completed successfully. Quality score: {quality_score}")
            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Pipeline failed: {e}")

            return {
                'success': False,
                'source': self.source.value,
                'error': str(e),
                'processing_time': processing_time,
                'pipeline_stages': pipeline_stages
            }

    def _run_validation(self, data: List[Dict]) -> Dict:
        """Run validation on the data."""
        try:
            validation_result = self.validator(data)
            logger.info(f"Validation completed: {validation_result['valid_records']}/{validation_result['total_records']} records valid")
            return validation_result
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise

    def _run_cleaning(self, original_data: List[Dict], validation_result: Dict) -> Dict:
        """Run cleaning on the data."""
        try:
            # Use only valid records for cleaning if validation was performed
            data_to_clean = original_data
            if 'results' in validation_result:
                # Filter out invalid records if needed
                valid_indices = [r['index'] for r in validation_result['results'] if r['is_valid']]
                data_to_clean = [original_data[i] for i in valid_indices]

            cleaning_config = self.config.get('cleaning_config', {})
            cleaning_result = self.cleaner(data_to_clean, cleaning_config)

            logger.info(f"Cleaning completed: {cleaning_result['original_count']} -> {cleaning_result['cleaned_count']} records")
            return cleaning_result
        except Exception as e:
            logger.error(f"Cleaning failed: {e}")
            raise

    def _run_quality_check(self, cleaning_result: Dict) -> Dict:
        """Run quality assurance checks on cleaned data."""
        cleaned_data = cleaning_result['cleaned_data']

        quality_metrics = {
            'total_records': len(cleaned_data),
            'completeness_score': self._calculate_completeness(cleaned_data),
            'consistency_score': self._calculate_consistency(cleaned_data),
            'accuracy_score': self._calculate_accuracy(cleaned_data),
            'timeliness_score': self._calculate_timeliness(cleaned_data)
        }

        # Calculate overall quality score
        weights = {'completeness': 0.3, 'consistency': 0.3, 'accuracy': 0.3, 'timeliness': 0.1}
        overall_score = sum(quality_metrics[metric] * weights[metric.split('_')[0]]
                          for metric in quality_metrics.keys() if metric.endswith('_score'))

        quality_metrics['overall_quality_score'] = overall_score

        logger.info(f"Quality check completed. Overall score: {overall_score:.2f}")
        return quality_metrics

    def _calculate_completeness(self, data: List[Dict]) -> float:
        """Calculate data completeness score (0-100)."""
        if not data:
            return 0.0

        total_fields = 0
        filled_fields = 0

        for record in data:
            for key, value in record.items():
                total_fields += 1
                if value is not None and (not isinstance(value, str) or value.strip()):
                    filled_fields += 1

        return (filled_fields / total_fields * 100) if total_fields > 0 else 0.0

    def _calculate_consistency(self, data: List[Dict]) -> float:
        """Calculate data consistency score (0-100)."""
        if not data:
            return 100.0

        # Check for consistent data types in same fields across records
        consistency_score = 100.0
        field_types = {}

        for record in data:
            for key, value in record.items():
                if key not in field_types:
                    field_types[key] = type(value) if value is not None else None
                elif value is not None:
                    if field_types[key] and type(value) != field_types[key]:
                        consistency_score -= 1  # Penalize type inconsistencies

        return max(0.0, consistency_score)

    def _calculate_accuracy(self, data: List[Dict]) -> float:
        """Calculate data accuracy score (0-100)."""
        # This is a simplified accuracy check - in practice, this would involve
        # more sophisticated validation rules
        if not data:
            return 100.0

        accuracy_score = 100.0

        for record in data:
            # Check for obviously invalid values
            if self.source == DataSource.WEATHER:
                temp = record.get('temperature')
                if temp is not None and isinstance(temp, (int, float)):
                    if not -100 <= temp <= 60:  # Reasonable temperature range
                        accuracy_score -= 0.1

                humidity = record.get('humidity')
                if humidity is not None and isinstance(humidity, (int, float)):
                    if not 0 <= humidity <= 100:
                        accuracy_score -= 0.1

            elif self.source == DataSource.POLYMARKET:
                prob = record.get('probability')
                if prob is not None and isinstance(prob, (int, float)):
                    if not 0 <= prob <= 1:
                        accuracy_score -= 0.1

        return max(0.0, accuracy_score)

    def _calculate_timeliness(self, data: List[Dict]) -> float:
        """Calculate data timeliness score (0-100)."""
        if not data:
            return 100.0

        current_time = datetime.now().timestamp()
        timeliness_score = 100.0

        for record in data:
            timestamp = record.get('timestamp') or record.get('scraped_at')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        # Try to parse timestamp
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        record_time = dt.timestamp()
                    elif isinstance(timestamp, (int, float)):
                        record_time = timestamp
                    else:
                        continue

                    # Penalize older data (more than 24 hours old)
                    age_hours = (current_time - record_time) / 3600
                    if age_hours > 24:
                        timeliness_score -= min(1.0, age_hours / 24)

                except (ValueError, AttributeError):
                    timeliness_score -= 0.5  # Penalize unparseable timestamps

        return max(0.0, timeliness_score)

    def _generate_report(self, original_data: List[Dict], validation_result: Dict,
                        cleaning_result: Dict, quality_result: Dict,
                        start_time: datetime, pipeline_stages: List[str],
                        quality_score: float) -> DataQualityReport:
        """Generate a comprehensive data quality report."""
        report = DataQualityReport(
            source=self.source.value,
            total_records=len(original_data),
            valid_records=validation_result.get('valid_records', 0),
            invalid_records=validation_result.get('invalid_records', 0),
            cleaned_records=cleaning_result.get('cleaned_count', 0),
            validation_errors=sum(len(r.get('errors', [])) for r in validation_result.get('results', [])),
            validation_warnings=sum(len(r.get('warnings', [])) for r in validation_result.get('results', [])),
            cleaning_actions=cleaning_result.get('cleaning_steps', []),
            processing_time=(datetime.now() - start_time).total_seconds(),
            timestamp=datetime.now().isoformat(),
            pipeline_stages=pipeline_stages,
            quality_score=round(quality_score, 2)
        )

        # Save report if configured
        if self.config.get('save_reports', False):
            self._save_report(report)

        return report

    def _save_report(self, report: DataQualityReport):
        """Save report to file."""
        report_dir = Path(self.config.get('report_dir', 'reports'))
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.source.value}_quality_report_{timestamp}"

        if self.config.get('report_format', 'json') == 'json':
            filepath = report_dir / f"{filename}.json"
            with open(filepath, 'w') as f:
                f.write(report.to_json())
        else:
            filepath = report_dir / f"{filename}.txt"
            with open(filepath, 'w') as f:
                f.write(f"Data Quality Report - {self.source.value}\n")
                f.write(f"Generated: {report.timestamp}\n\n")
                f.write(f"Total Records: {report.total_records}\n")
                f.write(f"Valid Records: {report.valid_records}\n")
                f.write(f"Quality Score: {report.quality_score}%\n")

        logger.info(f"Report saved to {filepath}")

    def get_latest_report(self) -> Optional[DataQualityReport]:
        """Get the most recent quality report."""
        return self.reports[-1] if self.reports else None

    def get_all_reports(self) -> List[DataQualityReport]:
        """Get all quality reports."""
        return self.reports.copy()


# Convenience functions for easy usage
def process_polymarket_data(data: List[Dict], config: Dict = None) -> Dict:
    """Process Polymarket data through the quality pipeline."""
    pipeline = DataQualityPipeline(DataSource.POLYMARKET, config)
    return pipeline.process_data(data)

def process_weather_data(data: List[Dict], config: Dict = None) -> Dict:
    """Process weather data through the quality pipeline."""
    pipeline = DataQualityPipeline(DataSource.WEATHER, config)
    return pipeline.process_data(data)

def create_quality_pipeline(source: str, config: Dict = None) -> DataQualityPipeline:
    """Create a data quality pipeline for the specified source."""
    source_enum = DataSource(source.lower())
    return DataQualityPipeline(source_enum, config)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test Polymarket pipeline
    polymarket_sample = [
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

    print("Testing Polymarket Data Quality Pipeline:")
    result = process_polymarket_data(polymarket_sample)
    print(f"Success: {result['success']}")
    print(f"Quality Score: {result['quality_score']}%")
    print(f"Processed Records: {result['processed_records']}")

    # Test weather pipeline
    weather_sample = [
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

    print("\nTesting Weather Data Quality Pipeline:")
    result = process_weather_data(weather_sample)
    print(f"Success: {result['success']}")
    print(f"Quality Score: {result['quality_score']}%")
    print(f"Processed Records: {result['processed_records']}")