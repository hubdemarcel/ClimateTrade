# ClimaTrade AI - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
4. [WebSocket API](#websocket-api)
5. [Python SDK](#python-sdk)
6. [Integration Examples](#integration-examples)
7. [Met Office API Integration Guide - London Weather Data](#met-office-api-integration-guide---london-weather-data)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [SDKs and Libraries](#sdks-and-libraries)
11. [Data Validation](#data-validation)
12. [Development](#development)

## Overview

ClimaTrade AI provides comprehensive APIs for accessing weather data, market information, trading functionality, and system management. The APIs are designed to be RESTful, real-time capable via WebSockets, and easily integrable with Python applications.

### API Versions

- **v1** (Current): Stable production API
- **v2** (Beta): Next-generation API with enhanced features

### Base URLs

```bash
# Development
http://localhost:8000/api/v1

# Production
https://api.climatetrade.ai/api/v1

# WebSocket
ws://localhost:8000/ws
wss://api.climatetrade.ai/ws
```

### Response Format

All API responses follow a consistent JSON format:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_123456",
    "version": "v1"
  },
  "error": null
}
```

## Authentication

### API Key Authentication

```bash
# Include in request headers
Authorization: Bearer your_api_key_here
X-API-Key: your_api_key_here
```

### JWT Token Authentication

```bash
# For authenticated user sessions
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Authentication Endpoints

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

#### Refresh Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer refresh_token_here
```

#### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer access_token_here
```

### Backend Authentication Middleware

```python
# backend/auth.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from datetime import datetime, timedelta

security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### Apply Authentication to Protected Endpoints

```python
# main.py - Update endpoints to require authentication
from .auth import verify_token

@app.get("/api/trading/performance")
async def get_trading_performance(
    days: int = 30,
    username: str = Depends(verify_token)
):
    """Get trading performance data (protected)"""
    # ... existing code ...

@app.get("/api/trading/positions")
async def get_current_positions(username: str = Depends(verify_token)):
    """Get current trading positions (protected)"""
    # ... existing code ...
```

## REST API Endpoints

### Weather Data Endpoints

#### Get Current Weather

```http
GET /api/v1/weather/{location}
```

**Parameters:**

- `location` (path): Location name or coordinates (e.g., "London,UK" or "51.5074,-0.1278")
- `units` (query, optional): "metric" or "imperial" (default: "metric")
- `source` (query, optional): Weather data source (default: "auto")
  - Available sources: "open_meteo", "met_office", "meteostat", "auto"

**Response:**

```json
{
  "success": true,
  "data": {
    "location": {
      "name": "London, UK",
      "coordinates": { "latitude": 51.5074, "longitude": -0.1278 },
      "timezone": "Europe/London"
    },
    "current": {
      "temperature": 18.5,
      "feels_like": 17.2,
      "humidity": 72,
      "pressure": 1013,
      "wind_speed": 3.2,
      "wind_direction": 180,
      "weather_code": 800,
      "weather_description": "Clear sky",
      "visibility": 10000,
      "uv_index": 5,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    "source": "met_office",
    "data_quality_score": 0.95
  }
}
```

#### Get Weather Forecast

```http
GET /api/v1/weather/{location}/forecast
```

**Parameters:**

- `location` (path): Location identifier
- `days` (query, optional): Number of days (1-14, default: 7)
- `hourly` (query, optional): Include hourly data (default: false)

### Polymarket Data Endpoints

#### Get Market Data

```http
GET /api/v1/markets/{market_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "market_id": "0x123...",
    "event_title": "Will it rain in London tomorrow?",
    "question": "Will the precipitation in London exceed 1mm tomorrow?",
    "outcomes": ["Yes", "No"],
    "probabilities": [0.65, 0.35],
    "volume": 125000,
    "liquidity": 45000,
    "end_date": "2024-01-02T00:00:00Z",
    "active": true,
    "closed": false
  }
}
```

#### Place Order

```http
POST /api/v1/orders
Authorization: Bearer your_token
Content-Type: application/json
```

**Request Body:**

```json
{
  "market_id": "0x123...",
  "outcome": "Yes",
  "side": "buy",
  "order_type": "limit",
  "price": 0.6,
  "size": 1000,
  "time_in_force": "GTC"
}
```

### Trading and Strategy Endpoints

#### Get Portfolio

```http
GET /api/v1/portfolio
Authorization: Bearer your_token
```

#### Run Backtest

```http
POST /api/v1/backtest
Authorization: Bearer your_token
Content-Type: application/json
```

**Request Body:**

```json
{
  "strategy_name": "temperature_threshold",
  "market_ids": ["0x123...", "0x456..."],
  "locations": ["London,UK", "New York,NY"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000.0,
  "parameters": {
    "hot_threshold": 25.0,
    "cold_threshold": 5.0
  }
}
```

### System Management Endpoints

#### Health Check

```http
GET /api/v1/health
```

#### System Metrics

```http
GET /api/v1/metrics
```

## WebSocket API

### Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.climatetrade.ai/ws');

// Authentication
ws.onopen = () => {
  ws.send(
    JSON.stringify({
      type: 'auth',
      token: 'your_jwt_token',
    })
  );
};
```

### Real-time Market Data

```javascript
// Subscribe to market updates
ws.send(
  JSON.stringify({
    type: 'subscribe',
    channel: 'market',
    market_id: '0x123...',
  })
);

// Handle market updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'market_update') {
    console.log('Market update:', data.payload);
  }
};
```

### Real-time Weather Data

```javascript
// Subscribe to weather updates
ws.send(
  JSON.stringify({
    type: 'subscribe',
    channel: 'weather',
    location: 'London,UK',
  })
);

// Handle weather updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'weather_update') {
    console.log('Weather update:', data.payload);
  }
};
```

### Trading Notifications

```javascript
// Subscribe to trading notifications
ws.send(
  JSON.stringify({
    type: 'subscribe',
    channel: 'trading',
  })
);

// Handle trading events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'order_filled') {
    console.log('Order filled:', data.payload);
  } else if (data.type === 'position_update') {
    console.log('Position update:', data.payload);
  }
};
```

## Python SDK

### Core Classes

#### ClimaTradeClient

Main client for interacting with ClimaTrade AI APIs.

```python
from climatetrade.client import ClimaTradeClient

# Initialize client
client = ClimaTradeClient(
    api_key='your_api_key',
    base_url='https://api.climatetrade.ai/api/v1'
)

# Or with JWT token
client = ClimaTradeClient(
    jwt_token='your_jwt_token',
    base_url='https://api.climatetrade.ai/api/v1'
)
```

**Methods:**

```python
# Weather data
weather = client.get_weather('London,UK')
forecast = client.get_weather_forecast('London,UK', days=7)
history = client.get_weather_history('London,UK', '2024-01-01', '2024-01-31')

# Market data
market = client.get_market('0x123...')
orderbook = client.get_orderbook('0x123...')
markets = client.get_markets(active=True, limit=50)

# Trading
order = client.place_order(
    market_id='0x123...',
    outcome='Yes',
    side='buy',
    price=0.60,
    size=1000
)
portfolio = client.get_portfolio()
orders = client.get_orders(status='open')

# Backtesting
backtest = client.run_backtest(
    strategy_name='temperature_threshold',
    market_ids=['0x123...', '0x456...'],
    locations=['London,UK', 'New York,NY'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)
results = client.get_backtest_results(backtest_id)

# System
health = client.health_check()
metrics = client.get_metrics()
```

#### WeatherDataClient

Specialized client for weather data operations.

```python
from climatetrade.weather import WeatherDataClient

weather_client = WeatherDataClient(api_key='your_api_key')

# Get current weather
current = weather_client.get_current_weather('London,UK')

# Get forecast
forecast = weather_client.get_forecast('London,UK', days=7, hourly=True)

# Get historical data
history = weather_client.get_historical_data(
    'London,UK',
    start_date='2024-01-01',
    end_date='2024-01-31',
    frequency='hourly'
)

# Batch operations
locations = ['London,UK', 'New York,NY', 'Tokyo,JP']
batch_weather = weather_client.get_batch_weather(locations)
```

#### PolymarketClient

Client for Polymarket operations.

```python
from climatetrade.polymarket import PolymarketClient

pm_client = PolymarketClient(
    api_key='your_api_key',
    private_key='your_private_key'
)

# Market operations
markets = pm_client.get_active_markets(limit=100)
market = pm_client.get_market('0x123...')
orderbook = pm_client.get_orderbook('0x123...')

# Trading operations
order = pm_client.place_limit_order(
    market_id='0x123...',
    outcome='Yes',
    side='buy',
    price=0.60,
    size=1000
)

# Portfolio operations
balance = pm_client.get_balance()
positions = pm_client.get_positions()
orders = pm_client.get_orders(status='open')
```

#### BacktestingClient

Client for backtesting operations.

```python
from climatetrade.backtesting import BacktestingClient

bt_client = BacktestingClient(api_key='your_api_key')

# Run backtest
backtest = bt_client.run_backtest(
    strategy_name='temperature_threshold',
    market_ids=['0x123...', '0x456...'],
    locations=['London,UK', 'New York,NY'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=10000.0,
    parameters={
        'hot_threshold': 25.0,
        'cold_threshold': 5.0,
        'signal_strength_threshold': 0.7
    }
)

# Get results
results = bt_client.get_backtest_results(backtest.backtest_id)

# List backtests
backtests = bt_client.list_backtests(status='completed', limit=20)

# Compare strategies
comparison = bt_client.compare_strategies(
    strategy_names=['temperature', 'precipitation', 'wind'],
    market_ids=['0x123...'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

## Integration Examples

### Python Integration

#### Basic Weather and Trading Integration

```python
import asyncio
from climatetrade.client import ClimaTradeClient

async def weather_trading_strategy():
    client = ClimaTradeClient(api_key='your_api_key')

    # Get weather data
    weather = await client.get_weather('London,UK')

    # Check if it's hot (above 25°C)
    if weather.temperature > 25.0:
        # Find relevant markets
        markets = await client.search_markets(
            query='temperature London',
            active=True
        )

        for market in markets:
            # Get current probabilities
            orderbook = await client.get_orderbook(market.market_id)

            # Calculate if it's a good trade opportunity
            if should_trade(weather, market, orderbook):
                # Place order
                order = await client.place_order(
                    market_id=market.market_id,
                    outcome='Yes',  # Assuming "Yes" means hot
                    side='buy',
                    price=orderbook.asks[0].price,
                    size=1000
                )
                print(f"Placed order: {order.order_id}")

def should_trade(weather, market, orderbook):
    """Determine if trading conditions are favorable"""
    # Implement your trading logic here
    return weather.temperature > 28.0 and orderbook.spread < 0.1
```

#### Real-time Trading Bot

```python
import asyncio
from climatetrade.websocket import ClimaTradeWebSocket
from climatetrade.client import ClimaTradeClient

class WeatherTradingBot:
    def __init__(self, api_key, jwt_token):
        self.client = ClimaTradeClient(api_key=api_key, jwt_token=jwt_token)
        self.ws = ClimaTradeWebSocket(jwt_token=jwt_token)
        self.ws.on_message = self.handle_message

    async def start(self):
        # Connect to WebSocket
        await self.ws.connect()

        # Subscribe to weather and market updates
        await self.ws.subscribe('weather', location='London,UK')
        await self.ws.subscribe('market', market_id='0x123...')

        # Keep running
        while True:
            await asyncio.sleep(1)

    async def handle_message(self, message):
        if message['type'] == 'weather_update':
            await self.handle_weather_update(message['payload'])
        elif message['type'] == 'market_update':
            await self.handle_market_update(message['payload'])

    async def handle_weather_update(self, weather_data):
        # Analyze weather data and make trading decisions
        if weather_data['temperature'] > 30.0:
            # Hot weather detected - trade accordingly
            await self.execute_trade_strategy(weather_data)

    async def handle_market_update(self, market_data):
        # React to market changes
        pass

    async def execute_trade_strategy(self, weather_data):
        # Implement your trading strategy
        pass

# Usage
bot = WeatherTradingBot(api_key='your_key', jwt_token='your_token')
asyncio.run(bot.start())
```

### JavaScript/Node.js Integration

#### Web Dashboard Integration

```javascript
// Initialize ClimaTrade client
const climaTrade = new ClimaTradeClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.climatetrade.ai/api/v1',
});

// Get weather data
async function updateWeatherData() {
  try {
    const weather = await climaTrade.getWeather('London,UK');
    document.getElementById(
      'temperature'
    ).textContent = `${weather.current.temperature}°C`;
    document.getElementById(
      'humidity'
    ).textContent = `${weather.current.humidity}%`;
  } catch (error) {
    console.error('Failed to fetch weather data:', error);
  }
}

// Get market data
async function updateMarketData() {
  try {
    const market = await climaTrade.getMarket('0x123...');
    document.getElementById('market-title').textContent = market.question;

    market.outcomes.forEach((outcome, index) => {
      const probability = market.probabilities[index];
      // Update UI with market data
    });
  } catch (error) {
    console.error('Failed to fetch market data:', error);
  }
}

// Real-time updates with WebSocket
const ws = new ClimaTradeWebSocket('your_jwt_token');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'weather_update') {
    updateWeatherDisplay(data.payload);
  } else if (data.type === 'market_update') {
    updateMarketDisplay(data.payload);
  }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
  updateWeatherData();
  updateMarketData();
  ws.connect();
});
```

#### Enhanced Error Handling for Frontend

```typescript
// Enhanced WeatherDashboard.tsx
const WeatherDashboard: React.FC<WeatherDashboardProps> = ({
  refreshTrigger,
}) => {
  const [weatherData, setWeatherData] = useState<WeatherData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  const fetchWeatherData = async (isRetry = false) => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get('/api/weather/data?hours=24');
      setWeatherData(response.data);

      // Reset retry count on success
      setRetryCount(0);
    } catch (error) {
      console.error('Failed to fetch weather data:', error);

      const errorMessage = axios.isAxiosError(error)
        ? `Network error: ${error.message}`
        : 'Failed to load weather data';

      setError(errorMessage);

      // Implement retry logic for network errors
      if (
        axios.isAxiosError(error) &&
        error.code === 'NETWORK_ERROR' &&
        retryCount < maxRetries
      ) {
        setRetryCount((prev) => prev + 1);
        setTimeout(() => fetchWeatherData(true), 2000 * (retryCount + 1)); // Exponential backoff
        return;
      }

      // Fallback to empty data
      setWeatherData([]);
    } finally {
      setLoading(false);
    }
  };

  // Add error display in render
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-800 font-medium">
            Error Loading Weather Data
          </span>
        </div>
        <p className="text-red-700 mt-2">{error}</p>
        <button
          onClick={() => fetchWeatherData()}
          className="mt-3 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  // ... rest of component
};
```

#### Caching Strategy Implementation

```typescript
// hooks/useApiCache.ts
import { useState, useEffect, useCallback } from 'react';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface CacheOptions {
  duration: number; // milliseconds
  key: string;
}

export function useApiCache<T>(
  fetcher: () => Promise<T>,
  options: CacheOptions,
  dependencies: any[] = []
): [T | null, boolean, Error | null, () => Promise<void>] {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(
    async (force = false) => {
      const cacheKey = `api_cache_${options.key}`;
      const now = Date.now();

      // Check cache first
      if (!force) {
        try {
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            const entry: CacheEntry<T> = JSON.parse(cached);
            if (entry.expiresAt > now) {
              setData(entry.data);
              setError(null);
              return;
            }
          }
        } catch (e) {
          // Cache corrupted, ignore
        }
      }

      // Fetch fresh data
      setLoading(true);
      try {
        const result = await fetcher();
        setData(result);
        setError(null);

        // Cache the result
        const entry: CacheEntry<T> = {
          data: result,
          timestamp: now,
          expiresAt: now + options.duration,
        };
        localStorage.setItem(cacheKey, JSON.stringify(entry));
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    },
    [fetcher, options]
  );

  useEffect(() => {
    fetchData();
  }, dependencies);

  const refetch = () => fetchData(true);

  return [data, loading, error, refetch];
}
```

## Met Office API Integration Guide - London Weather Data

### Overview

This guide provides complete integration instructions for the Met Office Weather DataHub API, optimized for London weather data collection with 350 daily API calls. The system uses an intelligent strategy: hourly data collection with enhanced 15-minute intervals during peak trading hours (12:00-18:00 GMT).

**Target Location**: London, UK (51.5074, -0.1278)  
**Daily API Limit**: 350 calls  
**Strategy**: Hourly + Peak 15-minute intervals

### Optimized Call Distribution Strategy

#### Daily Call Allocation (350 total)

```
🏙️ LONDON INTENSIVE STRATEGY:

📅 BASE COVERAGE (42 calls):
├── 00:00-11:59: Hourly data (12 calls)
├── 12:00-18:00: 15-minute intervals (24 calls)
├── 18:01-23:59: Hourly data (6 calls)
└── TOTAL BASE: 42 calls

🔄 ADDITIONAL USAGE (308 calls available):
├── London extended forecasts: 100 calls
├── London historical data: 100 calls
├── Data quality validation: 50 calls
├── Weather alerts & events: 40 calls
└── Emergency buffer: 18 calls
```

### Peak Hours Schedule (12:00-18:00 GMT)

```
🕐 15-MINUTE INTERVALS DURING TRADING HOURS:
12:00, 12:15, 12:30, 12:45
13:00, 13:15, 13:30, 13:45
14:00, 14:15, 14:30, 14:45
15:00, 15:15, 15:30, 15:45
16:00, 16:15, 16:30, 16:45
17:00, 17:15, 17:30, 17:45

Total: 6 hours × 4 calls = 24 calls
```

### Configuration Setup

#### Step 1: Configure API Key

Edit [`web/backend/.env`](../web/backend/.env):

```bash
# Replace the mock key
MET_OFFICE_API_KEY=your_real_api_key_here

# Add optimization configuration
MET_OFFICE_BASE_URL=https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/
MET_OFFICE_DAILY_LIMIT=350
MET_OFFICE_HOURLY_LIMIT=15
MET_OFFICE_CACHE_TTL=1800
MET_OFFICE_PRIORITY_ENABLED=true
MET_OFFICE_FALLBACK_ENABLED=true

# London-specific configuration
MET_OFFICE_LONDON_LATITUDE=51.5074
MET_OFFICE_LONDON_LONGITUDE=-0.1278
MET_OFFICE_LONDON_PRIORITY=CRITICAL
MET_OFFICE_PEAK_START_HOUR=12
MET_OFFICE_PEAK_END_HOUR=18
MET_OFFICE_PEAK_INTERVAL=15
MET_OFFICE_STANDARD_INTERVAL=60
```

#### Step 2: Test API Connectivity

```bash
cd scripts
python met_office_london_weather.py --apikey YOUR_API_KEY --current --json
```

**Expected Response:**

```json
{
  "location": "London",
  "temperature": 15.2,
  "weather_type": 3,
  "wind_speed": 8,
  "humidity": 72,
  "precipitation": 0.1,
  "timestamp": "2025-09-10T05:00:00Z"
}
```

#### Step 3: Database Integration

Add Met Office as a data source:

```bash
cd database
python -c "
import sqlite3
conn = sqlite3.connect('../data/climatetrade.db')
cursor = conn.cursor()
cursor.execute('''
    INSERT OR IGNORE INTO weather_sources
    (source_name, description, api_endpoint, api_key_required, rate_limit_per_hour, active)
    VALUES (?, ?, ?, ?, ?, ?)
''', ['met_office', 'UK Met Office Weather DataHub',
      'https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/',
      1, 15, 1])
conn.commit()
print('✅ Met Office added as data source')
conn.close()
"
```

### System Architecture

#### Core Components

##### 1. Optimized Client (`scripts/met_office_optimized_client.py`)

```python
class MetOfficeOptimizedClient:
    """Met Office client with intelligent rate limiting and caching"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.rate_limiter = MetOfficeRateLimiter()
        self.cache_manager = MetOfficeCacheManager()
        self.london_coords = (51.5074, -0.1278)

    def get_london_weather(self, priority: CallPriority) -> Dict:
        """Get London weather data with intelligent scheduling"""
        # Check cache first
        # Verify rate limits
        # Make API call if needed
        # Store in cache
        return weather_data
```

##### 2. Rate Limiter (`scripts/met_office_rate_limiter.py`)

```python
class MetOfficeRateLimiter:
    """Intelligent rate limiting for 350 daily calls"""

    def __init__(self):
        self.daily_limit = 350
        self.hourly_limit = 15
        self.london_schedule = self._init_london_schedule()

    def should_make_london_call(self) -> bool:
        """Determine if London call should be made based on schedule"""
        now = datetime.now()
        hour, minute = now.hour, now.minute

        if 12 <= hour < 18:  # Peak hours
            return minute in [0, 15, 30, 45]
        else:  # Standard hours
            return minute == 0
```

##### 3. Multi-Level Caching (`scripts/met_office_cache_manager.py`)

```python
class MetOfficeCacheManager:
    """Multi-level caching to minimize API calls"""

    def __init__(self):
        self.memory_cache = {}      # Level 1: 5 minutes
        self.db_cache_ttl = 1800    # Level 2: 30 minutes
        self.extended_cache_ttl = 7200  # Level 3: 2 hours

    def get_cached_london_data(self) -> Optional[Dict]:
        """Get cached London data from appropriate level"""
        # Check memory cache first
        # Check database cache
        # Check extended cache
        return cached_data
```

### Weather Service Integration

Update [`web/backend/weather_service.py`](../web/backend/weather_service.py):

```python
# Add Met Office import
try:
    from met_office_optimized_client import MetOfficeOptimizedClient, CallPriority
    MET_OFFICE_CLIENT_AVAILABLE = True
except ImportError:
    MET_OFFICE_CLIENT_AVAILABLE = False

class WeatherService:
    def __init__(self):
        # Initialize Met Office client
        met_office_key = os.getenv('MET_OFFICE_API_KEY')
        if (met_office_key and
            met_office_key != 'mock_met_office_key' and
            MET_OFFICE_CLIENT_AVAILABLE):
            self.met_office_client = MetOfficeOptimizedClient(met_office_key)
            logger.info("Met Office client initialized for London")

    def get_london_weather_optimized(self) -> Dict[str, Any]:
        """Get London weather with Met Office priority"""
        if self.met_office_client:
            try:
                return self.met_office_client.get_london_weather(CallPriority.CRITICAL)
            except Exception as e:
                logger.error(f"Met Office error: {e}")

        # Fallback to Open-Meteo
        return self.get_open_meteo_weather("London")
```

### Intelligent Caching Strategy

#### Cache Levels

##### Level 1: Memory Cache (5 minutes)

- Instant response for repeated requests
- London current data cached in RAM
- Automatic expiration and refresh

##### Level 2: Database Cache (30 minutes)

- Persistent storage in SQLite
- Structured data for quick queries
- Reduces API calls for recent data

##### Level 3: Extended Cache (2 hours)

- Long-term storage for forecasts
- Historical data preservation
- Fallback data availability

#### Cache Implementation

```sql
-- Cache table structure
SELECT raw_data FROM weather_data
WHERE source_id = (SELECT id FROM weather_sources WHERE source_name = 'met_office')
AND location = 'London'
AND datetime(created_at) > datetime('now', '-30 minutes')
ORDER BY created_at DESC LIMIT 1;
```

### Monitoring and Alerts

#### Real-Time Usage Dashboard

```
📊 MET OFFICE API STATUS
┌─────────────────────────────────────┐
│ 🔥 LONDON WEATHER MONITORING       │
├─────────────────────────────────────┤
│ Calls today: 127/350 (36%)         │
│ Calls this hour: 8/15 (53%)        │
│ London data age: 12 minutes        │
│ Cache hit rate: 78%                │
│ Next London call: 14:15 (2 min)    │
│ Fallback status: Inactive          │
└─────────────────────────────────────┘
```

#### Alert Thresholds

```python
ALERT_THRESHOLDS = {
    'daily_usage_warning': 0.8,     # 280/350 calls
    'daily_usage_critical': 0.95,   # 332/350 calls
    'hourly_usage_warning': 0.8,    # 12/15 calls
    'cache_hit_rate_low': 0.5,      # <50% cache efficiency
    'london_data_stale': 1800       # >30 minutes old
}
```

### Fallback Strategy

#### Automatic Fallback Chain

```
1️⃣ Met Office (Primary)
├── ✅ Official UK weather data
├── ✅ High accuracy for London
└── ⚠️ Limited to 350 calls/day

2️⃣ Open-Meteo (Fallback)
├── ✅ Unlimited calls
├── ✅ Global coverage
└── ⚠️ Lower precision for UK

3️⃣ Cached Data (Emergency)
├── ✅ Always available
├── ✅ Validated historical data
└── ⚠️ May be outdated
```

#### Fallback Logic

```python
def get_london_weather_with_fallback() -> Dict:
    # 1. Try Met Office (if quota available)
    if met_office_quota_available() and should_make_london_call():
        data = met_office_client.get_london_weather()
        if data: return data

    # 2. Check cache
    cached_data = cache_manager.get_cached_london_data()
    if cached_data and not is_stale(cached_data):
        return cached_data

    # 3. Fallback to Open-Meteo
    return open_meteo_client.get_weather(51.5074, -0.1278)
```

## Error Handling

### HTTP Status Codes

| Code | Meaning               | Description                     |
| ---- | --------------------- | ------------------------------- |
| 200  | OK                    | Request successful              |
| 201  | Created               | Resource created successfully   |
| 400  | Bad Request           | Invalid request parameters      |
| 401  | Unauthorized          | Authentication required         |
| 403  | Forbidden             | Insufficient permissions        |
| 404  | Not Found             | Resource not found              |
| 429  | Too Many Requests     | Rate limit exceeded             |
| 500  | Internal Server Error | Server error                    |
| 502  | Bad Gateway           | Gateway error                   |
| 503  | Service Unavailable   | Service temporarily unavailable |

### Error Response Format

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "location",
      "reason": "Location format is invalid"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_123456"
  },
  "meta": {
    "version": "v1"
  }
}
```

### Python Error Handling

```python
from climatetrade.client import ClimaTradeClient
from climatetrade.exceptions import APIError, RateLimitError, AuthenticationError

client = ClimaTradeClient(api_key='your_api_key')

try:
    weather = client.get_weather('London,UK')
    print(f"Temperature: {weather.temperature}°C")

except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Refresh token or check API key

except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Wait before retrying
    time.sleep(e.retry_after)

except APIError as e:
    print(f"API error: {e.code} - {e.message}")
    if e.code == 'MARKET_NOT_FOUND':
        # Handle market not found
        pass
    elif e.code == 'INVALID_PARAMETERS':
        # Handle invalid parameters
        print(f"Invalid field: {e.details.get('field')}")

except Exception as e:
    print(f"Unexpected error: {e}")
    # Log error for debugging
```

## Rate Limiting

### Rate Limits

| Endpoint Type         | Limit | Window         |
| --------------------- | ----- | -------------- |
| Weather data          | 1000  | per hour       |
| Market data           | 2000  | per hour       |
| Trading operations    | 100   | per hour       |
| Backtesting           | 50    | per hour       |
| WebSocket connections | 10    | per connection |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 3600
```

### Backend Rate Limiting Middleware

```python
# middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import os

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", max_requests))
        self.window_seconds = int(os.getenv("RATE_LIMIT_WINDOW", window_seconds))
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response
```

## SDKs and Libraries

### Official SDKs

#### Python SDK

```bash
pip install climatetrade-python
```

```python
from climatetrade import ClimaTrade

# Initialize
ct = ClimaTrade(api_key='your_key')

# Use high-level methods
weather = ct.weather.get('London,UK')
markets = ct.markets.search('temperature London')
backtest = ct.backtesting.run(strategy='temperature', markets=markets)
```

#### JavaScript SDK

```bash
npm install climatetrade-js
```

```javascript
import { ClimaTrade } from 'climatetrade-js';

const ct = new ClimaTrade({ apiKey: 'your_key' });

// Async/await usage
const weather = await ct.weather.get('London,UK');
const markets = await ct.markets.search('temperature London');
```

## Data Validation

### Data Validation with Pydantic

```python
# models.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime

class WeatherDataRequest(BaseModel):
    location: Optional[str] = Field(None, max_length=50)
    hours: int = Field(24, ge=1, le=168)  # 1 hour to 1 week

    @validator('location')
    def validate_location(cls, v):
        if v and not v.replace(' ', '').replace(',', '').replace('-', '').isalnum():
            raise ValueError('Location contains invalid characters')
        return v

class WeatherDataResponse(BaseModel):
    timestamp: str
    location: str
    source: str
    temperature: Optional[float]
    humidity: Optional[float]
    precipitation: Optional[float]
    wind_speed: Optional[float]
    description: Optional[str]

class MarketOverviewResponse(BaseModel):
    market_id: str
    question: str
    volume: float = Field(ge=0)
    liquidity: float = Field(ge=0)
    data_points: int = Field(ge=0)
    last_update: Optional[str]

class TradingDataResponse(BaseModel):
    date: str
    trades: int = Field(ge=0)
    volume: float = Field(ge=0)
    avg_price: float = Field(ge=0)
    total_pnl: float
```

## Development

### Database Seeding Scripts

#### Weather Data Seeder

```python
# scripts/seed_weather_data.py
import sqlite3
from datetime import datetime, timedelta
import random
import os

def seed_weather_data():
    """Seed weather data for testing and development"""

    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'climatetrade.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure weather_sources table has data
    cursor.execute("""
        INSERT OR IGNORE INTO weather_sources (id, source_name, description, api_key_required, active)
        VALUES (1, 'Open-Meteo', 'Free weather API', 0, 1)
    """)

    # Generate 24 hours of sample data
    base_time = datetime.now()
    locations = ['London,UK', 'New York,NY']

    for location in locations:
        for i in range(24):
            timestamp = base_time - timedelta(hours=23-i)

            # Generate realistic weather data
            temp_base = 15 if 'London' in location else 25
            temperature = temp_base + random.uniform(-5, 5)
            humidity = random.uniform(40, 80)
            precipitation = random.uniform(0, 1) if random.random() < 0.3 else 0
            wind_speed = random.uniform(0, 15)

            descriptions = ['Clear sky', 'Partly cloudy', 'Cloudy', 'Light rain', 'Overcast']
            description = random.choice(descriptions)

            cursor.execute("""
                INSERT INTO weather_data
                (timestamp, location_name, source_id, temperature, humidity,
                 precipitation, wind_speed, weather_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.isoformat(),
                location,
                1,
                round(temperature, 1),
                round(humidity, 1),
                round(precipitation, 2),
                round(wind_speed, 1),
                description
            ))

    conn.commit()
    conn.close()
    print(f"Seeded weather data for {len(locations)} locations with 24 hours each")

if __name__ == "__main__":
    seed_weather_data()
```

#### Market Data Seeder

```python
# scripts/seed_market_data.py
import sqlite3
from datetime import datetime, timedelta
import random
import os

def seed_market_data():
    """Seed market data for testing"""

    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'climatetrade.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Sample market questions
    markets = [
        {
            'id': 'will-it-rain-london-2025',
            'question': 'Will it rain in London on September 10, 2025?',
            'volume': 125000,
            'liquidity': 45000
        },
        {
            'id': 'temp-above-20-london-sept',
            'question': 'Will London temperature exceed 20°C on September 15, 2025?',
            'volume': 89000,
            'liquidity': 32000
        }
    ]

    for market in markets:
        # Insert market
        cursor.execute("""
            INSERT OR REPLACE INTO polymarket_markets
            (market_id, question, volume, liquidity)
            VALUES (?, ?, ?, ?)
        """, (market['id'], market['question'], market['volume'], market['liquidity']))

        # Generate time series data
        base_time = datetime.now()
        for i in range(24):
            timestamp = base_time - timedelta(hours=23-i)

            # Simulate probability changes
            base_prob = 0.5 + random.uniform(-0.2, 0.2)
            probability = max(0.01, min(0.99, base_prob))
            volume = random.uniform(100, 1000)

            cursor.execute("""
                INSERT INTO polymarket_data
                (market_id, timestamp, outcome_name, probability, volume)
                VALUES (?, ?, ?, ?, ?)
            """, (
                market['id'],
                timestamp.isoformat(),
                'Yes',
                probability,
                volume
            ))

            cursor.execute("""
                INSERT INTO polymarket_data
                (market_id, timestamp, outcome_name, probability, volume)
                VALUES (?, ?, ?, ?, ?)
            """, (
                market['id'],
                timestamp.isoformat(),
                'No',
                1 - probability,
                volume
            ))

    conn.commit()
    conn.close()
    print(f"Seeded market data for {len(markets)} markets")

if __name__ == "__main__":
    seed_market_data()
```

---

**API Documentation Version**: 2.0
**Last Updated**: September 2025
**Contact**: api@climatetrade.ai
