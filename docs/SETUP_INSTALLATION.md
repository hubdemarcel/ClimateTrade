# ClimaTrade AI - Setup & Installation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start Installation](#quick-start-installation)
3. [Detailed Installation](#detailed-installation)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Component Installation](#component-installation)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)

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
venv\Scripts\activate

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
pip install -r backtesting_framework/requirements.txt
pip install -r data_pipeline/requirements.txt
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

# Weather2Geo (optional)
cd scripts/Weather2Geo
pip install -r requirements.txt
```

#### Polymarket Setup

```bash
# Install Polymarket client
pip install -e scripts/polymarket-client/

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
pip install -r scripts/requirements-resolution.txt

# For local development:
cd scripts/resolution-subgraph
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

## Database Setup

### SQLite Setup (Development)

```bash
# Navigate to database directory
cd database

# Initialize database
python setup_database.py

# Verify database creation
ls -la ../data/
# Should see: climatetrade.db

# Check database schema
python validate_schema.py
```

### PostgreSQL Setup (Production)

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE climatetrade_prod;
CREATE USER climatetrade_prod WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE climatetrade_prod TO climatetrade_prod;
ALTER USER climatetrade_prod CREATEDB;

# Enable extensions
\c climatetrade_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

# Exit PostgreSQL
\q

# Test connection
psql -h localhost -U climatetrade_prod -d climatetrade_prod
```

### Database Migration

```bash
# Apply all migrations
cd database
python migrations/migration_manager.py apply

# Check migration status
python migrations/migration_manager.py status

# Create new migration (if needed)
python migrations/migration_manager.py create --name add_new_feature --description "Add new feature table"
```

## Component Installation

### Weather Data Pipeline Setup

```bash
# Install weather data dependencies
pip install requests beautifulsoup4 lxml

# Configure weather sources
python database/setup_database.py --setup-weather-sources

# Test weather data collection
python scripts/test_weather_apis.py
```

### Polymarket Integration Setup

```bash
# Install Polymarket client
cd scripts/polymarket-client
pip install -e .

# Test API connection
python -c "
from py_clob_client import ClobClient
client = ClobClient('https://clob.polymarket.com', key='your_key', secret='your_secret', passphrase='your_passphrase')
print('Connection successful')
"
```

### Backtesting Framework Setup

```bash
# Install backtesting dependencies
cd backtesting_framework
pip install -r requirements.txt

# Test backtesting framework
python main.py single --strategy temperature --help
```

### Data Validation Framework Setup

```bash
# Install validation dependencies
pip install pydantic[email] jsonschema

# Test validation framework
python -c "
from data_pipeline.validation_framework import create_validator
validator = create_validator()
print('Validation framework ready')
"
```

### Web Dashboard Setup

```bash
# Install web dependencies
pip install fastapi jinja2 uvicorn[standard] python-multipart

# Install frontend dependencies (if applicable)
cd web
npm install  # If package.json exists

# Start web server
python -m uvicorn web.main:app --reload --host 0.0.0.0 --port 8000
```

## Verification & Testing

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
python backtesting_framework/main.py single --strategy temperature
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

## Troubleshooting

### Common Installation Issues

#### Python Version Issues

```bash
# Check Python version
python --version

# If wrong version, use pyenv
pyenv install 3.9.7
pyenv global 3.9.7

# Or use conda
conda create -n climatetrade python=3.9
conda activate climatetrade
```

#### Dependency Conflicts

```bash
# Clear pip cache
pip cache purge

# Reinstall in clean environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Database Connection Issues

```bash
# Test SQLite connection
python -c "import sqlite3; print('SQLite OK')"

# Test PostgreSQL connection
psql -h localhost -U climatetrade_prod -d climatetrade_prod -c "SELECT version();"

# Check database file permissions
ls -la data/climatetrade.db
chmod 664 data/climatetrade.db
```

#### API Key Issues

```bash
# Verify API keys in environment
echo $MET_OFFICE_API_KEY
echo $POLYMARKET_API_KEY

# Test API connectivity
curl -H "X-API-Key: $MET_OFFICE_API_KEY" https://api.metoffice.gov.uk/v1/test

# Check API key format
python scripts/validate_api_keys.py
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

### Performance Issues

```bash
# Check system resources
top
df -h
free -h

# Monitor application performance
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"

# Check database performance
python database/monitor_performance.py
```

### Logging and Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Check application logs
tail -f logs/climatetrade.log

# Check system logs
journalctl -u climatetrade -f

# Debug database queries
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Run your code here
"
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

- [Project Overview](PROJECT_OVERVIEW.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Operations Guide](OPERATIONS_GUIDE.md)

### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **Documentation Wiki**: Detailed guides and tutorials
- **Slack Community**: Real-time help and discussions

### Professional Support

- **Enterprise Support**: 24/7 technical support
- **Consulting Services**: Architecture review and optimization
- **Training**: Team training and onboarding

---

**Installation completed successfully!** 🎉

Your ClimaTrade AI system is now ready for development or production use. Refer to the [API Documentation](API_DOCUMENTATION.md) for usage instructions and the [Operations Guide](OPERATIONS_GUIDE.md) for maintenance procedures.
