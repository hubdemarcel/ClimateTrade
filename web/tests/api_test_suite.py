#!/usr/bin/env python3
"""
ClimaTrade API Test Suite
Comprehensive testing for frontend data sources and API integrations
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class APITestSuite:
    """Test suite for ClimaTrade API endpoints"""

    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }

    def log_result(self, test_name, success, message="", response=None):
        """Log test result"""
        if success:
            self.results['passed'] += 1
            print(f"PASS {test_name}: {message}")
        else:
            self.results['failed'] += 1
            print(f"FAIL {test_name}: {message}")
            if response:
                print(f"   Response: {response.status_code} - {response.text[:200]}...")
            self.results['errors'].append({
                'test': test_name,
                'message': message,
                'response': response.text if response else None
            })

    def test_health_endpoints(self):
        """Test health and system endpoints"""
        print("\n[TEST] Testing Health Endpoints...")

        # Test root endpoint
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_result("Root endpoint", True, "API is running")
            else:
                self.log_result("Root endpoint", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Root endpoint", False, f"Connection failed: {str(e)}")

        # Test health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result("Health endpoint", True, "System is healthy")
                else:
                    self.log_result("Health endpoint", False, f"Unhealthy status: {data.get('status')}", response)
            else:
                self.log_result("Health endpoint", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Health endpoint", False, f"Connection failed: {str(e)}")

        # Test system health
        try:
            response = self.session.get(f"{self.base_url}/api/system/health")
            if response.status_code == 200:
                data = response.json()
                self.log_result("System health", True, f"Database connected, records: {data.get('weather_data_count', 0)} weather, {data.get('polymarket_data_count', 0)} market")
            else:
                self.log_result("System health", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("System health", False, f"Connection failed: {str(e)}")

    def test_weather_endpoints(self):
        """Test weather API endpoints"""
        print("\n[WEATHER]  Testing Weather Endpoints...")

        # Test weather data endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/weather/data")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Weather data", True, f"Returned {len(data)} records")
                else:
                    self.log_result("Weather data", False, "Expected array response", response)
            else:
                self.log_result("Weather data", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Weather data", False, f"Connection failed: {str(e)}")

        # Test weather sources
        try:
            response = self.session.get(f"{self.base_url}/api/weather/sources")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Weather sources", True, f"Found {len(data)} sources")
            else:
                self.log_result("Weather sources", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Weather sources", False, f"Connection failed: {str(e)}")

        # Test weather cities
        try:
            response = self.session.get(f"{self.base_url}/api/weather/cities")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Weather cities", True, f"Found {data.get('count', 0)} cities")
            else:
                self.log_result("Weather cities", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Weather cities", False, f"Connection failed: {str(e)}")

    def test_market_endpoints(self):
        """Test market API endpoints"""
        print("\n[MARKET] Testing Market Endpoints...")

        # Test markets overview
        try:
            response = self.session.get(f"{self.base_url}/api/markets/overview")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Markets overview", True, f"Returned {len(data)} markets")
                else:
                    self.log_result("Markets overview", False, "Expected array response", response)
            else:
                self.log_result("Markets overview", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Markets overview", False, f"Connection failed: {str(e)}")

        # Test market data (if markets exist)
        try:
            # First get markets to test with a real market ID
            response = self.session.get(f"{self.base_url}/api/markets/overview")
            if response.status_code == 200:
                markets = response.json()
                if markets:
                    market_id = markets[0]['market_id']
                    response = self.session.get(f"{self.base_url}/api/markets/{market_id}/data")
                    if response.status_code == 200:
                        data = response.json()
                        self.log_result("Market data", True, f"Returned {len(data)} data points for market {market_id}")
                    else:
                        self.log_result("Market data", False, f"Unexpected status: {response.status_code}", response)
                else:
                    self.log_result("Market data", True, "Skipped - no markets available")
        except Exception as e:
            self.log_result("Market data", False, f"Connection failed: {str(e)}")

    def test_trading_endpoints(self):
        """Test trading API endpoints"""
        print("\n[TRADING] Testing Trading Endpoints...")

        # Test trading performance
        try:
            response = self.session.get(f"{self.base_url}/api/trading/performance")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Trading performance", True, f"Returned {len(data)} performance records")
                else:
                    self.log_result("Trading performance", False, "Expected array response", response)
            else:
                self.log_result("Trading performance", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Trading performance", False, f"Connection failed: {str(e)}")

        # Test trading positions
        try:
            response = self.session.get(f"{self.base_url}/api/trading/positions")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Trading positions", True, f"Returned {len(data)} positions")
                else:
                    self.log_result("Trading positions", False, "Expected array response", response)
            else:
                self.log_result("Trading positions", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Trading positions", False, f"Connection failed: {str(e)}")

    def test_clob_endpoints(self):
        """Test CLOB trading endpoints"""
        print("\n[CLOB] Testing CLOB Endpoints...")

        # Test CLOB status
        try:
            response = self.session.get(f"{self.base_url}/api/clob/status")
            if response.status_code == 200:
                data = response.json()
                connected = data.get('connected', False)
                authenticated = data.get('authenticated', False)
                status_msg = f"Connected: {connected}, Authenticated: {authenticated}"
                self.log_result("CLOB status", True, status_msg)
            else:
                self.log_result("CLOB status", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("CLOB status", False, f"Connection failed: {str(e)}")

        # Test CLOB markets (read-only)
        try:
            response = self.session.get(f"{self.base_url}/api/clob/markets")
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                self.log_result("CLOB markets", True, f"Returned {len(markets)} markets")
            else:
                self.log_result("CLOB markets", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("CLOB markets", False, f"Connection failed: {str(e)}")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n[ERROR] Testing Error Handling...")

        # Test 404 endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/nonexistent")
            if response.status_code == 404:
                self.log_result("404 handling", True, "Proper 404 response")
            else:
                self.log_result("404 handling", False, f"Expected 404, got {response.status_code}", response)
        except Exception as e:
            self.log_result("404 handling", False, f"Connection failed: {str(e)}")

        # Test invalid parameters
        try:
            response = self.session.get(f"{self.base_url}/api/weather/data?location=invalid_city_12345")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Invalid location", True, "Gracefully handled invalid location")
                else:
                    self.log_result("Invalid location", False, "Unexpected response format", response)
            else:
                self.log_result("Invalid location", False, f"Unexpected status: {response.status_code}", response)
        except Exception as e:
            self.log_result("Invalid location", False, f"Connection failed: {str(e)}")

    def test_data_freshness(self):
        """Test data freshness indicators"""
        print("\n[FRESHNESS] Testing Data Freshness...")

        # Test weather data freshness
        try:
            response = self.session.get(f"{self.base_url}/api/weather/data")
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latest_record = max(data, key=lambda x: x.get('timestamp', ''))
                    timestamp = latest_record.get('timestamp')
                    if timestamp:
                        record_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        now = datetime.now(record_time.tzinfo)
                        age_minutes = (now - record_time).total_seconds() / 60
                        if age_minutes < 60:
                            self.log_result("Weather freshness", True, f"Data is {age_minutes:.1f} minutes old")
                        else:
                            self.log_result("Weather freshness", False, f"Data is stale: {age_minutes:.1f} minutes old")
                    else:
                        self.log_result("Weather freshness", False, "No timestamp in data")
                else:
                    self.log_result("Weather freshness", True, "No data to check freshness")
        except Exception as e:
            self.log_result("Weather freshness", False, f"Failed to check freshness: {str(e)}")

    def run_all_tests(self):
        """Run all test suites"""
        print("Starting ClimaTrade API Test Suite")
        print("=" * 50)

        start_time = time.time()

        self.test_health_endpoints()
        self.test_weather_endpoints()
        self.test_market_endpoints()
        self.test_trading_endpoints()
        self.test_clob_endpoints()
        self.test_error_handling()
        self.test_data_freshness()

        end_time = time.time()

        # Print summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Duration: {end_time - start_time:.2f} seconds")

        if self.results['errors']:
            print(f"\nERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                print(f"  • {error['test']}: {error['message']}")

        return self.results

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ClimaTrade API Test Suite")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL for API tests")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    suite = APITestSuite(args.url)
    results = suite.run_all_tests()

    if args.json:
        print(json.dumps(results, indent=2))

    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()