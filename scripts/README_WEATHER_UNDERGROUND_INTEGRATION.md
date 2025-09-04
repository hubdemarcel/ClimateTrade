# Weather Underground Integration for London Weather Data

This directory contains scripts for integrating Weather Underground API data with existing weather sources for comprehensive London weather analysis and market correlation studies.

## Overview

Weather Underground provides real-time weather observations from a global network of personal weather stations (PWS), offering high-resolution weather data that complements official meteorological sources.

### Key Features

- **Real-time Observations**: Current weather conditions from PWS network
- **High-Resolution Forecasts**: Hourly and daily forecasts with detailed parameters
- **Historical Data**: Past weather data for backtesting and analysis
- **CSV Export**: Structured data output for analysis and storage
- **Multi-Source Integration**: Combines with Met Office, Meteostat, and other sources
- **Error Handling**: Robust error handling and data validation
- **API Key Management**: Secure API key handling

## Files

### Core Scripts

- [`weather_underground_london.py`](weather_underground_london.py) - Main Weather Underground client and data fetching script
- [`example_weather_underground_integration.py`](example_weather_underground_integration.py) - Integration with existing weather sources
- [`requirements-weather-underground.txt`](requirements-weather-underground.txt) - Python dependencies

### Usage Examples

#### Basic Current Weather

```bash
python weather_underground_london.py --apikey YOUR_API_KEY --current
```

#### Hourly Forecast

```bash
python weather_underground_london.py --apikey YOUR_API_KEY --hourly 48
```

#### Historical Data

```bash
python weather_underground_london.py --apikey YOUR_API_KEY --historical --start-date 20231201 --end-date 20231207
```

#### CSV Export

```bash
python weather_underground_london.py --apikey YOUR_API_KEY --current --csv london_weather_current.csv
```

#### Multi-Source Integration

```bash
python example_weather_underground_integration.py --wu-key YOUR_WU_API_KEY --export-csv london_weather
```

## API Requirements

### Weather Underground API

1. **Sign up**: Visit [Weather Underground API](https://www.wunderground.com/member/api-keys) to obtain an API key
2. **API Key**: Required for all requests
3. **Rate Limits**: Vary by subscription tier
4. **Data Format**: JSON responses with metric units

### Data Sources

The integration supports multiple weather data sources:

| Source              | Type               | Resolution | Coverage           | Best For                |
| ------------------- | ------------------ | ---------- | ------------------ | ----------------------- |
| Weather Underground | Real-time PWS      | 5-15 min   | Global PWS network | Real-time monitoring    |
| Met Office          | Official forecasts | Hourly     | UK-wide            | Authoritative forecasts |
| Meteostat           | Historical         | Daily      | Global             | Backtesting             |
| Weather2Geo         | Current conditions | Real-time  | Global             | Quick lookups           |

## Data Structure

### Current Conditions

```json
{
  "station_id": "ILONDONL9",
  "station_name": "Heathrow, United Kingdom",
  "location": "London, UK",
  "timestamp": "2024-01-15T14:30:00+00:00",
  "temperature": 8.5,
  "feels_like": 6.2,
  "humidity": 82,
  "dewpoint": 5.8,
  "wind_speed": 15,
  "wind_direction": 240,
  "wind_gust": 22,
  "pressure": 1013.2,
  "visibility": 10.0,
  "uv_index": 2,
  "precipitation_1h": 0.0,
  "precipitation_6h": 0.2,
  "precipitation_24h": 1.5,
  "weather_condition": "Light Rain",
  "icon_code": 11
}
```

### Hourly Forecast

```json
{
  "timestamp": "2024-01-15T15:00:00+00:00",
  "temperature": 9.0,
  "feels_like": 7.1,
  "humidity": 78,
  "dewpoint": 5.5,
  "wind_speed": 14,
  "wind_direction": 235,
  "wind_gust": 20,
  "pressure": 1012.8,
  "precipitation_probability": 60,
  "precipitation_amount": 0.5,
  "snow_amount": 0.0,
  "uv_index": 1,
  "visibility": 9.5,
  "weather_condition": "Rain Likely",
  "icon_code": 12,
  "day_ind": "D"
}
```

### Daily Forecast

```json
{
  "date": "2024-01-15T00:00:00+00:00",
  "max_temp": 10.5,
  "min_temp": 6.2,
  "avg_temp": 8.3,
  "max_feels_like": 8.8,
  "min_feels_like": 3.9,
  "avg_humidity": 75,
  "max_wind_speed": 18,
  "avg_wind_speed": 12,
  "wind_direction": 240,
  "precipitation_probability": 70,
  "precipitation_amount": 3.2,
  "snow_amount": 0.0,
  "uv_index": 3,
  "sunrise": "08:15",
  "sunset": "16:45",
  "moon_phase": "Waning Gibbous",
  "weather_condition": "Rain",
  "icon_code": 12
}
```

## CSV Output

All scripts support CSV export with the following features:

- **Metadata Columns**: Data source, location, fetch timestamp
- **Structured Format**: Consistent column ordering
- **Multiple Files**: Separate files for different data types
- **Pandas Integration**: Uses pandas for data processing

### CSV File Types

- `*_current.csv` - Current weather conditions
- `*_hourly.csv` - Hourly forecast data
- `*_daily.csv` - Daily forecast data
- `*_historical.csv` - Historical weather data

## Error Handling

The scripts include comprehensive error handling:

- **API Errors**: Network issues, rate limits, invalid keys
- **Data Validation**: Range checks for temperature, humidity, etc.
- **Missing Data**: Graceful handling of incomplete responses
- **Logging**: Detailed logging for debugging

## Integration with Market Analysis

Weather Underground data is particularly valuable for:

### Real-time Monitoring

- High-frequency updates from PWS network
- Local weather conditions affecting markets
- Immediate response to weather events

### Forecast Analysis

- Detailed precipitation forecasts
- Wind speed and direction predictions
- Temperature trend analysis

### Historical Backtesting

- Past weather patterns correlation
- Seasonal trend analysis
- Extreme weather event studies

### Multi-source Validation

- Cross-validation with official sources
- Data quality assessment
- Robust analysis through redundancy

## Configuration

### Environment Variables

```bash
export WEATHER_UNDERGROUND_API_KEY="your_api_key_here"
```

### Command Line Options

- `--apikey`: Weather Underground API key
- `--station-id`: Specific weather station ID
- `--csv`: Output file for CSV export
- `--json`: JSON output format
- `--validate`: Enable data validation
- `--historical`: Fetch historical data

## Dependencies

Install required packages:

```bash
pip install -r requirements-weather-underground.txt
```

### Required Packages

- `requests>=2.25.0` - HTTP client for API requests
- `pandas>=1.3.0` - Data processing and CSV export

## Best Practices

### API Usage

- Respect rate limits and usage quotas
- Cache frequently accessed data
- Handle API key securely

### Data Processing

- Validate data ranges and formats
- Handle missing or invalid values
- Use appropriate data types

### Integration

- Combine multiple data sources
- Cross-validate critical data
- Implement fallback mechanisms

## Troubleshooting

### Common Issues

1. **API Key Errors**

   - Verify API key is valid and active
   - Check API key permissions

2. **Rate Limit Exceeded**

   - Implement request throttling
   - Use cached data when possible

3. **Data Validation Failures**

   - Check data ranges and formats
   - Handle edge cases gracefully

4. **Network Issues**
   - Implement retry logic
   - Use appropriate timeouts

## Contributing

When extending the Weather Underground integration:

1. Follow existing code patterns
2. Add comprehensive error handling
3. Include data validation
4. Update documentation
5. Test with multiple scenarios

## License

This code is provided for educational and research purposes. Ensure compliance with Weather Underground's terms of service and API usage policies.
