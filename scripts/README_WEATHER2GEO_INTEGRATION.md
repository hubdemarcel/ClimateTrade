# Weather2Geo Integration for ClimateTrade Data Pipeline

This document describes the Weather2Geo integration that provides enhanced weather data extraction capabilities for the ClimateTrade data collection pipeline.

## Overview

The Weather2Geo integration leverages the MSN Weather API to extract real-time weather data from global locations, providing enhanced data points for weather-market correlation analysis. This integration includes:

- **Automated Data Extraction**: Programmatic access to MSN Weather API
- **Data Enrichment**: Derived metrics like heat index, wind chill, and comfort levels
- **Pipeline Integration**: Seamless integration with existing data quality pipeline
- **Multiple Extraction Modes**: Bulk extraction, condition-specific queries, and location-based extraction
- **Automated Processing**: Scheduled runs and batch processing capabilities

## Architecture

### Components

1. **`weather2geo_client.py`**: Core client for Weather2Geo API interactions
2. **`weather2geo_integration.py`**: Main integration script for data pipeline
3. **`example_weather2geo_integration.py`**: Example integration with existing weather sources
4. **`weather2geo_automated_pipeline.py`**: Automated processing and scheduling
5. **`weather2geo_config.json`**: Configuration file for all settings

### Data Flow

```
Weather2Geo API → Client → Enrichment → Quality Pipeline → Database
       ↓
   Configuration → Scheduling → Monitoring → Alerts
```

## Installation

### Prerequisites

```bash
# Install Weather2Geo dependencies
cd scripts/Weather2Geo
pip install -r requirements.txt

# Install additional dependencies for integration
pip install schedule
```

### Setup

1. **Download Cities Database** (if not already present):

   ```bash
   # Download from GeoNames (cities15000.txt)
   wget https://download.geonames.org/export/dump/cities15000.txt
   mv cities15000.txt ../data/
   ```

2. **Configure Integration**:
   ```bash
   # Copy and modify configuration
   cp weather2geo_config.json weather2geo_config.local.json
   # Edit configuration as needed
   ```

## Usage

### Basic Data Extraction

#### Single Run Extraction

```bash
# Bulk extraction (default)
python weather2geo_integration.py

# Condition-specific extraction
python weather2geo_integration.py --mode conditions --condition "Mostly cloudy" --temp 20

# Location-specific extraction
python weather2geo_integration.py --mode locations --locations-file my_locations.json
```

#### Automated Pipeline

```bash
# Run automated pipeline with scheduling
python weather2geo_automated_pipeline.py --mode scheduled

# Run batch processing
python weather2geo_automated_pipeline.py --mode batch --batch-size 10

# Check pipeline status
python weather2geo_automated_pipeline.py --status
```

### Integration Examples

#### With Existing Weather Sources

```bash
# Run comprehensive integration example
python example_weather2geo_integration.py --extract-mode bulk

# Condition-specific with market analysis
python example_weather2geo_integration.py --extract-mode conditions --condition "Sunny" --temp 25
```

#### Data Pipeline Integration

```bash
# Extract and automatically ingest into database
python weather2geo_integration.py --mode bulk

# Manual ingestion (if auto-ingest is disabled)
python data_pipeline/ingest_weather.py data/weather2geo_output/weather2geo_*.json --source weather2geo --location multiple
```

## Configuration

### Main Configuration File

The `weather2geo_config.json` file contains all configuration options:

```json
{
  "weather2geo_settings": {
    "cities_file": "../data/cities15000.txt",
    "max_workers": 50,
    "output_dir": "data/weather2geo_output",
    "extraction_mode": "bulk",
    "max_locations": 500
  },
  "pipeline_integration": {
    "auto_ingest": true,
    "ingest_script": "data_pipeline/ingest_weather.py",
    "db_path": "data/climatetrade.db"
  },
  "automated_processing": {
    "schedule_interval_hours": 6,
    "batch_size": 10
  }
}
```

### Key Configuration Options

| Setting                   | Description                     | Default |
| ------------------------- | ------------------------------- | ------- |
| `max_workers`             | Concurrent API requests         | 50      |
| `max_locations`           | Maximum locations to query      | 500     |
| `schedule_interval_hours` | Hours between automated runs    | 6       |
| `enable_enrichment`       | Enable data enrichment features | true    |
| `quality_threshold`       | Minimum quality score (%)       | 80.0    |

## Data Enrichment Features

### Derived Metrics

The integration automatically calculates:

- **Heat Index**: Feels-like temperature in warm conditions
- **Wind Chill**: Feels-like temperature in cold/windy conditions
- **Comfort Level**: Categorical comfort classification
- **Weather Severity Score**: 0-10 scale of weather intensity

### Data Quality

- **Completeness Check**: Validates required fields presence
- **Reasonableness Check**: Validates data within expected ranges
- **Outlier Detection**: Identifies anomalous values
- **Quality Scoring**: Overall data quality percentage

## Extraction Modes

### 1. Bulk Mode

Extracts weather data from top population cities globally:

```bash
python weather2geo_integration.py --mode bulk
```

### 2. Conditions Mode

Finds locations matching specific weather conditions:

```bash
python weather2geo_integration.py --mode conditions --condition "Sunny" --temp 22
```

### 3. Locations Mode

Extracts data for specific locations:

```json
// locations.json
[
  { "name": "New York", "lat": 40.7128, "lon": -74.006 },
  { "name": "London", "lat": 51.5074, "lon": -0.1278 }
]
```

```bash
python weather2geo_integration.py --mode locations --locations-file locations.json
```

## Automated Processing

### Scheduled Runs

```bash
# Run every 6 hours
python weather2geo_automated_pipeline.py --mode scheduled
```

### Batch Processing

```bash
# Run 10 extractions of each mode
python weather2geo_automated_pipeline.py --mode batch --batch-size 10
```

### Monitoring and Alerts

The automated pipeline includes:

- **Statistics Tracking**: Success rates, processing times, data quality
- **Email Alerts**: Failure notifications and quality warnings
- **Log Rotation**: Automatic log file management
- **Data Cleanup**: Old file removal based on retention policy

## Output Data Format

### JSON Structure

```json
{
  "location_name": "London, United Kingdom",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "timestamp": "2025-01-15T14:30:00Z",
  "temperature": 18.5,
  "feels_like": 17.2,
  "humidity": 65,
  "pressure": 1013,
  "wind_speed": 12.5,
  "wind_direction": 225,
  "weather_description": "Partly cloudy",
  "visibility": 10000,
  "uv_index": 3,
  "heat_index": 19.1,
  "comfort_level": "comfortable",
  "weather_severity_score": 2,
  "source": "Weather2Geo (MSN Weather API)",
  "raw_data": "{...}"
}
```

## Database Integration

### Schema

Weather2Geo data integrates with the existing `weather_data` table:

```sql
INSERT INTO weather_data (
  source_id, location_name, latitude, longitude, timestamp,
  temperature, feels_like, humidity, pressure, wind_speed,
  wind_direction, weather_description, visibility, uv_index,
  raw_data
) VALUES (...)
```

### Quality Pipeline

Data passes through the existing quality pipeline:

1. **Validation**: Required fields and data ranges
2. **Cleaning**: Missing value imputation and outlier removal
3. **Enrichment**: Additional derived metrics
4. **Scoring**: Overall data quality assessment

## API Reference

### Weather2GeoClient

#### Methods

- `get_bulk_weather_data(max_locations=500)`: Bulk data extraction
- `extract_weather_by_conditions(target_datetime, desired_condition, desired_temp)`: Condition-based extraction
- `enrich_weather_data(weather_data)`: Apply data enrichment
- `calculate_data_quality(weather_data)`: Quality assessment

### Integration Classes

- `Weather2GeoIntegration`: Main integration interface
- `AutomatedPipeline`: Scheduled processing and monitoring
- `EnhancedWeatherAnalyzer`: Multi-source analysis

## Troubleshooting

### Common Issues

1. **Cities Database Not Found**

   ```
   Error: Cities file not found
   Solution: Download cities15000.txt from GeoNames
   ```

2. **API Rate Limiting**

   ```
   Error: Too many requests
   Solution: Reduce max_workers or add delays
   ```

3. **Database Connection Failed**
   ```
   Error: Database not found
   Solution: Run setup_database.py first
   ```

### Logs and Debugging

```bash
# Enable verbose logging
python weather2geo_integration.py --verbose

# Check pipeline status
python weather2geo_automated_pipeline.py --status

# View logs
tail -f weather2geo_integration.log
```

## Performance Considerations

### Optimization Tips

- **Concurrent Requests**: Adjust `max_workers` based on API limits
- **Batch Processing**: Use batch mode for large-scale extraction
- **Data Retention**: Configure retention policy for disk space
- **Quality Thresholds**: Set appropriate quality thresholds

### Resource Usage

- **Memory**: ~50MB per 1000 locations
- **Network**: ~2KB per API request
- **Storage**: ~1MB per 1000 records (JSON)

## Security Considerations

- **API Key**: Public MSN Weather API key (no authentication required)
- **Data Privacy**: No personal data collection
- **Rate Limiting**: Built-in delays to respect API limits
- **Logging**: Sensitive data not logged

## Future Enhancements

- **Real-time Streaming**: WebSocket-based real-time updates
- **Machine Learning**: Weather prediction models
- **Advanced Analytics**: Trend analysis and forecasting
- **Multi-API Support**: Additional weather data sources
- **Dashboard Integration**: Web-based monitoring interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This integration uses the same license as the original Weather2Geo project.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error details
3. Open an issue on the project repository
4. Contact the development team

---

_Last updated: January 2025_
