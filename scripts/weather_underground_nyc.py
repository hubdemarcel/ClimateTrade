#!/usr/bin/env python3
"""
Weather Underground Data Fetching for New York City (NYC) Weather Data

This script integrates Weather Underground API to provide current and historical
weather data for NYC, with CSV output and comprehensive error handling.

Weather Underground provides detailed weather observations from personal weather
stations (PWS) and official weather stations worldwide.

Requirements:
- Weather Underground API key (obtain from https://www.wunderground.com/member/api-keys)
- requests library
- pandas for data processing

Usage:
    python weather_underground_nyc.py --apikey YOUR_API_KEY [options]
"""

import requests
import argparse
import json
import sys
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Weather Underground API configuration
BASE_URL = "https://api.weather.com/v3"
NYC_COORDINATES = {
    'latitude': 40.7128,
    'longitude': -74.0060
}
NYC_STATION_ID = "KLGA"  # LaGuardia Airport station for Polymarket resolution

class WeatherUndergroundClient:
    """Client for accessing Weather Underground API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WeatherDataFetcher/1.0',
            'Accept': 'application/json'
        })

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Weather Underground API."""
        url = f"{BASE_URL}/{endpoint}"

        # Add API key to params
        if params is None:
            params = {}
        params['apiKey'] = self.api_key
        params['format'] = 'json'
        params['units'] = 'm'  # Metric units

        try:
            logger.info(f"Making request to: {endpoint}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info("Successfully retrieved data")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def get_current_conditions(self, station_id: str = NYC_STATION_ID) -> Dict:
        """Get current weather conditions for NYC."""
        try:
            # Get current observations
            endpoint = f"wxobs/current"
            params = {
                'stationId': station_id,
                'numericPrecision': 'decimal'
            }

            data = self._make_request(endpoint, params)

            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]

                return {
                    'station_id': obs.get('stationID'),
                    'station_name': obs.get('stationName'),
                    'location': 'New York City, NY',
                    'timestamp': obs.get('obsTimeLocal'),
                    'temperature': obs.get('temp'),
                    'feels_like': obs.get('feelsLike'),
                    'humidity': obs.get('rh'),
                    'dewpoint': obs.get('dewpt'),
                    'wind_speed': obs.get('windSpeed'),
                    'wind_direction': obs.get('windDir'),
                    'wind_gust': obs.get('windGust'),
                    'pressure': obs.get('pressure'),
                    'visibility': obs.get('visibility'),
                    'uv_index': obs.get('uvIndex'),
                    'precipitation_1h': obs.get('precip1Hour'),
                    'precipitation_6h': obs.get('precip6Hour'),
                    'precipitation_24h': obs.get('precip24Hour'),
                    'weather_condition': obs.get('wxPhraseLong'),
                    'icon_code': obs.get('iconCode'),
                    'latitude': obs.get('lat'),
                    'longitude': obs.get('lon')
                }
            else:
                logger.warning("No current observations found")
                return {}

        except Exception as e:
            logger.error(f"Failed to get current conditions: {e}")
            raise

    def get_hourly_forecast(self, latitude: float = NYC_COORDINATES['latitude'],
                           longitude: float = NYC_COORDINATES['longitude'],
                           hours: int = 24) -> List[Dict]:
        """Get hourly weather forecast."""
        try:
            endpoint = "wxfcst/hourly/7day"
            params = {
                'lat': latitude,
                'lon': longitude,
                'hours': min(hours, 168)  # Max 7 days (168 hours)
            }

            data = self._make_request(endpoint, params)

            hourly_data = []
            if 'forecasts' in data:
                for forecast in data['forecasts'][:hours]:
                    hourly_data.append({
                        'timestamp': forecast.get('fcstValidLocal'),
                        'temperature': forecast.get('temp'),
                        'feels_like': forecast.get('feelsLike'),
                        'humidity': forecast.get('rh'),
                        'dewpoint': forecast.get('dewpt'),
                        'wind_speed': forecast.get('windSpeed'),
                        'wind_direction': forecast.get('windDir'),
                        'wind_gust': forecast.get('windGust'),
                        'pressure': forecast.get('pressureMeanSeaLevel'),
                        'precipitation_probability': forecast.get('precipChance'),
                        'precipitation_amount': forecast.get('qpf'),
                        'snow_amount': forecast.get('qsf'),
                        'uv_index': forecast.get('uvIndex'),
                        'visibility': forecast.get('visibility'),
                        'weather_condition': forecast.get('wxPhraseLong'),
                        'icon_code': forecast.get('iconCode'),
                        'day_ind': forecast.get('dayInd')  # D=Day, N=Night
                    })

            return hourly_data

        except Exception as e:
            logger.error(f"Failed to get hourly forecast: {e}")
            raise

    def get_daily_forecast(self, latitude: float = NYC_COORDINATES['latitude'],
                          longitude: float = NYC_COORDINATES['longitude'],
                          days: int = 7) -> List[Dict]:
        """Get daily weather forecast."""
        try:
            endpoint = "wxfcst/daily/10day"
            params = {
                'lat': latitude,
                'lon': longitude,
                'days': min(days, 10)
            }

            data = self._make_request(endpoint, params)

            daily_data = []
            if 'forecasts' in data:
                for forecast in data['forecasts'][:days]:
                    daily_data.append({
                        'date': forecast.get('fcstValidLocal'),
                        'max_temp': forecast.get('maxTemp'),
                        'min_temp': forecast.get('minTemp'),
                        'avg_temp': forecast.get('avgTemp'),
                        'max_feels_like': forecast.get('maxFeelsLike'),
                        'min_feels_like': forecast.get('minFeelsLike'),
                        'avg_humidity': forecast.get('avgHumidity'),
                        'max_wind_speed': forecast.get('maxWindSpeed'),
                        'avg_wind_speed': forecast.get('avgWindSpeed'),
                        'wind_direction': forecast.get('windDir'),
                        'precipitation_probability': forecast.get('precipChance'),
                        'precipitation_amount': forecast.get('qpf'),
                        'snow_amount': forecast.get('qsf'),
                        'uv_index': forecast.get('uvIndex'),
                        'sunrise': forecast.get('sunrise'),
                        'sunset': forecast.get('sunset'),
                        'moon_phase': forecast.get('moonPhase'),
                        'weather_condition': forecast.get('wxPhraseLong'),
                        'icon_code': forecast.get('iconCode')
                    })

            return daily_data

        except Exception as e:
            logger.error(f"Failed to get daily forecast: {e}")
            raise

    def get_historical_data(self, station_id: str = NYC_STATION_ID,
                           start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get historical weather data for a date range."""
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')

            endpoint = "wxobs/historical/daily"
            params = {
                'stationId': station_id,
                'startDate': start_date,
                'endDate': end_date,
                'numericPrecision': 'decimal'
            }

            data = self._make_request(endpoint, params)

            historical_data = []
            if 'observations' in data:
                for obs in data['observations']:
                    historical_data.append({
                        'station_id': obs.get('stationID'),
                        'timestamp': obs.get('obsTimeLocal'),
                        'temperature': obs.get('tempAvg'),
                        'max_temp': obs.get('tempMax'),
                        'min_temp': obs.get('tempMin'),
                        'humidity': obs.get('rhAvg'),
                        'dewpoint': obs.get('dewptAvg'),
                        'wind_speed': obs.get('windSpeedAvg'),
                        'max_wind_speed': obs.get('windSpeedMax'),
                        'wind_direction': obs.get('windDirAvg'),
                        'pressure': obs.get('pressureAvg'),
                        'precipitation': obs.get('precipTotal'),
                        'snow': obs.get('snowTotal'),
                        'visibility': obs.get('visibilityAvg'),
                        'uv_index': obs.get('uvIndexAvg'),
                        'weather_condition': obs.get('wxPhraseLong'),
                        'icon_code': obs.get('iconCode')
                    })

            return historical_data

        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            raise

def validate_weather_data(data: Dict) -> bool:
    """Validate weather data structure and values."""
    if not isinstance(data, dict):
        return False

    # Check for required fields
    required_fields = ['temperature', 'humidity', 'timestamp']
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.warning(f"Missing required field: {field}")
            return False

    # Validate temperature range (-50°C to 60°C)
    if 'temperature' in data and data['temperature'] is not None:
        temp = data['temperature']
        if not (-50 <= temp <= 60):
            logger.warning(f"Temperature out of valid range: {temp}°C")
            return False

    # Validate humidity (0-100%)
    if 'humidity' in data and data['humidity'] is not None:
        humidity = data['humidity']
        if not (0 <= humidity <= 100):
            logger.warning(f"Humidity out of valid range: {humidity}%")
            return False

    return True

def save_to_csv(data: Union[Dict, List[Dict]], filename: str, data_type: str = 'current'):
    """Save weather data to CSV file."""
    try:
        if isinstance(data, dict):
            data = [data]

        if not data:
            logger.warning("No data to save to CSV")
            return

        # Ensure output directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

        # Convert to DataFrame for easier CSV handling
        df = pd.DataFrame(data)

        # Add metadata columns
        df['data_source'] = 'Weather Underground'
        df['fetch_timestamp'] = datetime.now().isoformat()
        df['location'] = 'New York City, NY'

        # Reorder columns to put metadata first
        cols = ['data_source', 'location', 'fetch_timestamp'] + [col for col in df.columns if col not in ['data_source', 'location', 'fetch_timestamp']]
        df = df[cols]

        # Save to CSV
        df.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename} ({len(data)} records)")

    except Exception as e:
        logger.error(f"Failed to save data to CSV: {e}")
        raise

def format_weather_output(data: Dict) -> str:
    """Format weather data for display."""
    if not data:
        return "No weather data available"

    output = f"""
🌤️  New York City Weather Report (Weather Underground)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Location: {data.get('location', 'New York City')}
🏢 Station: {data.get('station_name', 'N/A')} ({data.get('station_id', 'N/A')})
🌡️  Temperature: {data.get('temperature', 'N/A')}°C
🤒 Feels Like: {data.get('feels_like', 'N/A')}°C
💧 Humidity: {data.get('humidity', 'N/A')}%
🌧️  Precipitation (1h): {data.get('precipitation_1h', 'N/A')} mm
💨 Wind: {data.get('wind_speed', 'N/A')} km/h {data.get('wind_direction', 'N/A')}°
👁️  Visibility: {data.get('visibility', 'N/A')} km
🕒 Last Updated: {data.get('timestamp', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return output

def main():
    parser = argparse.ArgumentParser(
        description="Retrieve weather data for New York City using Weather Underground API"
    )
    parser.add_argument(
        "-k", "--apikey",
        required=True,
        help="Weather Underground API key"
    )
    parser.add_argument(
        "--station-id",
        default=NYC_STATION_ID,
        help=f"Weather station ID (default: {NYC_STATION_ID})"
    )
    parser.add_argument(
        "--current",
        action='store_true',
        help="Get current weather conditions only"
    )
    parser.add_argument(
        "--hourly",
        type=int,
        default=24,
        help="Number of hours for hourly forecast (default: 24, max: 168)"
    )
    parser.add_argument(
        "--daily",
        type=int,
        default=7,
        help="Number of days for daily forecast (default: 7, max: 10)"
    )
    parser.add_argument(
        "--historical",
        action='store_true',
        help="Get historical data for the past 7 days"
    )
    parser.add_argument(
        "--start-date",
        help="Start date for historical data (YYYYMMDD format)"
    )
    parser.add_argument(
        "--end-date",
        help="End date for historical data (YYYYMMDD format)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Save data to CSV file"
    )
    parser.add_argument(
        "--json",
        action='store_true',
        help="Output data in JSON format"
    )
    parser.add_argument(
        "--validate",
        action='store_true',
        help="Validate data before output"
    )

    args = parser.parse_args()

    try:
        client = WeatherUndergroundClient(args.apikey)

        if args.current:
            # Get current conditions
            current = client.get_current_conditions(args.station_id)

            if args.validate and not validate_weather_data(current):
                logger.error("Data validation failed")
                sys.exit(1)

            if args.json:
                print(json.dumps(current, indent=2))
            else:
                print(format_weather_output(current))

            if args.csv:
                save_to_csv(current, args.csv, 'current')

        elif args.historical:
            # Get historical data
            historical = client.get_historical_data(
                args.station_id,
                args.start_date,
                args.end_date
            )

            if args.validate:
                valid_data = [d for d in historical if validate_weather_data(d)]
                if len(valid_data) != len(historical):
                    logger.warning(f"Filtered out {len(historical) - len(valid_data)} invalid records")
                historical = valid_data

            if args.json:
                print(json.dumps(historical, indent=2))
            else:
                print(f"📊 Historical Weather Data: {len(historical)} records")
                if historical:
                    print(f"Date Range: {historical[0]['timestamp'][:10]} to {historical[-1]['timestamp'][:10]}")

            if args.csv:
                save_to_csv(historical, args.csv, 'historical')

        elif args.daily > 0:
            # Get daily forecast
            daily = client.get_daily_forecast(days=args.daily)

            if args.json:
                print(json.dumps(daily, indent=2))
            else:
                print("📅 New York City Daily Weather Forecast (Weather Underground)")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                for day in daily:
                    date = day.get('date', 'N/A')[:10]
                    max_t = day.get('max_temp', 'N/A')
                    min_t = day.get('min_temp', 'N/A')
                    precip = day.get('precipitation_amount', 'N/A')
                    condition = day.get('weather_condition', 'N/A')
                    print(f"📆 {date}: {min_t}°C - {max_t}°C, {precip}mm rain")
                    print(f"   {condition}")

            if args.csv:
                save_to_csv(daily, args.csv, 'daily_forecast')

        else:
            # Get hourly forecast (default)
            hourly = client.get_hourly_forecast(hours=args.hourly)

            if args.json:
                print(json.dumps(hourly, indent=2))
            else:
                print("🕒 New York City Hourly Weather Forecast (Weather Underground)")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                for hour in hourly[:12]:  # Show first 12 hours
                    time = datetime.fromisoformat(hour['timestamp'].replace('Z', '+00:00'))
                    temp = hour.get('temperature', 'N/A')
                    condition = hour.get('weather_condition', 'N/A')
                    precip_prob = hour.get('precipitation_probability', 'N/A')
                    print(f"🕐 {time.strftime('%H:%M')}: {temp}°C, {condition}, {precip_prob}% precip")

            if args.csv:
                save_to_csv(hourly, args.csv, 'hourly_forecast')

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()