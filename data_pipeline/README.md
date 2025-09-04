# ClimaTrade AI Data Validation Framework

## Overview

The ClimaTrade AI Data Validation Framework provides comprehensive validation capabilities for all data types and sources in the ClimaTrade AI project. This framework integrates multiple validation layers to ensure data quality, consistency, and reliability.

## Architecture

The validation framework consists of several integrated components:

```
data_pipeline/
├── validation_framework.py      # Unified validation interface
├── data_validation.py           # Core data validation (existing)
├── enhanced_data_validation.py  # Real-time validation & alerting
├── api_validation.py           # API parameter validation
├── config_validation.py        # Configuration validation
├── pydantic_models.py          # Type checking with Pydantic
└── README.md                   # This documentation
```

## Features

### ✅ Multi-Layer Validation

- **Pydantic Models**: Type checking and schema validation
- **Enhanced Validators**: Real-time validation with alerting
- **Legacy Validators**: Integration with existing validation patterns
- **Custom Validators**: Extensible validation framework

### ✅ Real-Time Validation

- Streaming data validation
- Cross-source consistency checks
- Automated quality alerting
- Performance monitoring

### ✅ API Validation

- REST API parameter validation
- WebSocket message validation
- External API response validation
- Rate limiting and authentication checks

### ✅ Configuration Validation

- JSON/YAML/Environment variable validation
- Schema-based validation
- Environment-specific rules
- File format validation

### ✅ Performance & Caching

- Validation result caching
- Performance metrics tracking
- Async validation support
- Memory-efficient processing

## Quick Start

### Basic Usage

```python
from data_pipeline.validation_framework import create_validator

# Create validator instance
validator = create_validator()

# Validate weather data
weather_data = {
    "source_id": 1,
    "location_name": "London, UK",
    "coordinates": {"latitude": 51.5074, "longitude": -0.1278},
    "timestamp": "2025-09-04T12:00:00Z",
    "temperature": 18.5,
    "humidity": 72
}

result = validator.validate_weather_data(weather_data)
if result.is_valid:
    print("Weather data is valid")
else:
    print(f"Validation errors: {result.errors}")
```

### API Validation

```python
from data_pipeline.api_validation import validate_rest_request

# Validate REST API request
request_data = {
    "user_id": 123,
    "location": "London",
    "units": "metric"
}

results = validate_rest_request(request_data, "GET", "/api/weather")
for result in results:
    if result.severity.name == "ERROR":
        print(f"API Error: {result.message}")
```

### Configuration Validation

```python
from data_pipeline.config_validation import validate_database_config, Environment

# Validate database configuration
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "climatetrade",
    "username": "user",
    "password": "password123"
}

result = validate_database_config(db_config, Environment.PRODUCTION)
if result.is_valid:
    print("Database configuration is valid")
```

### Pydantic Models

```python
from data_pipeline.pydantic_models import validate_weather_data

# Validate with Pydantic (throws exception on failure)
try:
    weather = validate_weather_data(weather_dict)
    print(f"Temperature: {weather.temperature}°C")
except Exception as e:
    print(f"Validation failed: {e}")
```

## Advanced Features

### Real-Time Validation with Alerting

```python
from data_pipeline.enhanced_data_validation import (
    AlertManager, RealTimeValidator, DataSource
)

# Setup alerting
alert_manager = AlertManager()
realtime_validator = RealTimeValidator(alert_manager)

# Start periodic consistency checks
realtime_validator.start_periodic_consistency_checks(interval_seconds=300)

# Validate streaming data
async def validate_stream():
    async for data in data_stream:
        result = await realtime_validator.validate_stream(
            [data], DataSource.WEATHER
        )
        # Process validated data
```

### Custom Validators

```python
from data_pipeline.validation_framework import UnifiedValidator

validator = UnifiedValidator()

# Add custom validator
def custom_weather_validator(data):
    if data.get('temperature', 0) > 50:
        return {'is_valid': False, 'errors': ['Temperature too high']}
    return {'is_valid': True, 'errors': []}

validator.add_custom_validator('weather', custom_weather_validator)
```

### Async Validation

```python
import asyncio
from data_pipeline.validation_framework import UnifiedValidator

async def validate_async():
    validator = UnifiedValidator()

    async def data_generator():
        for i in range(10):
            yield {"temperature": 20 + i, "humidity": 60 + i}
            await asyncio.sleep(0.1)

    async for validated_data in validator.validate_stream(
        data_generator(), 'weather'
    ):
        print(f"Validated: {validated_data['_validation']['is_valid']}")
```

## Configuration

### Environment Variables

Set the following environment variables for optimal performance:

```bash
# Validation settings
VALIDATION_CACHE_SIZE=1000
VALIDATION_CACHE_TTL=300
VALIDATION_ENABLE_ALERTS=true

# Alert settings
ALERT_WEBHOOK_URL=https://hooks.slack.com/your-webhook
ALERT_EMAIL_RECIPIENTS=admin@climatetrade.ai

# Performance settings
VALIDATION_MAX_WORKERS=4
VALIDATION_BATCH_SIZE=100
```

### Configuration File

Create a `config/validation_config.json`:

```json
{
  "cache": {
    "max_size": 1000,
    "ttl_seconds": 300
  },
  "alerting": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/your-webhook",
    "email_recipients": ["admin@climatetrade.ai"]
  },
  "performance": {
    "max_workers": 4,
    "batch_size": 100
  },
  "validation_rules": {
    "strict_mode": true,
    "fail_on_warnings": false
  }
}
```

## Validation Rules

### Weather Data Validation

- **Required Fields**: `location_name`, `timestamp`
- **Coordinate Ranges**: Latitude (-90 to 90), Longitude (-180 to 180)
- **Temperature Range**: -100°C to 60°C
- **Humidity Range**: 0% to 100%
- **Pressure Range**: 800 hPa to 1200 hPa
- **Wind Speed**: 0 to 150 m/s
- **Precipitation**: 0 to 500 mm

### Polymarket Data Validation

- **Required Fields**: `market_id`, `event_title`, `outcomes`, `timestamp`
- **Market ID Format**: Alphanumeric with hyphens
- **Probability Range**: 0.0 to 1.0
- **Volume**: Non-negative values
- **Outcome Probabilities**: Must sum to 1.0

### API Validation

- **REST Methods**: GET, POST, PUT, DELETE, PATCH
- **HTTP Status Codes**: 200-299 for success
- **Content-Type**: application/json preferred
- **Rate Limits**: Configurable per endpoint
- **Authentication**: API key or Bearer token

## Error Handling

### Validation Errors

```python
try:
    result = validator.validate_weather_data(weather_data)
    if not result.is_valid:
        for error in result.errors:
            logger.error(f"Validation error: {error}")
        for warning in result.warnings:
            logger.warning(f"Validation warning: {warning}")
except Exception as e:
    logger.error(f"Unexpected validation error: {e}")
```

### Alert Management

```python
# Get active alerts
active_alerts = validator.get_active_alerts(AlertLevel.CRITICAL)

# Resolve alert
validator.alert_manager.resolve_alert(alert_id, "Issue resolved")

# Get alert history
alert_history = validator.alert_manager.get_alert_history(hours=24)
```

## Performance Optimization

### Caching

```python
# Enable caching for repeated validations
validator = UnifiedValidator()
validator.context.enable_caching = True

# Clear cache when needed
validator.clear_cache()
```

### Batch Processing

```python
from data_pipeline.validation_framework import validate_weather_batch

# Validate multiple records efficiently
results = validate_weather_batch(weather_data_list, validator)
```

### Metrics Monitoring

```python
# Get validation performance metrics
summary = validator.get_validation_summary()
print(f"Success rate: {summary.successful_validations/summary.total_validations*100:.1f}%")
print(f"Average processing time: {summary.average_processing_time:.3f}s")
```

## Integration Examples

### With Existing Data Pipeline

```python
from data_pipeline.data_quality_pipeline import DataQualityPipeline, DataSource
from data_pipeline.validation_framework import UnifiedValidator

# Enhanced data quality pipeline
class EnhancedDataQualityPipeline(DataQualityPipeline):
    def __init__(self, source, config=None):
        super().__init__(source, config)
        self.validator = UnifiedValidator()

    def process_data(self, data, metadata=None):
        # Pre-validate data
        if self.source == DataSource.WEATHER:
            validation_results = [
                self.validator.validate_weather_data(record)
                for record in data
            ]
        # Continue with existing pipeline...
```

### With Web Framework

```python
from flask import Flask, request, jsonify
from data_pipeline.validation_framework import UnifiedValidator

app = Flask(__name__)
validator = UnifiedValidator()

@app.route('/api/weather', methods=['POST'])
def validate_weather_endpoint():
    data = request.get_json()

    # Validate API request
    api_result = validator.validate_api_request(
        data, request.method, request.path
    )

    if not api_result.is_valid:
        return jsonify({
            'error': 'Invalid request',
            'details': api_result.errors
        }), 400

    # Validate data
    data_result = validator.validate_weather_data(data)
    if not data_result.is_valid:
        return jsonify({
            'error': 'Invalid data',
            'details': data_result.errors
        }), 422

    return jsonify({'status': 'Data validated successfully'})
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed

   ```bash
   pip install pydantic pyyaml
   ```

2. **Performance Issues**: Enable caching and adjust batch sizes

   ```python
   validator.context.enable_caching = True
   ```

3. **Memory Usage**: Configure cache size and TTL

   ```python
   validator.cache = ValidationCache(max_size=500, ttl_seconds=180)
   ```

4. **Alert Spam**: Configure alert thresholds and filtering
   ```python
   # Only alert on critical issues
   alerts = validator.get_active_alerts(AlertLevel.CRITICAL)
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose validation logging
validator = UnifiedValidator()
# All validation steps will be logged
```

## Contributing

### Adding New Validators

1. Create validator class inheriting from `DataValidator`
2. Implement validation methods
3. Add to `UnifiedValidator._setup_validators()`
4. Update documentation

### Extending Pydantic Models

1. Add new fields to existing models
2. Create new model classes for new data types
3. Update validation functions in `pydantic_models.py`
4. Add model imports to `__init__.py`

### Custom Alert Handlers

```python
def custom_alert_handler(alert):
    # Send to external monitoring system
    send_to_monitoring_system(alert)

validator.alert_manager.add_alert_handler(custom_alert_handler)
```

## API Reference

### UnifiedValidator

- `validate_weather_data(data)`: Validate weather data
- `validate_polymarket_data(data)`: Validate polymarket data
- `validate_api_request(data, method, endpoint)`: Validate API request
- `validate_configuration(config, type)`: Validate configuration
- `validate_stream(stream, type)`: Validate async data stream
- `get_validation_summary()`: Get performance metrics
- `get_active_alerts(level)`: Get active alerts

### ValidationResult

- `is_valid`: Boolean validation status
- `errors`: List of error messages
- `warnings`: List of warning messages
- `field_errors`: Dict of field-specific errors

### AlertManager

- `raise_alert(alert)`: Raise new alert
- `resolve_alert(alert_id)`: Resolve alert
- `get_active_alerts(level)`: Get active alerts
- `get_alert_history(hours)`: Get alert history

## License

This validation framework is part of the ClimaTrade AI project and follows the same licensing terms.
