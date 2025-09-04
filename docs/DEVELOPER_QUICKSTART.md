# ClimaTrade AI Developer Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get you up and running with ClimaTrade AI development in under 5 minutes.

### Prerequisites

- **Python 3.9+** installed
- **Git** for version control
- **Docker** (optional, for containerized development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd climatetrade

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings (minimal for development)
nano .env
```

**Minimal .env for development:**

```bash
# Environment
CLIMATRADE_ENV=development
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite:///data/climatetrade.db

# Basic API keys (use test keys)
OPENAI_API_KEY=your-test-key-here
```

### 3. Initialize Database

```bash
# Navigate to database directory
cd database

# Setup database
python setup_database.py

# Run migrations
python migrations/migration_manager.py apply
```

### 4. Start Development Server

```bash
# Start the main API server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the development script
./scripts/dev-start.sh
```

### 5. Verify Installation

```bash
# Test API endpoint
curl http://localhost:8000/health

# Should return: {"status": "healthy", "services": {...}}
```

**🎉 You're ready to develop!**

---

## 🛠️ Development Workflows

### Adding a New Feature

#### 1. Create Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... development work ...

# Commit changes
git add .
git commit -m "Add: your feature description"
```

#### 2. Run Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_your_feature.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

#### 3. Code Quality Checks

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

#### 4. Submit Pull Request

```bash
# Push branch
git push origin feature/your-feature-name

# Create PR on GitHub/GitLab
# Add description and link to issue
```

### Working with the Database

#### Schema Changes

```bash
# Create new migration
cd database
python migrations/migration_manager.py create --name add_new_table --description "Add new feature table"

# Edit the generated migration file
nano migrations/YYYYMMDD_HHMMSS_add_new_table.py

# Apply migration
python migrations/migration_manager.py apply
```

#### Database Queries

```python
# Using SQLAlchemy
from database.connection import get_db

def get_weather_data(location: str, limit: int = 100):
    with get_db() as db:
        result = db.execute("""
            SELECT * FROM weather_data
            WHERE location_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (location, limit))

        return result.fetchall()
```

### API Development

#### Creating New Endpoints

```python
# In api/routes/weather.py
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/weather/{location}")
async def get_weather(location: str, days: int = 7):
    """Get weather data for a location"""
    try:
        data = await weather_service.get_forecast(location, days)
        return {"location": location, "forecast": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/weather")
async def create_weather_reading(reading: WeatherReading):
    """Create new weather reading"""
    try:
        result = await weather_service.save_reading(reading)
        return {"id": result.id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Testing API Endpoints

```python
# tests/test_weather_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_weather():
    response = client.get("/api/weather/London")
    assert response.status_code == 200
    data = response.json()
    assert "location" in data
    assert "forecast" in data

def test_create_weather_reading():
    reading = {
        "location": "London",
        "temperature": 20.5,
        "humidity": 65
    }
    response = client.post("/api/weather", json=reading)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
```

### Data Pipeline Development

#### Adding New Data Source

```python
# data_pipeline/sources/new_source.py
from data_pipeline.core import DataSource
from typing import Dict, Any, List
import requests

class NewWeatherSource(DataSource):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.new-weather.com/v1"

    async def fetch_data(self, location: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch weather data from new source"""
        params = {
            "location": location,
            "apikey": self.api_key,
            **kwargs
        }

        response = requests.get(f"{self.base_url}/weather", params=params)
        response.raise_for_status()

        data = response.json()

        # Transform to standard format
        return self._transform_data(data)

    def _transform_data(self, raw_data: Dict) -> List[Dict[str, Any]]:
        """Transform raw data to standard format"""
        return [{
            "location_name": raw_data["location"],
            "temperature": raw_data["temp"],
            "humidity": raw_data["humidity"],
            "timestamp": raw_data["timestamp"],
            "source": "new_weather_api"
        }]
```

#### Testing Data Pipeline

```python
# tests/test_data_pipeline.py
import pytest
from data_pipeline.sources.new_source import NewWeatherSource
from unittest.mock import Mock, patch

@pytest.fixture
def weather_source():
    return NewWeatherSource(api_key="test-key")

@patch('requests.get')
def test_fetch_data_success(mock_get, weather_source):
    # Mock successful API response
    mock_response = Mock()
    mock_response.json.return_value = {
        "location": "London",
        "temp": 20.5,
        "humidity": 65,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    mock_get.return_value = mock_response

    result = weather_source.fetch_data("London")

    assert len(result) == 1
    assert result[0]["location_name"] == "London"
    assert result[0]["temperature"] == 20.5

@patch('requests.get')
def test_fetch_data_api_error(mock_get, weather_source):
    # Mock API error
    mock_get.side_effect = requests.exceptions.RequestException("API Error")

    with pytest.raises(requests.exceptions.RequestException):
        weather_source.fetch_data("London")
```

### Backtesting Framework

#### Creating New Strategy

```python
# backtesting_framework/strategies/my_strategy.py
from backtesting_framework.strategies.base_strategy import BaseWeatherStrategy
from backtesting_framework.core.trading_signal import TradingSignal, SignalType
from typing import List, Dict, Any

class MyWeatherStrategy(BaseWeatherStrategy):
    def __init__(self, name: str = "MyStrategy", parameters: Dict[str, Any] = None):
        super().__init__(name, parameters or {})
        self.temp_threshold = self.parameters.get('temp_threshold', 25.0)

    def generate_signals(self, market_data: List[Dict], weather_data: List[Dict],
                        current_positions: Dict) -> List[TradingSignal]:
        """Generate trading signals based on weather and market data"""
        signals = []

        for market in market_data:
            # Find corresponding weather data
            weather = self._find_weather_for_market(weather_data, market)

            if weather and weather['temperature'] > self.temp_threshold:
                # Generate buy signal for hot weather
                signal = TradingSignal(
                    market_id=market['market_id'],
                    signal_type=SignalType.BUY,
                    strength=0.8,
                    reason=f"Temperature {weather['temperature']}°C above threshold",
                    metadata={
                        'temperature': weather['temperature'],
                        'threshold': self.temp_threshold
                    }
                )
                signals.append(signal)

        return signals

    def _find_weather_for_market(self, weather_data: List[Dict], market: Dict) -> Dict:
        """Find weather data for market location"""
        # Implementation to match weather data to market
        pass
```

#### Running Backtests

```python
# Run backtest from code
from backtesting_framework.main import run_single_strategy_backtest

result = run_single_strategy_backtest(
    strategy_name='my_strategy',
    market_ids=['temp_market_1', 'temp_market_2'],
    locations=['London, UK', 'New York City, NY'],
    start_date='2024-01-01',
    end_date='2024-12-31'
)

print(f"Strategy Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Win Rate: {result.win_rate:.2%}")
```

### Agent Development

#### Creating Trading Agent

```python
# agents/my_agent.py
from agents.application.base_agent import BaseTradingAgent
from agents.connectors.polymarket import PolymarketClient
from typing import Dict, Any

class MyWeatherAgent(BaseTradingAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.polymarket = PolymarketClient(
            api_key=config['polymarket_api_key'],
            private_key=config['polygon_private_key']
        )

    async def analyze_market(self, market_data: Dict) -> Dict[str, Any]:
        """Analyze market conditions"""
        # Get weather data
        weather = await self.get_weather_data(market_data['location'])

        # Analyze market
        analysis = {
            'market_id': market_data['market_id'],
            'weather_impact': self._calculate_weather_impact(weather),
            'confidence': self._calculate_confidence(weather, market_data),
            'recommended_action': self._get_recommended_action(weather)
        }

        return analysis

    async def execute_trade(self, analysis: Dict) -> bool:
        """Execute trade based on analysis"""
        if analysis['recommended_action'] == 'BUY':
            return await self.polymarket.place_buy_order(
                market_id=analysis['market_id'],
                amount=self.config['trade_amount'],
                price=self._calculate_optimal_price(analysis)
            )
        elif analysis['recommended_action'] == 'SELL':
            return await self.polymarket.place_sell_order(
                market_id=analysis['market_id'],
                amount=self.config['trade_amount'],
                price=self._calculate_optimal_price(analysis)
            )

        return False

    def _calculate_weather_impact(self, weather: Dict) -> float:
        """Calculate weather impact score"""
        # Implementation
        pass

    def _calculate_confidence(self, weather: Dict, market: Dict) -> float:
        """Calculate confidence score"""
        # Implementation
        pass

    def _get_recommended_action(self, weather: Dict) -> str:
        """Get recommended trading action"""
        # Implementation
        pass
```

### Docker Development

#### Development with Docker

```bash
# Build development image
docker build -f docker/dev.Dockerfile -t climatetrade/dev .

# Run with hot reload
docker run -v $(pwd):/app -p 8000:8000 climatetrade/dev

# Or use docker-compose for full stack
docker-compose -f docker-compose.dev.yml up
```

#### Development Dockerfile

```dockerfile
# docker/dev.Dockerfile
FROM python:3.9-slim

# Install development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Create development user
RUN useradd --create-home --shell /bin/bash dev
USER dev

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# Copy source code
COPY . .

# Development command
CMD ["python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

### Testing Best Practices

#### Unit Testing

```python
# tests/test_my_feature.py
import pytest
from my_feature import MyFeature

class TestMyFeature:
    @pytest.fixture
    def feature(self):
        return MyFeature()

    def test_initialization(self, feature):
        assert feature is not None
        assert feature.config is not None

    def test_process_data(self, feature):
        input_data = {"temperature": 25.0, "humidity": 60}
        result = feature.process_data(input_data)

        assert "processed" in result
        assert result["processed"] is True

    @pytest.mark.parametrize("temperature,humidity,expected", [
        (20, 50, "cool"),
        (30, 70, "hot"),
        (25, 60, "moderate")
    ])
    def test_temperature_classification(self, feature, temperature, humidity, expected):
        result = feature.classify_temperature(temperature, humidity)
        assert result == expected
```

#### Integration Testing

```python
# tests/integration/test_full_pipeline.py
import pytest
from data_pipeline.main import DataPipeline
from database.connection import get_db

@pytest.mark.integration
class TestFullPipeline:
    def test_data_ingestion_to_database(self):
        """Test complete data flow from API to database"""
        # Setup
        pipeline = DataPipeline()

        # Ingest data
        result = pipeline.ingest_weather_data("London")

        # Verify in database
        with get_db() as db:
            count = db.execute("""
                SELECT COUNT(*) FROM weather_data
                WHERE location_name = ?
                AND timestamp >= datetime('now', '-1 hour')
            """, ("London",)).fetchone()[0]

            assert count > 0

    def test_backtesting_integration(self):
        """Test backtesting with real data"""
        from backtesting_framework.main import run_single_strategy_backtest

        result = run_single_strategy_backtest(
            strategy_name='temperature',
            market_ids=['test_market'],
            locations=['London, UK']
        )

        assert result is not None
        assert hasattr(result, 'total_return')
        assert hasattr(result, 'sharpe_ratio')
```

### Debugging Tips

#### Common Debug Commands

```bash
# Check running processes
ps aux | grep python

# View application logs
tail -f logs/climatetrade.log

# Check database connections
psql -c "SELECT * FROM pg_stat_activity;"

# Monitor memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Debug API calls
curl -v http://localhost:8000/api/weather/London
```

#### Debug Configuration

```python
# debug_config.py
import logging
import sys

def setup_debug_logging():
    """Setup detailed logging for debugging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug.log')
        ]
    )

    # Enable SQL query logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    # Enable HTTP request logging
    logging.getLogger('urllib3').setLevel(logging.DEBUG)

if __name__ == "__main__":
    setup_debug_logging()
    print("Debug logging enabled")
```

### Performance Profiling

#### Code Profiling

```python
# profiling/profile_code.py
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator to profile function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions

        return result
    return wrapper

@profile_function
def slow_function():
    """Example function to profile"""
    # Your code here
    pass

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    """Function to profile memory usage"""
    # Your code here
    pass
```

### Contributing Guidelines

#### Code Style

```python
# Follow PEP 8
# Use type hints
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process weather data with proper typing"""
    pass

# Use descriptive variable names
weather_temperature_celsius = 25.0  # Good
temp = 25.0  # Bad

# Write docstrings
def calculate_impact(temperature: float, humidity: float) -> float:
    """
    Calculate weather impact on trading decisions.

    Args:
        temperature: Temperature in Celsius
        humidity: Humidity percentage (0-100)

    Returns:
        Impact score between 0 and 1
    """
    pass
```

#### Git Workflow

```bash
# Always work on feature branches
git checkout -b feature/add-weather-analysis

# Write clear commit messages
git commit -m "feat: add weather impact analysis function

- Add calculate_weather_impact() function
- Include temperature and humidity factors
- Return normalized impact score
- Add unit tests"

# Keep commits focused and atomic
# One feature per commit when possible
```

### Getting Help

#### Documentation Resources

- **API Documentation**: `http://localhost:8000/docs` (when running)
- **Code Documentation**: `docs/` directory
- **Database Schema**: `database/schema.sql`
- **Configuration Guide**: `docs/ENVIRONMENT_CONFIGURATION.md`

#### Community Support

- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
- **Slack**: Development chat for real-time help
- **Wiki**: Project wiki for detailed guides

#### Debug Checklist

When something isn't working:

1. **Check logs**: `tail -f logs/climatetrade.log`
2. **Verify configuration**: `python -c "import config; print(config)"`
3. **Test dependencies**: `python -c "import problematic_module"`
4. **Check database**: `psql -c "SELECT 1"`
5. **Verify API endpoints**: `curl http://localhost:8000/health`
6. **Check system resources**: `htop` or `top`
7. **Review recent changes**: `git log --oneline -10`

This quick start guide should get you productive quickly while providing the foundation for deeper development work.
