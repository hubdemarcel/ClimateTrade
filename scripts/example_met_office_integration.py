#!/usr/bin/env python3
"""
Example Integration: Met Office Weather DataHub with Existing Weather Sources

This script demonstrates how to integrate official UK Met Office weather data
with existing weather sources (Weather2Geo) for enhanced weather-market correlation analysis.

The Met Office provides authoritative UK weather data, particularly valuable for:
- London weather patterns and market impacts
- Official UK government weather forecasts
- High-quality meteorological data for financial analysis

Usage:
    python example_met_office_integration.py --met-office-key YOUR_API_KEY
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

# Import our Met Office client
from met_office_london_weather import MetOfficeWeatherClient

# Mock Weather2Geo integration (would import actual Weather2Geo in real usage)
class Weather2GeoMock:
    """Mock Weather2Geo client for demonstration."""

    def get_weather_data(self, location_query: str) -> Dict:
        """Mock method to get weather data from Weather2Geo."""
        # In real implementation, this would call Weather2Geo's API
        return {
            'source': 'Weather2Geo (MSN Weather API)',
            'location': location_query,
            'temperature': 18.5,
            'condition': 'Partly cloudy',
            'humidity': 65,
            'wind_speed': 12,
            'data_quality': 'Geolocation-based'
        }

class WeatherMarketAnalyzer:
    """Analyzes weather data from multiple sources for market correlation."""

    def __init__(self, met_office_key: str):
        self.met_office = MetOfficeWeatherClient(met_office_key)
        self.weather2geo = Weather2GeoMock()

    def get_comprehensive_weather_report(self) -> Dict:
        """Get weather data from all available sources."""

        report = {
            'timestamp': datetime.now().isoformat(),
            'location': 'London, UK',
            'sources': {}
        }

        try:
            # Get Met Office data
            met_office_current = self.met_office.get_current_conditions()
            met_office_hourly = self.met_office.get_hourly_forecast(12)
            met_office_daily = self.met_office.get_daily_forecast(3)

            report['sources']['met_office'] = {
                'current': met_office_current,
                'hourly_forecast': met_office_hourly,
                'daily_forecast': met_office_daily,
                'data_quality': 'Official UK Government',
                'coverage': 'UK-wide authoritative forecasts',
                'update_frequency': 'Hourly with detailed parameters'
            }

        except Exception as e:
            report['sources']['met_office'] = {'error': str(e)}

        try:
            # Get Weather2Geo data
            weather2geo_data = self.weather2geo.get_weather_data('London')
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

        # Extract Met Office data
        met_office = weather_data.get('sources', {}).get('met_office', {})

        if 'current' in met_office:
            current = met_office['current']

            # Temperature analysis
            temp = current.get('temperature')
            if temp is not None:
                if temp < 5:
                    analysis['weather_events'].append('Cold weather alert')
                    analysis['market_impacts'].append('Potential heating costs impact on energy markets')
                elif temp > 25:
                    analysis['weather_events'].append('Hot weather alert')
                    analysis['market_impacts'].append('Potential cooling costs and drought concerns')

            # Precipitation analysis
            precip = current.get('precipitation')
            if precip is not None and precip > 10:
                analysis['weather_events'].append('Heavy precipitation')
                analysis['market_impacts'].append('Potential flooding impacts on property markets')

            # Wind analysis
            wind = current.get('wind_speed')
            if wind is not None and wind > 20:
                analysis['weather_events'].append('Strong winds')
                analysis['market_impacts'].append('Potential disruption to transportation and supply chains')

        # Daily forecast analysis
        if 'daily_forecast' in met_office:
            daily = met_office['daily_forecast']
            for day in daily[:3]:  # Next 3 days
                max_temp = day.get('maxScreenTemperature')
                precip = day.get('totalPrecipAmount')

                if max_temp is not None and max_temp > 30:
                    analysis['weather_events'].append(f'Heatwave forecast for {day.get("date", "upcoming day")[:10]}')
                    analysis['market_impacts'].append('Extended heat may impact agricultural commodities')

                if precip is not None and precip > 20:
                    analysis['weather_events'].append(f'Heavy rain forecast for {day.get("date", "upcoming day")[:10]}')
                    analysis['market_impacts'].append('Potential weather-related disruptions')

        # Generate recommendations
        if analysis['weather_events']:
            analysis['recommendations'].append('Monitor weather-sensitive market sectors')
            analysis['recommendations'].append('Consider weather derivatives or hedging strategies')
            analysis['recommendations'].append('Track commodity prices for weather-impacted goods')

        return analysis

def print_weather_report(report: Dict):
    """Print a formatted weather report."""
    print("\n🌤️  COMPREHENSIVE LONDON WEATHER REPORT")
    print("=" * 60)
    print(f"📍 Location: {report['location']}")
    print(f"🕒 Generated: {report['timestamp']}")

    for source_name, source_data in report['sources'].items():
        print(f"\n🔍 Source: {source_name.upper()}")
        print("-" * 40)

        if 'error' in source_data:
            print(f"❌ Error: {source_data['error']}")
            continue

        if source_name == 'met_office':
            if 'current' in source_data:
                current = source_data['current']
                print("📊 Current Conditions:")
                print(f"   🌡️  Temperature: {current.get('temperature', 'N/A')}°C")
                print(f"   🌤️  Conditions: {current.get('weather_type', 'N/A')}")
                print(f"   💨 Wind: {current.get('wind_speed', 'N/A')} mph")
                print(f"   💧 Humidity: {current.get('humidity', 'N/A')}%")
                print(f"   🌧️  Precipitation: {current.get('precipitation', 'N/A')} mm")

            if 'daily_forecast' in source_data:
                print("📅 3-Day Forecast:")
                for day in source_data['daily_forecast'][:3]:
                    date = day.get('date', 'N/A')[:10]
                    max_t = day.get('maxScreenTemperature', 'N/A')
                    min_t = day.get('minScreenTemperature', 'N/A')
                    precip = day.get('totalPrecipAmount', 'N/A')
                    print(f"   📆 {date}: {min_t}°C - {max_t}°C, {precip}mm rain")

        elif source_name == 'weather2geo':
            print("📊 Current Conditions:")
            print(f"   🌡️  Temperature: {source_data.get('temperature', 'N/A')}°C")
            print(f"   🌤️  Conditions: {source_data.get('condition', 'N/A')}")
            print(f"   💧 Humidity: {source_data.get('humidity', 'N/A')}%")
            print(f"   💨 Wind: {source_data.get('wind_speed', 'N/A')} mph")
            print(f"   📈 Data Quality: {source_data.get('data_quality', 'N/A')}")

def print_market_analysis(analysis: Dict):
    """Print market impact analysis."""
    print("\n📈 WEATHER-MARKET CORRELATION ANALYSIS")
    print("=" * 60)

    if analysis['weather_events']:
        print("🌤️  Weather Events Detected:")
        for event in analysis['weather_events']:
            print(f"   • {event}")
    else:
        print("🌤️  No significant weather events detected")

    if analysis['market_impacts']:
        print("\n💰 Potential Market Impacts:")
        for impact in analysis['market_impacts']:
            print(f"   • {impact}")
    else:
        print("\n💰 No significant market impacts identified")

    if analysis['recommendations']:
        print("\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   • {rec}")

def main():
    parser = argparse.ArgumentParser(
        description="Integrate Met Office weather data with existing sources for market analysis"
    )
    parser.add_argument(
        "-k", "--met-office-key",
        required=True,
        help="Met Office Weather DataHub API key"
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
        analyzer = WeatherMarketAnalyzer(args.met_office_key)

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
            print(f"\n💾 Report saved to: {args.save_report}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()