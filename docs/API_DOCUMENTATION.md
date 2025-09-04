# ClimaTrade AI - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
4. [WebSocket API](#websocket-api)
5. [Python API Reference](#python-api-reference)
6. [Integration Examples](#integration-examples)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [SDKs and Libraries](#sdks-and-libraries)

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

**Response:**

```json
{
  "success": true,
  "data": {
    "location": "London, UK",
    "forecast": [
      {
        "date": "2024-01-02",
        "temperature_max": 22.0,
        "temperature_min": 15.0,
        "precipitation": 2.5,
        "weather_code": 500,
        "weather_description": "Light rain"
      }
    ],
    "hourly": [
      {
        "timestamp": "2024-01-02T00:00:00Z",
        "temperature": 18.0,
        "precipitation": 0.0,
        "weather_code": 800
      }
    ]
  }
}
```

#### Get Historical Weather

```http
GET /api/v1/weather/{location}/history
```

**Parameters:**

- `location` (path): Location identifier
- `start_date` (query): Start date (YYYY-MM-DD)
- `end_date` (query): End date (YYYY-MM-DD)
- `frequency` (query, optional): "hourly" or "daily" (default: "daily")

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

#### Get Order Book

```http
GET /api/v1/markets/{market_id}/orderbook
```

**Response:**

```json
{
  "success": true,
  "data": {
    "market_id": "0x123...",
    "bids": [
      { "price": 0.6, "size": 1000, "outcome": "Yes" },
      { "price": 0.55, "size": 2000, "outcome": "Yes" }
    ],
    "asks": [
      { "price": 0.45, "size": 1500, "outcome": "No" },
      { "price": 0.5, "size": 800, "outcome": "No" }
    ],
    "spread": 0.15,
    "mid_price": 0.525
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

**Response:**

```json
{
  "success": true,
  "data": {
    "order_id": "order_123456",
    "status": "pending",
    "market_id": "0x123...",
    "outcome": "Yes",
    "side": "buy",
    "price": 0.6,
    "size": 1000,
    "filled_size": 0,
    "remaining_size": 1000,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Trading and Strategy Endpoints

#### Get Portfolio

```http
GET /api/v1/portfolio
Authorization: Bearer your_token
```

**Response:**

```json
{
  "success": true,
  "data": {
    "total_value": 10500.0,
    "cash_balance": 2500.0,
    "positions": [
      {
        "market_id": "0x123...",
        "outcome": "Yes",
        "quantity": 1000,
        "average_price": 0.55,
        "current_price": 0.6,
        "unrealized_pnl": 50.0,
        "realized_pnl": 0.0
      }
    ],
    "performance": {
      "total_return": 0.05,
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.02
    }
  }
}
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

**Response:**

```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "running",
    "progress": 0.0,
    "estimated_completion": "2024-01-01T12:30:00Z"
  }
}
```

#### Get Backtest Results

```http
GET /api/v1/backtest/{backtest_id}/results
```

**Response:**

```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "completed",
    "results": {
      "total_return": 0.125,
      "annualized_return": 0.15,
      "sharpe_ratio": 1.8,
      "max_drawdown": 0.08,
      "win_rate": 0.62,
      "total_trades": 45,
      "equity_curve": [
        { "date": "2024-01-01", "value": 10000.0 },
        { "date": "2024-12-31", "value": 11250.0 }
      ]
    }
  }
}
```

### System Management Endpoints

#### Health Check

```http
GET /api/v1/health
```

**Response:**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "services": {
      "database": "ok",
      "redis": "ok",
      "weather_apis": "ok",
      "polymarket_api": "ok",
      "backtesting_engine": "ok"
    },
    "uptime": "7d 4h 23m",
    "version": "1.2.3"
  }
}
```

#### System Metrics

```http
GET /api/v1/metrics
```

**Response:**

```json
{
  "success": true,
  "data": {
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 62.8,
      "disk_usage": 34.1
    },
    "application": {
      "active_connections": 23,
      "requests_per_second": 12.5,
      "average_response_time": 245
    },
    "trading": {
      "active_positions": 8,
      "pending_orders": 3,
      "daily_volume": 125000
    }
  }
}
```

#### Configuration

```http
GET /api/v1/config
Authorization: Bearer admin_token
```

**Response:**

```json
{
  "success": true,
  "data": {
    "environment": "production",
    "database_url": "postgresql://...",
    "api_rate_limit": 1000,
    "features": {
      "real_trading_enabled": true,
      "backtesting_enabled": true,
      "auto_scaling_enabled": true
    }
  }
}
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

### WebSocket Message Types

#### Client Messages

```javascript
// Authentication
{
  "type": "auth",
  "token": "jwt_token_here"
}

// Subscription
{
  "type": "subscribe",
  "channel": "market|weather|trading",
  "market_id": "optional_market_id",
  "location": "optional_location"
}

// Unsubscription
{
  "type": "unsubscribe",
  "channel": "market|weather|trading",
  "market_id": "optional_market_id"
}

// Ping
{
  "type": "ping"
}
```

#### Server Messages

```javascript
// Authentication response
{
  "type": "auth_success",
  "user_id": "user_123"
}

// Market update
{
  "type": "market_update",
  "market_id": "0x123...",
  "probabilities": [0.65, 0.35],
  "volume": 125000,
  "timestamp": "2024-01-01T12:00:00Z"
}

// Weather update
{
  "type": "weather_update",
  "location": "London,UK",
  "temperature": 18.5,
  "humidity": 72,
  "timestamp": "2024-01-01T12:00:00Z"
}

// Order update
{
  "type": "order_update",
  "order_id": "order_123",
  "status": "filled|partial|canceled",
  "filled_size": 1000,
  "remaining_size": 0
}

// Error
{
  "type": "error",
  "code": "INVALID_TOKEN",
  "message": "Authentication token is invalid"
}

// Pong
{
  "type": "pong",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Python API Reference

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

### Data Models

#### WeatherData

```python
@dataclass
class WeatherData:
    location_name: str
    coordinates: Coordinates
    temperature: float
    feels_like: Optional[float]
    humidity: int
    pressure: int
    wind_speed: float
    wind_direction: Optional[int]
    precipitation: Optional[float]
    weather_code: int
    weather_description: str
    visibility: Optional[int]
    uv_index: Optional[float]
    timestamp: datetime
    source: str
    data_quality_score: float
```

#### MarketData

```python
@dataclass
class MarketData:
    market_id: str
    event_title: str
    question: str
    outcomes: List[str]
    probabilities: List[float]
    volume: float
    liquidity: float
    end_date: datetime
    active: bool
    closed: bool
    archived: bool
```

#### OrderData

```python
@dataclass
class OrderData:
    order_id: str
    market_id: str
    outcome: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    price: Optional[float]
    size: float
    filled_size: float
    remaining_size: float
    status: str
    timestamp: datetime
```

#### BacktestResult

```python
@dataclass
class BacktestResult:
    backtest_id: str
    strategy_name: str
    start_date: date
    end_date: date
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    equity_curve: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    execution_time_seconds: float
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

#### Backtesting Integration

```python
from climatetrade.backtesting import BacktestingClient
import matplotlib.pyplot as plt

def run_strategy_comparison():
    client = BacktestingClient(api_key='your_api_key')

    # Define strategies to compare
    strategies = ['temperature_threshold', 'precipitation', 'wind_speed']
    market_ids = ['0x123...', '0x456...', '0x789...']
    locations = ['London,UK', 'New York,NY', 'Tokyo,JP']

    # Run backtests for all strategies
    results = []
    for strategy in strategies:
        result = client.run_backtest(
            strategy_name=strategy,
            market_ids=market_ids,
            locations=locations,
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=10000.0
        )
        results.append(result)

    # Compare results
    comparison = client.compare_strategies(
        strategy_names=strategies,
        market_ids=market_ids,
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    # Plot equity curves
    plt.figure(figsize=(12, 8))
    for result in results:
        plt.plot(result.equity_curve_dates, result.equity_curve_values,
                label=result.strategy_name)

    plt.title('Strategy Comparison - Equity Curves')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.show()

    # Print performance summary
    print("Performance Summary:")
    print("-" * 50)
    for result in results:
        print(f"{result.strategy_name}:")
        print(".2%"        print(".2f"        print(".2%"        print()
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

### Trading Algorithm Example

```python
from climatetrade.client import ClimaTradeClient
from climatetrade.weather import WeatherDataClient
import time

class WeatherArbitrageBot:
    def __init__(self, api_key, jwt_token):
        self.client = ClimaTradeClient(api_key=api_key, jwt_token=jwt_token)
        self.weather_client = WeatherDataClient(api_key=api_key)

        # Trading parameters
        self.max_position_size = 0.1  # 10% of portfolio
        self.min_probability_edge = 0.05  # 5% edge required
        self.max_spread = 0.1  # Maximum acceptable spread

    def identify_arbitrage_opportunities(self):
        """Find markets where weather data suggests mispriced probabilities"""
        opportunities = []

        # Get active weather-related markets
        markets = self.client.get_markets(
            query='weather temperature',
            active=True,
            limit=50
        )

        for market in markets:
            # Extract location from market question
            location = self.extract_location_from_question(market.question)
            if not location:
                continue

            # Get current weather
            weather = self.weather_client.get_current_weather(location)

            # Get market data
            orderbook = self.client.get_orderbook(market.market_id)

            # Analyze for arbitrage opportunity
            opportunity = self.analyze_market_weather_arbitrage(
                market, weather, orderbook
            )

            if opportunity:
                opportunities.append(opportunity)

        return opportunities

    def analyze_market_weather_arbitrage(self, market, weather, orderbook):
        """Analyze if there's an arbitrage opportunity"""
        # This is a simplified example - implement your actual logic

        # Example: Market about "Will temperature exceed 25°C?"
        if 'temperature' in market.question.lower() and '25' in market.question:
            # Current temperature suggests outcome
            predicted_outcome = 'Yes' if weather.temperature > 25 else 'No'

            # Check if market probability is mispriced
            current_prob = market.probabilities[0]  # Assuming Yes is first outcome
            fair_prob = 0.7 if predicted_outcome == 'Yes' else 0.3

            if abs(current_prob - fair_prob) > self.min_probability_edge:
                return {
                    'market_id': market.market_id,
                    'predicted_outcome': predicted_outcome,
                    'current_probability': current_prob,
                    'fair_probability': fair_prob,
                    'edge': abs(current_prob - fair_prob),
                    'recommended_action': 'buy' if current_prob < fair_prob else 'sell'
                }

        return None

    def execute_arbitrage_trade(self, opportunity):
        """Execute the arbitrage trade"""
        market_id = opportunity['market_id']
        outcome = opportunity['predicted_outcome']
        action = opportunity['recommended_action']

        # Calculate position size
        portfolio = self.client.get_portfolio()
        position_size = min(
            self.max_position_size * portfolio.total_value,
            1000  # Maximum trade size
        )

        # Get orderbook for pricing
        orderbook = self.client.get_orderbook(market_id)

        # Place order
        if action == 'buy':
            price = orderbook.asks[0].price
            side = 'buy'
        else:
            price = orderbook.bids[0].price
            side = 'sell'

        order = self.client.place_order(
            market_id=market_id,
            outcome=outcome,
            side=side,
            price=price,
            size=position_size
        )

        return order

    def run(self):
        """Main bot loop"""
        while True:
            try:
                # Find arbitrage opportunities
                opportunities = self.identify_arbitrage_opportunities()

                # Execute trades for best opportunities
                for opportunity in opportunities[:3]:  # Top 3 opportunities
                    if opportunity['edge'] > self.min_probability_edge:
                        order = self.execute_arbitrage_trade(opportunity)
                        print(f"Executed arbitrage trade: {order.order_id}")

                # Wait before next iteration
                time.sleep(300)  # 5 minutes

            except Exception as e:
                print(f"Error in bot loop: {e}")
                time.sleep(60)  # Wait 1 minute on error

# Usage
bot = WeatherArbitrageBot(api_key='your_key', jwt_token='your_token')
bot.run()
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

### Common Error Codes

| Error Code                 | Description                | Resolution                    |
| -------------------------- | -------------------------- | ----------------------------- |
| `INVALID_API_KEY`          | API key is invalid         | Check your API key            |
| `RATE_LIMIT_EXCEEDED`      | Too many requests          | Wait and retry                |
| `INVALID_PARAMETERS`       | Request parameters invalid | Check parameter format        |
| `MARKET_NOT_FOUND`         | Market does not exist      | Verify market ID              |
| `INSUFFICIENT_BALANCE`     | Not enough funds           | Check account balance         |
| `ORDER_REJECTED`           | Order rejected by exchange | Check order parameters        |
| `WEATHER_DATA_UNAVAILABLE` | Weather data not available | Try different location/source |
| `SERVICE_UNAVAILABLE`      | Service temporarily down   | Retry later                   |

### Error Handling Examples

#### Python Error Handling

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

#### JavaScript Error Handling

```javascript
async function safeApiCall() {
  try {
    const weather = await climaTrade.getWeather('London,UK');
    console.log(`Temperature: ${weather.current.temperature}°C`);
  } catch (error) {
    if (error.code === 'RATE_LIMIT_EXCEEDED') {
      console.log(`Rate limited. Retry after ${error.retry_after} seconds`);
      setTimeout(() => safeApiCall(), error.retry_after * 1000);
    } else if (error.code === 'INVALID_API_KEY') {
      console.error('Invalid API key');
      // Prompt user to update API key
    } else if (error.code === 'WEATHER_DATA_UNAVAILABLE') {
      console.log('Weather data unavailable, trying backup source');
      // Try alternative weather source
    } else {
      console.error(`API error: ${error.code} - ${error.message}`);
    }
  }
}
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

### Handling Rate Limits

```python
import time
from climatetrade.exceptions import RateLimitError

def handle_rate_limit(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                print(f"Rate limited. Waiting {e.retry_after} seconds")
                time.sleep(e.retry_after)
    return wrapper

@handle_rate_limit
def get_weather_data(location):
    return client.get_weather(location)
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

#### Go SDK

```bash
go get github.com/climatetrade/climatetrade-go
```

```go
package main

import (
    "fmt"
    "github.com/climatetrade/climatetrade-go"
)

func main() {
    client := climatetrade.NewClient("your_api_key")

    weather, err := client.Weather.Get("London,UK")
    if err != nil {
        panic(err)
    }

    fmt.Printf("Temperature: %.1f°C\n", weather.Current.Temperature)
}
```

### Community Libraries

- **R Package**: `install.packages("climatetrade")`
- **Java Library**: Maven dependency available
- **C# SDK**: NuGet package available
- **Rust Crate**: `cargo add climatetrade`

### Third-party Integrations

- **TradingView**: Pine Script integration
- **MetaTrader**: MQL5 integration
- **Excel**: Add-in for spreadsheet integration
- **Google Sheets**: Custom functions

---

**API Documentation Version**: 1.0
**Last Updated**: January 2024
**Contact**: api@climatetrade.ai

For additional support, visit our [Developer Portal](https://developers.climatetrade.ai) or join our [Developer Community](https://community.climatetrade.ai).
