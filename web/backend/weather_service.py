"""
Weather Service for ClimaTrade
Provides 24-hour weather data integration for London and NYC
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
from pathlib import Path
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Add scripts directory to path to import Open-Meteo client
scripts_dir = Path(__file__).parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Initialize Met Office availability flag
MET_OFFICE_OPTIMIZED_CLIENT_AVAILABLE = False
MetOfficeOptimizedClient = None
CallPriority = None

def _load_met_office_client():
    """Load the optimized Met Office client with proper error handling"""
    global MET_OFFICE_OPTIMIZED_CLIENT_AVAILABLE, MetOfficeOptimizedClient, CallPriority

    try:
        # Prioritize the optimized client
        from met_office_optimized_client import MetOfficeOptimizedClient as MOOC, CallPriority as CP
        MetOfficeOptimizedClient = MOOC
        CallPriority = CP
        MET_OFFICE_OPTIMIZED_CLIENT_AVAILABLE = True
        logger.info("Met Office Optimized Client loaded successfully.")
        return True
    except ImportError as e:
        logger.warning(f"Met Office Optimized Client not available from scripts: {e}")
        MET_OFFICE_OPTIMIZED_CLIENT_AVAILABLE = False
        return False

# Load the clients on module import
_load_met_office_client()

class WeatherService:
    """Service for fetching and managing weather data"""

    # City coordinates with validation
    CITIES = {
        'london': {
            'name': 'London,UK',
            'lat': 51.5074,
            'lon': -0.1278,
            'timezone': 'Europe/London'
        },
        'nyc': {
            'name': 'New York,NY',
            'lat': 40.7128,
            'lon': -74.0060,
            'timezone': 'America/New_York'
        }
    }

    def celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius temperature to Fahrenheit."""
        if celsius is None:
            return None
        return round((celsius * 9/5) + 32, 1)

    # Input validation patterns
    CITY_NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-,\.]+$')
    MAX_CITY_NAME_LENGTH = 50

    def __init__(self):
        self.client = None
        self.db_manager = None
        self._health_status = {
            'met_office_available': MET_OFFICE_OPTIMIZED_CLIENT_AVAILABLE,
            'last_health_check': None,
            'error_count': 0,
            'last_error': None
        }

        self.met_office_client = None
        self.met_office_api_key = os.environ.get('MET_OFFICE_API_KEY')

        if MET_OFFICE_OPTIMIZED_CLIENT_AVAILABLE and self.met_office_api_key:
            try:
                self.met_office_client = MetOfficeOptimizedClient(self.met_office_api_key)
                logger.info("Met Office client initialized successfully")
                self._health_status['met_office_initialized'] = True
            except Exception as e:
                logger.error(f"Failed to initialize Met Office client: {e}")
                self._health_status['met_office_initialized'] = False
                self._health_status['last_error'] = str(e)
                self._health_status['error_count'] += 1
        else:
            if not self.met_office_api_key:
                logger.warning("Met Office API key not configured - set MET_OFFICE_API_KEY environment variable")
            else:
                logger.warning("Met Office client not available")

        # If neither client is available, use mock data
        if not (self._health_status.get('open_meteo_initialized', False) or
                self._health_status.get('met_office_initialized', False)):
            logger.warning("No weather clients available - will use mock data")
            self._health_status['client_initialized'] = False
        else:
            self._health_status['client_initialized'] = True

    def _validate_city_name(self, city: str) -> bool:
        """Validate city name input"""
        if not city or not isinstance(city, str):
            return False
        if len(city) > self.MAX_CITY_NAME_LENGTH:
            return False
        if not self.CITY_NAME_PATTERN.match(city):
            return False
        return True

    def _sanitize_city_name(self, city: str) -> str:
        """Sanitize city name input"""
        return city.strip().lower()

    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        self._health_status['last_health_check'] = datetime.now().isoformat()
        return self._health_status.copy()

    def get_city_coordinates(self, city: str) -> Optional[Dict[str, Any]]:
        """Get coordinates for a city with validation"""
        if not self._validate_city_name(city):
            logger.warning(f"Invalid city name format: {city}")
            return None

        sanitized_city = self._sanitize_city_name(city)
        city_info = self.CITIES.get(sanitized_city)

        if not city_info:
            logger.warning(f"City not found in predefined list: {sanitized_city}")
            return None

        return city_info

    def get_24h_weather_history(self, city: str) -> Dict[str, Any]:
        """Get 24-hour weather history for a city with comprehensive error handling"""
        sanitized_city = self._sanitize_city_name(city)
        
        # Check cache first
        if sanitized_city in self.cache:
            cached_time, cached_data = self.cache[sanitized_city]
            if datetime.now() - cached_time < self.cache_timeout:
                logger.info(f"Returning cached weather data for {sanitized_city}")
                # Add a 'cached' flag to the response
                cached_data['cached'] = True
                cached_data['cache_timestamp'] = cached_time.isoformat()
                return cached_data

        try:
            # Validate input
            if not self._validate_city_name(city):
                error_msg = f"Invalid city name format: {city}"
                logger.error(error_msg)
                self._health_status['error_count'] += 1
                self._health_status['last_error'] = error_msg
                return self._get_error_response(city, error_msg)

            # Get city coordinates
            city_info = self.get_city_coordinates(city)
            if not city_info:
                error_msg = f"City not supported: {city}"
                logger.error(error_msg)
                self._health_status['error_count'] += 1
                self._health_status['last_error'] = error_msg
                return self._get_error_response(city, error_msg)

            # Check if clients are available
            if not self._health_status.get('client_initialized', False):
                logger.warning("No weather clients available, using mock data")
                mock_data = self._get_mock_weather_data(city)
                # Save mock data to database for consistency
                self._save_mock_data_to_database(mock_data, city_info)
                self.cache[sanitized_city] = (datetime.now(), mock_data)
                return mock_data

            if city.lower() in ['nyc', 'new york,ny']:
                try:
                    logger.debug(f"Fetching NWS data for {city_info['name']}")
                    nws_data = self.nws_client.get_nyc_weather_data()
                    if 'error' not in nws_data:
                        formatted_data = self._format_nws_data(nws_data, city_info)
                        self.cache[sanitized_city] = (datetime.now(), formatted_data)
                        return formatted_data
                    else:
                        logger.warning("NWS data not available, falling back to mock data")
                except Exception as e:
                    logger.error(f"Failed to retrieve NWS data: {e}")

            # Try Met Office first if available and configured for London
            if (self.met_office_client and self._health_status.get('met_office_initialized', False) and
                city.lower() in ['london', 'london,uk']):
                try:
                    logger.debug(f"Fetching Met Office data for {city_info['name']}")
                    met_office_data = self._get_met_office_weather_data(city_info, city)
                    if met_office_data:
                        # Save to database using dedicated Met Office method
                        try:
                            self._save_met_office_data_to_database(met_office_data, city_info)
                        except Exception as e:
                            logger.warning(f"Failed to save Met Office data to database: {e}")
                            # Don't fail the request if DB save fails

                        # Reset error count on successful request
                        self._health_status['error_count'] = 0
                        self._health_status['last_error'] = None
                        self.cache[sanitized_city] = (datetime.now(), met_office_data)
                        return met_office_data
                    else:
                        logger.warning("Met Office data not available, falling back to mock data")
                except Exception as e:
                    logger.error(f"Failed to retrieve Met Office data: {e}")
                    self._health_status['error_count'] += 1
                    self._health_status['last_error'] = str(e)
                    # Fall through to mock data

            

            # If all else fails, use mock data
            logger.warning("All weather clients failed, using mock data")
            mock_data = self._get_mock_weather_data(city)
            self._save_mock_data_to_database(mock_data, city_info)
            self.cache[sanitized_city] = (datetime.now(), mock_data)
            return mock_data

        except Exception as e:
            error_msg = f"Unexpected error getting weather data for {city}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._health_status['error_count'] += 1
            self._health_status['last_error'] = error_msg
            mock_data = self._get_mock_weather_data(city)
            self.cache[sanitized_city] = (datetime.now(), mock_data)
            return mock_data

    def _get_error_response(self, city: str, error_message: str) -> Dict[str, Any]:
        """Generate error response with mock data fallback"""
        mock_data = self._get_mock_weather_data(city)
        mock_data['error'] = error_message
        mock_data['source'] = 'error_fallback'
        return mock_data

    def _combine_weather_data(self, current: Dict, forecast: Dict, city_info: Dict) -> Dict[str, Any]:
        """Combine current weather and forecast into 24h timeline"""
        now = datetime.now()

        # Start with current weather (convert temperatures to Fahrenheit)
        timeline = [{
            'timestamp': current.get('timestamp', now.isoformat()),
            'temperature': self.celsius_to_fahrenheit(current.get('temperature')),
            'feels_like': self.celsius_to_fahrenheit(current.get('feels_like')),
            'humidity': current.get('humidity'),
            'pressure': current.get('pressure'),
            'wind_speed': current.get('wind_speed'),
            'wind_direction': current.get('wind_direction'),
            'precipitation': current.get('precipitation', 0),
            'weather_code': current.get('weather_code'),
            'weather_description': current.get('weather_description'),
            'visibility': current.get('visibility'),
            'data_type': 'current'
        }]

        # Add hourly forecast data (next 23 hours) - convert temperatures to Fahrenheit
        hourly_data = forecast.get('forecast', [])
        hourly_records = [h for h in hourly_data if h.get('forecast_type') == 'hourly']

        for record in hourly_records[:23]:  # Next 23 hours
            timeline.append({
                'timestamp': record.get('timestamp'),
                'temperature': self.celsius_to_fahrenheit(record.get('temperature')),
                'feels_like': self.celsius_to_fahrenheit(record.get('feels_like')),
                'humidity': record.get('humidity'),
                'pressure': record.get('pressure'),
                'wind_speed': record.get('wind_speed'),
                'wind_direction': record.get('wind_direction'),
                'precipitation': record.get('precipitation', 0),
                'weather_code': record.get('weather_code'),
                'weather_description': record.get('weather_description'),
                'visibility': record.get('visibility'),
                'data_type': 'forecast'
            })

        return {
            'city': city_info['name'],
            'latitude': city_info['lat'],
            'longitude': city_info['lon'],
            'timezone': city_info['timezone'],
            'generated_at': now.isoformat(),
            'data_points': len(timeline),
            'timeline': timeline,
            'summary': self._generate_weather_summary(timeline),
            'source': 'open_meteo'
        }

    def _generate_weather_summary(self, timeline: List[Dict]) -> Dict[str, Any]:
        """Generate weather summary statistics"""
        if not timeline:
            return {}

        temperatures = [t['temperature'] for t in timeline if t.get('temperature') is not None]
        precipitation = [t['precipitation'] for t in timeline if t.get('precipitation') is not None]

        return {
            'temperature_avg': round(sum(temperatures) / len(temperatures), 1) if temperatures else None,
            'temperature_min': min(temperatures) if temperatures else None,
            'temperature_max': max(temperatures) if temperatures else None,
            'total_precipitation': round(sum(precipitation), 2) if precipitation else 0,
            'avg_humidity': round(sum(t['humidity'] for t in timeline if t.get('humidity')) / len(timeline), 1) if timeline else None,
            'avg_wind_speed': round(sum(t['wind_speed'] for t in timeline if t.get('wind_speed')) / len(timeline), 1) if timeline else None,
            'weather_conditions': list(set(t['weather_description'] for t in timeline if t.get('weather_description')))
        }

    def _format_nws_data(self, nws_data: Dict, city_info: Dict) -> Dict:
        """Formats NWS data into the format expected by the frontend."""
        timeline = []
        if 'hourly_forecast' in nws_data:
            periods = nws_data['hourly_forecast'].get('properties', {}).get('periods', [])
            for period in periods:
                timeline.append({
                    'timestamp': period.get('startTime'),
                    'temperature': period.get('temperature'),
                    'feels_like': None,  # NWS data doesn't have this
                    'humidity': period.get('relativeHumidity', {}).get('value'),
                    'precipitation': period.get('probabilityOfPrecipitation', {}).get('value'),
                    'weather_description': period.get('shortForecast'),
                    'data_type': 'nws'
                })

        return {
            'city': city_info['name'],
            'latitude': city_info['lat'],
            'longitude': city_info['lon'],
            'timezone': city_info['timezone'],
            'generated_at': datetime.now().isoformat(),
            'data_points': len(timeline),
            'timeline': timeline,
            'summary': self._generate_weather_summary(timeline),
            'source': 'nws'
        }

    def _get_met_office_weather_data(self, city_info: Dict[str, Any], city_name: str) -> Optional[Dict[str, Any]]:
        """Get weather data from Met Office API and format for frontend"""
        try:
            # Use the optimized client to get current weather, which includes forecast data
            # Use a high priority for this critical application data
            met_office_payload = self.met_office_client.get_current_weather(city_name, priority=CallPriority.HIGH)
            
            if not met_office_payload or 'forecast' not in met_office_payload:
                logger.warning("No data or forecast received from Met Office Optimized Client")
                return None

            hourly_data = met_office_payload.get('forecast', [])
            # Convert Met Office data to frontend format
            timeline = []
            for hour_data in hourly_data:
                # Convert temperature from Celsius to Fahrenheit for consistency
                temperature_f = self.celsius_to_fahrenheit(hour_data.get('temperature'))
                feels_like_f = self.celsius_to_fahrenheit(hour_data.get('feels_like'))

                weather_code = hour_data.get('weather_code')
                # The optimized client already provides the description
                weather_description = hour_data.get('weather_description', 'Unknown')

                timeline.append({
                    'timestamp': hour_data.get('timestamp'),
                    'temperature': temperature_f,
                    'feels_like': feels_like_f,
                    'humidity': hour_data.get('humidity'),
                    'pressure': hour_data.get('pressure'),
                    'wind_speed': hour_data.get('wind_speed'),
                    'wind_direction': hour_data.get('wind_direction'),
                    'precipitation': hour_data.get('precipitation', 0),
                    'weather_code': weather_code,
                    'weather_description': weather_description,
                    'visibility': hour_data.get('visibility'),
                    'data_type': 'met_office'
                })

            return {
                'city': city_info['name'],
                'latitude': city_info['lat'],
                'longitude': city_info['lon'],
                'timezone': city_info['timezone'],
                'generated_at': datetime.now().isoformat(),
                'data_points': len(timeline),
                'timeline': timeline,
                'summary': self._generate_weather_summary(timeline),
                'source': 'met_office'
            }

        except Exception as e:
            logger.error(f"Error processing Met Office data: {e}")
            return None

    def _save_met_office_data_to_database(self, met_office_data: Dict[str, Any], city_info: Dict[str, Any]):
        """Save Met Office weather data directly to database"""
        try:
            # Import database connection here to avoid circular imports
            import sqlite3
            from pathlib import Path

            db_path = Path(__file__).parent.parent.parent / "data" / "climatetrade.db"
            if not db_path.exists():
                logger.warning("Database not found, cannot save Met Office data")
                return

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get source ID for Met Office
            cursor.execute("SELECT id FROM weather_sources WHERE source_name = 'met_office' LIMIT 1")
            source_row = cursor.fetchone()
            if not source_row:
                # Insert Met Office source if it doesn't exist
                cursor.execute("""
                    INSERT INTO weather_sources (source_name, description, api_key_required, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ['met_office', 'UK Met Office Weather DataHub', 1, 1, datetime.now().isoformat(), datetime.now().isoformat()])
                source_id = cursor.lastrowid
            else:
                source_id = source_row[0]

            # Save timeline data to database
            weather_records = []
            for data_point in met_office_data.get('timeline', []):
                weather_records.append((
                    source_id,
                    city_info.get('name', 'Unknown'),
                    city_info.get('lat'),
                    city_info.get('lon'),
                    data_point.get('timestamp'),
                    data_point.get('temperature'),  # Already in Fahrenheit
                    None, None, None,  # temperature_min, temperature_max, feels_like
                    data_point.get('humidity'),
                    data_point.get('pressure'),
                    data_point.get('wind_speed'),
                    data_point.get('wind_direction'),
                    data_point.get('precipitation'),
                    data_point.get('weather_code'),
                    data_point.get('weather_description'),
                    data_point.get('visibility'),
                    None,  # uv_index
                    json.dumps({'source': 'met_office', 'api_version': 'v1'}),
                    json.dumps(data_point),
                    0.95,  # High data quality score for Met Office
                    datetime.now().isoformat()
                ))

            cursor.executemany("""
                INSERT OR REPLACE INTO weather_data
                (source_id, location_name, latitude, longitude, timestamp,
                 temperature, temperature_min, temperature_max, feels_like,
                 humidity, pressure, wind_speed, wind_direction, precipitation,
                 weather_code, weather_description, visibility, uv_index, alerts,
                 raw_data, data_quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, weather_records)

            conn.commit()
            conn.close()

            logger.info(f"Saved {len(weather_records)} Met Office weather records to database")

        except Exception as e:
            logger.error(f"Failed to save Met Office data to database: {str(e)}")

    def _map_met_office_weather_code(self, code: Optional[int]) -> str:
        """Map Met Office weather codes to descriptive text"""
        if code is None:
            return 'Unknown'
        
        weather_map = {
            0: 'Clear night',
            1: 'Sunny day',
            2: 'Partly cloudy',
            3: 'Partly cloudy',
            4: 'Not used',
            5: 'Mist',
            6: 'Fog',
            7: 'Cloudy',
            8: 'Overcast',
            9: 'Light rain shower',
            10: 'Light rain shower',
            11: 'Drizzle',
            12: 'Light rain',
            13: 'Heavy rain shower',
            14: 'Heavy rain shower',
            15: 'Heavy rain',
            16: 'Sleet shower',
            17: 'Sleet shower',
            18: 'Sleet',
            19: 'Hail shower',
            20: 'Hail shower',
            21: 'Hail',
            22: 'Light snow shower',
            23: 'Light snow shower',
            24: 'Light snow',
            25: 'Heavy snow shower',
            26: 'Heavy snow shower',
            27: 'Heavy snow',
            28: 'Thunder shower',
            29: 'Thunder shower',
            30: 'Thunder'
        }
        return weather_map.get(code, 'Unknown')

    def _get_mock_weather_data(self, city: str) -> Dict[str, Any]:
        """Generate mock weather data for testing with corrected timestamp logic"""
        now = datetime.now()
        city_info = self.get_city_coordinates(city) or {'name': city, 'lat': 0, 'lon': 0, 'timezone': 'UTC'}

        # Generate 24 hourly data points (current hour + next 23 hours)
        timeline = []
        # More realistic September temperatures in Celsius
        base_temp = 15 if city.lower() == 'london' else 20  # London: ~15°C (59°F), NYC: ~20°C (68°F)

        for i in range(24):
            # Calculate timestamp: current hour + i hours
            timestamp = (now + timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)

            # Realistic temperature variation throughout the day (in Celsius)
            hour_of_day = timestamp.hour
            if 6 <= hour_of_day <= 18:  # Daytime
                # Peak temperature around 2-4 PM, milder variation
                temp_variation = min(5, max(-2, (hour_of_day - 14) * 0.8))
            else:  # Nighttime
                temp_variation = -3  # Cooler at night

            temperature = base_temp + temp_variation + (i % 3 - 1) * 0.5  # Add minimal randomness

            # Weather conditions based on time of day
            if hour_of_day in [6, 7, 18, 19]:  # Morning/evening
                weather_code = 2  # Partly cloudy
                weather_desc = 'Partly cloudy'
                precipitation = 0.1 if hour_of_day == 6 else 0
            elif hour_of_day in [12, 13, 14]:  # Midday
                weather_code = 0  # Clear sky
                weather_desc = 'Clear sky'
                precipitation = 0
            else:
                weather_code = 1  # Mainly clear
                weather_desc = 'Mainly clear'
                precipitation = 0

            # Convert temperatures to Fahrenheit for consistency
            temp_fahrenheit = self.celsius_to_fahrenheit(temperature)
            feels_like_fahrenheit = self.celsius_to_fahrenheit(temperature + 1)

            timeline.append({
                'timestamp': timestamp.isoformat(),
                'temperature': round(max(41, min(95, temp_fahrenheit)), 1),  # Clamp temperature in Fahrenheit
                'feels_like': round(max(41, min(95, feels_like_fahrenheit)), 1),
                'humidity': max(30, min(90, 65 + (i % 20 - 10))),  # Realistic humidity range
                'pressure': 1013 + (i % 10 - 5),  # Slight pressure variation
                'wind_speed': max(0, 5 + (i % 8 - 4)),  # Realistic wind speeds
                'wind_direction': (180 + i * 15) % 360,  # Varying wind direction
                'precipitation': precipitation,
                'weather_code': weather_code,
                'weather_description': weather_desc,
                'visibility': max(5000, 10000 - i * 200),  # Decreasing visibility
                'data_type': 'mock'
            })

        return {
            'city': city_info.get('name', city),
            'latitude': city_info.get('lat', 0.0),
            'longitude': city_info.get('lon', 0.0),
            'timezone': city_info.get('timezone', 'UTC'),
            'generated_at': now.isoformat(),
            'data_points': len(timeline),
            'timeline': timeline,
            'summary': self._generate_weather_summary(timeline),
            'source': 'mock_data',
            'note': 'Using mock data - weather clients not available or request failed'
        }

    

    def get_weather_comparison(self, city1: str = 'london', city2: str = 'nyc') -> Dict[str, Any]:
        """Compare weather between two cities"""
        weather1 = self.get_24h_weather_history(city1)
        weather2 = self.get_24h_weather_history(city2)

        return {
            'comparison': {
                'city1': weather1,
                'city2': weather2,
                'temperature_difference': (
                    weather1['summary'].get('temperature_avg', 0) -
                    weather2['summary'].get('temperature_avg', 0)
                ),
                'generated_at': datetime.now().isoformat()
            }
        }

# Global weather service instance