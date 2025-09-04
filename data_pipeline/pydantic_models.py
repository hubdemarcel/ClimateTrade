#!/usr/bin/env python3
"""
Pydantic Models for Type Checking and Schema Validation

This module provides Pydantic models for all data structures, API responses,
and configuration objects in the ClimaTrade AI project.
"""

from typing import Dict, List, Optional, Union, Any, Literal
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field, validator, root_validator, constr, conint, confloat
from pydantic.dataclasses import dataclass
from enum import Enum
import re


class DataSource(str, Enum):
    """Data source enumeration."""
    WEATHER = "weather"
    POLYMARKET = "polymarket"
    EXTERNAL = "external"


class WeatherCondition(str, Enum):
    """Weather condition enumeration."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"
    STORMY = "stormy"
    FOGGY = "foggy"


class MarketStatus(str, Enum):
    """Market status enumeration."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Base Models
class BaseDataModel(BaseModel):
    """Base model with common fields and validation."""

    id: Optional[int] = Field(None, description="Unique identifier")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Coordinates(BaseModel):
    """Geographic coordinates model."""
    latitude: confloat(ge=-90, le=90) = Field(..., description="Latitude in degrees")
    longitude: confloat(ge=-180, le=180) = Field(..., description="Longitude in degrees")

    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v, field):
        """Validate coordinate ranges."""
        if field.name == 'latitude' and not (-90 <= v <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        if field.name == 'longitude' and not (-180 <= v <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v


# Weather Data Models
class WeatherData(BaseDataModel):
    """Weather data model."""
    source_id: int = Field(..., description="Weather source identifier")
    location_name: constr(min_length=1, max_length=255) = Field(..., description="Location name")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    timestamp: datetime = Field(..., description="Weather data timestamp")

    temperature: Optional[confloat(ge=-100, le=60)] = Field(None, description="Temperature in Celsius")
    temperature_min: Optional[confloat(ge=-100, le=60)] = Field(None, description="Minimum temperature")
    temperature_max: Optional[confloat(ge=-100, le=60)] = Field(None, description="Maximum temperature")
    feels_like: Optional[confloat(ge=-100, le=60)] = Field(None, description="Feels like temperature")

    humidity: Optional[conint(ge=0, le=100)] = Field(None, description="Humidity percentage")
    pressure: Optional[confloat(ge=800, le=1200)] = Field(None, description="Atmospheric pressure in hPa")
    wind_speed: Optional[confloat(ge=0, le=150)] = Field(None, description="Wind speed in m/s")
    wind_direction: Optional[conint(ge=0, le=360)] = Field(None, description="Wind direction in degrees")

    precipitation: Optional[confloat(ge=0, le=500)] = Field(None, description="Precipitation in mm")
    visibility: Optional[confloat(ge=0, le=100000)] = Field(None, description="Visibility in meters")
    uv_index: Optional[confloat(ge=0, le=15)] = Field(None, description="UV index")

    weather_code: Optional[Union[int, str]] = Field(None, description="Weather condition code")
    weather_description: Optional[constr(max_length=255)] = Field(None, description="Weather description")
    condition: Optional[WeatherCondition] = Field(None, description="Weather condition enum")

    alerts: Optional[List[str]] = Field(default_factory=list, description="Weather alerts")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw API response data")
    data_quality_score: Optional[confloat(ge=0, le=100)] = Field(None, description="Data quality score")

    @root_validator
    def validate_temperature_relationships(cls, values):
        """Validate temperature relationships."""
        temp = values.get('temperature')
        temp_min = values.get('temperature_min')
        temp_max = values.get('temperature_max')

        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            raise ValueError("Minimum temperature cannot be greater than maximum temperature")

        if temp is not None:
            if temp_min is not None and temp < temp_min:
                raise ValueError("Current temperature cannot be less than minimum temperature")
            if temp_max is not None and temp > temp_max:
                raise ValueError("Current temperature cannot be greater than maximum temperature")

        return values

    @validator('weather_code')
    def validate_weather_code(cls, v):
        """Validate weather code format."""
        if isinstance(v, str):
            if not v.isdigit():
                raise ValueError("Weather code must be numeric when provided as string")
        return v


class WeatherForecast(BaseDataModel):
    """Weather forecast model."""
    source_id: int
    location_name: constr(min_length=1, max_length=255)
    coordinates: Coordinates
    forecast_timestamp: datetime = Field(..., description="Forecast timestamp")
    forecast_horizon: int = Field(..., description="Forecast horizon in hours")

    forecasts: List[WeatherData] = Field(..., description="List of forecast data points")

    @validator('forecasts')
    def validate_forecasts(cls, v):
        """Validate forecast data points."""
        if not v:
            raise ValueError("Forecasts list cannot be empty")
        return v


# Polymarket Data Models
class MarketOutcome(BaseModel):
    """Market outcome model."""
    name: constr(min_length=1, max_length=255) = Field(..., description="Outcome name")
    probability: confloat(ge=0, le=1) = Field(..., description="Outcome probability")
    volume: confloat(ge=0) = Field(..., description="Trading volume")

    @validator('probability')
    def validate_probability(cls, v):
        """Validate probability is between 0 and 1."""
        if not (0 <= v <= 1):
            raise ValueError(f"Probability must be between 0 and 1, got {v}")
        return v


class PolymarketData(BaseDataModel):
    """Polymarket data model."""
    market_id: constr(pattern=r'^[a-zA-Z0-9\-]+$', max_length=100) = Field(..., description="Market identifier")
    event_title: constr(min_length=1, max_length=500) = Field(..., description="Event title")
    event_url: Optional[constr(pattern=r'^https?://')] = Field(None, description="Event URL")

    outcomes: List[MarketOutcome] = Field(..., description="Market outcomes")
    timestamp: datetime = Field(..., description="Data timestamp")
    scraped_at: datetime = Field(..., description="Scraping timestamp")

    market_status: MarketStatus = Field(MarketStatus.ACTIVE, description="Market status")
    total_volume: confloat(ge=0) = Field(..., description="Total market volume")
    num_outcomes: conint(ge=2) = Field(..., description="Number of outcomes")

    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw API response data")

    @root_validator
    def validate_outcomes(cls, values):
        """Validate market outcomes."""
        outcomes = values.get('outcomes', [])
        num_outcomes = values.get('num_outcomes')

        if num_outcomes and len(outcomes) != num_outcomes:
            raise ValueError(f"Number of outcomes ({len(outcomes)}) does not match num_outcomes ({num_outcomes})")

        # Validate probabilities sum to approximately 1
        if outcomes:
            total_prob = sum(outcome.probability for outcome in outcomes)
            if not (0.99 <= total_prob <= 1.01):  # Allow small tolerance for rounding
                raise ValueError(f"Outcome probabilities must sum to 1, got {total_prob}")

        return values

    @validator('scraped_at')
    def validate_scraped_timestamp(cls, v):
        """Validate scraped timestamp is not in the future."""
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError("Scraped timestamp cannot be in the future")
        return v


class MarketTrade(BaseDataModel):
    """Market trade model."""
    market_id: constr(pattern=r'^[a-zA-Z0-9\-]+$', max_length=100)
    outcome_name: constr(min_length=1, max_length=255)
    price: confloat(ge=0, le=1) = Field(..., description="Trade price")
    quantity: confloat(ge=0) = Field(..., description="Trade quantity")
    timestamp: datetime
    trade_type: Literal["buy", "sell"] = Field(..., description="Trade type")


# API Response Models
class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool = Field(..., description="Response success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = Field(None, description="Request identifier")

    @root_validator
    def validate_response(cls, values):
        """Validate response structure."""
        success = values.get('success')
        data = values.get('data')
        error = values.get('error')

        if success and error:
            raise ValueError("Successful response cannot contain error message")
        if not success and not error:
            raise ValueError("Failed response must contain error message")

        return values


class WeatherAPIResponse(APIResponse):
    """Weather API response model."""
    data: Optional[WeatherData] = Field(None, description="Weather data")


class MarketAPIResponse(APIResponse):
    """Market API response model."""
    data: Optional[PolymarketData] = Field(None, description="Market data")


class ValidationResult(BaseModel):
    """Validation result model."""
    is_valid: bool = Field(..., description="Validation status")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    field_errors: Dict[str, List[str]] = Field(default_factory=dict, description="Field-specific errors")


class ValidationAlert(BaseModel):
    """Validation alert model."""
    alert_id: str = Field(..., description="Unique alert identifier")
    severity: ValidationSeverity = Field(..., description="Alert severity")
    source: DataSource = Field(..., description="Data source")
    message: str = Field(..., description="Alert message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Alert details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = Field(False, description="Alert resolution status")


# Configuration Models
class DatabaseConfig(BaseModel):
    """Database configuration model."""
    host: constr(min_length=1, max_length=255) = Field(..., description="Database host")
    port: conint(ge=1, le=65535) = Field(5432, description="Database port")
    database: constr(min_length=1, max_length=255) = Field(..., description="Database name")
    username: constr(min_length=1, max_length=255) = Field(..., description="Database username")
    password: constr(min_length=1) = Field(..., description="Database password")

    ssl_mode: Optional[Literal["disable", "require", "verify-ca", "verify-full"]] = Field("require")
    connection_timeout: conint(ge=1, le=300) = Field(30, description="Connection timeout in seconds")
    max_connections: conint(ge=1, le=1000) = Field(100, description="Maximum connections")

    @validator('host')
    def validate_host(cls, v):
        """Validate database host format."""
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError("Invalid database host format")
        return v


class APIConfig(BaseModel):
    """API configuration model."""
    base_url: constr(pattern=r'^https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/.*)?$') = Field(..., description="API base URL")
    timeout: conint(ge=1, le=300) = Field(30, description="Request timeout in seconds")
    api_key: Optional[constr(min_length=1)] = Field(None, description="API key")
    rate_limit: conint(ge=1, le=10000) = Field(1000, description="Rate limit per minute")
    retry_attempts: conint(ge=0, le=10) = Field(3, description="Number of retry attempts")
    headers: Dict[str, str] = Field(default_factory=dict, description="Default headers")


class LoggingConfig(BaseModel):
    """Logging configuration model."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field("INFO", description="Log level")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file_path: Optional[constr(pattern=r'.*\.log$')] = Field(None, description="Log file path")
    max_file_size: conint(ge=1024, le=104857600) = Field(10485760, description="Max file size in bytes")
    backup_count: conint(ge=1, le=100) = Field(5, description="Number of backup files")
    console_output: bool = Field(True, description="Enable console output")


class ApplicationConfig(BaseModel):
    """Main application configuration model."""
    database: DatabaseConfig = Field(..., description="Database configuration")
    weather_api: APIConfig = Field(..., description="Weather API configuration")
    polymarket_api: APIConfig = Field(..., description="Polymarket API configuration")
    logging: LoggingConfig = Field(..., description="Logging configuration")

    environment: Literal["development", "staging", "production"] = Field("development", description="Deployment environment")
    debug: bool = Field(False, description="Debug mode")
    max_workers: conint(ge=1, le=100) = Field(4, description="Maximum worker threads")


# Data Quality Models
class DataQualityMetrics(BaseModel):
    """Data quality metrics model."""
    completeness_score: confloat(ge=0, le=100) = Field(..., description="Data completeness percentage")
    consistency_score: confloat(ge=0, le=100) = Field(..., description="Data consistency percentage")
    accuracy_score: confloat(ge=0, le=100) = Field(..., description="Data accuracy percentage")
    timeliness_score: confloat(ge=0, le=100) = Field(..., description="Data timeliness percentage")
    overall_score: confloat(ge=0, le=100) = Field(..., description="Overall quality score")

    total_records: conint(ge=0) = Field(..., description="Total number of records")
    valid_records: conint(ge=0) = Field(..., description="Number of valid records")
    invalid_records: conint(ge=0) = Field(..., description="Number of invalid records")


class DataQualityReport(BaseModel):
    """Data quality report model."""
    source: DataSource = Field(..., description="Data source")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: DataQualityMetrics = Field(..., description="Quality metrics")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    recommendations: List[str] = Field(default_factory=list, description="Quality improvement recommendations")


# Utility functions
def validate_weather_data(data: Dict) -> WeatherData:
    """Validate and create WeatherData model from dictionary."""
    return WeatherData(**data)


def validate_polymarket_data(data: Dict) -> PolymarketData:
    """Validate and create PolymarketData model from dictionary."""
    return PolymarketData(**data)


def validate_config(config: Dict) -> ApplicationConfig:
    """Validate and create ApplicationConfig model from dictionary."""
    return ApplicationConfig(**config)


def create_validation_result(is_valid: bool, errors: List[str] = None,
                           warnings: List[str] = None) -> ValidationResult:
    """Create a ValidationResult model."""
    return ValidationResult(
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or []
    )


if __name__ == "__main__":
    # Example usage
    import json

    # Test WeatherData validation
    weather_data = {
        "source_id": 1,
        "location_name": "London, UK",
        "coordinates": {"latitude": 51.5074, "longitude": -0.1278},
        "timestamp": "2025-09-04T12:00:00Z",
        "temperature": 18.5,
        "humidity": 72,
        "pressure": 1013.2,
        "wind_speed": 8.5
    }

    try:
        weather = validate_weather_data(weather_data)
        print(f"Weather data validated: {weather.location_name}, {weather.temperature}°C")
    except Exception as e:
        print(f"Weather data validation failed: {e}")

    # Test PolymarketData validation
    market_data = {
        "market_id": "0x1234567890abcdef",
        "event_title": "Will it rain in London tomorrow?",
        "outcomes": [
            {"name": "Yes", "probability": 0.65, "volume": 10000.50},
            {"name": "No", "probability": 0.35, "volume": 7500.25}
        ],
        "timestamp": "2025-09-04T12:00:00Z",
        "scraped_at": "2025-09-04T12:30:00Z",
        "total_volume": 17500.75,
        "num_outcomes": 2
    }

    try:
        market = validate_polymarket_data(market_data)
        print(f"Market data validated: {market.event_title}")
    except Exception as e:
        print(f"Market data validation failed: {e}")

    # Test configuration validation
    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "climatetrade",
            "username": "user",
            "password": "password123"
        },
        "weather_api": {
            "base_url": "https://api.openweathermap.org",
            "timeout": 30,
            "rate_limit": 1000
        },
        "polymarket_api": {
            "base_url": "https://api.polymarket.com",
            "timeout": 30,
            "rate_limit": 500
        },
        "logging": {
            "level": "INFO",
            "console_output": True
        },
        "environment": "development",
        "max_workers": 4
    }

    try:
        config = validate_config(config_data)
        print(f"Configuration validated for environment: {config.environment}")
    except Exception as e:
        print(f"Configuration validation failed: {e}")