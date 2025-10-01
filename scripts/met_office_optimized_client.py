
#!/usr/bin/env python3
"""
Met Office API Client Optimizado para 350 Llamadas Diarias
Implementa rate limiting inteligente, caché multi-nivel y fallback automático
"""

import os
import json
import time
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallPriority(Enum):
    """Prioridades para llamadas API"""
    CRITICAL = 1    # Datos actuales para trading
    HIGH = 2        # Pronósticos importantes
    MEDIUM = 3      # Datos de validación
    LOW = 4         # Datos de desarrollo

@dataclass
class ApiCall:
    """Registro de llamada API"""
    timestamp: datetime
    endpoint: str
    location: str
    priority: CallPriority
    success: bool
    response_size: int = 0
    cache_hit: bool = False

class MetOfficeRateLimiter:
    """Rate limiter inteligente para Met Office API"""
    
    def __init__(self, daily_limit: int = 350, hourly_limit: int = 15):
        self.daily_limit = daily_limit
        self.hourly_limit = hourly_limit
        self.db_path = Path(__file__).parent.parent / "data" / "met_office_rate_limits.db"
        self._init_database()
        
    def _init_database(self):
        """Inicializar base de datos de rate limiting"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                location TEXT,
                priority INTEGER,
                success BOOLEAN,
                response_size INTEGER DEFAULT 0,
                cache_hit BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp 
            ON api_calls(timestamp)
        """)
        
        conn.commit()
        conn.close()
        
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso actual"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        # Llamadas hoy
        cursor.execute("""
            SELECT COUNT(*) FROM api_calls 
            WHERE timestamp >= ? AND success = 1
        """, [today_start.isoformat()])
        calls_today = cursor.fetchone()[0]
        
        # Llamadas esta hora
        cursor.execute("""
            SELECT COUNT(*) FROM api_calls 
            WHERE timestamp >= ? AND success = 1
        """, [hour_start.isoformat()])
        calls_this_hour = cursor.fetchone()[0]
        
        # Cache hit rate (últimas 24 horas)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as cache_hits
            FROM api_calls 
            WHERE timestamp >= ?
        """, [(now - timedelta(days=1)).isoformat()])
        
        cache_stats = cursor.fetchone()
        cache_hit_rate = (cache_stats[1] / cache_stats[0] * 100) if cache_stats[0] > 0 else 0
        
        conn.close()
        
        return {
            'calls_today': calls_today,
            'calls_this_hour': calls_this_hour,
            'daily_limit': self.daily_limit,
            'hourly_limit': self.hourly_limit,
            'daily_remaining': max(0, self.daily_limit - calls_today),
            'hourly_remaining': max(0, self.hourly_limit - calls_this_hour),
            'cache_hit_rate': round(cache_hit_rate, 1),
            'next_hour_reset': (hour_start + timedelta(hours=1)).isoformat(),
            'next_day_reset': (today_start + timedelta(days=1)).isoformat()
        }
    
    def can_make_call(self, priority: CallPriority) -> Tuple[bool, str]:
        """Verificar si se puede hacer una llamada API"""
        stats = self.get_usage_stats()
        
        # Verificar límite diario
        if stats['daily_remaining'] <= 0:
            return False, "Daily limit exceeded"
            
        # Verificar límite horario
        if stats['hourly_remaining'] <= 0:
            return False, "Hourly limit exceeded"
            
        # Lógica de prioridad
        if priority == CallPriority.CRITICAL:
            # Siempre permitir llamadas críticas si hay cuota
            return True, "Critical priority approved"
            
        elif priority == CallPriority.HIGH:
            # Permitir si tenemos al menos 20% del límite diario
            if stats['daily_remaining'] >= (self.daily_limit * 0.2):
                return True, "High priority approved"
            else:
                return False, "Insufficient quota for high priority"
                
        elif priority == CallPriority.MEDIUM:
            # Permitir si tenemos al menos 40% del límite diario
            if stats['daily_remaining'] >= (self.daily_limit * 0.4):
                return True, "Medium priority approved"
            else:
                return False, "Insufficient quota for medium priority"
                
        else:  # LOW priority
            # Permitir solo si tenemos al menos 60% del límite diario
            if stats['daily_remaining'] >= (self.daily_limit * 0.6):
                return True, "Low priority approved"
            else:
                return False, "Insufficient quota for low priority"
    
    def record_call(self, call: ApiCall):
        """Registrar una llamada API"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_calls 
            (timestamp, endpoint, location, priority, success, response_size, cache_hit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            call.timestamp.isoformat(),
            call.endpoint,
            call.location,
            call.priority.value,
            call.success,
            call.response_size,
            call.cache_hit
        ])
        
        conn.commit()
        conn.close()

class MetOfficeCacheManager:
    """Sistema de caché multi-nivel para Met Office"""
    
    def __init__(self):
        self.memory_cache = {}
        self.memory_ttl = 300  # 5 minutos
        self.db_ttl = 1800     # 30 minutos
        self.db_path = Path(__file__).parent.parent / "data" / "climatetrade.db"
        
    def _get_cache_key(self, location: str, endpoint: str) -> str:
        """Generar clave de caché"""
        return f"met_office:{location}:{endpoint}"
        
    def get_cached_data(self, location: str, endpoint: str) -> Optional[Dict]:
        """Buscar datos en caché (memoria primero, luego DB)"""
        cache_key = self._get_cache_key(location, endpoint)
        
        # Nivel 1: Memoria
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            if datetime.now() - cached_item['timestamp'] < timedelta(seconds=self.memory_ttl):
                logger.debug(f"Cache hit (memory): {cache_key}")
                return cached_item['data']
            else:
                # Expirado, remover
                del self.memory_cache[cache_key]
        
        # Nivel 2: Base de datos
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT raw_data, created_at FROM weather_data 
                WHERE location_name = ? 
                AND source_id = (SELECT id FROM weather_sources WHERE source_name = 'met_office')
                AND datetime(created_at) > datetime('now', '-30 minutes')
                ORDER BY created_at DESC LIMIT 1
            """, [location])
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                try:
                    cached_data = json.loads(result[0])
                    logger.debug(f"Cache hit (database): {cache_key}")
                    
                    # Guardar en memoria para próximas consultas
                    self.memory_cache[cache_key] = {
                        'data': cached_data,
                        'timestamp': datetime.now()
                    }
                    
                    return cached_data
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in cached data for {cache_key}")
                    
        except Exception as e:
            logger.error(f"Error accessing cache database: {e}")
            
        return None
    
    def set_cached_data(self, location: str, endpoint: str, data: Dict):
        """Guardar datos en caché (memoria y DB)"""
        cache_key = self._get_cache_key(location, endpoint)
        
        # Nivel 1: Memoria
        self.memory_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        
        # Nivel 2: Base de datos (se guarda automáticamente por el weather service)
        logger.debug(f"Data cached: {cache_key}")

class MetOfficeOptimizedClient:
    """Cliente optimizado de Met Office con rate limiting y caché"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/"
        self.rate_limiter = MetOfficeRateLimiter()
        self.cache_manager = MetOfficeCacheManager()
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'apikey': api_key
        })
        
        # Coordenadas predefinidas para ubicaciones importantes
        self.locations = {
            'london': {'lat': 51.5074, 'lon': -0.1278, 'name': 'London,UK'},
            'manchester': {'lat': 53.4808, 'lon': -2.2426, 'name': 'Manchester,UK'},
            'birmingham': {'lat': 52.4862, 'lon': -1.8904, 'name': 'Birmingham,UK'},
            'glasgow': {'lat': 55.8642, 'lon': -4.2518, 'name': 'Glasgow,UK'},
            'cardiff': {'lat': 51.4816, 'lon': -3.1791, 'name': 'Cardiff,UK'}
        }
    
    def get_current_weather(self, location: str, priority: CallPriority = CallPriority.HIGH) -> Optional[Dict]:
        """Obtener datos meteorológicos actuales"""
        return self._make_api_call(location, 'hourly', priority, hours_limit=1)
    
    def get_hourly_forecast(self, location: str, hours: int = 24, priority: CallPriority = CallPriority.MEDIUM) -> Optional[Dict]:
        """Obtener pronóstico horario"""
        return self._make_api_call(location, 'hourly', priority, hours_limit=hours)
    
    def get_daily_forecast(self, location: str, days: int = 5, priority: CallPriority = CallPriority.MEDIUM) -> Optional[Dict]:
        """Obtener pronóstico diario"""
        return self._make_api_call(location, 'daily', priority, days_limit=days)
    
    def _make_api_call(self, location: str, timestep: str, priority: CallPriority, 
                      hours_limit: int = None, days_limit: int = None) -> Optional[Dict]:
        """Realizar llamada API con rate limiting y caché"""
        
        # Normalizar ubicación
        location_key = location.lower().replace(',uk', '').replace(' ', '')
        if location_key not in self.locations:
            logger.warning(f"Location not supported by Met Office: {location}")
            return None
            
        location_info = self.locations[location_key]
        endpoint = f"{timestep}_{location_key}"
        
        # 1. Verificar caché primero
        cached_data = self.cache_manager.get_cached_data(location, endpoint)
        if cached_data:
            # Registrar cache hit
            call_record = ApiCall(
                timestamp=datetime.now(),
                endpoint=endpoint,
                location=location,
                priority=priority,
                success=True,
                cache_hit=True
            )
            self.rate_limiter.record_call(call_record)
            return cached_data
        
        # 2. Verificar rate limit
        can_call, reason = self.rate_limiter.can_make_call(priority)
        if not can_call:
            logger.warning(f"API call blocked: {reason}")
            return None
        
        # 3. Realizar llamada API
        try:
            url = f"{self.base_url}{timestep}"
            params = {
                'latitude': location_info['lat'],
                'longitude': location_info['lon'],
                'includeLocationName': 'true',
                'excludeParameterMetadata': 'false'
            }
            
            logger.info(f"Making Met Office API call: {endpoint} (Priority: {priority.name})")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 4. Procesar y normalizar datos
            processed_data = self._process_met_office_data(data, location_info, timestep)
            
            # 5. Guardar en caché
            self.cache_manager.set_cached_data(location, endpoint, processed_data)
            
            # 6. Registrar llamada exitosa
            call_record = ApiCall(
                timestamp=datetime.now(),
                endpoint=endpoint,
                location=location,
                priority=priority,
                success=True,
                response_size=len(response.text),
                cache_hit=False
            )
            self.rate_limiter.record_call(call_record)
            
            logger.info(f"Met Office API call successful: {endpoint}")
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Met Office API call failed: {e}")
            
            # Registrar llamada fallida
            call_record = ApiCall(
                timestamp=datetime.now(),
                endpoint=endpoint,
                location=location,
                priority=priority,
                success=False
            )
            self.rate_limiter.record_call(call_record)
            
            return None
    
    def _process_met_office_data(self, raw_data: Dict, location_info: Dict, timestep: str) -> Dict:
        """Procesar datos de Met Office al formato estándar"""
        processed = {
            'source': 'met_office',
            'location': location_info['name'],
            'latitude': location_info['lat'],
            'longitude': location_info['lon'],
            'timestamp': datetime.now().isoformat(),
            'data_quality_score': 0.95,  # Met Office tiene alta calidad
            'raw_data': raw_data
        }
        
        if 'features' in raw_data and raw_data['features']:
            feature = raw_data['features'][0]
            properties = feature.get('properties', {})
            time_series = properties.get('timeSeries', [])
            
            if time_series:
                # Procesar datos según el tipo de timestep
                if timestep == 'hourly':
                    processed['forecast'] = self._process_hourly_data(time_series)
                elif timestep == 'daily':
                    processed['forecast'] = self._process_daily_data(time_series)
                
                # Datos actuales (primer elemento)
                current = time_series[0] if time_series else {}
                processed['current'] = {
                    'temperature': current.get('screenTemperature'),
                    'feels_like': current.get('feelsLikeTemperature'),
                    'humidity': current.get('screenRelativeHumidity'),
                    'pressure': current.get('mslp'),
                    'wind_speed': current.get('windSpeed10m'),
                    'wind_direction': current.get('windDirectionFrom10m'),
                    'precipitation': current.get('totalPrecipAmount', 0),
                    'weather_code': current.get('significantWeatherCode'),
                    'weather_description': self._weather_code_to_description(current.get('significantWeatherCode')),
                    'visibility': current.get('visibility'),
                    'timestamp': current.get('time', datetime.now().isoformat())
                }
        
        return processed
    
    def _process_hourly_data(self, time_series: List[Dict]) -> List[Dict]:
        """Procesar datos horarios"""
        hourly_data = []
        for ts in time_series[:24]:  # Máximo 24 horas
            hourly_data.append({
                'timestamp': ts.get('time'),
                'temperature': ts.get('screenTemperature'),
                'feels_like': ts.get('feelsLikeTemperature'),
                'humidity': ts.get('screenRelativeHumidity'),
                'pressure': ts.get('mslp'),
                'wind_speed': ts.get('windSpeed10m'),
                'wind_direction': ts.get('windDirectionFrom10m'),
                'precipitation': ts.get('totalPrecipAmount', 0),
                'weather_code': ts.get('significantWeatherCode'),
                'weather_description': self._weather_code_to_description(ts.get('significantWeatherCode')),
                'visibility': ts.get('visibility'),
                'forecast_type': 'hourly'
            })
        return hourly_data
    
    def _process_daily_data(self, time_series: List[Dict]) -> List[Dict]:
        """Procesar datos diarios"""
        daily_data = []
        for ts in time_series[:7]:  # Máximo 7 días
            daily_data.append({
                'date': ts.get('time'),
                'temperature_max': ts.get('maxScreenTemperature'),
                'temperature_min': ts.get('minScreenTemperature'),
                'humidity': ts.get('screenRelativeHumidity'),
                'wind_speed_max': ts.get('max10mWindGust'),
                'precipitation_total': ts.get('totalPrecipAmount', 0),
                'weather_code': ts.get('significantWeatherCode'),
                'weather_description': self._weather_code_to_description(ts.get('significantWeatherCode')),
                'forecast_type': 'daily'
            })
        return daily_data
    
    def _weather_code_to_description(self, code: Optional[int]) -> str:
        """Convertir código meteorológico a descripción"""
        if code is None:
            return "Unknown"
            
        # Met Office weather codes
        weather_codes = {
            0: "Clear night",
            1: "Sunny day",
            2: "Partly cloudy (night)",
            3: "Partly cloudy (day)",
            4: "Not used",
            5: "Mist",
            6: "Fog",
            7: "Cloudy",
            8: "Overcast",
            9: "Light rain shower (night)",
            10: "Light rain shower (day)",
            11: "Drizzle",
            12: "Light rain",
            13: "Heavy rain shower (night)",
            14: "Heavy rain shower (day)",
            15: "Heavy rain",
            16: "Sleet shower (night)",
            17: "Sleet shower (day)",
            18: "Sleet",
            19: "Hail shower (night)",
            20: "Hail shower (day)",
            21: "Hail",
            22: "Light snow shower (night)",
            23: "Light snow shower (day)",
            24: "Light snow",
            25: "Heavy snow shower (night)",
            26: "Heavy snow shower (day)",
            27: "Heavy snow",
            28: "Thunder
        }
        
        return weather_codes.get(code, f"Unknown weather code: {code}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso de la API"""
        return self.rate_limiter.get_usage_stats()
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar conectividad con Met Office API"""
        try:
            # Hacer una llamada de prueba con prioridad baja
            test_data = self.get_current_weather('london', CallPriority.LOW)
            
            if test_data:
                return {
                    'status': 'success',
                    'message': 'Met Office API connection successful',
                    'data_quality_score': test_data.get('data_quality_score', 0),
                    'location': test_data.get('location'),
                    'timestamp': test_data.get('timestamp')
                }
            else:
                return {
                    'status': 'failed',
                    'message': 'No data returned from Met Office API',
                    'usage_stats': self.get_usage_stats()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Met Office API test failed: {str(e)}',
                'usage_stats': self.get_usage_stats()
            }

def main():
    """Función principal para testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Met Office Optimized Client")
    parser.add_argument('--api-key', required=True, help='Met Office API key')
    parser.add_argument('--location', default='london', help='Location to query')
    parser.add_argument('--test', action='store_true', help='Run connection test')
    parser.add_argument('--stats', action='store_true', help='Show usage statistics')
    parser.add_argument('--current', action='store_true', help='Get current weather')
    parser.add_argument('--forecast', action='store_true', help='Get forecast')
    
    args = parser.parse_args()
    
    client = MetOfficeOptimizedClient(args.api_key)
    
    if args.test:
        result = client.test_connection()
        print(json.dumps(result, indent=2))
        
    elif args.stats:
        stats = client.get_usage_stats()
        print(json.dumps(stats, indent=2))
        
    elif args.current:
        data = client.get_current_weather(args.location, CallPriority.HIGH)
        if data:
            print(json.dumps(data, indent=2))
        else:
            print("No data available")
            
    elif args.forecast:
        data = client.get_hourly_forecast(args.location, 24, CallPriority.MEDIUM)
        if data:
            print(json.dumps(data, indent=2))
        else:
            print("No forecast data available")
    
    else:
        # Mostrar estadísticas por defecto
        stats = client.get_usage_stats()
        print("Met Office API Usage Statistics:")
        print(f"Daily calls: {stats['calls_today']}/{stats['daily_limit']}")
        print(f"Hourly calls: {stats['calls_this_hour']}/{stats['hourly_limit']}")
        print(f"Cache hit rate: {stats['cache_hit_rate']}%")

if __name__ == "__main__":
    main()