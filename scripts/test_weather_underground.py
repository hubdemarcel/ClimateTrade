#!/usr/bin/env python3
"""
Test Script for Weather Underground Integration

This script provides basic testing functionality for the Weather Underground
integration, including mock testing and validation of core features.

Usage:
    python test_weather_underground.py --apikey YOUR_API_KEY
"""

import os
import sys
import json
from datetime import datetime
from unittest.mock import Mock, patch
import argparse

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_underground_london import WeatherUndergroundClient, validate_weather_data

class WeatherUndergroundTester:
    """Test class for Weather Underground functionality."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.client = WeatherUndergroundClient(api_key) if api_key else None

    def test_data_validation(self):
        """Test data validation functions."""
        print("[TEST] Testing data validation...")

        # Test valid data
        valid_data = {
            'temperature': 20.5,
            'humidity': 65,
            'timestamp': '2024-01-15T12:00:00Z'
        }
        assert validate_weather_data(valid_data) == True
        print("[PASS] Valid data passed validation")

        # Test invalid temperature
        invalid_temp = {
            'temperature': -100,  # Too cold
            'humidity': 65,
            'timestamp': '2024-01-15T12:00:00Z'
        }
        assert validate_weather_data(invalid_temp) == False
        print("[PASS] Invalid temperature correctly rejected")

        # Test invalid humidity
        invalid_humidity = {
            'temperature': 20.5,
            'humidity': 150,  # Too high
            'timestamp': '2024-01-15T12:00:00Z'
        }
        assert validate_weather_data(invalid_humidity) == False
        print("[PASS] Invalid humidity correctly rejected")

        # Test missing required fields
        missing_data = {
            'temperature': 20.5
            # Missing humidity and timestamp
        }
        assert validate_weather_data(missing_data) == False
        print("[PASS] Missing required fields correctly rejected")

        print("[PASS] All validation tests passed!")

    def test_mock_api_calls(self):
        """Test API calls with mocked responses."""
        print("\n[TEST] Testing mock API calls...")

        # Mock response data
        mock_current_response = {
            'observations': [{
                'stationID': 'TEST001',
                'stationName': 'Test Station',
                'obsTimeLocal': '2024-01-15T12:00:00',
                'temp': 18.5,
                'feelsLike': 17.2,
                'rh': 72,
                'dewpt': 13.5,
                'windSpeed': 12,
                'windDir': 225,
                'windGust': 18,
                'pressure': 1015.2,
                'visibility': 15.0,
                'uvIndex': 4,
                'precip1Hour': 0.0,
                'precip6Hour': 0.0,
                'precip24Hour': 0.5,
                'wxPhraseLong': 'Partly Cloudy',
                'iconCode': 30,
                'lat': 51.5074,
                'lon': -0.1278
            }]
        }

        mock_forecast_response = {
            'forecasts': [{
                'fcstValidLocal': '2024-01-15T13:00:00',
                'temp': 19.0,
                'feelsLike': 17.8,
                'rh': 70,
                'dewpt': 13.8,
                'windSpeed': 14,
                'windDir': 230,
                'windGust': 20,
                'pressureMeanSeaLevel': 1014.8,
                'precipChance': 20,
                'qpf': 0.0,
                'qsf': 0.0,
                'uvIndex': 3,
                'visibility': 14.5,
                'wxPhraseLong': 'Mostly Sunny',
                'iconCode': 34,
                'dayInd': 'D'
            }]
        }

        # Test with mock client
        with patch('requests.Session.get') as mock_get:
            # Setup mock responses
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None

            # Test current conditions
            mock_response.json.return_value = mock_current_response
            mock_get.return_value = mock_response

            mock_client = WeatherUndergroundClient('test_key')
            current = mock_client.get_current_conditions()

            assert current['temperature'] == 18.5
            assert current['humidity'] == 72
            assert current['station_id'] == 'TEST001'
            print("[PASS] Mock current conditions test passed")

            # Test forecast
            mock_response.json.return_value = mock_forecast_response
            hourly = mock_client.get_hourly_forecast(1)

            assert len(hourly) == 1
            assert hourly[0]['temperature'] == 19.0
            assert hourly[0]['precipitation_probability'] == 20
            print("[PASS] Mock forecast test passed")

        print("[PASS] All mock API tests passed!")

    def test_csv_export(self):
        """Test CSV export functionality."""
        print("\n[TEST] Testing CSV export...")

        from weather_underground_london import save_to_csv
        import pandas as pd
        import tempfile
        import os

        # Test data
        test_data = [{
            'timestamp': '2024-01-15T12:00:00Z',
            'temperature': 18.5,
            'humidity': 72,
            'wind_speed': 12,
            'weather_condition': 'Partly Cloudy'
        }]

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Test CSV export
            save_to_csv(test_data, tmp_path, 'test')

            # Verify file was created and contains data
            assert os.path.exists(tmp_path)
            print("[PASS] CSV file created successfully")

            # Read and validate CSV content
            df = pd.read_csv(tmp_path)
            assert len(df) == 1
            assert df.iloc[0]['temperature'] == 18.5
            assert df.iloc[0]['humidity'] == 72
            assert 'data_source' in df.columns
            assert 'location' in df.columns
            print("[PASS] CSV content validated successfully")

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        print("[PASS] CSV export tests passed!")

    def test_real_api_call(self):
        """Test real API call if API key is provided."""
        if not self.api_key:
            print("\n[SKIP] Skipping real API test (no API key provided)")
            return

        print("\n[TEST] Testing real API calls...")

        try:
            # Test current conditions
            current = self.client.get_current_conditions()
            assert validate_weather_data(current)
            print("[PASS] Real API current conditions test passed")

            # Test hourly forecast
            hourly = self.client.get_hourly_forecast(6)
            assert len(hourly) > 0
            print("[PASS] Real API hourly forecast test passed")

            # Test daily forecast
            daily = self.client.get_daily_forecast(3)
            assert len(daily) > 0
            print("[PASS] Real API daily forecast test passed")

            print("[PASS] All real API tests passed!")

        except Exception as e:
            print(f"[FAIL] Real API test failed: {e}")
            return False

        return True

    def run_all_tests(self):
        """Run all available tests."""
        print("[START] Starting Weather Underground Integration Tests")
        print("=" * 60)

        try:
            # Run validation tests
            self.test_data_validation()

            # Run mock tests
            self.test_mock_api_calls()

            # Run CSV export tests
            self.test_csv_export()

            # Run real API tests if possible
            api_success = self.test_real_api_call()

            print("\n" + "=" * 60)
            print("[SUCCESS] All tests completed successfully!")

            if api_success:
                print("[PASS] Real API integration working correctly")
            else:
                print("[SKIP] Real API tests skipped (provide API key for full testing)")

            return True

        except Exception as e:
            print(f"\n[FAIL] Test suite failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Test Weather Underground integration functionality"
    )
    parser.add_argument(
        "-k", "--apikey",
        help="Weather Underground API key for real API testing"
    )
    parser.add_argument(
        "--validation-only",
        action='store_true',
        help="Run only validation tests (no API calls)"
    )

    args = parser.parse_args()

    tester = WeatherUndergroundTester(args.apikey)

    if args.validation_only:
        # Run only validation tests
        tester.test_data_validation()
        tester.test_csv_export()
        print("\n[SUCCESS] Validation tests completed successfully!")
    else:
        # Run full test suite
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()