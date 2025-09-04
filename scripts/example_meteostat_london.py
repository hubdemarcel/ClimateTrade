"""
Example: Accessing historical daily weather data for London using Meteostat

This script demonstrates how to fetch comprehensive historical weather data for London,
which can be used for backtesting weather-market correlations.

Meteorological data provided by Meteostat (https://dev.meteostat.net)
under the terms of the Creative Commons Attribution-NonCommercial
4.0 International Public License.

The code is licensed under the MIT license.
"""

from datetime import datetime
import matplotlib.pyplot as plt
from meteostat import Point, Daily

# Set time period (example: last 5 years for backtesting)
start = datetime(2019, 1, 1)
end = datetime(2023, 12, 31)

# Create Point for London, UK
# Coordinates: 51.5074° N, 0.1278° W, Elevation: ~11m
london = Point(51.5074, -0.1278, 11)

# Get daily data
print("Fetching historical daily weather data for London...")
data = Daily(london, start, end)
data = data.fetch()

# Display basic info
print(f"Data shape: {data.shape}")
print(f"Date range: {data.index.min()} to {data.index.max()}")
print("\nAvailable columns:")
print(data.columns.tolist())

# Display first few rows
print("\nFirst 5 rows of data:")
print(data.head())

# Basic statistics
print("\nBasic statistics for temperature:")
print(data[['tavg', 'tmin', 'tmax']].describe())

# Optional: Plot temperature trends
try:
    data.plot(y=["tavg", "tmin", "tmax"])
    plt.title("London Daily Temperature (2019-2023)")
    plt.xlabel("Date")
    plt.ylabel("Temperature (°C)")
    plt.legend(["Average", "Minimum", "Maximum"])
    plt.show()
except ImportError:
    print("Matplotlib not available for plotting")

print("\nData fetched successfully! This data can be used for weather-market correlation analysis.")