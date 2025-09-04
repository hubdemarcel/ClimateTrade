#!/usr/bin/env python3
"""
Example Integration: Weather Underground with Existing Weather Sources

This script demonstrates how to integrate Weather Underground weather data
with existing weather sources (Met Office, Meteostat, Weather2Geo) for enhanced
weather-market correlation analysis.

Weather Underground provides:
- Real-time observations from personal weather stations
- Detailed forecasts with high temporal resolution
- Historical data for backtesting
- Comprehensive meteorological parameters

Usage:
    python example_weather_underground_integration.py --wu-key YOUR_WU_API_KEY
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import pandas as pd

# Import our weather clients
from weather_underground_london import WeatherUndergroundClient

# Mock other weather clients for demonstration (would import actual clients in real usage)
class MetOfficeMock:
    """Mock Met Office client for demonstration."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_current_conditions(self) -> Dict:
        return {
            'source': 'Met Office',
            'location': 'London, UK',
            'temperature': 16.8,
            'humidity': 72,
            'wind_speed': 15,
            'weather_type': 'Partly cloudy',
            'timestamp': datetime.now().isoformat()
        }

class MeteostatMock:
    """Mock Meteostat client for demonstration."""
    def get_historical_data(self, days: int = 30) -> List[Dict]:
        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'temperature': 15.5 + (i % 10 - 5),  # Vary temperature
                'precipitation': 0.5 if i % 7 == 0 else 0,  # Rain every 7 days
                'source': 'Meteostat'
            })
        return data

class Weather2GeoMock:
    """Mock Weather2Geo client for demonstration."""
    def get_weather_data(self, location_query: str) -> Dict:
        return {
            'source': 'Weather2Geo (MSN Weather API)',
            'location': location_query,
            'temperature': 17.2,
            'condition': 'Mostly cloudy',
            'humidity': 68,
            'wind_speed': 14,
            'data_quality': 'Geolocation-based'
        }

class ComprehensiveWeatherAnalyzer:
    """Analyzes weather data from multiple sources for market correlation."""

    def __init__(self, wu_api_key: str, met_office_key: str = None):
        self.weather_underground = WeatherUndergroundClient(wu_api_key)
        self.met_office = MetOfficeMock(met_office_key) if met_office_key else None
        self.meteostat = MeteostatMock()
        self.weather2geo = Weather2GeoMock()

    def get_comprehensive_weather_report(self) -> Dict:
        """Get weather data from all available sources."""

        report = {
            'timestamp': datetime.now().isoformat(),
            'location': 'London, UK',
            'sources': {}
        }

        try:
            # Get Weather Underground data (primary source)
            wu_current = self.weather_underground.get_current_conditions()
            wu_hourly = self.weather_underground.get_hourly_forecast(24)
            wu_daily = self.weather_underground.get_daily_forecast(5)
            wu_historical = self.weather_underground.get_historical_data()

            report['sources']['weather_underground'] = {
                'current': wu_current,
                'hourly_forecast': wu_hourly,
                'daily_forecast': wu_daily,
                'historical_data': wu_historical,
                'data_quality': 'Real-time PWS observations',
                'coverage': 'Global PWS network',
                'update_frequency': 'Real-time (every 5-15 minutes)',
                'advantages': ['High temporal resolution', 'Local observations', 'Comprehensive parameters']
            }

        except Exception as e:
            report['sources']['weather_underground'] = {'error': str(e)}

        try:
            # Get Met Office data
            if self.met_office:
                met_office_current = self.met_office.get_current_conditions()
                report['sources']['met_office'] = {
                    'current': met_office_current,
                    'data_quality': 'Official UK Government',
                    'coverage': 'UK-wide authoritative forecasts'
                }
            else:
                report['sources']['met_office'] = {'error': 'API key not provided'}

        except Exception as e:
            report['sources']['met_office'] = {'error': str(e)}

        try:
            # Get Meteostat historical data
            meteostat_data = self.meteostat.get_historical_data(7)
            report['sources']['meteostat'] = {
                'historical_data': meteostat_data,
                'data_quality': 'Historical meteorological database',
                'coverage': 'Global historical records',
                'advantages': ['Long-term historical data', 'Multiple data sources']
            }

        except Exception as e:
            report['sources']['meteostat'] = {'error': str(e)}

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
            'recommendations': [],
            'data_quality_comparison': {},
            'correlation_opportunities': []
        }

        # Extract Weather Underground data
        wu = weather_data.get('sources', {}).get('weather_underground', {})

        if 'current' in wu:
            current = wu['current']

            # Temperature analysis
            temp = current.get('temperature')
            if temp is not None:
                if temp < 5:
                    analysis['weather_events'].append('Cold weather alert (WU)')
                    analysis['market_impacts'].append('Potential heating costs impact on energy markets')
                elif temp > 25:
                    analysis['weather_events'].append('Hot weather alert (WU)')
                    analysis['market_impacts'].append('Potential cooling costs and drought concerns')

            # Precipitation analysis
            precip_1h = current.get('precipitation_1h')
            if precip_1h is not None and precip_1h > 5:
                analysis['weather_events'].append('Heavy precipitation (WU)')
                analysis['market_impacts'].append('Potential flooding impacts on property markets')

            # Wind analysis
            wind = current.get('wind_speed')
            if wind is not None and wind > 30:
                analysis['weather_events'].append('Strong winds (WU)')
                analysis['market_impacts'].append('Potential disruption to transportation and supply chains')

        # Daily forecast analysis
        if 'daily_forecast' in wu:
            daily = wu['daily_forecast']
            for day in daily[:3]:  # Next 3 days
                max_temp = day.get('max_temp')
                precip = day.get('precipitation_amount')

                if max_temp is not None and max_temp > 30:
                    analysis['weather_events'].append(f'Heatwave forecast for {day.get("date", "upcoming day")[:10]} (WU)')
                    analysis['market_impacts'].append('Extended heat may impact agricultural commodities')

                if precip is not None and precip > 20:
                    analysis['weather_events'].append(f'Heavy rain forecast for {day.get("date", "upcoming day")[:10]} (WU)')
                    analysis['market_impacts'].append('Potential weather-related disruptions')

        # Historical analysis for trends
        if 'historical_data' in wu and wu['historical_data']:
            historical = wu['historical_data']
            temps = [h.get('temperature') for h in historical if h.get('temperature') is not None]
            if temps:
                avg_temp = sum(temps) / len(temps)
                analysis['correlation_opportunities'].append(f'Historical temperature average: {avg_temp:.1f}°C')
                analysis['correlation_opportunities'].append('Weather Underground historical data available for backtesting')

        # Data quality comparison
        analysis['data_quality_comparison'] = {
            'weather_underground': {
                'strengths': ['Real-time PWS data', 'High-frequency updates', 'Local observations'],
                'limitations': ['Variable station quality', 'Potential gaps in coverage'],
                'best_for': ['Real-time monitoring', 'Local weather patterns', 'High-resolution data']
            },
            'met_office': {
                'strengths': ['Official government data', 'Authoritative forecasts', 'UK-wide coverage'],
                'limitations': ['Lower temporal resolution', 'Limited historical depth'],
                'best_for': ['Official forecasts', 'Regulatory compliance', 'UK weather patterns']
            },
            'meteostat': {
                'strengths': ['Long-term historical data', 'Global coverage', 'Multiple sources'],
                'limitations': ['Lower temporal resolution', 'Potential data gaps'],
                'best_for': ['Historical analysis', 'Backtesting', 'Long-term trends']
            }
        }

        # Generate recommendations
        if analysis['weather_events']:
            analysis['recommendations'].append('Monitor weather-sensitive market sectors')
            analysis['recommendations'].append('Consider weather derivatives or hedging strategies')
            analysis['recommendations'].append('Track commodity prices for weather-impacted goods')
            analysis['recommendations'].append('Use Weather Underground for real-time monitoring')
            analysis['recommendations'].append('Combine multiple sources for robust analysis')

        return analysis

    def export_to_csv(self, weather_data: Dict, filename: str):
        """Export comprehensive weather data to CSV files."""
        try:
            # Create output directory
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

            # Export current conditions
            wu = weather_data.get('sources', {}).get('weather_underground', {})
            if 'current' in wu:
                current_df = pd.DataFrame([wu['current']])
                current_df['data_source'] = 'Weather Underground'
                current_df['export_timestamp'] = datetime.now().isoformat()
                current_df.to_csv(f"{filename}_current.csv", index=False)

            # Export hourly forecast
            if 'hourly_forecast' in wu and wu['hourly_forecast']:
                hourly_df = pd.DataFrame(wu['hourly_forecast'])
                hourly_df['data_source'] = 'Weather Underground'
                hourly_df['export_timestamp'] = datetime.now().isoformat()
                hourly_df.to_csv(f"{filename}_hourly.csv", index=False)

            # Export daily forecast
            if 'daily_forecast' in wu and wu['daily_forecast']:
                daily_df = pd.DataFrame(wu['daily_forecast'])
                daily_df['data_source'] = 'Weather Underground'
                daily_df['export_timestamp'] = datetime.now().isoformat()
                daily_df.to_csv(f"{filename}_daily.csv", index=False)

            # Export historical data
            if 'historical_data' in wu and wu['historical_data']:
                historical_df = pd.DataFrame(wu['historical_data'])
                historical_df['data_source'] = 'Weather Underground'
                historical_df['export_timestamp'] = datetime.now().isoformat()
                historical_df.to_csv(f"{filename}_historical.csv", index=False)

            print(f"✅ Data exported to {filename}_*.csv files")

        except Exception as e:
            print(f"❌ Failed to export data: {e}")

def print_weather_report(report: Dict):
    """Print a formatted weather report."""
    print("\n🌤️  COMPREHENSIVE LONDON WEATHER REPORT")
    print("=" * 80)
    print(f"📍 Location: {report['location']}")
    print(f"🕒 Generated: {report['timestamp']}")

    for source_name, source_data in report['sources'].items():
        print(f"\n🔍 Source: {source_name.upper()}")
        print("-" * 60)

        if 'error' in source_data:
            print(f"❌ Error: {source_data['error']}")
            continue

        if source_name == 'weather_underground':
            if 'current' in source_data:
                current = source_data['current']
                print("📊 Current Conditions:")
                print(f"   🌡️  Temperature: {current.get('temperature', 'N/A')}°C")
                print(f"   🤒 Feels Like: {current.get('feels_like', 'N/A')}°C")
                print(f"   💧 Humidity: {current.get('humidity', 'N/A')}%")
                print(f"   💨 Wind: {current.get('wind_speed', 'N/A')} km/h {current.get('wind_direction', 'N/A')}°")
                print(f"   🌧️  Precipitation (1h): {current.get('precipitation_1h', 'N/A')} mm")
                print(f"   👁️  Visibility: {current.get('visibility', 'N/A')} km")
                print(f"   🏢 Station: {current.get('station_name', 'N/A')}")

            if 'daily_forecast' in source_data and source_data['daily_forecast']:
                print("📅 5-Day Forecast:")
                for day in source_data['daily_forecast'][:5]:
                    date = day.get('date', 'N/A')[:10]
                    max_t = day.get('max_temp', 'N/A')
                    min_t = day.get('min_temp', 'N/A')
                    precip = day.get('precipitation_amount', 'N/A')
                    condition = day.get('weather_condition', 'N/A')[:30]
                    print(f"   📆 {date}: {min_t}°C - {max_t}°C, {precip}mm rain")
                    print(f"      {condition}")

        elif source_name == 'met_office':
            if 'current' in source_data:
                current = source_data['current']
                print("📊 Current Conditions:")
                print(f"   🌡️  Temperature: {current.get('temperature', 'N/A')}°C")
                print(f"   🌤️  Conditions: {current.get('weather_type', 'N/A')}")
                print(f"   💨 Wind: {current.get('wind_speed', 'N/A')} mph")

        elif source_name == 'meteostat':
            if 'historical_data' in source_data and source_data['historical_data']:
                historical = source_data['historical_data']
                print(f"📊 Historical Data: {len(historical)} records")
                if historical:
                    print(f"   Date Range: {historical[0]['date']} to {historical[-1]['date']}")

        elif source_name == 'weather2geo':
            print("📊 Current Conditions:")
            print(f"   🌡️  Temperature: {source_data.get('temperature', 'N/A')}°C")
            print(f"   🌤️  Conditions: {source_data.get('condition', 'N/A')}")
            print(f"   💧 Humidity: {source_data.get('humidity', 'N/A')}%")
            print(f"   💨 Wind: {source_data.get('wind_speed', 'N/A')} mph")

def print_market_analysis(analysis: Dict):
    """Print market impact analysis."""
    print("\n📈 WEATHER-MARKET CORRELATION ANALYSIS")
    print("=" * 80)

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

    if analysis['correlation_opportunities']:
        print("\n🔗 Correlation Opportunities:")
        for opp in analysis['correlation_opportunities']:
            print(f"   • {opp}")

    if analysis['recommendations']:
        print("\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   • {rec}")

def main():
    parser = argparse.ArgumentParser(
        description="Integrate Weather Underground with existing weather sources for market analysis"
    )
    parser.add_argument(
        "-k", "--wu-key",
        required=True,
        help="Weather Underground API key"
    )
    parser.add_argument(
        "--met-office-key",
        help="Met Office API key (optional)"
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
    parser.add_argument(
        "--export-csv",
        type=str,
        help="Export data to CSV files (base filename)"
    )

    args = parser.parse_args()

    try:
        analyzer = ComprehensiveWeatherAnalyzer(args.wu_key, args.met_office_key)

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

        # Export to CSV if requested
        if args.export_csv:
            analyzer.export_to_csv(weather_report, args.export_csv)

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