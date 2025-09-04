#!/usr/bin/env python3
"""
Test Utilities and Helpers for ClimaTrade Project

This module provides utility functions, test helpers, and common test patterns
used across the ClimaTrade test suite.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import logging
import time
from contextlib import contextmanager


# Test configuration
TEST_TIMEOUT = 30  # seconds
PERFORMANCE_THRESHOLD = 1.0  # seconds for performance tests


@contextmanager
def timer_context(description: str = "Operation"):
    """Context manager for timing operations"""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        print(f"{description} took {elapsed:.3f} seconds")


def assert_dataframe_equal(df1: pd.DataFrame, df2: pd.DataFrame, check_dtype: bool = True):
    """Assert that two DataFrames are equal with detailed error messages"""
    try:
        pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype)
    except AssertionError as e:
        # Provide more detailed error information
        print(f"DataFrame 1 shape: {df1.shape}")
        print(f"DataFrame 2 shape: {df2.shape}")
        print(f"DataFrame 1 columns: {list(df1.columns)}")
        print(f"DataFrame 2 columns: {list(df2.columns)}")

        if len(df1) != len(df2):
            print(f"Length mismatch: {len(df1)} vs {len(df2)}")

        if set(df1.columns) != set(df2.columns):
            print(f"Column mismatch: {set(df1.columns) - set(df2.columns)} vs {set(df2.columns) - set(df1.columns)}")

        raise e


def assert_series_equal(s1: pd.Series, s2: pd.Series, check_dtype: bool = True):
    """Assert that two Series are equal with detailed error messages"""
    try:
        pd.testing.assert_series_equal(s1, s2, check_dtype=check_dtype)
    except AssertionError as e:
        print(f"Series 1 length: {len(s1)}")
        print(f"Series 2 length: {len(s2)}")
        print(f"Series 1 dtype: {s1.dtype}")
        print(f"Series 2 dtype: {s2.dtype}")
        raise e


def create_mock_response(status_code: int = 200, json_data: Dict = None, text: str = None):
    """Create a mock HTTP response object"""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = text or ""
    mock_response.raise_for_status.return_value = None
    return mock_response


def create_async_mock(coro_func: Callable = None):
    """Create an async mock that can be used as a coroutine"""
    async def async_func(*args, **kwargs):
        if coro_func:
            return coro_func(*args, **kwargs)
        return None

    return AsyncMock(side_effect=async_func)


def wait_for_condition(condition_func: Callable, timeout: float = TEST_TIMEOUT, interval: float = 0.1):
    """Wait for a condition to become true"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)

    return False


def retry_on_failure(func: Callable, max_attempts: int = 3, delay: float = 0.1):
    """Retry a function on failure"""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            time.sleep(delay)


class TestDataValidator:
    """Validator for test data integrity"""

    @staticmethod
    def validate_market_data(df: pd.DataFrame) -> List[str]:
        """Validate market data DataFrame"""
        errors = []

        required_columns = ['timestamp', 'market_id', 'outcome_name', 'probability']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        if not df.empty:
            # Check probability range
            if 'probability' in df.columns:
                invalid_probs = df[~df['probability'].between(0.0, 1.0)]
                if not invalid_probs.empty:
                    errors.append(f"Invalid probabilities found: {len(invalid_probs)} rows")

            # Check for required non-null values
            for col in ['market_id', 'outcome_name']:
                if col in df.columns:
                    null_count = df[col].isnull().sum()
                    if null_count > 0:
                        errors.append(f"Null values in {col}: {null_count} rows")

        return errors

    @staticmethod
    def validate_weather_data(df: pd.DataFrame) -> List[str]:
        """Validate weather data DataFrame"""
        errors = []

        required_columns = ['timestamp', 'location_name', 'temperature']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        if not df.empty:
            # Check temperature range (reasonable bounds)
            if 'temperature' in df.columns:
                extreme_temps = df[~df['temperature'].between(-50, 60)]
                if not extreme_temps.empty:
                    errors.append(f"Extreme temperatures found: {len(extreme_temps)} rows")

            # Check humidity range
            if 'humidity' in df.columns:
                invalid_humidity = df[~df['humidity'].between(0, 100)]
                if not invalid_humidity.empty:
                    errors.append(f"Invalid humidity values: {len(invalid_humidity)} rows")

        return errors


class PerformanceMonitor:
    """Monitor performance of test operations"""

    def __init__(self):
        self.measurements = []

    def measure(self, operation_name: str):
        """Decorator to measure operation performance"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    self.measurements.append({
                        'operation': operation_name,
                        'duration': elapsed,
                        'success': True
                    })
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    self.measurements.append({
                        'operation': operation_name,
                        'duration': elapsed,
                        'success': False,
                        'error': str(e)
                    })
                    raise e
            return wrapper
        return decorator

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.measurements:
            return {}

        successful = [m for m in self.measurements if m['success']]
        failed = [m for m in self.measurements if not m['success']]

        return {
            'total_operations': len(self.measurements),
            'successful_operations': len(successful),
            'failed_operations': len(failed),
            'average_duration': np.mean([m['duration'] for m in self.measurements]),
            'max_duration': max([m['duration'] for m in self.measurements]),
            'min_duration': min([m['duration'] for m in self.measurements]),
            'success_rate': len(successful) / len(self.measurements)
        }


class MockWebSocket:
    """Mock WebSocket for testing WebSocket clients"""

    def __init__(self, messages=None):
        self.messages = messages or []
        self.sent_messages = []
        self.closed = False

    async def send(self, message: str):
        """Mock send method"""
        self.sent_messages.append(message)

    async def recv(self):
        """Mock receive method"""
        if self.messages:
            return self.messages.pop(0)
        else:
            # Simulate connection close
            raise Exception("Connection closed")

    async def close(self):
        """Mock close method"""
        self.closed = True

    def __aiter__(self):
        """Make mock iterable for async iteration"""
        return self

    async def __anext__(self):
        """Async iterator next"""
        try:
            return await self.recv()
        except Exception:
            raise StopAsyncIteration


class AsyncTestHelper:
    """Helper for async test operations"""

    @staticmethod
    async def wait_for_async_condition(condition_func: Callable, timeout: float = TEST_TIMEOUT):
        """Wait for an async condition to become true"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(0.1)

        return False

    @staticmethod
    async def run_with_timeout(coro, timeout: float = TEST_TIMEOUT):
        """Run a coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout} seconds")


class TestEnvironment:
    """Test environment setup and teardown"""

    def __init__(self):
        self.setup_called = False
        self.teardown_called = False

    def setup(self):
        """Setup test environment"""
        self.setup_called = True
        # Configure logging for tests
        logging.basicConfig(level=logging.WARNING)

    def teardown(self):
        """Teardown test environment"""
        self.teardown_called = True

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()


# Global test environment
test_env = TestEnvironment()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment for the entire test session"""
    with test_env:
        yield


@pytest.fixture
def performance_monitor():
    """Performance monitor fixture"""
    return PerformanceMonitor()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket fixture"""
    return MockWebSocket()


# Custom pytest markers and configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "flaky: marks tests as potentially flaky")


def pytest_runtest_setup(item):
    """Setup for each test"""
    # Set random seed for reproducible tests
    np.random.seed(42)


def pytest_runtest_teardown(item):
    """Teardown for each test"""
    pass


# Utility functions for common test patterns

def parametrize_test_data(*test_cases):
    """Parametrize test with multiple data cases"""
    return pytest.mark.parametrize("test_input,expected", test_cases)


def skip_if_no_database():
    """Skip test if database is not available"""
    return pytest.mark.skipif(
        not _database_available(),
        reason="Database not available"
    )


def _database_available() -> bool:
    """Check if test database is available"""
    try:
        import sqlite3
        # Try to connect to a test database
        conn = sqlite3.connect(":memory:")
        conn.close()
        return True
    except ImportError:
        return False


def create_temp_file(content: str, suffix: str = ".txt") -> str:
    """Create a temporary file with content"""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def cleanup_temp_file(file_path: str):
    """Clean up temporary file"""
    try:
        os.unlink(file_path)
    except OSError:
        pass


# Error handling utilities

class TestError(Exception):
    """Base exception for test errors"""
    pass


class DataValidationError(TestError):
    """Error for data validation failures"""
    pass


class PerformanceError(TestError):
    """Error for performance test failures"""
    pass


def validate_test_data(data: Any, schema: Dict[str, Any]) -> bool:
    """Validate test data against a schema"""
    # Simple schema validation
    if not isinstance(data, dict):
        return False

    for key, expected_type in schema.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            return False

    return True


# Logging utilities for tests

def setup_test_logging(level=logging.INFO):
    """Setup logging for tests"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def log_test_start(test_name: str):
    """Log test start"""
    logging.info(f"Starting test: {test_name}")


def log_test_end(test_name: str, success: bool, duration: float):
    """Log test end"""
    status = "PASSED" if success else "FAILED"
    logging.info(f"Test {test_name} {status} in {duration:.3f}s")


# Memory usage monitoring

def get_memory_usage():
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        return 0


def assert_memory_usage_increase(max_increase_mb: float = 100):
    """Assert that memory usage increase is within limits"""
    initial_memory = get_memory_usage()

    def check_memory():
        current_memory = get_memory_usage()
        increase = current_memory - initial_memory
        assert increase <= max_increase_mb, f"Memory increase too high: {increase:.2f} MB"

    return check_memory