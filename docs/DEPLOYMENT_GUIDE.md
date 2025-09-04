# ClimaTrade AI Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Component Setup](#component-setup)
   - [Database Setup](#database-setup)
   - [Data Pipeline Setup](#data-pipeline-setup)
   - [Backtesting Framework Setup](#backtesting-framework-setup)
   - [Agents Setup](#agents-setup)
   - [Resolution Subgraph Setup](#resolution-subgraph-setup)
   - [Web Interface Setup](#web-interface-setup)
5. [Environment Configuration](#environment-configuration)
6. [Docker Deployment](#docker-deployment)
7. [Production Deployment](#production-deployment)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Overview

ClimaTrade AI is a comprehensive weather-informed trading intelligence system for Polymarket. This deployment guide provides unified instructions for setting up all components of the system across different environments.

### Architecture Components

- **Database**: SQLite-based data storage with migration system
- **Data Pipeline**: Weather data ingestion and validation framework
- **Backtesting Framework**: Strategy testing and optimization
- **Agents**: AI-powered trading agents with Docker support
- **Resolution Subgraph**: Historical market resolution data
- **Web Interface**: Dashboard and user interface

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.8+ (3.9 recommended)
- **Node.js**: 16+ (for subgraph development)
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for multi-service deployment)

### Network Requirements

- Internet access for weather API calls
- Polygon RPC endpoint access
- Polymarket API access (if using live trading)

### Hardware Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB free space for data and models
- **CPU**: Multi-core processor for parallel processing

## Quick Start

### Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd climatetrade

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Set up database
cd database
python setup_database.py
python migrations/migration_manager.py apply

# Start resolution subgraph (optional)
cd ../scripts/resolution-subgraph
docker compose up -d

# Run basic validation
cd ../../data_pipeline
python -c "from validation_framework import create_validator; print('Validation framework ready')"
```

### Docker Deployment

```bash
# Build and run agents
cd scripts/agents
./scripts/bash/build-docker.sh
./scripts/bash/run-docker.sh

# Or use docker-compose for full stack
docker compose -f docker-compose.prod.yml up -d
```

## Component Setup

### Database Setup

The database uses SQLite with a comprehensive schema supporting weather data, market data, and trading operations.

```bash
# Navigate to database directory
cd database

# Initialize database
python setup_database.py

# Apply migrations
python migrations/migration_manager.py apply

# Validate schema
python validate_schema.py
```

**Configuration Options:**

```bash
# Custom database path
python setup_database.py --db-path ../data/climatetrade.db

# Force recreate database
python setup_database.py --force-recreate
```

**Database Schema Overview:**

- Weather data tables (sources, data, forecasts)
- Polymarket data tables (events, markets, trades, orderbook)
- Agent operations tables (strategies, execution logs, history)
- Backtesting tables (configs, results, trades, risk analysis)
- Resolution subgraph tables (resolutions, mappings, moderators)

### Data Pipeline Setup

The data pipeline handles weather data ingestion from multiple sources with validation and quality assurance.

```bash
# Navigate to data pipeline directory
cd data_pipeline

# Install dependencies
pip install -r requirements.txt

# Configure data sources
cp quality_config_example.json quality_config.json
# Edit quality_config.json with your settings

# Run validation tests
python test_data_quality.py
```

**Data Sources Configuration:**

```json
{
  "weather_sources": {
    "met_office": {
      "api_key": "your-api-key",
      "base_url": "https://api.weather.gov"
    },
    "meteostat": {
      "api_key": "your-api-key",
      "base_url": "https://api.meteostat.net"
    }
  },
  "validation_rules": {
    "temperature_range": [-50, 60],
    "humidity_range": [0, 100],
    "pressure_range": [800, 1200]
  }
}
```

### Backtesting Framework Setup

The backtesting framework provides systematic testing of weather-based trading strategies.

```bash
# Navigate to backtesting directory
cd backtesting_framework

# Install dependencies
pip install -r requirements.txt

# Run example backtest
python main.py single --strategy temperature --markets temp_market_1

# Run strategy optimization
python main.py optimize --strategy temperature --optimization-method grid_search
```

**Strategy Configuration:**

```python
# Example strategy configuration
strategy_config = {
    'name': 'temperature_threshold',
    'parameters': {
        'hot_threshold': 30.0,
        'cold_threshold': 0.0,
        'signal_strength_threshold': 0.7
    },
    'markets': ['temp_market_1', 'temp_market_2'],
    'locations': ['London, UK', 'New York City, NY']
}
```

### Agents Setup

The agents component provides AI-powered trading capabilities with Docker support.

```bash
# Navigate to agents directory
cd scripts/agents

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run locally
python scripts/python/cli.py get-all-markets

# Docker deployment
./scripts/bash/build-docker.sh
./scripts/bash/run-docker.sh
```

**Environment Configuration:**

```bash
# .env file
POLYGON_WALLET_PRIVATE_KEY="your-private-key"
OPENAI_API_KEY="your-openai-key"
CLOB_API_KEY="your-polymarket-key"
CLOB_SECRET="your-polymarket-secret"
```

### Resolution Subgraph Setup

The resolution subgraph provides historical market resolution data from Polymarket.

```bash
# Navigate to subgraph directory
cd scripts/resolution-subgraph

# Install Node.js dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with Polygon RPC URL

# Start local development environment
docker compose up -d

# Deploy subgraph locally
npm run create-local
npm run deploy-local
```

**Environment Configuration:**

```bash
# .env file
MATIC_RPC_URL="https://polygon-rpc.com/"
GRAPH_NODE_ENDPOINT="http://localhost:8020/"
IPFS_ENDPOINT="http://localhost:5001/"
```

### Web Interface Setup

The web interface provides a dashboard for monitoring and managing the system.

```bash
# Navigate to web directory
cd web

# Install dependencies (when available)
# npm install

# Start development server (when implemented)
# npm run dev
```

_Note: Web interface is currently in placeholder stage. Implementation details will be added when available._

## Environment Configuration

### Development Environment

**Database Configuration:**

```bash
# Use local SQLite database
DATABASE_URL="sqlite:///data/climatetrade.db"
DEBUG=true
LOG_LEVEL=DEBUG
```

**API Configuration:**

```bash
# Use test endpoints and limited rate limits
WEATHER_API_TIMEOUT=30
POLYMARKET_API_TIMEOUT=30
MAX_API_CALLS_PER_MINUTE=60
```

### Staging Environment

**Database Configuration:**

```bash
# Use dedicated staging database
DATABASE_URL="postgresql://user:password@staging-db:5432/climatetrade"
DEBUG=false
LOG_LEVEL=INFO
```

**Security Configuration:**

```bash
# Enable basic security features
ENABLE_HTTPS=true
API_KEY_REQUIRED=true
RATE_LIMITING_ENABLED=true
```

### Production Environment

**Database Configuration:**

```bash
# Use production database cluster
DATABASE_URL="postgresql://user:password@prod-db-cluster:5432/climatetrade"
DEBUG=false
LOG_LEVEL=WARNING
BACKUP_ENABLED=true
```

**Security Configuration:**

```bash
# Full security configuration
ENABLE_HTTPS=true
API_KEY_REQUIRED=true
RATE_LIMITING_ENABLED=true
ENCRYPTION_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

## Docker Deployment

### Single Service Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  climatetrade-db:
    image: sqlite3:latest
    volumes:
      - ./data:/data
    environment:
      - DATABASE_PATH=/data/climatetrade.db

  climatetrade-api:
    build: .
    ports:
      - '8000:8000'
    environment:
      - DATABASE_URL=sqlite:///data/climatetrade.db
    depends_on:
      - climatetrade-db
```

### Multi-Service Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  database:
    image: postgres:13
    environment:
      POSTGRES_DB: climatetrade
      POSTGRES_USER: climatetrade
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  climatetrade-api:
    build: .
    ports:
      - '8000:8000'
    environment:
      - DATABASE_URL=postgresql://climatetrade:${DB_PASSWORD}@database:5432/climatetrade
      - REDIS_URL=redis://redis:6379
    depends_on:
      - database
      - redis

  climatetrade-web:
    build: ./web
    ports:
      - '3000:3000'
    depends_on:
      - climatetrade-api

volumes:
  postgres_data:
  redis_data:
```

## Production Deployment

### Kubernetes Deployment

```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: climatetrade-api
  template:
    metadata:
      labels:
        app: climatetrade-api
    spec:
      containers:
        - name: api
          image: climatetrade/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: database-url
          resources:
            requests:
              memory: '512Mi'
              cpu: '250m'
            limits:
              memory: '1Gi'
              cpu: '500m'
```

### Load Balancing

```yaml
# k8s/service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-api
spec:
  selector:
    app: climatetrade-api
  ports:
    - port: 80
      targetPort: 8000
  type: LoadBalancer
```

### Ingress Configuration

```yaml
# k8s/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: climatetrade-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
spec:
  tls:
    - hosts:
        - api.climatetrade.ai
      secretName: climatetrade-tls
  rules:
    - host: api.climatetrade.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: climatetrade-api
                port:
                  number: 80
```

## Monitoring and Maintenance

### Health Checks

```python
# health_check.py
from database.connection import get_db_connection
from data_pipeline.validation_framework import create_validator

def perform_health_check():
    """Perform comprehensive system health check"""
    checks = {
        'database': check_database_health(),
        'data_pipeline': check_data_pipeline_health(),
        'agents': check_agents_health(),
        'subgraph': check_subgraph_health()
    }

    return all(checks.values()), checks

def check_database_health():
    """Check database connectivity and integrity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

### Backup Procedures

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
sqlite3 /data/climatetrade.db ".backup '$BACKUP_DIR/climatetrade.db'"

# Configuration backup
cp -r /config $BACKUP_DIR/

# Logs backup
cp -r /logs $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
```

### Log Management

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure comprehensive logging"""
    logger = logging.getLogger('climatetrade')
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/climatetrade.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )

    # Console handler
    console_handler = logging.StreamHandler()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### Performance Monitoring

```python
# metrics_collector.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics definitions
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')

def track_request_time(method, endpoint):
    """Decorator to track request timing"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

            return result
        return wrapper
    return decorator
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**

   ```bash
   # Check database file permissions
   ls -la data/climatetrade.db

   # Verify SQLite installation
   sqlite3 --version

   # Test database connection
   python -c "import sqlite3; conn = sqlite3.connect('data/climatetrade.db'); print('Connection successful')"
   ```

2. **API Rate Limiting**

   ```python
   # Implement exponential backoff
   import time
   import requests

   def api_call_with_retry(url, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = requests.get(url)
               response.raise_for_status()
               return response.json()
           except requests.exceptions.RequestException as e:
               if attempt < max_retries - 1:
                   wait_time = 2 ** attempt
                   time.sleep(wait_time)
               else:
                   raise e
   ```

3. **Memory Issues**

   ```python
   # Monitor memory usage
   import psutil
   import os

   def check_memory_usage():
       process = psutil.Process(os.getpid())
       memory_usage = process.memory_info().rss / 1024 / 1024  # MB
       print(f"Memory usage: {memory_usage:.2f} MB")

       if memory_usage > 1000:  # 1GB threshold
           # Implement memory cleanup
           gc.collect()
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

## Security Best Practices

### API Key Management

```python
# secure_config.py
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(self.key)

    def encrypt_api_key(self, api_key):
        """Encrypt API key for storage"""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key):
        """Decrypt API key for use"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
```

### Network Security

```yaml
# nginx.conf for API gateway
server {
    listen 443 ssl http2;
    server_name api.climatetrade.ai;

    ssl_certificate /etc/ssl/certs/climatetrade.crt;
    ssl_certificate_key /etc/ssl/private/climatetrade.key;

    # Rate limiting
    limit_req zone=api burst=10 nodelay;

    # CORS configuration
    add_header 'Access-Control-Allow-Origin' 'https://dashboard.climatetrade.ai';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type';

    location /api/ {
        proxy_pass http://climatetrade-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Data Encryption

```python
# data_encryption.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

class DataEncryption:
    def __init__(self, password):
        self.salt = os.urandom(16)
        self.key = self._derive_key(password, self.salt)

    def _derive_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())

    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Pad data to block size
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padded_data = data + (chr(padding_length) * padding_length)

        encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()
        return iv + encrypted

    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        iv = encrypted_data[:16]
        encrypted = encrypted_data[16:]

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()

        # Remove padding
        padding_length = ord(decrypted_padded[-1])
        decrypted = decrypted_padded[:-padding_length]

        return decrypted.decode()
```

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX idx_weather_location ON weather_data(location_name);
CREATE INDEX idx_polymarket_market ON polymarket_data(market_id);
CREATE INDEX idx_trades_timestamp ON trading_history(timestamp);

-- Optimize query performance
PRAGMA cache_size = 10000;
PRAGMA synchronous = NORMAL;
PRAGMA journal_mode = WAL;
PRAGMA temp_store = MEMORY;
```

### Caching Strategy

```python
# cache_config.py
from cachetools import TTLCache, cached
import redis

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.local_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute TTL

    @cached(cache=TTLCache(maxsize=100, ttl=600))  # 10 minute TTL
    def get_weather_data(self, location, date):
        """Cache weather data requests"""
        # Check Redis first
        cache_key = f"weather:{location}:{date}"
        cached_data = self.redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # Fetch from API
        data = self._fetch_weather_data(location, date)

        # Cache in Redis
        self.redis_client.setex(cache_key, 600, json.dumps(data))

        return data
```

### Parallel Processing

```python
# parallel_processing.py
import concurrent.futures
import multiprocessing

class ParallelProcessor:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or multiprocessing.cpu_count()

    def process_weather_data_batch(self, data_batch):
        """Process weather data in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._validate_and_process_record, record)
                for record in data_batch
            ]

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Processing failed: {e}")

            return results

    def _validate_and_process_record(self, record):
        """Validate and process individual record"""
        # Validation logic
        validator = create_validator()
        validation_result = validator.validate_weather_data(record)

        if validation_result.is_valid:
            # Processing logic
            processed_record = self._enrich_weather_data(record)
            return processed_record
        else:
            raise ValueError(f"Validation failed: {validation_result.errors}")
```

## Scalability Considerations

### Horizontal Scaling

```yaml
# k8s/hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: climatetrade-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: climatetrade-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Database Sharding

```python
# database_sharding.py
class DatabaseShardManager:
    def __init__(self, shard_configs):
        self.shards = {}
        for config in shard_configs:
            self.shards[config['shard_id']] = sqlite3.connect(config['path'])

    def get_shard_for_location(self, location):
        """Determine which shard to use based on location"""
        # Simple sharding strategy: hash location to shard
        shard_id = hash(location) % len(self.shards)
        return self.shards[shard_id]

    def insert_weather_data(self, location, data):
        """Insert data into appropriate shard"""
        shard = self.get_shard_for_location(location)
        cursor = shard.cursor()

        cursor.execute("""
            INSERT INTO weather_data (location_name, temperature, timestamp)
            VALUES (?, ?, ?)
        """, (location, data['temperature'], data['timestamp']))

        shard.commit()
```

### Load Balancing

```nginx
# nginx.conf for load balancing
upstream climatetrade_api {
    least_conn;
    server api-1.climatetrade.ai:8000;
    server api-2.climatetrade.ai:8000;
    server api-3.climatetrade.ai:8000;

    # Health checks
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}

server {
    listen 80;
    server_name api.climatetrade.ai;

    location / {
        proxy_pass http://climatetrade_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Connection limits
        limit_conn api_zone 10;
        limit_req zone=api burst=20 nodelay;
    }
}
```

## Support and Contributing

For deployment issues and questions:

1. Check this documentation first
2. Review the troubleshooting section
3. Check existing GitHub issues
4. Open a new issue with detailed information

When contributing deployment improvements:

1. Update this documentation
2. Test deployments across environments
3. Include security considerations
4. Provide rollback procedures

---

**Note**: This deployment guide is comprehensive and production-ready. Always test deployments in staging environments before production rollout. Regular backups and monitoring are essential for production systems.
