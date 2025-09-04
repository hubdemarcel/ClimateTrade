#!/usr/bin/env python3
"""
Example Integration: Weather2Geo with Existing Weather Sources

This script demonstrates how to integrate Weather2Geo data extraction
with existing weather sources (Met Office, NWS, Meteostat) for enhanced
weather-market correlation analysis in the ClimateTrade pipeline.

The Weather2Geo integration provides:
- MSN Weather API data for global coverage
- Automated data extraction for multiple locations
- Enhanced data enrichment with derived metrics
- Integration with existing data quality pipeline
- Support for both bulk and condition-specific extraction

Usage:
    python example_weather2geo_integration.py --extract-mode bulk
    python example_weather2geo_integration.py --extract-mode conditions --condition "Mostly cloudy" --temp 20
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import logging

# Add Weather2Geo to path
sys.path.append(str(sys.path[0] + "/Weather2Geo"))

try:
    from weather2geo_client import Weather2GeoClient
except ImportError as e:
    print(f"Error importing Weather2Geo client: {e}")
    print("Make sure Weather2Geo dependencies are installed")
    sys.exit(1)

# Mock other weather sources for demonstration
class MetOfficeMock:
    """Mock Met Office client for demonstration."""
    def get_current_conditions(self):
        return {
            'temperature': 18.5,
            'weather_type': 'Partly cloudy',
            'wind_speed': 12,
            'humidity': 65,
            'precipitation': 0.0
        }

class NWSMock:
    """Mock NWS client for demonstration."""
    def get_nyc_weather_data(self):
        return {
            'forecast': {
                'properties': {
                    'periods': [
                        {
                            'name': 'This Afternoon',
                            'temperature': 22,
                            'temperatureUnit': 'C',
                            'shortForecast': 'Mostly Sunny',
                            'detailedForecast': 'Mostly sunny with a high of 22°C'
                        }
                    ]
                }
            },
            'alerts': {'features': []}
        }

class MeteostatMock:
    """Mock Meteostat client for demonstration."""
    def get_weather_data(self, location):
        return {
            'temperature': 19.2,
            'humidity': 68,
            'wind_speed': 8.5,
            'pressure': 1013.2
        }

class EnhancedWeatherAnalyzer:
    """Analyzes weather data from multiple sources including Weather2Geo."""

    def __init__(self):
        self.weather2geo = Weather2GeoClient()
        self.met_office = MetOfficeMock()
        self.nws = NWSMock()
        self.meteostat = MeteostatMock()

    def get_comprehensive_weather_report(self,
                                       extract_mode: str = 'bulk',
                                       condition: str = None,
                                       temperature: float = None,
                                       target_datetime: datetime = None) -> Dict:
        """Get weather data from all available sources including Weather2Geo."""

        if target_datetime is None:
            target_datetime = datetime.now()

        report = {
            'timestamp': datetime.now().isoformat(),
            'extraction_mode': extract_mode,
            'target_datetime': target_datetime.isoformat(),
            'sources': {}
        }

        # Get Weather2Geo data
        try:
            if extract_mode == 'conditions' and (condition or temperature is not None):
                weather2geo_data = self.weather2geo.extract_weather_by_conditions(
                    target_datetime=target_datetime,
                    desired_condition=condition,
                    desired_temp=temperature,
                    max_locations=100
                )
            else:
                weather2geo_data = self.weather2geo.get_bulk_weather_data(
                    target_datetime=target_datetime,
                    max_locations=50
                )

            # Enrich the data
            weather2geo_data = self.weather2geo.enrich_weather_data(weather2geo_data)

            report['sources']['weather2geo'] = {
                'data': weather2geo_data,
                'count': len(weather2geo_data),
                'data_quality': 'MSN Weather API with enrichment',
                'coverage': 'Global cities with population >10k',
                'update_frequency': 'Real-time extraction',
                'features': [
                    'Temperature, humidity, wind, pressure',
                    'Heat index, wind chill calculations',
                    'Comfort level classification',
                    'Weather severity scoring'
                ]
            }

        except Exception as e:
            report['sources']['weather2geo'] = {'error': str(e)}

        # Get other weather sources for comparison
        try:
            met_office_data = self.met_office.get_current_conditions()
            report['sources']['met_office'] = {
                'current': met_office_data,
                'data_quality': 'Official UK Government',
                'coverage': 'UK-focused',
                'location': 'London, UK'
            }
        except Exception as e:
            report['sources']['met_office'] = {'error': str(e)}

        try:
            nws_data = self.nws.get_nyc_weather_data()
            report['sources']['nws'] = {
                'forecast': nws_data['forecast'],
                'alerts': nws_data['alerts'],
                'data_quality': 'Official US Government (NOAA)',
                'coverage': 'US-focused',
                'location': 'New York City, NY'
            }
        except Exception as e:
            report['sources']['nws'] = {'error': str(e)}

        try:
            meteostat_data = self.meteostat.get_weather_data('London')
            report['sources']['meteostat'] = {
                'data': meteostat_data,
                'data_quality': 'Historical weather database',
                'coverage': 'Global weather stations',
                'location': 'London, UK'
            }
        except Exception as e:
            report['sources']['meteostat'] = {'error': str(e)}

        return report

    def analyze_weather_market_impacts(self, weather_data: Dict) -> Dict:
        """Analyze potential market impacts based on comprehensive weather data."""

        analysis = {
            'weather_events': [],
            'market_impacts': [],
            'recommendations': [],
            'data_quality_comparison': {},
            'correlation_opportunities': []
        }

        # Analyze Weather2Geo data
        weather2geo = weather_data.get('sources', {}).get('weather2geo', {})
        if 'data' in weather2geo and weather2geo['data']:
            # Analyze global weather patterns
            temps = [d.get('temperature') for d in weather2geo['data'] if d.get('temperature') is not None]
            if temps:
                avg_temp = sum(temps) / len(temps)
                if avg_temp < 10:
                    analysis['weather_events'].append('Global cooling trend detected')
                    analysis['market_impacts'].append('Potential increase in energy demand for heating')
                elif avg_temp > 25:
                    analysis['weather_events'].append('Global warming trend detected')
                    analysis['market_impacts'].append('Potential increase in cooling costs and drought concerns')

            # Analyze severe weather conditions
            severe_count = sum(1 for d in weather2geo['data'] if d.get('weather_severity_score', 0) > 5)
            if severe_count > len(weather2geo['data']) * 0.1:  # More than 10% severe
                analysis['weather_events'].append('Multiple severe weather events detected globally')
                analysis['market_impacts'].append('Potential disruptions to global supply chains')

        # Compare data quality across sources
        sources = weather_data.get('sources', {})
        analysis['data_quality_comparison'] = {
            'weather2geo': 'High - Real-time global coverage with derived metrics',
            'met_office': 'Very High - Official UK government data',
            'nws': 'Very High - Official US government data',
            'meteostat': 'High - Historical weather database'
        }

        # Identify correlation opportunities
        analysis['correlation_opportunities'] = [
            'Weather2Geo + Met Office: UK weather pattern validation',
            'Weather2Geo + NWS: Transatlantic weather correlation',
            'Weather2Geo + Meteostat: Real-time vs historical comparison',
            'Multi-source temperature averaging for accuracy',
            'Global weather severity scoring for risk assessment'
        ]

        # Generate recommendations
        if analysis['weather_events']:
            analysis['recommendations'].extend([
                'Monitor weather-sensitive commodities (energy, agriculture)',
                'Consider weather derivatives for risk hedging',
                'Track transportation and logistics stocks',
                'Analyze retail sector impacts from weather patterns',
                'Monitor insurance market responses to weather events'
            ])

        analysis['recommendations'].extend([
            'Leverage Weather2Geo for global weather intelligence',
            'Combine multiple sources for comprehensive market analysis',
            'Use enriched metrics for advanced correlation studies',
            'Implement automated weather monitoring alerts'
        ])

        return analysis

    def generate_integration_report(self,
                                  weather_data: Dict,
                                  market_analysis: Dict,
                                  output_format: str = 'console') -> str:
        """Generate a comprehensive integration report."""

        report_lines = []

        if output_format == 'console':
            report_lines.append("\n" + "="*80)
            report_lines.append("🌤️  COMPREHENSIVE WEATHER INTEGRATION REPORT")
            report_lines.append("="*80)
            report_lines.append(f"📅 Generated: {weather_data['timestamp']}")
            report_lines.append(f"🎯 Extraction Mode: {weather_data['extraction_mode']}")
            report_lines.append(f"🎯 Target Time: {weather_data['target_datetime']}")

            # Weather2Geo summary
            weather2geo = weather_data.get('sources', {}).get('weather2geo', {})
            if 'data' in weather2geo:
                report_lines.append(f"\n🔍 Weather2Geo Data:")
                report_lines.append(f"   📊 Locations: {weather2geo['count']}")
                report_lines.append(f"   🌍 Coverage: {weather2geo['coverage']}")
                report_lines.append(f"   ⚡ Update Frequency: {weather2geo['update_frequency']}")
                report_lines.append(f"   🏆 Quality: {weather2geo['data_quality']}")

                if weather2geo['data']:
                    # Show sample enriched data
                    sample = weather2geo['data'][0]
                    report_lines.append(f"\n   📋 Sample Location: {sample.get('location_name', 'N/A')}")
                    report_lines.append(f"   🌡️  Temperature: {sample.get('temperature', 'N/A')}°C")
                    report_lines.append(f"   💨 Wind: {sample.get('wind_speed', 'N/A')} km/h")
                    report_lines.append(f"   💧 Humidity: {sample.get('humidity', 'N/A')}%")
                    report_lines.append(f"   🏖️  Comfort Level: {sample.get('comfort_level', 'N/A')}")
                    report_lines.append(f"   ⚠️  Severity Score: {sample.get('weather_severity_score', 'N/A')}/10")

            # Data quality comparison
            report_lines.append(f"\n🔍 Data Quality Comparison:")
            for source, quality in market_analysis.get('data_quality_comparison', {}).items():
                report_lines.append(f"   {source.upper()}: {quality}")

            # Weather events and impacts
            if market_analysis.get('weather_events'):
                report_lines.append(f"\n🌤️  Weather Events Detected:")
                for event in market_analysis['weather_events']:
                    report_lines.append(f"   • {event}")

            if market_analysis.get('market_impacts'):
                report_lines.append(f"\n💰 Potential Market Impacts:")
                for impact in market_analysis['market_impacts']:
                    report_lines.append(f"   • {impact}")

            # Correlation opportunities
            if market_analysis.get('correlation_opportunities'):
                report_lines.append(f"\n🔗 Correlation Opportunities:")
                for opp in market_analysis['correlation_opportunities']:
                    report_lines.append(f"   • {opp}")

            # Recommendations
            if market_analysis.get('recommendations'):
                report_lines.append(f"\n💡 Recommendations:")
                for rec in market_analysis['recommendations']:
                    report_lines.append(f"   • {rec}")

        return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(
        description="Integrate Weather2Geo with existing weather sources for market analysis"
    )

    parser.add_argument(
        '--extract-mode',
        choices=['bulk', 'conditions'],
        default='bulk',
        help='Weather2Geo extraction mode'
    )

    parser.add_argument(
        '--condition',
        type=str,
        help='Weather condition to match (for conditions mode)'
    )

    parser.add_argument(
        '--temp', '--temperature',
        type=float,
        help='Target temperature in Celsius (for conditions mode)'
    )

    parser.add_argument(
        '--datetime',
        type=str,
        help='Target date/time in ISO format (YYYY-MM-DDTHH:MM:SS)'
    )

    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results in JSON format'
    )

    parser.add_argument(
        '--save-report',
        type=str,
        help='Save report to JSON file'
    )

    args = parser.parse_args()

    try:
        analyzer = EnhancedWeatherAnalyzer()

        # Parse target datetime
        target_datetime = None
        if args.datetime:
            try:
                target_datetime = datetime.fromisoformat(args.datetime.replace('Z', '+00:00'))
            except ValueError:
                print("❌ Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
                sys.exit(1)

        # Get comprehensive weather report
        weather_report = analyzer.get_comprehensive_weather_report(
            extract_mode=args.extract_mode,
            condition=args.condition,
            temperature=args.temp,
            target_datetime=target_datetime
        )

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
            # Generate and print formatted report
            report = analyzer.generate_integration_report(weather_report, market_analysis)
            print(report)

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