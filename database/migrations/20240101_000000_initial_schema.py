"""
Migration: 20240101_000000_initial_schema
Description: Initial comprehensive database schema for ClimateTrade AI
Version: 1.0.0
"""

def upgrade(cursor):
    """
    Upgrade function - apply the initial schema

    Args:
        cursor: SQLite cursor object
    """
    # Weather sources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_sources (
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
    """)

    # Weather data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
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
    """)

    # Polymarket events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polymarket_events (
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
    """)

    # Polymarket markets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polymarket_markets (
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
    """)

    # Polymarket data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polymarket_data (
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
    """)

    # Trading strategies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_name TEXT NOT NULL UNIQUE,
            strategy_type TEXT NOT NULL,
            description TEXT,
            parameters TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Agent execution logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_execution_logs (
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
    """)

    # Trading history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_history (
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
    """)

    # Backtesting configurations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backtest_configs (
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
    """)

    # Backtesting results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
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
    """)

    # System configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT NOT NULL UNIQUE,
            config_value TEXT,
            config_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Insert default data
    _insert_default_data(cursor)


def downgrade(cursor):
    """
    Downgrade function - rollback the initial schema

    Args:
        cursor: SQLite cursor object
    """
    # Drop tables in reverse order (respecting foreign keys)
    tables_to_drop = [
        'trading_history',
        'agent_execution_logs',
        'backtest_results',
        'trading_strategies',
        'polymarket_data',
        'polymarket_markets',
        'polymarket_events',
        'weather_data',
        'weather_sources',
        'system_config'
    ]

    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
        except Exception as e:
            print(f"Warning: Could not drop table {table}: {e}")


def _insert_default_data(cursor):
    """Insert default data for initial setup"""
    # Weather sources
    cursor.execute("""
        INSERT OR IGNORE INTO weather_sources (source_name, description, api_endpoint, api_key_required, rate_limit_per_hour)
        VALUES
        ('met_office', 'UK Met Office Weather DataHub', 'https://data.hub.api.metoffice.gov.uk', 1, 1000),
        ('meteostat', 'Meteostat Historical Weather Data', 'https://dev.meteostat.net', 1, 2000),
        ('nws', 'US National Weather Service', 'https://api.weather.gov', 0, 1000),
        ('weather_underground', 'Weather Underground API', 'https://api.weather.com', 1, 500),
        ('weather2geo', 'Weather2Geo API', 'https://api.weather2geo.com', 1, 1000);
    """)

    # System configuration
    cursor.execute("""
        INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description)
        VALUES
        ('database_version', '1.0.0', 'string', 'Current database schema version'),
        ('data_retention_days', '365', 'number', 'Number of days to retain historical data'),
        ('max_parallel_backtests', '4', 'number', 'Maximum number of parallel backtest executions'),
        ('default_risk_free_rate', '0.02', 'number', 'Default risk-free rate for calculations'),
        ('enable_data_quality_checks', 'true', 'boolean', 'Enable automatic data quality validation');
    """)

    # Trading strategies
    cursor.execute("""
        INSERT OR IGNORE INTO trading_strategies (strategy_name, strategy_type, description, parameters)
        VALUES
        ('weather_arbitrage', 'weather_based', 'Arbitrage between weather predictions and market prices', '{"weather_weight": 0.7, "market_weight": 0.3}'),
        ('momentum_trading', 'momentum', 'Momentum-based trading strategy', '{"lookback_period": 24, "threshold": 0.05}'),
        ('mean_reversion', 'mean_reversion', 'Mean reversion trading strategy', '{"reversion_threshold": 0.1, "holding_period": 12}');
    """)