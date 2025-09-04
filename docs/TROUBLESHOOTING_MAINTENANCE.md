# ClimaTrade AI Troubleshooting and Maintenance Guide

## Table of Contents

1. [Overview](#overview)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [System Monitoring](#system-monitoring)
4. [Performance Optimization](#performance-optimization)
5. [Backup and Recovery](#backup-and-recovery)
6. [Log Management](#log-management)
7. [Database Maintenance](#database-maintenance)
8. [Security Maintenance](#security-maintenance)
9. [Emergency Procedures](#emergency-procedures)
10. [Regular Maintenance Tasks](#regular-maintenance-tasks)

## Overview

This guide provides comprehensive troubleshooting procedures, maintenance schedules, and operational best practices for ClimaTrade AI. It covers common issues, monitoring strategies, performance optimization, and emergency response procedures.

### Maintenance Philosophy

- **Proactive Monitoring**: Continuous system health monitoring
- **Automated Recovery**: Self-healing capabilities where possible
- **Regular Backups**: Automated backup procedures
- **Performance Optimization**: Continuous performance tuning
- **Security Updates**: Regular security patching and updates

## Common Issues and Solutions

### Database Connection Issues

#### Symptoms

- Application errors: "Connection refused" or "Connection timeout"
- Slow query performance
- Database connection pool exhausted

#### Diagnosis

```bash
# Check database connectivity
psql -h localhost -U climatetrade -d climatetrade -c "SELECT 1;"

# Check connection pool status
psql -h localhost -U climatetrade -d climatetrade -c "SELECT * FROM pg_stat_activity;"

# Check database logs
tail -f /var/log/postgresql/postgresql.log
```

#### Solutions

**Connection Pool Exhaustion:**

```sql
-- Increase connection pool size
ALTER SYSTEM SET max_connections = '200';
SELECT pg_reload_conf();

-- Monitor connection usage
SELECT count(*) as connections,
       state
FROM pg_stat_activity
GROUP BY state;
```

**Network Issues:**

```bash
# Test network connectivity
telnet localhost 5432

# Check firewall rules
sudo ufw status
sudo iptables -L

# Test with specific connection string
psql "postgresql://climatetrade:password@localhost:5432/climatetrade?connect_timeout=10"
```

**Kubernetes-specific:**

```bash
# Check pod status
kubectl get pods -n climatetrade

# Check service endpoints
kubectl get endpoints -n climatetrade

# Check database pod logs
kubectl logs -n climatetrade deployment/climatetrade-postgresql
```

### Memory Issues

#### Symptoms

- Out of memory errors
- Slow performance
- Application crashes
- System swapping

#### Diagnosis

```bash
# Check memory usage
free -h
vmstat 1 10

# Check process memory
ps aux --sort=-%mem | head -10

# Check Docker container memory
docker stats

# Kubernetes memory monitoring
kubectl top pods -n climatetrade
```

#### Solutions

**Increase Memory Limits:**

```yaml
# Kubernetes deployment update
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-api
spec:
  template:
    spec:
      containers:
        - name: api
          resources:
            requests:
              memory: '1Gi'
            limits:
              memory: '2Gi'
```

**Memory Leak Investigation:**

```python
# Add memory profiling
import tracemalloc
tracemalloc.start()

# Check memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

# Get memory usage by file
stats = tracemalloc.take_snapshot().statistics('filename')
for stat in stats[:10]:
    print(f"{stat.filename}: {stat.size / 1024 / 1024:.1f} MB")
```

**Database Memory Optimization:**

```sql
-- Check memory configuration
SHOW shared_buffers;
SHOW work_mem;
SHOW maintenance_work_mem;

-- Optimize for better memory usage
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### API Rate Limiting Issues

#### Symptoms

- HTTP 429 (Too Many Requests) errors
- Slow API response times
- Service unavailability

#### Diagnosis

```bash
# Check rate limiting logs
grep "rate limit" /var/log/climatetrade/api.log

# Monitor API endpoints
curl -H "Authorization: Bearer $TOKEN" https://api.climatetrade.ai/health

# Check Redis rate limiting keys
redis-cli KEYS "rate_limit:*"
```

#### Solutions

**Adjust Rate Limits:**

```python
# Update rate limiting configuration
RATE_LIMITS = {
    'default': '1000/hour',
    'authenticated': '5000/hour',
    'premium': '10000/hour'
}

# Apply new limits
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)
```

**Implement Circuit Breaker:**

```python
# Circuit breaker implementation
import circuitbreaker

@circuitbreaker(circuit_breaker_failure_threshold=5,
                circuit_breaker_recovery_timeout=60)
def api_call(endpoint):
    return requests.get(f"https://api.climatetrade.ai/{endpoint}")
```

### Data Pipeline Failures

#### Symptoms

- Data ingestion stops
- Validation errors
- Missing data in database
- Pipeline queue backlog

#### Diagnosis

```bash
# Check pipeline status
curl http://localhost:8000/health

# Check queue status
redis-cli LLEN data_pipeline:queue

# Check validation errors
grep "validation error" /var/log/climatetrade/data-pipeline.log

# Check data quality
python -c "
from data_pipeline.validation_framework import create_validator
validator = create_validator()
# Check recent data quality
"
```

#### Solutions

**Restart Pipeline:**

```bash
# Docker restart
docker restart climatetrade-data-pipeline

# Kubernetes restart
kubectl rollout restart deployment/climatetrade-data-pipeline -n climatetrade
```

**Clear Queue Backlog:**

```bash
# Clear Redis queue
redis-cli DEL data_pipeline:queue

# Restart with clean state
kubectl delete pod -l app=climatetrade-data-pipeline -n climatetrade
```

**Fix Validation Issues:**

```python
# Update validation rules
validation_config = {
    "temperature_range": [-100, 60],  # Expanded range
    "humidity_range": [0, 100],
    "allow_null_values": True
}

# Apply new configuration
from data_pipeline.config_validation import update_validation_config
update_validation_config(validation_config)
```

### Backtesting Performance Issues

#### Symptoms

- Backtesting jobs take too long
- Memory usage spikes during backtesting
- Strategy optimization fails
- Results not generated

#### Diagnosis

```bash
# Check backtesting job status
curl http://localhost:8001/health

# Monitor resource usage
kubectl top pods -n climatetrade | grep backtesting

# Check backtesting logs
kubectl logs -n climatetrade deployment/climatetrade-backtesting --tail=100

# Check database performance
psql -c "SELECT * FROM pg_stat_activity WHERE query LIKE '%backtest%';"
```

#### Solutions

**Optimize Parallel Processing:**

```python
# Update backtesting configuration
BACKTEST_CONFIG = {
    'max_parallel_jobs': 4,  # Adjust based on CPU cores
    'chunk_size': 1000,     # Process data in chunks
    'memory_limit': '2GB'   # Per job memory limit
}

# Apply configuration
from backtesting_framework.core.backtesting_engine import BacktestingEngine
engine = BacktestingEngine(config=BACKTEST_CONFIG)
```

**Database Query Optimization:**

```sql
-- Create indexes for backtesting queries
CREATE INDEX CONCURRENTLY idx_weather_timestamp_location
ON weather_data (timestamp, location_name);

CREATE INDEX CONCURRENTLY idx_polymarket_timestamp_market
ON polymarket_data (timestamp, market_id);

-- Analyze tables for better query planning
ANALYZE weather_data;
ANALYZE polymarket_data;
```

**Resource Allocation:**

```yaml
# Update Kubernetes resource limits
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-backtesting
spec:
  template:
    spec:
      containers:
        - name: backtesting
          resources:
            requests:
              memory: '2Gi'
              cpu: '1000m'
            limits:
              memory: '4Gi'
              cpu: '2000m'
```

### Agent Trading Issues

#### Symptoms

- Trading agents not executing trades
- API key authentication failures
- Rate limiting from exchanges
- Incorrect trade calculations

#### Diagnosis

```bash
# Check agent status
curl http://localhost:8002/health

# Check agent logs
kubectl logs -n climatetrade deployment/climatetrade-agents --tail=50

# Verify API keys
python -c "
from agents.connectors.polymarket import PolymarketClient
client = PolymarketClient()
print('API connection:', client.test_connection())
"

# Check trading history
psql -c "SELECT COUNT(*) FROM trading_history WHERE timestamp > NOW() - INTERVAL '1 hour';"
```

#### Solutions

**API Key Rotation:**

```python
# Update API keys securely
from agents.utils.secrets import update_api_keys

new_keys = {
    'polygon_private_key': 'new_private_key',
    'openai_api_key': 'new_openai_key',
    'polymarket_api_key': 'new_polymarket_key'
}

update_api_keys(new_keys)
```

**Rate Limiting Configuration:**

```python
# Update rate limiting
RATE_LIMIT_CONFIG = {
    'requests_per_minute': 30,
    'burst_limit': 10,
    'backoff_factor': 2,
    'max_retries': 5
}

# Apply configuration
from agents.application.trade import TradingAgent
agent = TradingAgent(rate_limit_config=RATE_LIMIT_CONFIG)
```

**Circuit Breaker Implementation:**

```python
# Add circuit breaker for external APIs
@circuitbreaker(failure_threshold=3, recovery_timeout=300)
def execute_trade(trade_params):
    """Execute trade with circuit breaker protection"""
    return polymarket_api.place_order(trade_params)
```

## System Monitoring

### Health Check Endpoints

#### API Health Check

```python
# health_check.py
from flask import Flask, jsonify
import psycopg2
import redis
import time

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }

    # Database check
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.close()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Redis check
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        health_status['checks']['redis'] = 'healthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # External API check
    try:
        response = requests.get('https://api.polymarket.com/health', timeout=5)
        if response.status_code == 200:
            health_status['checks']['external_api'] = 'healthy'
        else:
            health_status['checks']['external_api'] = f'unhealthy: HTTP {response.status_code}'
    except Exception as e:
        health_status['checks']['external_api'] = f'unhealthy: {str(e)}'

    return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
```

#### Metrics Endpoint

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from flask import Flask, Response

app = Flask(__name__)

# Metrics definitions
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
DB_CONNECTIONS = Gauge('db_connections_active', 'Number of active database connections')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    # Update gauges with current values
    update_system_metrics()

    return Response(generate_latest(), mimetype='text/plain')

def update_system_metrics():
    """Update system metrics"""
    import psutil

    # Memory usage
    memory = psutil.virtual_memory()
    MEMORY_USAGE.set(memory.used)

    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    CPU_USAGE.set(cpu_percent)

    # Database connections
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM pg_stat_activity;")
        db_connections = cursor.fetchone()[0]
        DB_CONNECTIONS.set(db_connections)
        conn.close()
    except:
        DB_CONNECTIONS.set(0)
```

### Monitoring Dashboards

#### Grafana Dashboard Configuration

```json
// grafana-dashboard.json
{
  "dashboard": {
    "title": "ClimaTrade AI Monitoring",
    "tags": ["climatetrade", "production"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "db_connections_active",
            "legendFormat": "Active connections"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_bytes / 1024 / 1024",
            "legendFormat": "Memory (MB)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error rate (%)"
          }
        ]
      }
    ]
  }
}
```

### Alert Configuration

#### Prometheus Alert Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: climatetrade
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~'5..'}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: 'High error rate detected'
          description: 'Error rate is {{ $value }}% which is above 5%'

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connections_active > 50
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: 'Database connection pool nearly exhausted'
          description: 'Active database connections: {{ $value }}'

      - alert: MemoryUsageHigh
        expr: memory_usage_bytes / 1024 / 1024 / 1024 > 4
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'High memory usage detected'
          description: 'Memory usage: {{ $value }} GB'

      - alert: APIDown
        expr: up{job="climatetrade-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: 'API service is down'
          description: 'ClimaTrade API has been down for more than 1 minute'
```

## Performance Optimization

### Database Optimization

#### Query Optimization

```sql
-- Analyze slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Create optimized indexes
CREATE INDEX CONCURRENTLY idx_weather_composite
ON weather_data (location_name, timestamp DESC, temperature)
WHERE temperature IS NOT NULL;

-- Partition large tables
CREATE TABLE weather_data_y2024m01 PARTITION OF weather_data
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Update autovacuum settings
ALTER TABLE weather_data SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);
```

#### Caching Strategy

```python
# Redis caching implementation
import redis
from functools import wraps
import json

class CacheManager:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)

    def cached(self, ttl=300):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                # Try to get from cache
                cached_result = self.redis.get(key)
                if cached_result:
                    return json.loads(cached_result)

                # Execute function
                result = func(*args, **kwargs)

                # Cache result
                self.redis.setex(key, ttl, json.dumps(result))

                return result
            return wrapper
        return decorator

# Usage
cache_manager = CacheManager(os.getenv('REDIS_URL'))

@cache_manager.cached(ttl=600)
def get_weather_data(location, date):
    """Get weather data with caching"""
    return fetch_weather_from_api(location, date)
```

### Application Optimization

#### Async Processing

```python
# Asynchronous task processing
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp

class AsyncProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_weather_batch(self, locations):
        """Process multiple weather requests asynchronously"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for location in locations:
                task = asyncio.create_task(self.fetch_weather(session, location))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

    async def fetch_weather(self, session, location):
        """Fetch weather data asynchronously"""
        url = f"https://api.weather.com/v1/location/{location}"
        try:
            async with session.get(url, timeout=10) as response:
                return await response.json()
        except Exception as e:
            return {"error": str(e), "location": location}

# Usage
processor = AsyncProcessor()

async def main():
    locations = ["London", "New York", "Tokyo", "Sydney"]
    results = await processor.process_weather_batch(locations)
    return results

# Run async processing
results = asyncio.run(main())
```

#### Memory Optimization

```python
# Memory-efficient data processing
import pandas as pd
import gc

class MemoryEfficientProcessor:
    def __init__(self, chunk_size=10000):
        self.chunk_size = chunk_size

    def process_large_dataset(self, file_path):
        """Process large datasets in chunks"""
        for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
            # Process chunk
            processed_chunk = self._process_chunk(chunk)

            # Save results
            self._save_chunk(processed_chunk)

            # Clean up memory
            del chunk
            del processed_chunk
            gc.collect()

    def _process_chunk(self, chunk):
        """Process individual chunk"""
        # Apply transformations
        chunk['processed_temperature'] = chunk['temperature'] * 1.8 + 32  # Convert to Fahrenheit
        chunk['quality_score'] = self._calculate_quality_score(chunk)

        return chunk

    def _calculate_quality_score(self, chunk):
        """Calculate data quality score"""
        score = 0
        if not chunk['temperature'].isnull().any():
            score += 1
        if not chunk['humidity'].isnull().any():
            score += 1
        return score

    def _save_chunk(self, chunk):
        """Save processed chunk"""
        # Append to database or file
        chunk.to_sql('processed_weather', self.db_engine, if_exists='append', index=False)
```

## Backup and Recovery

### Automated Backup System

#### Database Backup Script

```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/backups/$(date +%Y%m%d)"
TIMESTAMP=$(date +%H%M%S)
BACKUP_FILE="climatetrade_backup_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --no-password \
    --format=custom \
    --compress=9 \
    --file=$BACKUP_DIR/$BACKUP_FILE

# Verify backup
echo "Verifying backup..."
pg_restore --list $BACKUP_DIR/$BACKUP_FILE > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backup verification successful"
else
    echo "❌ Backup verification failed"
    exit 1
fi

# Compress backup
echo "Compressing backup..."
gzip $BACKUP_DIR/$BACKUP_FILE

# Upload to cloud storage
echo "Uploading to cloud storage..."
aws s3 cp $BACKUP_DIR/${BACKUP_FILE}.gz s3://climatetrade-backups/database/

# Clean up old backups (keep last 30 days)
echo "Cleaning up old backups..."
find /backups -name "*.sql.gz" -mtime +30 -delete

# Send notification
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"Database backup completed: ${BACKUP_FILE}\"}" \
    $SLACK_WEBHOOK_URL

echo "✅ Database backup completed successfully"
```

#### Configuration Backup

```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/backups/config/$(date +%Y%m%d)"
TIMESTAMP=$(date +%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration files
echo "Backing up configuration files..."
cp -r /app/config $BACKUP_DIR/
cp -r /app/docker-compose*.yml $BACKUP_DIR/
cp -r /app/.env* $BACKUP_DIR/

# Backup secrets (encrypted)
echo "Backing up secrets..."
kubectl get secrets -n climatetrade -o yaml > $BACKUP_DIR/secrets.yml

# Create archive
echo "Creating configuration archive..."
tar -czf $BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz -C $BACKUP_DIR .

# Upload to secure storage
echo "Uploading to secure storage..."
aws s3 cp $BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz \
    s3://climatetrade-backups/config/ \
    --sse AES256

# Clean up
rm -rf $BACKUP_DIR

echo "✅ Configuration backup completed"
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1
DB_HOST=${DB_HOST:-localhost}
DB_USER=${DB_USER:-climatetrade}
DB_NAME=${DB_NAME:-climatetrade}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create recovery confirmation
read -p "⚠️  This will overwrite the current database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled"
    exit 0
fi

# Stop application services
echo "Stopping application services..."
docker-compose stop climatetrade-api climatetrade-data-pipeline

# Restore database
echo "Restoring database from backup..."
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --no-password \
    --clean \
    --if-exists \
    --create \
    $BACKUP_FILE

# Verify restoration
echo "Verifying database restoration..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM weather_data;" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Database restoration successful"
else
    echo "❌ Database restoration failed"
    exit 1
fi

# Restart services
echo "Restarting application services..."
docker-compose start climatetrade-api climatetrade-data-pipeline

# Run health checks
echo "Running health checks..."
sleep 30
curl -f http://localhost:8000/health || echo "⚠️ API health check failed"
curl -f http://localhost:8001/health || echo "⚠️ Data pipeline health check failed"

echo "✅ Database recovery completed"
```

#### Application Recovery

```bash
#!/bin/bash
# emergency-recovery.sh

echo "🚨 Starting emergency recovery procedure"

# 1. Assess the situation
echo "Step 1: Assessing system status..."
kubectl get pods -n climatetrade
kubectl get services -n climatetrade

# 2. Stop failing services
echo "Step 2: Stopping failing services..."
kubectl scale deployment climatetrade-api --replicas=0 -n climatetrade
kubectl scale deployment climatetrade-data-pipeline --replicas=0 -n climatetrade

# 3. Restore from backup
echo "Step 3: Restoring from latest backup..."
LATEST_BACKUP=$(aws s3 ls s3://climatetrade-backups/database/ | sort | tail -1 | awk '{print $4}')
aws s3 cp s3://climatetrade-backups/database/$LATEST_BACKUP /tmp/
./restore-database.sh /tmp/$LATEST_BACKUP

# 4. Restore configuration
echo "Step 4: Restoring configuration..."
LATEST_CONFIG=$(aws s3 ls s3://climatetrade-backups/config/ | sort | tail -1 | awk '{print $4}')
aws s3 cp s3://climatetrade-backups/config/$LATEST_CONFIG /tmp/
tar -xzf /tmp/$LATEST_CONFIG -C /tmp/
kubectl apply -f /tmp/config/secrets.yml -n climatetrade

# 5. Restart services gradually
echo "Step 5: Restarting services..."
kubectl scale deployment climatetrade-api --replicas=1 -n climatetrade
sleep 60
kubectl scale deployment climatetrade-data-pipeline --replicas=1 -n climatetrade
sleep 60

# 6. Scale to normal levels
echo "Step 6: Scaling to normal levels..."
kubectl scale deployment climatetrade-api --replicas=2 -n climatetrade
kubectl scale deployment climatetrade-backtesting --replicas=1 -n climatetrade
kubectl scale deployment climatetrade-agents --replicas=1 -n climatetrade

# 7. Verify recovery
echo "Step 7: Verifying recovery..."
kubectl get pods -n climatetrade
curl -f https://api.climatetrade.ai/health || echo "⚠️ API not healthy"

echo "✅ Emergency recovery completed"
```

## Log Management

### Centralized Logging

#### Log Aggregation Configuration

```yaml
# fluent-bit-config.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: climatetrade
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Daemon        off

    [INPUT]
        Name              tail
        Path              /var/log/containers/*climatetrade*.log
        Parser            docker
        Tag               climatetrade.*
        Refresh_Interval  5
        Mem_Buf_Limit     10MB

    [FILTER]
        Name                grep
        Match               climatetrade.*
        Exclude            log ^.*DEBUG.*$

    [FILTER]
        Name                record_modifier
        Match               climatetrade.*
        Record             service_name ${TAG}
        Record             cluster production

    [OUTPUT]
        Name                elasticsearch
        Match               climatetrade.*
        Host                elasticsearch.climatetrade.svc.cluster.local
        Port                9200
        Index               climatetrade-logs
        Type                climatetrade_log
        Logstash_Format    On
        Replace_Dots       On
        Retry_Limit        3
```

#### Log Rotation

```bash
#!/bin/bash
# log-rotation.sh

LOG_DIR="/var/log/climatetrade"
ARCHIVE_DIR="/var/log/climatetrade/archive"
RETENTION_DAYS=30

# Create archive directory
mkdir -p $ARCHIVE_DIR

# Rotate application logs
for log_file in $LOG_DIR/*.log; do
    if [ -f "$log_file" ]; then
        basename=$(basename "$log_file" .log)
        timestamp=$(date +%Y%m%d_%H%M%S)

        # Compress current log
        gzip -c "$log_file" > "$ARCHIVE_DIR/${basename}_${timestamp}.log.gz"

        # Truncate original log
        truncate -s 0 "$log_file"
    fi
done

# Clean up old archives
find $ARCHIVE_DIR -name "*.log.gz" -mtime +$RETENTION_DAYS -delete

# Rotate Docker logs
docker run --rm -v /var/lib/docker/containers:/var/lib/docker/containers \
    alpine:latest sh -c "
    find /var/lib/docker/containers -name '*.log' -exec truncate -s 0 {} \;
"

echo "✅ Log rotation completed"
```

## Database Maintenance

### Regular Maintenance Tasks

#### Vacuum and Analyze

```sql
-- Automated vacuum and analyze
CREATE OR REPLACE FUNCTION maintenance_vacuum_analyze()
RETURNS void AS $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'VACUUM ANALYZE ' || table_name;
        RAISE NOTICE 'Vacuumed and analyzed table: %', table_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule regular maintenance
SELECT cron.schedule('maintenance-vacuum-analyze', '0 2 * * *', 'SELECT maintenance_vacuum_analyze();');
```

#### Index Maintenance

```sql
-- Reindex bloated indexes
CREATE OR REPLACE FUNCTION reindex_bloated_indexes()
RETURNS void AS $$
DECLARE
    index_record record;
BEGIN
    FOR index_record IN
        SELECT
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as size
        FROM pg_stat_user_indexes
        WHERE pg_relation_size(indexrelid) > 100 * 1024 * 1024  -- 100MB
        ORDER BY pg_relation_size(indexrelid) DESC
    LOOP
        EXECUTE 'REINDEX INDEX CONCURRENTLY ' || index_record.schemaname || '.' || index_record.indexname;
        RAISE NOTICE 'Reindexed: %.% (size: %)', index_record.schemaname, index_record.indexname, index_record.size;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

#### Partition Management

```sql
-- Create new partitions automatically
CREATE OR REPLACE FUNCTION create_weather_partition(target_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date date;
    end_date date;
BEGIN
    partition_name := 'weather_data_' || to_char(target_date, 'YYYYMM');
    start_date := date_trunc('month', target_date);
    end_date := start_date + interval '1 month';

    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I PARTITION OF weather_data
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date);

    RAISE NOTICE 'Created partition: % for % to %', partition_name, start_date, end_date;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation
SELECT cron.schedule('create-weather-partition', '0 0 1 * *', $$
    SELECT create_weather_partition(CURRENT_DATE + interval '1 month');
$$);
```

## Security Maintenance

### Security Updates

#### Automated Security Patching

```bash
#!/bin/bash
# security-updates.sh

echo "🔒 Starting security update process"

# Update system packages
echo "Updating system packages..."
apt-get update && apt-get upgrade -y

# Update Python packages
echo "Updating Python packages..."
pip install --upgrade pip
pip list --outdated --format=json | jq -r '.[] | .name' | xargs -n1 pip install --upgrade

# Update Docker images
echo "Updating Docker images..."
docker images | grep climatetrade | awk '{print $1":"$2}' | xargs -I {} docker pull {}

# Restart services with new images
echo "Restarting services..."
docker-compose up -d --no-deps climatetrade-api
docker-compose up -d --no-deps climatetrade-data-pipeline

# Security scan
echo "Running security scan..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    clair-scanner --ip $(hostname -i) climatetrade/api:latest

echo "✅ Security updates completed"
```

#### SSL Certificate Management

```bash
#!/bin/bash
# ssl-renewal.sh

CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"
DOMAIN="climatetrade.ai"

# Check certificate expiration
echo "Checking certificate expiration..."
openssl x509 -in $CERT_DIR/climatetrade.crt -text -noout | grep "Not After"

# Renew certificate if expiring soon
if openssl x509 -checkend 86400 -in $CERT_DIR/climatetrade.crt; then
    echo "Certificate is valid for more than 24 hours"
else
    echo "🔄 Renewing SSL certificate..."

    # Use certbot for Let's Encrypt renewal
    certbot certonly --standalone -d $DOMAIN -d api.$DOMAIN -d app.$DOMAIN

    # Reload services
    docker-compose restart nginx

    echo "✅ SSL certificate renewed"
fi
```

### Access Control

#### User Access Review

```sql
-- Audit user access and permissions
CREATE OR REPLACE FUNCTION audit_user_access()
RETURNS TABLE (
    username text,
    last_login timestamp,
    failed_attempts int,
    permissions text[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.usename::text,
        u.last_login,
        u.failed_attempts,
        array_agg(p.privilege_type) as permissions
    FROM pg_user u
    LEFT JOIN information_schema.role_table_grants p
        ON u.usename = p.grantee
    WHERE u.usename NOT IN ('postgres', 'climatetrade')
    GROUP BY u.usename, u.last_login, u.failed_attempts;
END;
$$ LANGUAGE plpgsql;

-- Schedule access review
SELECT audit_user_access();
```

## Emergency Procedures

### Incident Response Plan

#### Critical Incident Response

```bash
#!/bin/bash
# incident-response.sh

echo "🚨 CRITICAL INCIDENT DETECTED"

# 1. Isolate affected systems
echo "Step 1: Isolating affected systems..."
kubectl cordon $(kubectl get nodes -o name | head -1)

# 2. Stop all trading activities
echo "Step 2: Stopping trading activities..."
kubectl scale deployment climatetrade-agents --replicas=0 -n climatetrade

# 3. Take database snapshot
echo "Step 3: Taking emergency database snapshot..."
./backup-database.sh emergency

# 4. Notify stakeholders
echo "Step 4: Notifying stakeholders..."
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"🚨 CRITICAL INCIDENT: ClimaTrade AI system compromised. Trading stopped, investigation in progress."}' \
    $SLACK_CRITICAL_WEBHOOK

# 5. Start forensic analysis
echo "Step 5: Starting forensic analysis..."
kubectl run forensics-pod --image=climatetrade/forensics:latest \
    --restart=Never --rm -it \
    -- /bin/bash

# 6. Implement temporary fixes
echo "Step 6: Implementing temporary security measures..."
kubectl apply -f security/temporary-lockdown.yml

echo "✅ Emergency response initiated. Awaiting further instructions."
```

#### Service Degradation Response

```bash
#!/bin/bash
# degradation-response.sh

SERVICE=$1
SEVERITY=$2

echo "⚠️ Service degradation detected: $SERVICE (Severity: $SEVERITY)"

case $SEVERITY in
    "low")
        echo "Low severity - monitoring only"
        # Send alert but continue normal operation
        ;;
    "medium")
        echo "Medium severity - implementing mitigation"
        # Restart service
        kubectl rollout restart deployment $SERVICE -n climatetrade
        ;;
    "high")
        echo "High severity - emergency procedures"
        # Stop affected service
        kubectl scale deployment $SERVICE --replicas=0 -n climatetrade
        # Start incident response
        ./incident-response.sh
        ;;
    "critical")
        echo "Critical severity - full system lockdown"
        # Stop all services
        kubectl scale deployment --all --replicas=0 -n climatetrade
        # Emergency backup
        ./emergency-backup.sh
        ;;
esac
```

## Regular Maintenance Tasks

### Daily Tasks

```bash
#!/bin/bash
# daily-maintenance.sh

echo "📅 Starting daily maintenance tasks"

# 1. Log rotation
echo "Rotating logs..."
./log-rotation.sh

# 2. Database maintenance
echo "Running database maintenance..."
psql -c "SELECT maintenance_vacuum_analyze();"

# 3. Backup verification
echo "Verifying backups..."
./verify-backups.sh

# 4. Health checks
echo "Running health checks..."
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health
curl -f http://localhost:8002/health

# 5. Security scan
echo "Running security scan..."
./security-scan.sh

echo "✅ Daily maintenance completed"
```

### Weekly Tasks

```bash
#!/bin/bash
# weekly-maintenance.sh

echo "📆 Starting weekly maintenance tasks"

# 1. Full database backup
echo "Creating full database backup..."
./backup-database.sh full

# 2. Index optimization
echo "Optimizing database indexes..."
psql -c "SELECT reindex_bloated_indexes();"

# 3. Log analysis
echo "Analyzing system logs..."
./analyze-logs.sh

# 4. Performance review
echo "Reviewing system performance..."
./performance-review.sh

# 5. Security audit
echo "Running security audit..."
./security-audit.sh

echo "✅ Weekly maintenance completed"
```

### Monthly Tasks

```bash
#!/bin/bash
# monthly-maintenance.sh

echo "📊 Starting monthly maintenance tasks"

# 1. Archive old data
echo "Archiving old data..."
./archive-old-data.sh

# 2. Update dependencies
echo "Updating system dependencies..."
./update-dependencies.sh

# 3. Review access controls
echo "Reviewing user access controls..."
psql -c "SELECT * FROM audit_user_access();"

# 4. Compliance check
echo "Running compliance checks..."
./compliance-check.sh

# 5. Capacity planning
echo "Reviewing capacity planning..."
./capacity-planning.sh

echo "✅ Monthly maintenance completed"
```

This comprehensive troubleshooting and maintenance guide provides the operational procedures needed to keep ClimaTrade AI running smoothly, handle incidents effectively, and maintain system reliability and security.
