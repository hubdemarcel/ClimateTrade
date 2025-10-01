#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Weather Service

This module contains comprehensive tests for the WeatherService class,
covering functionality, error handling, input validation, and edge cases.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add the backend directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from weather_service import WeatherService, OPEN_METEO_AVAILABLE


class TestWeatherService:
    """Test cases for WeatherService class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = WeatherService()

    def test_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, 'client')
        assert hasattr(self.service, 'db_manager')
        assert hasattr(self.service, '_health_status')

    def test_city_validation(self):
        """Test city name validation"""
        # Valid city names
        assert self.service._validate_city_name("London") == True
        assert self.service._validate_city_name("New York") == True
        assert self.service._validate_city_name("london") == True

        # Invalid city names
        assert self.service._validate_city_name("") == False
        assert self.service._validate_city_name(None) == False
        assert self.service._validate_city_name("London123") == False
        assert self.service._validate_city_name("A" * 51) == False  # Too long
        assert self.service._validate_city_name("London<script>") == False

    def test_city_sanitization(self):
        """Test city name sanitization"""
        assert self.service._sanitize_city_name("  LONDON  ") == "london"
        assert self.service._sanitize_city_name("New York") == "new york"

    def test_get_city_coordinates(self):
        """Test getting city coordinates"""
        # Valid cities
        london = self.service.get_city_coordinates("london")
        assert london is not None
        assert london['name'] == 'London,UK'
        assert london['lat'] == 51.50530
        assert london['lon'] == -0.05528

        nyc = self.service.get_city_coordinates("nyc")
        assert nyc is not None
        assert nyc['name'] == 'New York,NY'

        # Invalid cities
        assert self.service.get_city_coordinates("") is None
        assert self.service.get_city_coordinates("invalid_city") is None

    def test_health_status(self):
        """Test health status reporting"""
        status = self.service.get_health_status()
        assert isinstance(status, dict)
        assert 'open_meteo_available' in status
        assert 'last_health_check' in status
        assert 'error_count' in status

    @patch('weather_service.OPEN_METEO_AVAILABLE', False)
    def test_mock_weather_data_generation(self):
        """Test mock weather data generation"""
        mock_data = self.service._get_mock_weather_data("london")

        assert mock_data['city'] == 'London,UK'
        assert mock_data['source'] == 'mock_data'
        assert mock_data['data_points'] == 24
        assert len(mock_data['timeline']) == 24
        assert 'summary' in mock_data

        # Check timeline structure
        first_entry = mock_data['timeline'][0]
        required_fields = [
            'timestamp', 'temperature', 'feels_like', 'humidity',
            'pressure', 'wind_speed', 'wind_direction', 'precipitation',
            'weather_code', 'weather_description', 'visibility', 'data_type'
        ]

        for field in required_fields:
            assert field in first_entry

    def test_mock_weather_data_realistic_values(self):
        """Test that mock data has realistic value ranges"""
        mock_data = self.service._get_mock_weather_data("london")

        for entry in mock_data['timeline']:
            # Temperature should be reasonable
            assert 5 <= entry['temperature'] <= 35
            assert 30 <= entry['humidity'] <= 90
            assert 0 <= entry['wind_speed'] <= 20
            assert 0 <= entry['wind_direction'] <= 360
            assert entry['precipitation'] >= 0
            assert entry['visibility'] >= 5000

    @pytest.mark.skipif(not OPEN_METEO_AVAILABLE, reason="Open-Meteo client not available")
    def test_real_weather_data_structure(self):
        """Test real weather data structure when Open-Meteo is available"""
        weather_data = self.service.get_24h_weather_history("london")

        assert weather_data['source'] == 'open_meteo'
        assert weather_data['data_points'] >= 24
        assert len(weather_data['timeline']) >= 24
        assert 'summary' in weather_data

        # Check that we have both current and forecast data
        data_types = set(entry['data_type'] for entry in weather_data['timeline'])
        assert 'current' in data_types or 'forecast' in data_types

    def test_weather_comparison(self):
        """Test weather comparison between cities"""
        comparison = self.service.get_weather_comparison("london", "nyc")

        assert 'comparison' in comparison
        assert 'city1' in comparison['comparison']
        assert 'city2' in comparison['comparison']
        assert 'temperature_difference' in comparison['comparison']

    def test_error_handling_invalid_city(self):
        """Test error handling for invalid city"""
        result = self.service.get_24h_weather_history("invalid_city_123")

        # Should fall back to mock data with error
        assert result['source'] in ['mock_data', 'error_fallback']
        assert 'error' in result

    def test_error_response_structure(self):
        """Test error response structure"""
        error_response = self.service._get_error_response("test_city", "Test error")

        assert error_response['city'] == 'test_city'
        assert error_response['error'] == "Test error"
        assert error_response['source'] == 'error_fallback'

    def test_summary_generation(self):
        """Test weather summary generation"""
        mock_timeline = [
            {
                'temperature': 20.0,
                'humidity': 65,
                'precipitation': 0.0,
                'wind_speed': 5.0,
                'weather_description': 'Partly cloudy'
            },
            {
                'temperature': 22.0,
                'humidity': 70,
                'precipitation': 0.5,
                'wind_speed': 7.0,
                'weather_description': 'Light rain'
            }
        ]

        summary = self.service._generate_weather_summary(mock_timeline)

        assert 'temperature_avg' in summary
        assert 'temperature_min' in summary
        assert 'temperature_max' in summary
        assert 'total_precipitation' in summary
        assert 'weather_conditions' in summary

        assert summary['temperature_avg'] == 21.0
        assert summary['temperature_min'] == 20.0
        assert summary['temperature_max'] == 22.0
        assert summary['total_precipitation'] == 0.5

    def test_summary_generation_empty_timeline(self):
        """Test summary generation with empty timeline"""
        summary = self.service._generate_weather_summary([])
        assert summary == {}

    def test_combine_weather_data(self):
        """Test combining current and forecast weather data"""
        current = {
            'timestamp': datetime.now().isoformat(),
            'temperature': 20.0,
            'humidity': 65,
            'weather_description': 'Partly cloudy'
        }

        forecast = {
            'forecast': [
                {
                    'timestamp': (datetime.now() + timedelta(hours=1)).isoformat(),
                    'temperature': 21.0,
                    'humidity': 70,
                    'weather_description': 'Clear sky'
                }
            ]
        }

        city_info = {
            'name': 'London,UK',
            'lat': 51.50530,
            'lon': -0.05528,
            'timezone': 'Europe/London'
        }

        combined = self.service._combine_weather_data(current, forecast, city_info)

        assert combined['city'] == 'London,UK'
        assert combined['source'] == 'open_meteo'
        assert len(combined['timeline']) >= 1
        assert combined['timeline'][0]['data_type'] == 'current'


class TestWeatherServiceIntegration:
    """Integration tests for WeatherService"""

    def test_full_weather_request_london(self):
        """Test full weather request for London"""
        service = WeatherService()
        result = service.get_24h_weather_history("london")

        # Should return valid weather data
        assert isinstance(result, dict)
        assert 'timeline' in result
        assert 'summary' in result
        assert 'source' in result

    def test_full_weather_request_nyc(self):
        """Test full weather request for NYC"""
        service = WeatherService()
        result = service.get_24h_weather_history("nyc")

        # Should return valid weather data
        assert isinstance(result, dict)
        assert 'timeline' in result
        assert 'summary' in result
        assert 'source' in result

    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import threading
        import time

        service = WeatherService()
        results = []
        errors = []

        def make_request(city):
            try:
                result = service.get_24h_weather_history(city)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        cities = ["london", "nyc", "london", "nyc"]

        for city in cities:
            thread = threading.Thread(target=make_request, args=(city,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have results for all requests
        assert len(results) == len(cities)
        assert len(errors) == 0


class TestWeatherServiceEdgeCases:
    """Test edge cases and error conditions"""

    def test_none_inputs(self):
        """Test handling of None inputs"""
        service = WeatherService()

        # These should not crash
        assert service._validate_city_name(None) == False
        assert service.get_city_coordinates(None) is None

    def test_empty_strings(self):
        """Test handling of empty strings"""
        service = WeatherService()

        assert service._validate_city_name("") == False
        assert service.get_city_coordinates("") is None

    def test_special_characters(self):
        """Test handling of special characters in city names"""
        service = WeatherService()

        # These should be rejected
        assert service._validate_city_name("London<script>") == False
        assert service._validate_city_name("London; DROP TABLE") == False
        assert service._validate_city_name("London'or 1=1") == False

    def test_very_long_city_names(self):
        """Test handling of very long city names"""
        service = WeatherService()

        long_name = "A" * 100
        assert service._validate_city_name(long_name) == False

    def test_timezone_handling(self):
        """Test timezone handling in mock data"""
        service = WeatherService()
        mock_data = service._get_mock_weather_data("london")

        assert 'timezone' in mock_data
        assert mock_data['timezone'] in ['Europe/London', 'UTC']


if __name__ == '__main__':
    pytest.main([__file__])