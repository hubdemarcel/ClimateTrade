#!/usr/bin/env python3
"""
Example Integration: US National Weather Service (NWS) API with Existing Weather Sources

This script demonstrates how to integrate official US National Weather Service data
with existing weather sources (Weather2Geo) for enhanced weather-market correlation analysis.

The NWS provides authoritative US weather data, particularly valuable for:
- New York City weather patterns and market impacts
- Official US government weather forecasts and alerts
- High-quality meteorological data for financial analysis
- Comprehensive US weather intelligence

Usage:
    python example_nws_integration.py
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import requests

# Mock Weather2Geo integration (would import actual Weather2Geo in real usage)
class Weather2GeoMock:
    """Mock Weather2Geo client for demonstration."""

    def get_weather_data(self, location_query: str) -> Dict:
        """Mock method to get weather data from Weather2Geo."""
        # In real implementation, this would call Weather2Geo's API
        return {
            'source': 'Weather2Geo (MSN Weather API)',
            'location': location_query,
            'temperature': 22.5,
            'condition': 'Partly cloudy',
            'humidity': 60,
            'wind_speed': 15,
            'data_quality': 'Geolocation-based'
        }

class NWSWeatherClient:
    """Client for US National Weather Service API."""

    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'climatetrade-integration/1.0 (contact@example.com)',
            'Accept': 'application/geo+json'
        })

    def get_point_data(self, lat: float, lon: float) -> Dict:
        """Get point metadata for a latitude/longitude."""
        url = f"{self.base_url}/points/{lat},{lon}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_forecast(self, grid_id: str, grid_x: int, grid_y: int) -> Dict:
        """Get forecast for a grid point."""
        url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_hourly_forecast(self, grid_id: str, grid_x: int, grid_y: int) -> Dict:
        """Get hourly forecast for a grid point."""
        url = f"{self.base_url}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast/hourly"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_alerts(self, area: str = None) -> Dict:
        """Get active weather alerts."""
        url = f"{self.base_url}/alerts/active"
        params = {}
        if area:
            params['area'] = area
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_nyc_weather_data(self) -> Dict:
        """Get comprehensive weather data for NYC."""
        # NYC coordinates
        nyc_lat, nyc_lon = 40.7128, -74.0060

        try:
            # Get point data
            point_data = self.get_point_data(nyc_lat, nyc_lon)
            grid_id = point_data['properties']['gridId']
            grid_x = point_data['properties']['gridX']
            grid_y = point_data['properties']['gridY']

            # Get forecasts
            forecast = self.get_forecast(grid_id, grid_x, grid_y)
            hourly_forecast = self.get_hourly_forecast(grid_id, grid_x, grid_y)

            # Get alerts for NY area
            alerts = self.get_alerts('NY')

            return {
                'point_data': point_data,
                'forecast': forecast,
                'hourly_forecast': hourly_forecast,
                'alerts': alerts,
                'location': 'New York City, NY'
            }

        except Exception as e:
            return {'error': str(e)}

class WeatherMarketAnalyzer:
    """Analyzes weather data from multiple sources for market correlation."""

    def __init__(self):
        self.nws = NWSWeatherClient()
        self.weather2geo = Weather2GeoMock()

    def get_comprehensive_weather_report(self) -> Dict:
        """Get weather data from all available sources."""

        report = {
            'timestamp': datetime.now().isoformat(),
            'location': 'New York City, NY',
            'sources': {}
        }

        try:
            # Get NWS data
            nws_data = self.nws.get_nyc_weather_data()

            if 'error' not in nws_data:
                report['sources']['nws'] = {
                    'forecast': nws_data['forecast'],
                    'hourly_forecast': nws_data['hourly_forecast'],
                    'alerts': nws_data['alerts'],
                    'data_quality': 'Official US Government (NOAA/NWS)',
                    'coverage': 'US-wide authoritative forecasts',
                    'update_frequency': 'Hourly with detailed parameters'
                }
            else:
                report['sources']['nws'] = {'error': nws_data['error']}

        except Exception as e:
            report['sources']['nws'] = {'error': str(e)}

        try:
            # Get Weather2Geo data
            weather2geo_data = self.weather2geo.get_weather_data('New York City')
            report['sources']['weather2geo'] = weather2geo_data

        except Exception as e:
            report['sources']['weather2geo'] = {'error': str(e)}

        return report

    def analyze_weather_market_impacts(self, weather_data: Dict) -> Dict:
        """Analyze potential market impacts based on weather patterns."""

        analysis = {
            'weather_events': [],
            'market_impacts': [],
            'recommendations': []
        }

        # Extract NWS data
        nws = weather_data.get('sources', {}).get('nws', {})

        if 'forecast' in nws:
            forecast = nws['forecast']
            periods = forecast.get('properties', {}).get('periods', [])

            for period in periods[:7]:  # Next 7 periods (typically 12-24 hours)
                temp = period.get('temperature')
                detailed_forecast = period.get('detailedForecast', '').lower()

                # Temperature analysis
                if temp is not None:
                    if temp < 0:
                        analysis['weather_events'].append('Extreme cold weather')
                        analysis['market_impacts'].append('Potential heating costs impact on energy markets')
                    elif temp > 32:  # 90°F
                        analysis['weather_events'].append('Heat alert')
                        analysis['market_impacts'].append('Potential cooling costs and energy demand spikes')

                # Precipitation analysis
                if 'rain' in detailed_forecast or 'snow' in detailed_forecast:
                    if 'heavy' in detailed_forecast:
                        analysis['weather_events'].append('Heavy precipitation forecast')
                        analysis['market_impacts'].append('Potential flooding impacts on property and transportation')
                    else:
                        analysis['weather_events'].append('Precipitation forecast')
                        analysis['market_impacts'].append('Weather-related transportation disruptions possible')

                # Wind analysis
                if 'wind' in detailed_forecast and ('strong' in detailed_forecast or 'gusty' in detailed_forecast):
                    analysis['weather_events'].append('Strong winds forecast')
                    analysis['market_impacts'].append('Potential disruption to transportation and supply chains')

        # Alert analysis
        if 'alerts' in nws:
            alerts = nws['alerts']
            features = alerts.get('features', [])

            for alert in features:
                properties = alert.get('properties', {})
                event = properties.get('event', '')
                severity = properties.get('severity', '')

                if severity in ['Severe', 'Extreme']:
                    analysis['weather_events'].append(f'Severe weather alert: {event}')
                    analysis['market_impacts'].append('High-impact weather event may affect multiple market sectors')

        # Generate recommendations
        if analysis['weather_events']:
            analysis['recommendations'].append('Monitor weather-sensitive market sectors (energy, agriculture, transportation)')
            analysis['recommendations'].append('Consider weather derivatives or hedging strategies')
            analysis['recommendations'].append('Track commodity prices for weather-impacted goods')
            analysis['recommendations'].append('Monitor NWS alerts for real-time updates')

        return analysis

def print_weather_report(report: Dict):
    """Print a formatted weather report."""
    print("\n[*] COMPREHENSIVE NYC WEATHER REPORT")
    print("=" * 60)
    print(f"Location: {report['location']}")
    print(f"Generated: {report['timestamp']}")

    for source_name, source_data in report['sources'].items():
        print(f"\nSource: {source_name.upper()}")
        print("-" * 40)

        if 'error' in source_data:
            print(f"Error: {source_data['error']}")
            continue

        if source_name == 'nws':
            if 'forecast' in source_data:
                forecast = source_data['forecast']
                periods = forecast.get('properties', {}).get('periods', [])

                print("7-Day Forecast:")
                for period in periods[:7]:
                    name = period.get('name', 'N/A')
                    temp = period.get('temperature', 'N/A')
                    unit = period.get('temperatureUnit', '')
                    condition = period.get('shortForecast', 'N/A')
                    print(f"   {name}: {temp}°{unit}, {condition}")

            if 'alerts' in source_data:
                alerts = source_data['alerts']
                features = alerts.get('features', [])
                if features:
                    print("Active Weather Alerts:")
                    for alert in features[:3]:  # Show first 3 alerts
                        properties = alert.get('properties', {})
                        event = properties.get('event', 'Unknown')
                        area = properties.get('areaDesc', 'Unknown area')
                        print(f"   ALERT: {event} in {area}")
                else:
                    print("No active weather alerts")

        elif source_name == 'weather2geo':
            print("Current Conditions:")
            print(f"   Temperature: {source_data.get('temperature', 'N/A')}°C")
            print(f"   Conditions: {source_data.get('condition', 'N/A')}")
            print(f"   Humidity: {source_data.get('humidity', 'N/A')}%")
            print(f"   Wind: {source_data.get('wind_speed', 'N/A')} mph")
            print(f"   Data Quality: {source_data.get('data_quality', 'N/A')}")

def print_market_analysis(analysis: Dict):
    """Print market impact analysis."""
    print("\n[*] WEATHER-MARKET CORRELATION ANALYSIS")
    print("=" * 60)

    if analysis['weather_events']:
        print("Weather Events Detected:")
        for event in analysis['weather_events']:
            print(f"   • {event}")
    else:
        print("No significant weather events detected")

    if analysis['market_impacts']:
        print("\nPotential Market Impacts:")
        for impact in analysis['market_impacts']:
            print(f"   • {impact}")
    else:
        print("\nNo significant market impacts identified")

    if analysis['recommendations']:
        print("\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"   • {rec}")

def main():
    parser = argparse.ArgumentParser(
        description="Integrate NWS weather data with existing sources for market analysis"
    )
    parser.add_argument(
        "--json-output",
        action='store_true',
        help="Output results in JSON format"
    )
    parser.add_argument(
        "--save-report",
        type=str,
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    try:
        analyzer = WeatherMarketAnalyzer()

        # Get comprehensive weather report
        weather_report = analyzer.get_comprehensive_weather_report()

        # Analyze market impacts
        market_analysis = analyzer.analyze_weather_market_impacts(weather_report)

        if args.json_output:
            # Output JSON
            output = {
                'weather_report': weather_report,
                'market_analysis': market_analysis
            }
            print(json.dumps(output, indent=2))
        else:
            # Print formatted report
            print_weather_report(weather_report)
            print_market_analysis(market_analysis)

        # Save to file if requested
        if args.save_report:
            output = {
                'weather_report': weather_report,
                'market_analysis': market_analysis
            }
            with open(args.save_report, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"\nReport saved to: {args.save_report}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()