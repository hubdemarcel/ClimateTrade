# ClimateTrade AI Database Setup and Documentation

This directory contains the comprehensive database setup for the ClimateTrade AI project, including schema definitions, initialization scripts, migration management, and maintenance documentation.

## Overview

The database supports:

- **Weather Data**: Multi-source weather data from Met Office, Meteostat, NWS, Weather2Geo
- **Polymarket Data**: Market data, events, trades, and order book information
- **Agent Operations**: Execution logs, trading history, and strategy management
- **Backtesting**: Performance metrics, risk analysis, and simulation results
- **Resolution Data**: Market resolution tracking from subgraph data

## Directory Structure

```
database/
├── schema.sql                 # Complete database schema definition
├── setup_database.py          # Database initialization script
├── README.md                  # This documentation file
└── migrations/                # Database migration system
    ├── __init__.py
    ├── migration_manager.py   # Migration management tool
    └── 20240101_000000_initial_schema.py  # Initial migration
```

## Quick Start

### 1. Initial Database Setup

```bash
# Navigate to the database directory
cd database

# Run the setup script
python setup_database.py

# Or specify a custom database path
python setup_database.py --db-path ../data/climatetrade.db
```

### 2. Apply Migrations

```bash
# Check migration status
python migrations/migration_manager.py status

# Apply all pending migrations
python migrations/migration_manager.py apply

# Apply a specific migration
python migrations/migration_manager.py apply --migration 20240101_000000_initial_schema
```

### 3. Create New Migration

```bash
# Create a new migration template
python migrations/migration_manager.py create --name add_new_feature --description "Add new feature to database"
```

## Database Schema

### Core Tables

#### Weather Data Tables

- **`weather_sources`**: Weather data providers configuration
- **`weather_data`**: Unified weather observations from all sources
- **`weather_forecasts`**: Weather forecast data

#### Polymarket Data Tables

- **`polymarket_events`**: Market events and categories
- **`polymarket_markets`**: Individual prediction markets
- **`polymarket_data`**: Market data and probability history
- **`polymarket_trades`**: Trade execution records
- **`polymarket_orderbook`**: Live order book data

#### Agent and Trading Tables

- **`trading_strategies`**: Trading strategy definitions
- **`agent_execution_logs`**: Agent execution tracking
- **`trading_history`**: Complete trading history
- **`portfolio_positions`**: Current portfolio positions

#### Backtesting Tables

- **`backtest_configs`**: Backtesting configuration presets
- **`backtest_results`**: Backtesting performance results
- **`backtest_trades`**: Simulated trades from backtesting
- **`risk_analysis`**: Risk metrics and stress test results

#### Resolution Subgraph Tables

- **`market_resolutions`**: Market resolution tracking
- **`ancillary_data_mappings`**: Question ID mappings
- **`moderators`**: Moderator permissions
- **`revisions`**: Market revision history

#### System Tables

- **`data_quality_logs`**: Data quality monitoring
- **`system_config`**: System configuration settings
- **`api_rate_limits`**: API rate limiting tracking

## Key Features

### Data Quality Management

- Automatic data quality scoring
- Validation and cleaning pipelines
- Quality monitoring and alerting

### Performance Optimization

- Comprehensive indexing strategy
- Optimized for time-series queries
- Efficient foreign key relationships

### Migration System

- Version-controlled schema changes
- Rollback capabilities
- Migration dependency management

### Multi-Source Support

- Unified data models across sources
- Source-specific metadata tracking
- Flexible data ingestion pipelines

## Usage Examples

### Python Database Connection

```python
import sqlite3
from pathlib import Path

# Connect to database
db_path = Path("data/climatetrade.db")
conn = sqlite3.connect(db_path)

# Query weather data
cursor = conn.cursor()
cursor.execute("""
    SELECT location_name, temperature, timestamp
    FROM weather_data
    WHERE source_id = (SELECT id FROM weather_sources WHERE source_name = 'met_office')
    ORDER BY timestamp DESC
    LIMIT 10
""")

results = cursor.fetchall()
for row in results:
    print(f"{row[0]}: {row[1]}°C at {row[2]}")
```

### Working with Migrations

```python
from database.migrations.migration_manager import MigrationManager

# Initialize migration manager
manager = MigrationManager("data/climatetrade.db")

# Check status
status = manager.get_migration_status()
print(f"Applied: {status['total_applied']}, Pending: {status['total_pending']}")

# Apply pending migrations
manager.apply_pending_migrations()
```

## Maintenance Tasks

### Regular Maintenance

1. **Data Cleanup**:

   ```sql
   -- Remove old data (older than 1 year)
   DELETE FROM weather_data WHERE timestamp < datetime('now', '-1 year');
   DELETE FROM polymarket_data WHERE timestamp < datetime('now', '-1 year');
   ```

2. **Index Optimization**:

   ```sql
   -- Rebuild indexes for better performance
   REINDEX;
   ```

3. **Vacuum Database**:
   ```sql
   -- Reclaim space and optimize database
   VACUUM;
   ```

### Backup and Recovery

```bash
# Create backup
python setup_database.py --backup backup_20241201.db

# Restore from backup
cp backup_20241201.db data/climatetrade.db
```

### Monitoring

```python
# Check database health
setup = DatabaseSetup("data/climatetrade.db")
info = setup.get_database_info()
print(f"Tables: {info['table_count']}")
print(f"Records: {info['total_records']}")
print(f"Size: {info['database_size_mb']} MB")
```

## Configuration

### System Configuration

The database includes a configuration system for runtime settings:

```sql
-- View current configuration
SELECT config_key, config_value, description FROM system_config;

-- Update configuration
UPDATE system_config SET config_value = '2' WHERE config_key = 'max_parallel_backtests';
```

### Default Configuration Values

- `database_version`: Current schema version
- `data_retention_days`: Days to keep historical data (default: 365)
- `max_parallel_backtests`: Maximum parallel backtest executions (default: 4)
- `default_risk_free_rate`: Risk-free rate for calculations (default: 0.02)
- `enable_data_quality_checks`: Enable data quality validation (default: true)

## Troubleshooting

### Common Issues

1. **Migration Failures**:

   ```bash
   # Check migration status
   python migrations/migration_manager.py status

   # Rollback problematic migration
   python migrations/migration_manager.py rollback --migration migration_name
   ```

2. **Database Corruption**:

   ```bash
   # Restore from backup
   cp backup_file.db data/climatetrade.db

   # Re-run setup
   python setup_database.py --force-recreate
   ```

3. **Performance Issues**:

   ```sql
   -- Analyze query performance
   EXPLAIN QUERY PLAN SELECT * FROM weather_data WHERE timestamp > '2024-01-01';

   -- Check index usage
   SELECT * FROM sqlite_master WHERE type = 'index';
   ```

### Data Integrity Checks

```python
# Validate data integrity
def validate_data_integrity(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check foreign key constraints
    cursor.execute("PRAGMA foreign_key_check;")

    # Check for orphaned records
    cursor.execute("""
        SELECT COUNT(*) FROM weather_data
        WHERE source_id NOT IN (SELECT id FROM weather_sources);
    """)

    conn.close()
```

## API Reference

### DatabaseSetup Class

- `__init__(db_path)`: Initialize setup manager
- `setup_database(force_recreate)`: Create or recreate database
- `get_database_info()`: Get database statistics
- `backup_database(backup_path)`: Create database backup

### MigrationManager Class

- `__init__(db_path)`: Initialize migration manager
- `apply_pending_migrations()`: Apply all pending migrations
- `apply_migration(name)`: Apply specific migration
- `rollback_migration(name)`: Rollback specific migration
- `get_migration_status()`: Get migration status information

## Contributing

When making schema changes:

1. Create a new migration file
2. Test the migration on a copy of production data
3. Update this documentation
4. Commit migration and documentation together

## Version History

- **v1.0.0**: Initial comprehensive schema
  - Weather data integration
  - Polymarket data structures
  - Agent execution tracking
  - Backtesting framework
  - Migration system

## Support

For database-related issues:

1. Check the troubleshooting section
2. Review migration status
3. Validate data integrity
4. Check system logs

## License

This database schema and associated code are part of the ClimateTrade AI project.
