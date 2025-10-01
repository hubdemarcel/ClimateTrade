# ClimaTrade AI Setup & Development Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5-10 minutes)](#quick-start-5-10-minutes)
3. [Detailed Setup Instructions](#detailed-setup-instructions)
4. [Environment Configuration](#environment-configuration)
5. [Development Workflows](#development-workflows)
6. [Troubleshooting](#troubleshooting)
7. [Testing & Verification](#testing--verification)
8. [Production Deployment](#production-deployment)

## Prerequisites

### System Requirements

#### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Processor**: Intel/AMD x64 processor with 4 cores
- **Memory**: 8GB RAM
- **Storage**: 50GB free disk space
- **Network**: Stable internet connection (10Mbps minimum)

#### Recommended Requirements

- **Operating System**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Processor**: Intel/AMD x64 processor with 8+ cores
- **Memory**: 16GB RAM or more
- **Storage**: 100GB+ SSD storage
- **Network**: High-speed internet (100Mbps+)

### Software Dependencies

#### Required Software

- **Python**: Version 3.9 or higher
- **Git**: Version control system
- **SQLite**: Database (comes with Python)
- **Docker**: Containerization platform (optional but recommended)
- **Node.js**: Version 16+ (for subgraph development)

#### Python Packages

```bash
# Core dependencies
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv requests websockets

# Data processing
pip install pandas numpy scipy matplotlib seaborn plotly

# Machine learning
pip install scikit-learn tensorflow torch

# Testing and development
pip install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit

# Additional utilities
pip install typer rich pytz timezonefinder eth-account python-multipart
```

## Quick Start (5-10 minutes)

### Prerequisites Check

- **Python 3.9+** installed
- **Git** for version control
- **Docker** (optional, for containerized development)

### Step 1: Clone and Setup

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

### Step 2: Configure Environment

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

### Step 3: Initialize Database

```bash
# Navigate to database directory
cd database

# Setup database
python setup_database.py

# Run migrations
python migrations/migration_manager.py apply
```

### Step 4: Start Development Server

```bash
# Start the main API server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Or use the development script
./src/scripts/dev-start.sh
```

### Step 5: Verify Installation

```bash
# Test API endpoint
curl http://localhost:8000/health

# Should return: {"status": "healthy", "services": {...}}
```

**🎉 You're ready to develop!**

## Detailed Setup Instructions

### Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd climatetrade

# Verify the structure
ls -la
# Should see: data/, scripts/, database/, docs/, etc.
```

### Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify Python version
python --version
# Should be 3.9 or higher

# Upgrade pip
pip install --upgrade pip
```

### Install Core Dependencies

```bash
# Install core requirements
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Install component-specific dependencies
pip install -r src/backtesting/requirements.txt
pip install -r src/data_pipeline/requirements.txt
```

### External Service Setup

#### Weather API Setup

```bash
# Met Office API (requires API key)
# Sign up at: https://www.metoffice.gov.uk/services/data/met-office-weather-datahub
# Add to .env: MET_OFFICE_API_KEY=your_api_key_here

# Meteostat API (requires API key)
# Sign up at: https://dev.meteostat.net/
# Add to .env: METEOSTAT_API_KEY=your_api_key_here

# Open-Meteo API (free, no API key required)
# No setup required - ready to use immediately
# python src/scripts/open_meteo_client.py --location "London,UK" --current

# Weather2Geo (optional)
cd src/scripts/Weather2Geo
pip install -r requirements.txt
```

#### Polymarket Setup

```bash
# Install Polymarket client
pip install -e src/scripts/polymarket-client/

# Setup wallet (for trading)
# Create a wallet on Polygon network
# Add to .env:
# POLYGON_WALLET_PRIVATE_KEY=your_private_key
# CLOB_API_KEY=your_api_key (optional)
# CLOB_SECRET=your_secret (optional)
```

#### Resolution Subgraph Setup

```bash
# Install dependencies
pip install -r src/scripts/requirements-resolution.txt

# For local development:
cd src/scripts/resolution-subgraph
npm install
npm run codegen
```

## Environment Configuration

### Development Environment

Create a `.env.development` file:

```bash
# Environment Settings
CLIMATRADE_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database Configuration
DATABASE_URL=sqlite:///data/climatetrade.db
DATABASE_DEBUG=true

# API Configuration
WEATHER_API_TIMEOUT=30
POLYMARKET_API_TIMEOUT=30
MAX_API_RETRIES=3

# Weather APIs
MET_OFFICE_API_KEY=your_met_office_key
METEOSTAT_API_KEY=your_meteostat_key
NWS_API_BASE_URL=https://api.weather.gov

# Polymarket Configuration
POLYGON_RPC_URL=https://polygon-rpc.com/
POLYGON_WALLET_PRIVATE_KEY=your_dev_private_key
CLOB_API_KEY=your_dev_api_key
CLOB_SECRET=your_dev_secret

# Resolution Subgraph
MATIC_RPC_URL=https://matic-mumbai.chainstacklabs.com

# Development Features
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_MOCK_APIS=true

# Logging
LOG_FILE=logs/development.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Testing
TEST_DATABASE_URL=sqlite:///data/test.db
ENABLE_COVERAGE=true
```

### Staging Environment

Create a `.env.staging` file:

```bash
# Environment Settings
CLIMATRADE_ENV=staging
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://climatetrade_staging:password@staging-db.climatetrade.internal:5432/climatetrade_staging
DATABASE_SSL_MODE=require
DATABASE_CONNECTION_POOL_SIZE=10

# Redis Configuration
REDIS_URL=redis://staging-redis.climatetrade.internal:6379/0
REDIS_PASSWORD=staging_redis_password

# API Configuration
WEATHER_API_TIMEOUT=60
POLYMARKET_API_TIMEOUT=60
MAX_API_RETRIES=5
API_RATE_LIMIT=1000

# Security
JWT_SECRET=staging_jwt_secret_key
API_KEY_SECRET=staging_api_key_secret
ENCRYPTION_KEY=staging_encryption_key

# Monitoring
PROMETHEUS_METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true

# External Services
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_KEY
MATIC_RPC_URL=https://polygon-mumbai.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
```

### Production Environment

Create a `.env.production` file:

```bash
# Environment Settings
CLIMATRADE_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# Database Configuration
DATABASE_URL=postgresql://climatetrade_prod:secure_password@prod-db-cluster.climatetrade.internal:5432/climatetrade_prod
DATABASE_SSL_MODE=verify-full
DATABASE_SSL_CERT=/etc/ssl/certs/climatetrade.crt
DATABASE_SSL_KEY=/etc/ssl/private/climatetrade.key
DATABASE_SSL_ROOT_CERT=/etc/ssl/certs/ca.crt
DATABASE_CONNECTION_POOL_SIZE=50
DATABASE_MAX_CONNECTIONS=100

# Redis Cluster
REDIS_URL=redis://prod-redis-cluster.climatetrade.internal:6379/0
REDIS_PASSWORD=production_redis_secure_password
REDIS_SSL=true

# API Configuration
WEATHER_API_TIMEOUT=120
POLYMARKET_API_TIMEOUT=120
MAX_API_RETRIES=10
API_RATE_LIMIT=10000
CIRCUIT_BREAKER_ENABLED=true

# Security Configuration
JWT_SECRET=production_jwt_secret_64_chars_minimum
API_KEY_SECRET=production_api_key_secret_32_chars
ENCRYPTION_KEY=production_encryption_key_32_chars
SSL_CERT_PATH=/etc/ssl/certs/climatetrade.crt
SSL_KEY_PATH=/etc/ssl/private/climatetrade.key

# External Services
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_KEY
MATIC_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ETHERSCAN_API_KEY=production_etherscan_api_key
COINGECKO_API_KEY=production_coingecko_api_key

# Monitoring and Alerting
PROMETHEUS_METRICS_ENABLED=true
GRAFANA_URL=https://monitoring.climatetrade.ai
ALERTMANAGER_URL=https://alerts.climatetrade.ai
LOGSTASH_HOST=logstash.climatetrade.internal
LOGSTASH_PORT=5044

# Load Balancing
LOAD_BALANCER_ENDPOINT=https://api.climatetrade.ai
HEALTH_CHECK_ENDPOINT=https://api.climatetrade.ai/health
METRICS_ENDPOINT=https://api.climatetrade.ai/metrics

# Feature Flags
ENABLE_REAL_TRADING=true
ENABLE_AUTO_SCALING=true
ENABLE_CIRCUIT_BREAKER=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true

# Performance Tuning
MAX_WORKERS=8
MEMORY_LIMIT=2GB
CPU_LIMIT=4
REQUEST_TIMEOUT=300
```

## Development Workflows

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
from src.database.connection import get_db

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
# In src/api/routes/weather.py
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
from src.main import app

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

## Troubleshooting

### Common Issues

#### Port Conflicts

**Problem**: Port 8080 or 8001 already in use

**Solution**:

```bash
# Check what's using the ports
lsof -i :8080
lsof -i :8001

# Kill process using port
kill -9 <PID>

# Or change ports in configuration
```

#### Database Connection Issues

**Problem**: Backend can't connect to database

**Solution**:

```bash
# Check database file exists
ls -la data/climatetrade.db

# Verify database integrity
cd database
python -c "import sqlite3; sqlite3.connect('../data/climatetrade.db').execute('PRAGMA integrity_check').fetchone()"

# Recreate database if corrupted
python setup_database.py
```

#### CORS Issues

**Problem**: Frontend can't communicate with backend

**Solution**:

- Verify backend is running on port 8001
- Check CORS configuration in `web/backend/main.py`
- Ensure frontend proxy is configured correctly in `web/frontend/vite.config.ts`

#### Module Import Errors

**Problem**: Python import errors

**Solution**:

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Verify virtual environment
which python
which pip
```

### Development Server Issues

#### Frontend Not Starting

```bash
# Clear node modules and reinstall
cd web/frontend
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version
npm --version
```

#### Backend Not Starting

```bash
# Check Python version
python --version

# Verify FastAPI installation
python -c "import fastapi; print('FastAPI OK')"

# Check port availability
netstat -tlnp | grep 8001
```

### Performance Issues

#### Slow Database Queries

```bash
# Enable query logging
export SQLALCHEMY_ECHO=true

# Check slow queries
python -c "
import sqlite3
conn = sqlite3.connect('data/climatetrade.db')
cursor = conn.cursor()
cursor.execute(\"\"\"
    SELECT name FROM sqlite_master
    WHERE type='table'
    AND name NOT LIKE 'sqlite_%'
\"\"\")
print('Tables:', [row[0] for row in cursor.fetchall()])
conn.close()
"
```

#### Memory Issues

```bash
# Monitor memory usage
python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'Available: {psutil.virtual_memory().available / 1024 / 1024:.0f} MB')
"
```

### Network Issues

```bash
# Test internet connectivity
ping 8.8.8.8

# Test API endpoints
curl https://api.weather.gov
curl https://clob.polymarket.com

# Check firewall settings
sudo ufw status
sudo ufw allow 8000
```

### API Key Issues

```bash
# Verify API keys in environment
echo $MET_OFFICE_API_KEY
echo $POLYMARKET_API_KEY

# Test API connectivity
curl -H "X-API-Key: $MET_OFFICE_API_KEY" https://api.metoffice.gov.uk/v1/test

# Check API key format
python scripts/validate_api_keys.py
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --verbose --debug

# Enable database query logging
export SQLALCHEMY_ECHO=True
```

## Testing & Verification

### Health Checks

```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "services": {"database": "ok", "redis": "ok", "apis": "ok"}}

# Test database connection
python -c "
import sqlite3
conn = sqlite3.connect('data/climatetrade.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM weather_sources')
print(f'Weather sources: {cursor.fetchone()[0]}')
conn.close()
"
```

### Component Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_database.py -v
pytest tests/test_weather_apis.py -v
pytest tests/test_polymarket_integration.py -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests
pytest tests/integration/ -v
```

### Data Pipeline Testing

```bash
# Test weather data collection
python scripts/test_weather_collection.py

# Test data validation
python data_pipeline/test_data_quality.py

# Test backtesting
python src/backtesting/main.py single --strategy temperature
```

### Performance Testing

```bash
# Load testing
ab -n 1000 -c 10 http://localhost:8000/api/weather/London

# Memory profiling
python -m memory_profiler scripts/profile_memory.py

# CPU profiling
python -m cProfile scripts/profile_cpu.py
```

## Production Deployment

### Docker Production Setup

```bash
# Build production images
docker build -t climatetrade/api:prod -f docker/api/Dockerfile.prod .
docker build -t climatetrade/data-pipeline:prod -f docker/data-pipeline/Dockerfile.prod .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d

# Check container health
docker ps
docker logs climatetrade-api
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/database/
kubectl apply -f k8s/api/
kubectl apply -f k8s/data-pipeline/
kubectl apply -f k8s/backtesting/
kubectl apply -f k8s/agents/
kubectl apply -f k8s/web/

# Check deployment status
kubectl get pods -n climatetrade
kubectl get services -n climatetrade
kubectl get ingress -n climatetrade
```

### Production Configuration

```bash
# Set production environment
export CLIMATRADE_ENV=production

# Configure production secrets
kubectl create secret generic climatetrade-secrets \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  --from-literal=api-key-secret=$(openssl rand -hex 16) \
  --from-literal=encryption-key=$(openssl rand -hex 16)

# Setup SSL certificates
kubectl create secret tls climatetrade-tls \
  --cert=/path/to/cert.pem \
  --key=/path/to/key.pem
```

### Monitoring Setup

```bash
# Deploy monitoring stack
kubectl apply -f k8s/monitoring/prometheus.yml
kubectl apply -f k8s/monitoring/grafana.yml
kubectl apply -f k8s/monitoring/alertmanager.yml

# Setup log aggregation
kubectl apply -f k8s/logging/elasticsearch.yml
kubectl apply -f k8s/logging/kibana.yml
kubectl apply -f k8s/logging/filebeat.yml
```

### Backup Configuration

```bash
# Setup automated backups
kubectl apply -f k8s/backup/cronjob.yml

# Test backup manually
kubectl create job --from=cronjob/climatetrade-backup backup-test

# Verify backup
kubectl logs job/backup-test
```

## Post-Installation Checklist

- [ ] Python environment activated
- [ ] All dependencies installed
- [ ] Database initialized and migrated
- [ ] Environment variables configured
- [ ] API keys set up
- [ ] External services accessible
- [ ] Health checks passing
- [ ] Basic functionality tested
- [ ] Logging configured
- [ ] Monitoring enabled (production)
- [ ] Backups configured (production)

## Getting Help

### Documentation Resources

- **[README.md](README.md)** - Project overview and navigation
- **[API.md](API.md)** - Complete API documentation
- **[DATABASE.md](DATABASE.md)** - Database schema and management
- **[FRONTEND.md](FRONTEND.md)** - Frontend architecture
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[OPERATIONS.md](OPERATIONS.md)** - System operations

### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **Documentation Wiki**: Detailed guides and tutorials
- **Slack Community**: Real-time help and discussions

### Professional Support

- **Enterprise Support**: 24/7 technical support
- **Consulting Services**: Architecture review and optimization
- **Training**: Team training and onboarding

---

**Setup Complete!** 🎉

Your ClimaTrade AI system is now ready for development or production use. Refer to the [API.md](API.md) for usage instructions and the [OPERATIONS.md](OPERATIONS.md) for maintenance procedures.
