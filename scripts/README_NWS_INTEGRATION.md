# NWS (National Weather Service) API Integration

## Overview

This integration adds official US National Weather Service (NWS) data to the climatetrade project, providing authoritative weather forecasts, alerts, and meteorological data specifically optimized for New York City weather patterns and market correlation analysis.

## Features

### Core Capabilities

- **Official NWS Data**: Access to NOAA/NWS authoritative weather forecasts and alerts
- **NYC-Focused**: Optimized for New York City weather patterns and market impacts
- **Real-time Alerts**: Integration with NWS weather alert system for immediate notifications
- **Multi-source Integration**: Combines NWS data with existing Weather2Geo sources
- **Market Correlation Analysis**: Automated analysis of weather events and their potential market impacts

### Data Sources

- **NWS Forecast API**: 7-day detailed forecasts with hourly granularity
- **NWS Alerts API**: Real-time weather alerts and warnings
- **Grid-based Forecasts**: High-resolution 2.5km grid forecasts
- **Point-based Data**: Location-specific weather data for any US coordinate

## API Integration Details

### NWS API Endpoints Used

- `/points/{lat},{lon}` - Get grid coordinates for a location
- `/gridpoints/{wfo}/{x},{y}/forecast` - Get forecast data
- `/gridpoints/{wfo}/{x},{y}/forecast/hourly` - Get hourly forecast
- `/alerts/active` - Get active weather alerts

### Authentication

- **No API Key Required**: NWS API is free and open
- **User-Agent Header**: Required for all requests (included in client)
- **Rate Limits**: None officially documented, but respectful usage recommended

## Usage

### Basic Usage

```bash
# Run the integration script
python scripts/example_nws_integration.py

# Save results to JSON file
python scripts/example_nws_integration.py --save-report nyc_weather_report.json

# Output in JSON format only
python scripts/example_nws_integration.py --json-output
```

### Integration with Existing Code

```python
from example_nws_integration import NWSWeatherClient, WeatherMarketAnalyzer

# Initialize client
nws_client = NWSWeatherClient()

# Get NYC weather data
nyc_data = nws_client.get_nyc_weather_data()

# Analyze market impacts
analyzer = WeatherMarketAnalyzer()
report = analyzer.get_comprehensive_weather_report()
analysis = analyzer.analyze_weather_market_impacts(report)
```

## Data Quality and Reliability

### NWS Data Characteristics

- **Authority**: Official US government weather data from NOAA/NWS
- **Coverage**: Complete US coverage with high-resolution forecasts
- **Update Frequency**: Forecasts updated hourly, alerts in real-time
- **Accuracy**: High accuracy for US weather patterns
- **Historical Data**: Limited historical data available through API

### Integration Benefits

- **Enhanced Accuracy**: Official government data improves forecast reliability
- **Comprehensive Coverage**: US-wide weather intelligence for market analysis
- **Alert Integration**: Real-time severe weather notifications
- **Multi-source Validation**: Cross-validation with existing Weather2Geo data

## Market Correlation Analysis

### Weather Events Detected

- **Temperature Extremes**: Heat/cold alerts with market impact analysis
- **Precipitation Events**: Rain/snow forecasts and flood risk assessment
- **Wind Events**: High wind warnings and transportation disruption analysis
- **Severe Weather Alerts**: NWS alerts with severity-based market impact scoring

### Market Impact Categories

- **Energy Markets**: Heating/cooling costs, demand spikes
- **Agriculture**: Crop impacts, commodity price movements
- **Transportation**: Supply chain disruptions, logistics impacts
- **Property Markets**: Flood risk, insurance implications
- **Financial Instruments**: Weather derivatives and hedging opportunities

## Technical Implementation

### Dependencies

- `requests` - HTTP client for API calls
- `json` - JSON data handling
- `datetime` - Timestamp management
- `argparse` - Command-line argument parsing

### Architecture

```
NWSWeatherClient
├── get_point_data() - Get grid coordinates
├── get_forecast() - Get forecast data
├── get_hourly_forecast() - Get hourly data
├── get_alerts() - Get weather alerts
└── get_nyc_weather_data() - NYC-specific integration

WeatherMarketAnalyzer
├── get_comprehensive_weather_report() - Multi-source data
├── analyze_weather_market_impacts() - Market correlation
└── print_*() - Formatted output functions
```

### Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **API Errors**: Graceful degradation with error reporting
- **Data Validation**: Type checking and null value handling
- **Rate Limiting**: Built-in delays between requests

## Comparison with Existing Sources

### Weather2Geo (MSN Weather API)

- **Pros**: Global coverage, real-time current conditions
- **Cons**: Commercial data, less detailed forecasts
- **Best For**: Current conditions, global weather patterns

### NWS API

- **Pros**: Official US data, detailed forecasts, free access
- **Cons**: US-only coverage, requires coordinate conversion
- **Best For**: US weather intelligence, authoritative forecasts

### Combined Benefits

- **Enhanced Accuracy**: Official data validates commercial sources
- **Comprehensive Coverage**: US focus complements global Weather2Geo data
- **Alert Integration**: Real-time notifications not available elsewhere
- **Market Intelligence**: Better weather-market correlation analysis

## Future Enhancements

### Potential Improvements

- **Historical Data Integration**: Add NWS historical weather data
- **Radar Data**: Integrate NEXRAD radar imagery
- **Marine Forecasts**: Add coastal and marine weather data
- **Climate Data**: Long-term climate trend analysis
- **Machine Learning**: Predictive market impact modeling

### Additional Endpoints

- `/stations/{stationId}/observations` - Weather station observations
- `/radar/stations` - Radar station data
- `/products` - Text weather products
- `/zones` - Weather zone information

## Configuration

### NYC Coordinates

- **Latitude**: 40.7128°N
- **Longitude**: 74.0060°W
- **Grid ID**: OKX (New York City WFO)
- **Grid Coordinates**: Automatically resolved via API

### User-Agent Header

```
User-Agent: climatetrade-integration/1.0 (contact@example.com)
```

## Troubleshooting

### Common Issues

- **403 Forbidden**: Check User-Agent header is included
- **404 Not Found**: Verify coordinates are within US boundaries
- **429 Too Many Requests**: Implement delays between requests
- **Network Errors**: Check internet connection and API availability

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Code Standards

- Follow PEP 8 style guidelines
- Include docstrings for all functions
- Add type hints where possible
- Handle exceptions gracefully

### Testing

- Unit tests for API client functions
- Integration tests with mock data
- End-to-end tests with live API (rate-limited)

## License and Attribution

### NWS Data Usage

- **Free Access**: NWS API data is free for public use
- **Attribution**: Credit NOAA/NWS as data source
- **Terms of Service**: Follow NWS API terms and conditions
- **Fair Use**: Respectful usage with appropriate delays

### Integration License

- **MIT License**: Open source integration code
- **Commercial Use**: Allowed with attribution
- **Modification**: Permitted with license preservation

## References

### Official Documentation

- [NWS API Documentation](https://www.weather.gov/documentation/services-web-api)
- [NWS API GitHub](https://github.com/weather-gov/api)
- [NOAA Weather Data](https://www.noaa.gov/weather)

### Related Projects

- [Weather2Geo Integration](README_WEATHER2GEO_INTEGRATION.md)
- [Met Office Integration](README_MET_OFFICE_INTEGRATION.md)
- [Real-time Data Integration](README_REAL_TIME_INTEGRATION.md)

---

_This integration enhances climatetrade's weather intelligence capabilities by adding authoritative US weather data, enabling more accurate weather-market correlation analysis for comprehensive financial decision-making._
