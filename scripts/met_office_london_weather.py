#!/usr/bin/env python3
"""
Met Office Weather DataHub Integration for London Weather Patterns

This script integrates the Met Office Weather DataHub utilities to provide
official UK weather data for London, enhancing weather-market correlation analysis.

Requirements:
- Met Office Weather DataHub API key (obtain from https://www.metoffice.gov.uk/services/data)
- requests library

Usage:
    python met_office_london_weather.py --apikey YOUR_API_KEY [options]
"""

import requests
import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Met Office API configuration
BASE_URL = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/"
LONDON_COORDINATES = {
    'latitude': 51.5074,  # Westminster, Central London
    'longitude': -0.1278
}

class MetOfficeWeatherClient:
    """Client for accessing Met Office Weather DataHub site-specific forecasts."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'apikey': api_key
        })

    def get_forecast(self,
                    latitude: float = LONDON_COORDINATES['latitude'],
                    longitude: float = LONDON_COORDINATES['longitude'],
                    timesteps: str = 'hourly',
                    include_location: bool = True,
                    exclude_metadata: bool = False) -> Dict:
        """
        Retrieve weather forecast for specified location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            timesteps: Frequency of timesteps ('hourly', 'three-hourly', 'daily')
            include_location: Whether to include location name in response
            exclude_metadata: Whether to exclude parameter metadata

        Returns:
            Dictionary containing forecast data
        """
        url = f"{BASE_URL}{timesteps}"

        params = {
            'latitude': latitude,
            'longitude': longitude,
            'includeLocationName': str(include_location).lower(),
            'excludeParameterMetadata': str(exclude_metadata).lower()
        }

        try:
            logger.info(f"Requesting forecast for {latitude}, {longitude} with {timesteps} timesteps")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info("Successfully retrieved forecast data")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve forecast: {e}")
            raise

    def get_current_conditions(self) -> Dict:
        """Get current weather conditions for London."""
        forecast = self.get_forecast(timesteps='hourly')
        if 'features' in forecast and len(forecast['features']) > 0:
            current_feature = forecast['features'][0]
            return {
                'location': current_feature.get('properties', {}).get('location', {}).get('name', 'London'),
                'temperature': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('screenTemperature'),
                'weather_type': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('significantWeatherCode'),
                'wind_speed': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('windSpeed10m'),
                'wind_direction': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('windDirectionFrom10m'),
                'humidity': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('screenRelativeHumidity'),
                'precipitation': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('totalPrecipAmount'),
                'timestamp': current_feature.get('properties', {}).get('timeSeries', [{}])[0].get('time')
            }
        return {}

    def get_hourly_forecast(self, hours: int = 24) -> List[Dict]:
        """Get hourly forecast for specified number of hours."""
        forecast = self.get_forecast(timesteps='hourly')
        hourly_data = []

        if 'features' in forecast and len(forecast['features']) > 0:
            time_series = forecast['features'][0].get('properties', {}).get('timeSeries', [])

            for i, ts in enumerate(time_series[:hours]):
                hourly_data.append({
                    'timestamp': ts.get('time'),
                    'temperature': ts.get('screenTemperature'),
                    'feels_like': ts.get('feelsLikeTemperature'),
                    'weather_code': ts.get('significantWeatherCode'),
                    'wind_speed': ts.get('windSpeed10m'),
                    'wind_direction': ts.get('windDirectionFrom10m'),
                    'humidity': ts.get('screenRelativeHumidity'),
                    'precipitation': ts.get('totalPrecipAmount'),
                    'visibility': ts.get('visibility'),
                    'pressure': ts.get('mslp')
                })

        return hourly_data

    def get_daily_forecast(self, days: int = 5) -> List[Dict]:
        """Get daily forecast for specified number of days."""
        forecast = self.get_forecast(timesteps='daily')
        daily_data = []

        if 'features' in forecast and len(forecast['features']) > 0:
            time_series = forecast['features'][0].get('properties', {}).get('timeSeries', [])

            for i, ts in enumerate(time_series[:days]):
                daily_data.append({
                    'date': ts.get('time'),
                    'max_temp': ts.get('maxScreenTemperature'),
                    'min_temp': ts.get('minScreenTemperature'),
                    'weather_code': ts.get('significantWeatherCode'),
                    'max_wind_speed': ts.get('max10mWindGust'),
                    'total_precipitation': ts.get('totalPrecipAmount'),
                    'humidity': ts.get('screenRelativeHumidity')
                })

        return daily_data

def format_weather_output(data: Dict) -> str:
    """Format weather data for display."""
    if not data:
        return "No weather data available"

    output = f"""
🌤️  London Weather Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Location: {data.get('location', 'London')}
🌡️  Temperature: {data.get('temperature', 'N/A')}°C
🌤️  Conditions: {data.get('weather_type', 'N/A')}
💨 Wind: {data.get('wind_speed', 'N/A')} mph {data.get('wind_direction', 'N/A')}°
💧 Humidity: {data.get('humidity', 'N/A')}%
🌧️  Precipitation: {data.get('precipitation', 'N/A')} mm
🕒 Last Updated: {data.get('timestamp', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return output

def main():
    parser = argparse.ArgumentParser(
        description="Retrieve official UK weather data for London using Met Office Weather DataHub"
    )
    parser.add_argument(
        "-k", "--apikey",
        required=True,
        help="Met Office Weather DataHub API key"
    )
    parser.add_argument(
        "-t", "--timesteps",
        choices=['hourly', 'three-hourly', 'daily'],
        default='hourly',
        help="Frequency of forecast timesteps (default: hourly)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours for hourly forecast (default: 24)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Number of days for daily forecast (default: 5)"
    )
    parser.add_argument(
        "--current",
        action='store_true',
        help="Get current weather conditions only"
    )
    parser.add_argument(
        "--json",
        action='store_true',
        help="Output data in JSON format"
    )
    parser.add_argument(
        "--latitude",
        type=float,
        default=LONDON_COORDINATES['latitude'],
        help=f"Latitude (default: {LONDON_COORDINATES['latitude']} - London)"
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=LONDON_COORDINATES['longitude'],
        help=f"Longitude (default: {LONDON_COORDINATES['longitude']} - London)"
    )

    args = parser.parse_args()

    try:
        client = MetOfficeWeatherClient(args.apikey)

        if args.current:
            # Get current conditions
            current = client.get_current_conditions()
            if args.json:
                print(json.dumps(current, indent=2))
            else:
                print(format_weather_output(current))

        elif args.timesteps == 'daily':
            # Get daily forecast
            daily = client.get_daily_forecast(args.days)
            if args.json:
                print(json.dumps(daily, indent=2))
            else:
                print("📅 London Daily Weather Forecast")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                for day in daily:
                    print(f"📆 {day['date'][:10]}: {day.get('min_temp', 'N/A')}°C - {day.get('max_temp', 'N/A')}°C, {day.get('weather_code', 'N/A')}")

        else:
            # Get hourly forecast
            hourly = client.get_hourly_forecast(args.hours)
            if args.json:
                print(json.dumps(hourly, indent=2))
            else:
                print("🕒 London Hourly Weather Forecast")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                for hour in hourly[:12]:  # Show first 12 hours
                    time = datetime.fromisoformat(hour['timestamp'].replace('Z', '+00:00'))
                    print(f"🕐 {time.strftime('%H:%M')}: {hour.get('temperature', 'N/A')}°C, {hour.get('weather_code', 'N/A')}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()