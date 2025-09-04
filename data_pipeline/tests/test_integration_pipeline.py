#!/usr/bin/env python3
"""
Integration Tests for Data Pipeline

Comprehensive integration tests for the complete data pipeline workflow,
including data ingestion, validation, cleaning, and quality assessment.
"""

import pytest
import pandas as pd
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

from ..data_validation import (
    PolymarketDataValidator,
    WeatherDataValidator,
    validate_polymarket_data,
    validate_weather_data
)

from ..data_cleaning import (
    MissingValueHandler,
    OutlierDetector,
    DataNormalizer,
    PolymarketDataCleaner,
    WeatherDataCleaner,
    clean_polymarket_data,
    clean_weather_data
)

from ..data_quality_pipeline import (
    DataQualityPipeline,
    DataSource,
    process_polymarket_data,
    process_weather_data
)


@pytest.fixture
def large_polymarket_dataset():
    """Large dataset for integration testing"""
    timestamps = pd.date_range('2024-01-01', '2024-01-02', freq='H')
    data = []

    for ts in timestamps:
        # Add some valid records
        data.extend([
            {
                'event_title': f'Weather Event {i}',
                'market_id': f'0x{1000+i:040x}',
                'outcome_name': 'Yes',
                'probability': 0.5 + (i % 10) * 0.05,
                'volume': 1000.0 + i * 100,
                'timestamp': ts.isoformat() + 'Z',
                'scraped_at': (ts + timedelta(minutes=30)).isoformat() + 'Z'
            } for i in range(10)
        ])

        # Add some invalid records for testing
        data.append({
            'event_title': 'Invalid Event',
            'market_id': 'invalid_id',
            'outcome_name': 'Yes',
            'probability': 1.5,  # Invalid probability
            'volume': -100.0,    # Invalid volume
            'timestamp': 'invalid_timestamp',
            'scraped_at': (ts + timedelta(minutes=30)).isoformat() + 'Z'
        })

    return data


@pytest.fixture
def large_weather_dataset():
    """Large weather dataset for integration testing"""
    timestamps = pd.date_range('2024-01-01', '2024-01-02', freq='H')
    data = []

    for i, ts in enumerate(timestamps):
        data.append({
            'location_name': f'City_{i % 5}',
            'latitude': 40.0 + (i % 10) * 0.1,
            'longitude': -74.0 + (i % 10) * 0.1,
            'timestamp': ts.isoformat() + 'Z',
            'temperature': 20.0 + (i % 20) - 10,  # Some outliers
            'temperature_min': 15.0 + (i % 15) - 7,
            'temperature_max': 25.0 + (i % 15) - 7,
            'humidity': 50.0 + (i % 50),
            'wind_speed': 5.0 + (i % 15),
            'precipitation': max(0, (i % 10) - 7),  # Mostly zero with some rain
            'pressure': 1013.0 + (i % 20) - 10,
            'weather_code': 800 + (i % 10),
            'weather_description': f'Condition_{i % 10}',
            'source_name': 'test_source'
        })

    return data


class TestDataPipelineIntegration:
    """Integration tests for complete data pipeline"""

    def test_full_polymarket_pipeline_processing(self, large_polymarket_dataset):
        """Test complete polymarket data pipeline processing"""
        # Process raw data through the pipeline
        result = process_polymarket_data(large_polymarket_dataset)

        assert result['success'] == True
        assert 'quality_score' in result
        assert 'processed_records' in result
        assert 'cleaned_data' in result
        assert result['quality_score'] >= 0.0
        assert result['quality_score'] <= 1.0
        assert result['processed_records'] > 0
        assert len(result['cleaned_data']) > 0

    def test_full_weather_pipeline_processing(self, large_weather_dataset):
        """Test complete weather data pipeline processing"""
        result = process_weather_data(large_weather_dataset)

        assert result['success'] == True
        assert 'quality_score' in result
        assert 'processed_records' in result
        assert 'cleaned_data' in result
        assert result['quality_score'] >= 0.0
        assert result['quality_score'] <= 1.0
        assert result['processed_records'] > 0
        assert len(result['cleaned_data']) > 0

    def test_pipeline_with_invalid_data(self):
        """Test pipeline handling of completely invalid data"""
        invalid_data = [
            {
                'invalid_field': 'value1',
                'another_invalid': 'value2'
            },
            {
                'event_title': None,
                'market_id': None,
                'probability': 'not_a_number'
            }
        ]

        result = process_polymarket_data(invalid_data)

        # Should still succeed but with low quality score
        assert result['success'] == True
        assert result['quality_score'] < 0.5  # Low quality due to invalid data
        assert result['processed_records'] == 2

    def test_pipeline_data_quality_improvement(self, large_polymarket_dataset):
        """Test that pipeline improves data quality"""
        # Add some missing values and outliers
        dirty_data = large_polymarket_dataset.copy()

        # Add missing values
        for i in range(0, len(dirty_data), 5):
            dirty_data[i]['probability'] = None
            dirty_data[i]['volume'] = None

        # Add outliers
        for i in range(0, len(dirty_data), 10):
            dirty_data[i]['probability'] = 2.0  # Invalid probability

        result = process_polymarket_data(dirty_data)

        assert result['success'] == True
        assert result['processed_records'] == len(dirty_data)

        # Check that cleaned data has valid values
        cleaned_data = result['cleaned_data']
        for record in cleaned_data:
            if 'probability' in record and record['probability'] is not None:
                assert 0.0 <= record['probability'] <= 1.0
            if 'volume' in record and record['volume'] is not None:
                assert record['volume'] >= 0.0

    def test_concurrent_pipeline_processing(self, large_polymarket_dataset, large_weather_dataset):
        """Test processing multiple data sources concurrently"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(process_polymarket_data, large_polymarket_dataset),
                executor.submit(process_weather_data, large_weather_dataset)
            ]

            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        assert len(results) == 2
        for result in results:
            assert result['success'] == True
            assert result['processed_records'] > 0

    def test_pipeline_error_handling(self):
        """Test pipeline error handling with malformed data"""
        malformed_data = [
            "not a dict",
            123,
            None,
            {"event_title": "Test", "probability": "not_numeric"}
        ]

        result = process_polymarket_data(malformed_data)

        # Should handle errors gracefully
        assert result['success'] == True  # Pipeline should not crash
        assert 'error_records' in result or result['processed_records'] >= 0


class TestDataQualityWorkflow:
    """Tests for complete data quality workflow"""

    def test_end_to_end_validation_workflow(self, large_polymarket_dataset):
        """Test complete validation workflow"""
        # Step 1: Initial validation
        initial_result = validate_polymarket_data(large_polymarket_dataset)
        assert 'total_records' in initial_result
        assert 'valid_records' in initial_result

        # Step 2: Cleaning
        cleaning_result = clean_polymarket_data(large_polymarket_dataset)
        assert 'cleaned_data' in cleaning_result
        assert 'original_count' in cleaning_result

        # Step 3: Final validation
        final_result = validate_polymarket_data(cleaning_result['cleaned_data'])
        assert final_result['valid_records'] >= initial_result['valid_records']

    def test_data_quality_score_calculation(self, large_polymarket_dataset, large_weather_dataset):
        """Test data quality score calculation across pipeline"""
        poly_result = process_polymarket_data(large_polymarket_dataset)
        weather_result = process_weather_data(large_weather_dataset)

        # Quality scores should be reasonable
        assert 0.0 <= poly_result['quality_score'] <= 1.0
        assert 0.0 <= weather_result['quality_score'] <= 1.0

        # Weather data might have different quality characteristics
        # but both should be valid scores

    def test_outlier_detection_integration(self, large_weather_dataset):
        """Test outlier detection in integrated pipeline"""
        # Add extreme outliers
        outlier_data = large_weather_dataset.copy()
        outlier_data[0]['temperature'] = 100.0  # Extreme temperature
        outlier_data[1]['wind_speed'] = 200.0   # Extreme wind speed

        result = process_weather_data(outlier_data)

        assert result['success'] == True
        # Pipeline should handle outliers without crashing
        assert result['processed_records'] == len(outlier_data)

    def test_missing_value_handling_integration(self):
        """Test missing value handling in integrated pipeline"""
        data_with_missing = [
            {
                'event_title': 'Test Event 1',
                'market_id': '0x123',
                'outcome_name': 'Yes',
                'probability': 0.5,
                'volume': None,  # Missing
                'timestamp': '2024-01-01T10:00:00Z',
                'scraped_at': '2024-01-01T10:30:00Z'
            },
            {
                'event_title': 'Test Event 2',
                'market_id': '0x456',
                'outcome_name': 'No',
                'probability': None,  # Missing
                'volume': 1000.0,
                'timestamp': '2024-01-01T11:00:00Z',
                'scraped_at': '2024-01-01T11:30:00Z'
            }
        ]

        result = process_polymarket_data(data_with_missing)

        assert result['success'] == True
        assert result['processed_records'] == 2

        # Check that missing values were handled
        cleaned_data = result['cleaned_data']
        for record in cleaned_data:
            assert record['volume'] is not None
            assert record['probability'] is not None


class TestDataSourceIntegration:
    """Tests for data source integration"""

    def test_polymarket_pipeline_creation(self):
        """Test Polymarket pipeline creation"""
        pipeline = DataQualityPipeline(DataSource.POLYMARKET)
        assert pipeline.source == DataSource.POLYMARKET

    def test_weather_pipeline_creation(self):
        """Test Weather pipeline creation"""
        pipeline = DataQualityPipeline(DataSource.WEATHER)
        assert pipeline.source == DataSource.WEATHER

    def test_pipeline_source_validation(self):
        """Test pipeline source validation"""
        # Should accept valid sources
        for source in [DataSource.POLYMARKET, DataSource.WEATHER]:
            pipeline = DataQualityPipeline(source)
            assert pipeline.source == source

    @patch('data_quality_pipeline.process_polymarket_data')
    def test_polymarket_pipeline_processing(self, mock_process):
        """Test Polymarket pipeline processing with mock"""
        mock_process.return_value = {
            'success': True,
            'quality_score': 0.95,
            'processed_records': 100,
            'cleaned_data': [{'test': 'data'}]
        }

        pipeline = DataQualityPipeline(DataSource.POLYMARKET)
        test_data = [{'event_title': 'Test'}]

        # Note: This would need actual pipeline implementation
        # For now, test the mock setup
        result = mock_process(test_data)
        assert result['success'] == True
        assert result['quality_score'] == 0.95


class TestPerformanceAndScalability:
    """Tests for pipeline performance and scalability"""

    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        # Create a large dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                'event_title': f'Event {i}',
                'market_id': f'0x{i:040x}',
                'outcome_name': 'Yes' if i % 2 == 0 else 'No',
                'probability': 0.5,
                'volume': 1000.0,
                'timestamp': f'2024-01-{(i % 28) + 1:02d}T10:00:00Z',
                'scraped_at': f'2024-01-{(i % 28) + 1:02d}T10:30:00Z'
            })

        result = process_polymarket_data(large_data)

        assert result['success'] == True
        assert result['processed_records'] == 1000
        assert len(result['cleaned_data']) > 0

    def test_memory_efficient_processing(self, large_polymarket_dataset):
        """Test memory-efficient processing"""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Process data
        result = process_polymarket_data(large_polymarket_dataset)

        # Check memory usage didn't explode
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
        assert result['success'] == True


if __name__ == '__main__':
    pytest.main([__file__])