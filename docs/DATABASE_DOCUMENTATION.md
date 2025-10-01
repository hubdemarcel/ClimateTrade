# ClimaTrade AI - Database Documentation

## Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Schema Documentation](#schema-documentation)
4. [Data Models](#data-models)
5. [Query Examples](#query-examples)
6. [Performance Optimization](#performance-optimization)
7. [Backup and Recovery](#backup-and-recovery)
8. [Maintenance Procedures](#maintenance-procedures)
9. [Troubleshooting](#troubleshooting)

## Overview

ClimaTrade AI uses SQLite as its primary database for development and testing, with PostgreSQL support for production deployments. The database is designed to handle high-volume time-series data from weather APIs, market data from Polymarket, and complex analytical computations for trading strategies.

### Key Features

- **Time-Series Optimized**: Efficient storage and querying of temporal data
- **Multi-Source Integration**: Unified schema for diverse data sources
- **Analytical Capabilities**: Built-in support for complex trading analytics
- **Migration System**: Version-controlled schema changes
- **Data Quality Tracking**: Comprehensive data validation and quality monitoring

### Database Specifications

| Aspect                | Development       | Production         |
| --------------------- | ----------------- | ------------------ |
| **Engine**            | SQLite 3.x        | PostgreSQL 13+     |
| **Size Limit**        | 1TB (theoretical) | Unlimited          |
| **Connections**       | Single-writer     | Multi-writer       |
| **Backup**            | File copy         | pg_dump/pg_restore |
| **High Availability** | N/A               | Read replicas      |

## Database Architecture

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ClimaTrade Database                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────┐ │
│  │ Weather     │  │ Market      │  │ Trading     │  │ Sys │ │
│  │ Data        │  │ Data        │  │ Analytics   │  │ tem │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Time-Series Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────┐ │
│  │ Historical  │  │ Real-time   │  │ Aggregated  │  │ Arc │ │
│  │ Data        │  │ Data        │  │ Data        │  │ hive│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
Weather APIs → Data Pipeline → Validation → Database → Analytics → Trading Signals
     ↓              ↓             ↓         ↓         ↓            ↓
   Raw Data → Cleaning → Quality Check → Storage → Processing → Strategy → Orders
```

### Storage Strategy

#### Data Partitioning

- **Time-based**: Data partitioned by date ranges for efficient querying
- **Source-based**: Separate storage for different data sources
- **Hot/Warm/Cold**: Different storage tiers based on data age and access patterns

#### Indexing Strategy

- **Composite Indexes**: Multi-column indexes for complex queries
- **Partial Indexes**: Indexes on filtered data subsets
- **Functional Indexes**: Indexes on computed values

## Schema Documentation

### Weather Data Tables

#### `weather_sources`

Configuration table for weather data providers.

```sql
CREATE TABLE weather_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    description TEXT,
    api_endpoint TEXT,
    api_key_required BOOLEAN DEFAULT 0,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    data_format TEXT DEFAULT 'json',
    active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### `weather_data`

Core weather observations table with comprehensive meteorological data.

```sql
CREATE TABLE weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    location_name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    timestamp TEXT NOT NULL,
    temperature REAL,
    temperature_min REAL,
    temperature_max REAL,
    feels_like REAL,
    humidity REAL,
    pressure REAL,
    wind_speed REAL,
    wind_direction REAL,
    precipitation REAL,
    weather_code INTEGER,
    weather_description TEXT,
    visibility REAL,
    uv_index REAL,
    alerts TEXT,
    raw_data TEXT,
    data_quality_score REAL DEFAULT 1.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES weather_sources (id),
    UNIQUE(source_id, location_name, timestamp)
);
```

#### `weather_forecasts`

Weather forecast data with prediction horizons.

```sql
CREATE TABLE weather_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    location_name TEXT NOT NULL,
    forecast_timestamp TEXT NOT NULL,
    forecast_for_timestamp TEXT NOT NULL,
    temperature REAL,
    temperature_min REAL,
    temperature_max REAL,
    feels_like REAL,
    humidity REAL,
    pressure REAL,
    wind_speed REAL,
    wind_direction REAL,
    precipitation REAL,
    precipitation_probability REAL,
    weather_code INTEGER,
    weather_description TEXT,
    visibility REAL,
    uv_index REAL,
    raw_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES weather_sources (id),
    UNIQUE(source_id, location_name, forecast_timestamp, forecast_for_timestamp)
);
```

### Polymarket Data Tables

#### `polymarket_events`

Market events and categories from Polymarket.

```sql
CREATE TABLE polymarket_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    ticker TEXT,
    slug TEXT,
    title TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    creation_date TEXT,
    image TEXT,
    icon TEXT,
    active BOOLEAN DEFAULT 1,
    closed BOOLEAN DEFAULT 0,
    archived BOOLEAN DEFAULT 0,
    new BOOLEAN DEFAULT 0,
    featured BOOLEAN DEFAULT 0,
    restricted BOOLEAN DEFAULT 0,
    liquidity REAL DEFAULT 0,
    volume REAL DEFAULT 0,
    volume_24hr REAL DEFAULT 0,
    competitive REAL,
    comment_count INTEGER DEFAULT 0,
    enable_order_book BOOLEAN DEFAULT 0,
    liquidity_clob REAL DEFAULT 0,
    review_status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### `polymarket_markets`

Individual prediction markets within events.

```sql
CREATE TABLE polymarket_markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL UNIQUE,
    event_id TEXT,
    question TEXT NOT NULL,
    condition_id TEXT,
    slug TEXT,
    resolution_source TEXT,
    end_date TEXT,
    start_date TEXT,
    image TEXT,
    icon TEXT,
    description TEXT,
    volume REAL DEFAULT 0,
    volume_24hr REAL DEFAULT 0,
    volume_clob REAL DEFAULT 0,
    liquidity REAL DEFAULT 0,
    liquidity_clob REAL DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    closed BOOLEAN DEFAULT 0,
    archived BOOLEAN DEFAULT 0,
    new BOOLEAN DEFAULT 0,
    featured BOOLEAN DEFAULT 0,
    restricted BOOLEAN DEFAULT 0,
    market_maker_address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES polymarket_events (event_id)
);
```

#### `polymarket_data`

Time-series market data and probability history.

```sql
CREATE TABLE polymarket_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    event_title TEXT,
    event_url TEXT,
    outcome_name TEXT NOT NULL,
    probability REAL,
    volume REAL,
    timestamp TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id),
    UNIQUE(market_id, outcome_name, timestamp)
);
```

#### `polymarket_trades`

Complete trade execution records.

```sql
CREATE TABLE polymarket_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL UNIQUE,
    taker_order_id TEXT,
    market_id TEXT NOT NULL,
    asset_id TEXT,
    side TEXT NOT NULL,
    size TEXT NOT NULL,
    fee_rate_bps TEXT,
    price TEXT NOT NULL,
    status TEXT NOT NULL,
    match_time TEXT NOT NULL,
    last_update TEXT NOT NULL,
    outcome TEXT,
    maker_address TEXT,
    owner TEXT NOT NULL,
    transaction_hash TEXT,
    bucket_index TEXT,
    type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id)
);
```

#### `polymarket_orderbook`

Live order book data for market analysis.

```sql
CREATE TABLE polymarket_orderbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    price REAL NOT NULL,
    size REAL NOT NULL,
    side TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id)
);
```

### Trading System Tables

#### `trading_strategies`

Trading strategy definitions and configurations.

```sql
CREATE TABLE trading_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL UNIQUE,
    strategy_type TEXT NOT NULL,
    description TEXT,
    parameters TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### `agent_execution_logs`

Agent execution tracking and monitoring.

```sql
CREATE TABLE agent_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    strategy_id INTEGER,
    market_id TEXT,
    event_id TEXT,
    execution_timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL,
    status TEXT NOT NULL,
    input_data TEXT,
    output_data TEXT,
    error_message TEXT,
    execution_time_ms INTEGER,
    llm_tokens_used INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id),
    FOREIGN KEY (event_id) REFERENCES polymarket_events (event_id)
);
```

#### `trading_history`

Complete trading history with P&L tracking.

```sql
CREATE TABLE trading_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL UNIQUE,
    strategy_id INTEGER,
    market_id TEXT NOT NULL,
    outcome TEXT,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total_value REAL NOT NULL,
    fee REAL DEFAULT 0,
    pnl REAL,
    status TEXT NOT NULL,
    open_timestamp TEXT NOT NULL,
    close_timestamp TEXT,
    execution_id TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id),
    FOREIGN KEY (execution_id) REFERENCES agent_execution_logs (execution_id)
);
```

#### `portfolio_positions`

Current portfolio positions and unrealized P&L.

```sql
CREATE TABLE portfolio_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    quantity REAL NOT NULL,
    average_price REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL,
    realized_pnl REAL DEFAULT 0,
    status TEXT NOT NULL,
    open_timestamp TEXT NOT NULL,
    close_timestamp TEXT,
    strategy_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id),
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
    UNIQUE(market_id, outcome, status)
);
```

### Backtesting Tables

#### `backtest_configs`

Backtesting configuration presets.

```sql
CREATE TABLE backtest_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT NOT NULL UNIQUE,
    strategy_id INTEGER,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    initial_capital REAL DEFAULT 10000.0,
    commission_per_trade REAL DEFAULT 0.001,
    max_position_size REAL DEFAULT 0.1,
    max_positions INTEGER DEFAULT 10,
    data_frequency TEXT DEFAULT 'H',
    risk_free_rate REAL DEFAULT 0.02,
    enable_parallel BOOLEAN DEFAULT 0,
    parameters TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id)
);
```

#### `backtest_results`

Backtesting performance results.

```sql
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id TEXT NOT NULL UNIQUE,
    config_id INTEGER NOT NULL,
    strategy_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_return REAL NOT NULL,
    annualized_return REAL NOT NULL,
    volatility REAL NOT NULL,
    sharpe_ratio REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    win_rate REAL NOT NULL,
    total_trades INTEGER NOT NULL,
    equity_curve TEXT,
    metrics TEXT,
    execution_time_seconds REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES backtest_configs (id)
);
```

#### `backtest_trades`

Simulated trades from backtesting.

```sql
CREATE TABLE backtest_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id TEXT NOT NULL,
    trade_timestamp TEXT NOT NULL,
    market_id TEXT,
    outcome TEXT,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    pnl REAL,
    status TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (backtest_id) REFERENCES backtest_results (backtest_id),
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id)
);
```

#### `risk_analysis`

Risk metrics and stress test results.

```sql
CREATE TABLE risk_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    confidence_level REAL,
    value_at_risk REAL,
    expected_shortfall REAL,
    maximum_drawdown REAL,
    ulcer_index REAL,
    volatility REAL,
    downside_volatility REAL,
    beta REAL,
    stress_test_results TEXT,
    risk_adjusted_metrics TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (backtest_id) REFERENCES backtest_results (backtest_id)
);
```

### System Tables

#### `data_quality_logs`

Data quality monitoring and validation.

```sql
CREATE TABLE data_quality_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    quality_check TEXT NOT NULL,
    score REAL,
    issues TEXT,
    fixed BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### `system_config`

System configuration settings.

```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT,
    config_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### `api_rate_limits`

API rate limiting tracking.

```sql
CREATE TABLE api_rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    requests_per_hour INTEGER DEFAULT 1000,
    last_request_timestamp TEXT,
    request_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name, endpoint)
);
```

### Relationships

The database schema includes the following key relationships:

- **Weather Data Relationships**:

  - `weather_data.source_id` → `weather_sources.id`
  - `weather_forecasts.source_id` → `weather_sources.id`

- **Polymarket Data Relationships**:

  - `polymarket_markets.event_id` → `polymarket_events.event_id`
  - `polymarket_data.market_id` → `polymarket_markets.market_id`
  - `polymarket_trades.market_id` → `polymarket_markets.market_id`
  - `polymarket_orderbook.market_id` → `polymarket_markets.market_id`

- **Trading System Relationships**:

  - `agent_execution_logs.strategy_id` → `trading_strategies.id`
  - `agent_execution_logs.market_id` → `polymarket_markets.market_id`
  - `agent_execution_logs.event_id` → `polymarket_events.event_id`
  - `trading_history.strategy_id` → `trading_strategies.id`
  - `trading_history.market_id` → `polymarket_markets.market_id`
  - `trading_history.execution_id` → `agent_execution_logs.execution_id`
  - `portfolio_positions.market_id` → `polymarket_markets.market_id`
  - `portfolio_positions.strategy_id` → `trading_strategies.id`

- **Backtesting Relationships**:
  - `backtest_configs.strategy_id` → `trading_strategies.id`
  - `backtest_results.config_id` → `backtest_configs.id`
  - `backtest_trades.backtest_id` → `backtest_results.backtest_id`
  - `backtest_trades.market_id` → `polymarket_markets.market_id`
  - `risk_analysis.backtest_id` → `backtest_results.backtest_id`

## Data Models

### Weather Data Model

```python
@dataclass
class WeatherData:
    id: int
    source_id: int
    location_name: str
    coordinates: Coordinates
    timestamp: datetime
    temperature: Optional[float]
    feels_like: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    wind_speed: Optional[float]
    wind_direction: Optional[float]
    precipitation: Optional[float]
    weather_code: Optional[int]
    weather_description: Optional[str]
    visibility: Optional[float]
    uv_index: Optional[float]
    alerts: Optional[Dict[str, Any]]
    raw_data: Optional[Dict[str, Any]]
    data_quality_score: float
    created_at: datetime
```

### Market Data Model

```python
@dataclass
class MarketData:
    id: int
    market_id: str
    event_title: str
    event_url: Optional[str]
    outcome_name: str
    probability: float
    volume: float
    timestamp: datetime
    scraped_at: datetime
    created_at: datetime
```

## Query Examples

### Weather Data Queries

#### Get Latest Weather for Location

```sql
SELECT wd.*, ws.source_name
FROM weather_data wd
JOIN weather_sources ws ON wd.source_id = ws.id
WHERE wd.location_name = ?
ORDER BY wd.timestamp DESC
LIMIT 1;
```

#### Get Weather History for Date Range

```sql
SELECT *
FROM weather_data
WHERE location_name = ?
  AND timestamp BETWEEN ? AND ?
  AND data_quality_score > 0.8
ORDER BY timestamp;
```

#### Get Average Temperature by Month

```sql
SELECT
    strftime('%Y-%m', timestamp) as month,
    AVG(temperature) as avg_temp,
    MIN(temperature) as min_temp,
    MAX(temperature) as max_temp,
    COUNT(*) as readings
FROM weather_data
WHERE location_name = ?
  AND timestamp >= date('now', '-1 year')
GROUP BY strftime('%Y-%m', timestamp)
ORDER BY month;
```

### Market Data Queries

#### Get Active Markets

```sql
SELECT m.*, e.title as event_title
FROM polymarket_markets m
JOIN polymarket_events e ON m.event_id = e.event_id
WHERE m.active = 1
  AND m.closed = 0
  AND m.end_date > datetime('now')
ORDER BY m.volume DESC;
```

#### Get Market Probability History

```sql
SELECT
    timestamp,
    outcome_name,
    probability,
    volume
FROM polymarket_data
WHERE market_id = ?
ORDER BY timestamp DESC
LIMIT 1000;
```

### Trading Queries

#### Get Portfolio Summary

```sql
SELECT
    pp.market_id,
    pp.outcome,
    pp.quantity,
    pp.average_price,
    pd.probability as current_price,
    (pd.probability - pp.average_price) * pp.quantity as unrealized_pnl,
    pp.realized_pnl
FROM portfolio_positions pp
JOIN polymarket_data pd ON pp.market_id = pd.market_id
    AND pp.outcome = pd.outcome_name
WHERE pp.status = 'open'
ORDER BY ABS((pd.probability - pp.average_price) * pp.quantity) DESC;
```

#### Get Trading Performance by Strategy

```sql
SELECT
    ts.strategy_name,
    COUNT(*) as total_trades,
    SUM(CASE WHEN th.pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    AVG(th.pnl) as avg_pnl,
    SUM(th.pnl) as total_pnl,
    SUM(th.fee) as total_fees,
    MAX(th.pnl) as best_trade,
    MIN(th.pnl) as worst_trade
FROM trading_history th
JOIN trading_strategies ts ON th.strategy_id = ts.id
WHERE th.status = 'closed'
GROUP BY ts.strategy_name
ORDER BY total_pnl DESC;
```

## Performance Optimization

### Indexing Strategy

#### Composite Indexes for Complex Queries

```sql
-- Weather data queries
CREATE INDEX idx_weather_location_time ON weather_data(location_name, timestamp);
CREATE INDEX idx_weather_source_quality ON weather_data(source_id, data_quality_score);

-- Market data queries
CREATE INDEX idx_market_time_prob ON polymarket_data(market_id, timestamp, probability);
CREATE INDEX idx_market_outcome_time ON polymarket_data(outcome_name, timestamp);

-- Trading queries
CREATE INDEX idx_trades_strategy_time ON trading_history(strategy_id, open_timestamp);
CREATE INDEX idx_trades_market_status ON trading_history(market_id, status);
```

#### Partial Indexes for Filtered Data

```sql
-- Active markets only
CREATE INDEX idx_active_markets ON polymarket_markets(market_id, volume)
WHERE active = 1 AND closed = 0;

-- Recent weather data
CREATE INDEX idx_recent_weather ON weather_data(timestamp, location_name)
WHERE timestamp >= datetime('now', '-30 days');

-- Open positions
CREATE INDEX idx_open_positions ON portfolio_positions(market_id, quantity)
WHERE status = 'open';
```

### Query Optimization Techniques

#### Efficient Time-Series Queries

```sql
-- Use date ranges efficiently
SELECT * FROM weather_data
WHERE timestamp BETWEEN '2024-01-01' AND '2024-12-31'
  AND location_name = 'London,UK'
ORDER BY timestamp;

-- Use indexed columns in WHERE clauses
SELECT * FROM polymarket_data
WHERE market_id = ?
  AND timestamp >= ?
ORDER BY timestamp DESC
LIMIT 100;
```

## Backup and Recovery

### SQLite Backup Strategy

#### Full Database Backup

```bash
#!/bin/bash
# backup-sqlite.sh

BACKUP_DIR="/backups/sqlite/$(date +%Y%m%d)"
TIMESTAMP=$(date +%H%M%S)
BACKUP_FILE="$BACKUP_DIR/climatetrade_backup_$TIMESTAMP.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup using sqlite3 .backup command
sqlite3 /data/climatetrade.db ".backup '$BACKUP_FILE'"

# Compress backup
gzip $BACKUP_FILE

# Verify backup
if sqlite3 $BACKUP_FILE ".tables" > /dev/null; then
    echo "✅ Backup successful: $BACKUP_FILE.gz"
else
    echo "❌ Backup verification failed"
    exit 1
fi

# Clean old backups (keep last 30 days)
find /backups/sqlite -name "*.gz" -mtime +30 -delete
```

### Recovery Procedures

#### SQLite Recovery

```bash
#!/bin/bash
# restore-sqlite.sh

BACKUP_FILE=$1
DB_PATH="/data/climatetrade.db"

# Stop application
systemctl stop climatetrade

# Create backup of current database
cp $DB_PATH $DB_PATH.backup.$(date +%Y%m%d_%H%M%S)

# Restore from backup
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE > $DB_PATH
else
    cp $BACKUP_FILE $DB_PATH
fi

# Verify database integrity
if sqlite3 $DB_PATH "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✅ Database integrity check passed"
else
    echo "❌ Database integrity check failed"
    # Restore from backup
    cp $DB_PATH.backup.* $DB_PATH
    exit 1
fi

# Start application
systemctl start climatetrade
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Maintenance

```bash
#!/bin/bash
# daily-maintenance.sh

echo "🧹 Starting daily database maintenance"

# Update table statistics
sqlite3 /data/climatetrade.db "ANALYZE;"

# Clean old log entries (older than 90 days)
sqlite3 /data/climatetrade.db "
DELETE FROM data_quality_logs WHERE created_at < datetime('now', '-90 days');
DELETE FROM agent_execution_logs WHERE execution_timestamp < datetime('now', '-90 days');
"

# Vacuum database to reclaim space
sqlite3 /data/climatetrade.db "VACUUM;"

# Check database integrity
INTEGRITY=$(sqlite3 /data/climatetrade.db "PRAGMA integrity_check;")
if [[ $INTEGRITY == "ok" ]]; then
    echo "✅ Database integrity OK"
else
    echo "❌ Database integrity issues found"
    # Send alert
fi

echo "✅ Daily maintenance completed"
```

## Troubleshooting

### Common Database Issues

#### Connection Issues

```bash
# Test database connection
sqlite3 /data/climatetrade.db ".tables"

# Check file permissions
ls -la /data/climatetrade.db

# Check disk space
df -h /data

# Check database locks
sqlite3 /data/climatetrade.db "SELECT * FROM sqlite_master WHERE type='table';"
```

#### Performance Issues

```sql
-- Check slow queries
SELECT sql, execution_time
FROM query_log
WHERE execution_time > 1000
ORDER BY execution_time DESC
LIMIT 10;

-- Check index usage
EXPLAIN QUERY PLAN
SELECT * FROM weather_data
WHERE location_name = 'London,UK'
  AND timestamp >= '2024-01-01';

-- Check table sizes
SELECT name, sql FROM sqlite_master WHERE type='table';
```

#### Data Corruption

```sql
-- Check database integrity
PRAGMA integrity_check;

-- Check foreign key constraints
PRAGMA foreign_key_check;

-- Rebuild corrupted indexes
REINDEX;
```

### Query Optimization Issues

#### Slow Queries

```sql
-- Analyze query execution
EXPLAIN QUERY PLAN
SELECT * FROM weather_data
WHERE temperature > 25.0
  AND location_name = 'London,UK'
ORDER BY timestamp DESC
LIMIT 100;

-- Check if indexes are being used
EXPLAIN QUERY PLAN
SELECT COUNT(*), AVG(temperature)
FROM weather_data
WHERE location_name = ?
  AND timestamp >= date('now', '-30 days');
```

#### Memory Issues

```sql
-- Check memory usage
PRAGMA cache_size;
PRAGMA temp_store;

-- Optimize memory settings
PRAGMA cache_size = 10000;  -- 10MB cache
PRAGMA temp_store = memory; -- Store temp tables in memory
PRAGMA mmap_size = 268435456; -- 256MB memory map
```

#### Lock Contention

```sql
-- Check for long-running transactions
SELECT * FROM sqlite_master WHERE type='table';

-- Use WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Optimize write performance
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 1000000;
```

## Best Practices

### Database Design Principles

1. **Normalization**: Maintain data integrity through proper normalization
2. **Indexing**: Strategic indexing for query performance
3. **Constraints**: Use foreign keys and check constraints
4. **Data Types**: Choose appropriate data types for storage efficiency
5. **Documentation**: Keep schema documentation current

### Performance Best Practices

1. **Query Optimization**: Use EXPLAIN PLAN to analyze queries
2. **Index Maintenance**: Regular index rebuilds and statistics updates
3. **Connection Pooling**: Reuse database connections efficiently
4. **Batch Operations**: Use bulk inserts/updates for large datasets
5. **Caching**: Implement query result caching where appropriate

### Security Best Practices

1. **Access Control**: Implement proper user permissions
2. **Encryption**: Encrypt sensitive data at rest and in transit
3. **Audit Logging**: Log all database access and changes
4. **Input Validation**: Validate all input data before insertion
5. **Regular Backups**: Maintain secure, tested backup procedures

### Monitoring Best Practices

1. **Performance Metrics**: Monitor query performance and resource usage
2. **Health Checks**: Regular database health and integrity checks
3. **Alerting**: Set up alerts for critical database issues
4. **Capacity Planning**: Monitor database growth and plan for scaling
5. **Log Analysis**: Regular review of database logs for issues

---

**Database Documentation Version**: 1.1
**Last Updated**: September 2025
**Schema Version**: 1.0.0

For additional support, refer to the [Setup & Installation Guide](SETUP_INSTALLATION.md) or contact the development team.