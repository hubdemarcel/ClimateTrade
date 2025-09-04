#!/usr/bin/env python3
"""
Unified Validation Framework

This module provides a unified interface for all validation components in the
ClimaTrade AI project, integrating existing patterns with new enhancements.

Features:
- Unified validation interface for all data types
- Real-time validation with alerting
- Configuration validation
- Type checking with Pydantic
- Performance monitoring and caching
- Comprehensive error handling and reporting
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from functools import wraps

from .data_validation import DataValidator, validate_polymarket_data, validate_weather_data
from .enhanced_data_validation import (
    AlertManager, RealTimeValidator, EnhancedWeatherValidator,
    EnhancedPolymarketValidator, ValidationAlert, AlertLevel, DataSource
)
from .api_validation import (
    RESTAPIValidator, WebSocketValidator, ExternalAPIValidator,
    validate_rest_request, validate_websocket_message, validate_external_api_response
)
from .config_validation import (
    ConfigValidator, DatabaseConfigValidator, APIConfigValidator, LoggingConfigValidator,
    ConfigFileLoader, EnvironmentVariableValidator, ConfigFormat, Environment,
    validate_database_config, validate_api_config, validate_logging_config
)
from .pydantic_models import (
    WeatherData, PolymarketData, ApplicationConfig, ValidationResult,
    validate_weather_data as pydantic_validate_weather,
    validate_polymarket_data as pydantic_validate_polymarket,
    validate_config as pydantic_validate_config
)

logger = logging.getLogger(__name__)


class ValidationMode(Enum):
    """Validation mode enumeration."""
    STRICT = "strict"
    LENIENT = "lenient"
    MONITORING = "monitoring"


@dataclass
class ValidationContext:
    """Validation context for tracking validation state."""
    mode: ValidationMode = ValidationMode.STRICT
    source: Optional[str] = None
    environment: Environment = Environment.DEVELOPMENT
    enable_alerts: bool = True
    enable_caching: bool = True
    custom_validators: Dict[str, Callable] = field(default_factory=dict)


@dataclass
class ValidationSummary:
    """Summary of validation operations."""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    alerts_raised: int = 0
    average_processing_time: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationCache:
    """Cache for validation results to improve performance."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.access_times: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Dict]:
        """Get cached validation result."""
        if key in self.cache:
            entry = self.cache[key]
            if self._is_expired(key):
                self.delete(key)
                return None
            self.access_times[key] = datetime.now(timezone.utc)
            return entry
        return None

    def set(self, key: str, value: Dict):
        """Set cached validation result."""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = value
        self.access_times[key] = datetime.now(timezone.utc)

    def delete(self, key: str):
        """Delete cached entry."""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.access_times.clear()

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.access_times:
            return True
        age = (datetime.now(timezone.utc) - self.access_times[key]).total_seconds()
        return age > self.ttl_seconds

    def _evict_oldest(self):
        """Evict the oldest cache entry."""
        if not self.access_times:
            return

        oldest_key = min(self.access_times.keys(),
                        key=lambda k: self.access_times[k])
        self.delete(oldest_key)


class UnifiedValidator:
    """Unified validator that integrates all validation components."""

    def __init__(self, context: Optional[ValidationContext] = None):
        self.context = context or ValidationContext()
        self.alert_manager = AlertManager()
        self.cache = ValidationCache()
        self.summary = ValidationSummary()

        # Initialize validators
        self._setup_validators()

        # Setup alert handlers
        self._setup_alert_handlers()

    def _setup_validators(self):
        """Setup all validation components."""
        self.weather_validator = EnhancedWeatherValidator(self.alert_manager)
        self.polymarket_validator = EnhancedPolymarketValidator(self.alert_manager)
        self.realtime_validator = RealTimeValidator(self.alert_manager)

        # Configuration validators
        self.config_validators = {
            'database': DatabaseConfigValidator(environment=self.context.environment),
            'api': APIConfigValidator(environment=self.context.environment),
            'logging': LoggingConfigValidator(environment=self.context.environment)
        }

    def _setup_alert_handlers(self):
        """Setup alert notification handlers."""
        # Log alerts
        def log_alert_handler(alert: ValidationAlert):
            level_map = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.CRITICAL: logging.CRITICAL
            }
            logger.log(
                level_map.get(alert.level, logging.ERROR),
                f"Validation Alert: {alert.message}"
            )

        self.alert_manager.add_alert_handler(log_alert_handler)

    def validate_weather_data(self, data: Dict, use_cache: bool = True) -> ValidationResult:
        """Validate weather data using multiple validation layers."""
        return self._validate_data('weather', data, use_cache)

    def validate_polymarket_data(self, data: Dict, use_cache: bool = True) -> ValidationResult:
        """Validate polymarket data using multiple validation layers."""
        return self._validate_data('polymarket', data, use_cache)

    def _validate_data(self, data_type: str, data: Dict, use_cache: bool = True) -> ValidationResult:
        """Generic data validation with caching and multiple layers."""
        start_time = time.time()

        # Generate cache key
        cache_key = None
        if use_cache and self.context.enable_caching:
            cache_key = f"{data_type}_{hash(json.dumps(data, sort_keys=True))}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.summary.total_validations += 1
                self.summary.successful_validations += 1
                return ValidationResult(**cached_result)

        try:
            errors = []
            warnings = []

            # Layer 1: Pydantic validation
            pydantic_result = self._validate_with_pydantic(data_type, data)
            if not pydantic_result.is_valid:
                errors.extend(pydantic_result.errors)

            # Layer 2: Enhanced validation
            enhanced_result = self._validate_with_enhanced(data_type, data)
            if not enhanced_result.is_valid:
                errors.extend(enhanced_result.errors)
            warnings.extend(enhanced_result.warnings)

            # Layer 3: Custom validators
            if data_type in self.context.custom_validators:
                custom_result = self.context.custom_validators[data_type](data)
                if hasattr(custom_result, 'errors'):
                    errors.extend(custom_result.errors)
                if hasattr(custom_result, 'warnings'):
                    warnings.extend(custom_result.warnings)

            is_valid = len(errors) == 0
            result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )

            # Update summary
            self.summary.total_validations += 1
            if is_valid:
                self.summary.successful_validations += 1
            else:
                self.summary.failed_validations += 1

            processing_time = time.time() - start_time
            self.summary.average_processing_time = (
                (self.summary.average_processing_time * (self.summary.total_validations - 1)) +
                processing_time
            ) / self.summary.total_validations

            # Cache result
            if cache_key and use_cache and self.context.enable_caching:
                self.cache.set(cache_key, result.dict())

            return result

        except Exception as e:
            logger.error(f"Validation error for {data_type}: {e}")
            self.summary.failed_validations += 1
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"]
            )

    def _validate_with_pydantic(self, data_type: str, data: Dict) -> ValidationResult:
        """Validate using Pydantic models."""
        try:
            if data_type == 'weather':
                pydantic_validate_weather(data)
            elif data_type == 'polymarket':
                pydantic_validate_polymarket(data)
            return ValidationResult(is_valid=True)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Pydantic validation failed: {str(e)}"]
            )

    def _validate_with_enhanced(self, data_type: str, data: Dict) -> ValidationResult:
        """Validate using enhanced validators."""
        try:
            if data_type == 'weather':
                is_valid = self.weather_validator.validate_record(data)
                return ValidationResult(
                    is_valid=is_valid,
                    errors=self.weather_validator.validation_errors,
                    warnings=self.weather_validator.validation_warnings
                )
            elif data_type == 'polymarket':
                is_valid = self.polymarket_validator.validate_record(data)
                return ValidationResult(
                    is_valid=is_valid,
                    errors=self.polymarket_validator.validation_errors,
                    warnings=self.polymarket_validator.validation_warnings
                )
            return ValidationResult(is_valid=True)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Enhanced validation failed: {str(e)}"]
            )

    def validate_api_request(self, request_data: Dict, method: str = "GET",
                           endpoint: str = "", api_type: str = "rest") -> ValidationResult:
        """Validate API request parameters."""
        try:
            if api_type.lower() == "rest":
                results = validate_rest_request(request_data, method, endpoint)
            elif api_type.lower() == "websocket":
                results = validate_websocket_message(request_data)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Unsupported API type: {api_type}"]
                )

            errors = [r.message for r in results if r.severity.name == "ERROR"]
            warnings = [r.message for r in results if r.severity.name == "WARNING"]

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"API validation failed: {str(e)}"]
            )

    def validate_configuration(self, config: Dict, config_type: str = "application") -> ValidationResult:
        """Validate configuration using appropriate validator."""
        try:
            if config_type in self.config_validators:
                result = self.config_validators[config_type].validate_config(config)
                return ValidationResult(
                    is_valid=result.is_valid,
                    errors=result.errors,
                    warnings=result.warnings
                )
            elif config_type == "application":
                pydantic_validate_config(config)
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Unknown configuration type: {config_type}"]
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Configuration validation failed: {str(e)}"]
            )

    async def validate_stream(self, data_stream: AsyncGenerator[Dict, None],
                            data_type: str) -> AsyncGenerator[Dict, None]:
        """Validate streaming data asynchronously."""
        async for data_item in data_stream:
            result = self._validate_data(data_type, data_item, use_cache=False)

            # Add validation metadata
            validated_item = {
                **data_item,
                '_validation': {
                    'is_valid': result.is_valid,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }

            yield validated_item

    def validate_config_file(self, file_path: Union[str, Path],
                           format_type: ConfigFormat = ConfigFormat.JSON) -> ValidationResult:
        """Validate configuration file."""
        try:
            loader = ConfigFileLoader()
            result = loader.load_and_validate(
                file_path, format_type,
                self.config_validators.get('database', ConfigValidator()),
                self.context.environment
            )

            return ValidationResult(
                is_valid=result.is_valid,
                errors=result.errors,
                warnings=result.warnings
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Config file validation failed: {str(e)}"]
            )

    def validate_environment_variables(self, required_vars: List[str] = None,
                                     optional_vars: Dict[str, Any] = None) -> ValidationResult:
        """Validate environment variables."""
        try:
            validator = EnvironmentVariableValidator(required_vars, optional_vars)
            result = validator.validate()

            return ValidationResult(
                is_valid=result.is_valid,
                errors=result.errors,
                warnings=result.warnings
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Environment validation failed: {str(e)}"]
            )

    def get_validation_summary(self) -> ValidationSummary:
        """Get validation summary statistics."""
        return self.summary

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[ValidationAlert]:
        """Get active validation alerts."""
        return self.alert_manager.get_active_alerts(level)

    def clear_cache(self):
        """Clear validation cache."""
        self.cache.clear()

    def add_custom_validator(self, data_type: str, validator_func: Callable):
        """Add custom validator for specific data type."""
        self.context.custom_validators[data_type] = validator_func


# Decorator for automatic validation
def validate_data(data_type: str, validator: Optional[UnifiedValidator] = None):
    """Decorator to automatically validate function inputs."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal validator
            if validator is None:
                validator = UnifiedValidator()

            # Validate function arguments
            for arg_name, arg_value in kwargs.items():
                if isinstance(arg_value, dict):
                    result = validator._validate_data(data_type, arg_value)
                    if not result.is_valid:
                        raise ValueError(f"Validation failed for {arg_name}: {result.errors}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience functions
def create_validator(context: Optional[ValidationContext] = None) -> UnifiedValidator:
    """Create a unified validator instance."""
    return UnifiedValidator(context)


def validate_weather_batch(data_list: List[Dict], validator: Optional[UnifiedValidator] = None) -> List[ValidationResult]:
    """Validate a batch of weather data."""
    if validator is None:
        validator = UnifiedValidator()

    return [validator.validate_weather_data(data) for data in data_list]


def validate_polymarket_batch(data_list: List[Dict], validator: Optional[UnifiedValidator] = None) -> List[ValidationResult]:
    """Validate a batch of polymarket data."""
    if validator is None:
        validator = UnifiedValidator()

    return [validator.validate_polymarket_data(data) for data in data_list]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create validator
    validator = create_validator()

    # Test weather data validation
    weather_data = {
        "source_id": 1,
        "location_name": "London, UK",
        "coordinates": {"latitude": 51.5074, "longitude": -0.1278},
        "timestamp": "2025-09-04T12:00:00Z",
        "temperature": 18.5,
        "humidity": 72
    }

    result = validator.validate_weather_data(weather_data)
    print(f"Weather validation: {'PASS' if result.is_valid else 'FAIL'}")
    if not result.is_valid:
        print(f"Errors: {result.errors}")

    # Test API request validation
    api_request = {
        "user_id": 123,
        "location": "London",
        "units": "metric"
    }

    result = validator.validate_api_request(api_request, "GET", "/api/weather")
    print(f"API validation: {'PASS' if result.is_valid else 'FAIL'}")

    # Test configuration validation
    config = {
        "host": "localhost",
        "port": 5432,
        "database": "climatetrade",
        "username": "user",
        "password": "password123"
    }

    result = validator.validate_configuration(config, "database")
    print(f"Config validation: {'PASS' if result.is_valid else 'FAIL'}")

    # Get summary
    summary = validator.get_validation_summary()
    print(f"Total validations: {summary.total_validations}")
    print(f"Success rate: {summary.successful_validations/summary.total_validations*100:.1f}%")