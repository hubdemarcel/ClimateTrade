# ClimaTrade AI - Setup, Installation, and Running Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start Installation](#quick-start-installation)
4. [Detailed Installation](#detailed-installation)
5. [Environment Configuration](#environment-configuration)
6. [Running the System](#running-the-system)
7. [Development Workflows](#development-workflows)
8. [Docker Setup](#docker-setup)
9. [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive instructions for setting up, installing, running, and developing the ClimaTrade AI application. Whether you are a developer looking to contribute or an operator running the system, this guide has you covered.

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

## Quick Start Installation

### One-Command Setup (Development)

```bash
# Clone the repository
git clone <repository-url>
cd climatetrade

# Run the automated setup script
./scripts/setup-development.sh

# Or manually:
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python database/setup_database.py

# Run initial migration
python database/migrations/migration_manager.py apply

# Start development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual services
docker build -t climatetrade/api -f docker/api/Dockerfile .
docker build -t climatetrade/data-pipeline -f docker/data-pipeline/Dockerfile .
docker build -t climatetrade/backtesting -f docker/backtesting/Dockerfile .

# Run services
docker run -d -p 8000:8000 climatetrade/api
docker run -d climatetrade/data-pipeline
docker run -d climatetrade/backtesting
```

## Detailed Installation

### Step 1: Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd climatetrade

# Verify the structure
ls -la
# Should see: data/, scripts/, database/, docs/, etc.
```

### Step 2: Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
virtualenv\Scripts\activate

# Verify Python version
python --version
# Should be 3.9 or higher

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Core Dependencies

```bash
# Install core requirements
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Install component-specific dependencies
pip install -r src/backtesting/requirements.txt
pip install -r src/data_pipeline/requirements.txt
```

### Step 4: External Service Setup

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

## Running the System

### System Components

ClimaTrade AI consists of several interconnected components:

### 1. Backtesting Framework

- **Purpose**: Test and optimize weather-based trading strategies
- **Entry Point**: `src/backtesting/main.py`
- **Data**: Historical weather and market data

### 2. AI Trading Agents

- **Purpose**: Autonomous trading with AI decision making
- **Entry Point**: `src/scripts/agents/cli.py`
- **Features**: Market analysis, trade execution, risk management

### 3. Data Pipeline

- **Purpose**: Collect and process weather data from multiple sources
- **Entry Points**: Various scripts in `src/data_pipeline/` and `src/scripts/`
- **Sources**: Met Office, Meteostat, Weather Underground, NWS

### 4. Database Layer

- **Purpose**: Centralized data storage and management
- **Technology**: SQLite (dev) / PostgreSQL (prod)
- **Location**: `data/climatetrade.db`

### 5. Web Interface

- **Purpose**: Dashboard for monitoring and management
- **Technology**: Vite-based React application
- **Location**: `web/frontend/`

### Running Individual Components

#### Backtesting Framework

##### Single Strategy Backtest

```bash
# Run temperature-based strategy
python src/backtesting/main.py single --strategy temperature

# Run with specific markets and locations
python src/backtesting/main.py single \
  --strategy temperature \
  --markets temp_market_1 temp_market_2 \
  --locations "London, UK" "New York City, NY"

# Run with custom parameters
python src/backtesting/main.py single \
  --strategy temperature \
  --locations "London, UK"
```

##### Multiple Strategies Comparison

```bash
# Compare multiple strategies
python src/backtesting/main.py multi \
  --strategy temperature precipitation wind \
  --locations "London, UK"
```

##### Strategy Optimization

```bash
# Optimize strategy parameters
python src/backtesting/main.py optimize \
  --strategy temperature \
  --optimization-method random_search \
  --max-evaluations 100
```

#### AI Trading Agents

##### Market Exploration

```bash
# Get active markets
python src/scripts/agents/cli.py get-all-markets --limit 10

# Get market events
python src/scripts/agents/cli.py get-all-events --limit 5
```

##### News and Research

```bash
# Get relevant news for trading decisions
python src/scripts/agents/cli.py get-relevant-news "climate change impact on agriculture"
```

##### Autonomous Trading

```bash
# Run autonomous trading system
python src/scripts/agents/cli.py run-autonomous-trader
```

##### Market Creation

```bash
# Generate market creation request
python src/scripts/agents/cli.py create-market
```

#### Data Pipeline

##### Weather Data Collection

```bash
# Collect Met Office data for London
python src/scripts/example_met_office_integration.py

# Collect Meteostat data
python src/scripts/example_meteostat_london.py

# Collect Weather Underground data
python src/scripts/example_weather_underground_integration.py

# Collect Open-Meteo data (free, no API key required)
python src/scripts/open_meteo_client.py --location "London,UK" --current
python src/scripts/open_meteo_client.py --location "New York,NY" --forecast --days 7
python src/scripts/open_meteo_client.py --location "London,UK" --current --save-to-db
```

##### Data Validation and Processing

```bash
# Run data quality checks
python src/data_pipeline/test_data_quality.py

# Validate and clean data
python src/data_pipeline/data_cleaning.py
```

##### Real-time Data Integration

```bash
# Start real-time data collection
python src/scripts/example_real_time_integration.py
```

#### Database Operations

##### Setup and Migration

```bash
# Initialize database
python database/setup_database.py

# Run migrations
python database/migrations/migration_manager.py apply

# Validate schema
python database/validate_schema.py
```

#### Web Interface

##### Starting the Development Server

```bash
# Navigate to the frontend directory
cd web/frontend

# Start the development server
npm run dev

# Or specify a port (e.g., 8080)
npm run dev -- --port 8080
```

**Why Vite?** Vite is required because it provides fast development server capabilities with hot module replacement and supports compiling TypeScript and JSX files on-the-fly. Unlike simple static servers like Python's http.server, Vite handles the build process for modern React applications.

**Accessing the Application**: Once the server starts, open your browser and navigate to `http://localhost:3000` (or the specified port if using --port).

### Full System Integration

#### Development Mode

```bash
# Start all components in development mode
python src/scripts/start_system.py --mode development --components all

# Or start individually:
# 1. Start data collection
python src/scripts/example_real_time_integration.py &

# 2. Start backtesting (in another terminal)
python src/backtesting/main.py single --strategy temperature &

# 3. Start agent system
python src/scripts/agents/cli.py get-all-markets
```

#### Production Mode

```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.prod.yml up -d

# Or using Kubernetes
kubectl apply -f k8s/
kubectl get pods -n climatetrade
```

### Integration Testing

```bash
# Run integration tests
pytest tests/integration/ -v

# Test data pipeline end-to-end
python src/scripts/example_resolution_integration.py

# Test agent-market integration
python src/scripts/agents/tests/test.py
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

## Docker Setup

### Using Docker Compose (Recommended)

```bash
# Navigate to web directory
cd web

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Services

#### Backend Service

```yaml
# web/docker-compose.yml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
  ports:
    - '8001:8001'
  volumes:
    - ../data:/app/data:ro
  environment:
    - DATABASE_PATH=/app/data/climatetrade.db
```

#### Frontend Service

```yaml
# web/docker-compose.yml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - '8080:8080'
  depends_on:
    - backend
```

### Building Individual Services

```bash
# Build backend
cd web/backend
docker build -t climatetrade/backend .

# Build frontend
cd ../frontend
docker build -t climatetrade/frontend .

# Run services
docker run -d -p 8001:8001 climatetrade/backend
docker run -d -p 8080:8080 climatetrade/frontend
```

### Docker Development Workflow

```bash
# Development with hot reload
docker run -v $(pwd):/app -p 8080:8080 climatetrade/frontend

# Production build
docker build -t climatetrade/frontend:prod -f Dockerfile.prod .
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
