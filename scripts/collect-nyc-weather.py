#!/usr/bin/env python3
"""
Convenience script to collect weather data for New York City using Meteostat
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def main():
    # Import the main collector
    try:
        import meteostat_weather_collector
        collector_class = meteostat_weather_collector.WeatherDataCollector
    except ImportError as e:
        print(f"Error: Could not import meteostat_weather_collector.py: {e}")
        print("Make sure the file exists in the same directory")
        sys.exit(1)

    print("=== Collecting Weather Data for New York City ===")

    collector = collector_class()

    if collector.collect_and_store('nyc'):
        print("✅ Successfully collected and stored weather data for New York City")
        return True
    else:
        print("❌ Failed to collect weather data for New York City")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)