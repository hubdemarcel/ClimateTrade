-- ClimateTrade AI Database Schema
-- Comprehensive schema for storing weather data, Polymarket data,
-- agent execution logs, trading history, backtesting results, and resolution data

-- ===========================================
-- WEATHER DATA TABLES
-- ===========================================

-- Weather sources table (existing, enhanced)
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

-- Unified weather data table (existing, enhanced)
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
    alerts TEXT, -- JSON string for weather alerts
    raw_data TEXT, -- JSON string for source-specific data
    data_quality_score REAL DEFAULT 1.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES weather_sources (id),
    UNIQUE(source_id, location_name, timestamp)
);

-- Weather forecast data
CREATE TABLE IF NOT EXISTS weather_forecasts (
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

-- ===========================================
-- POLYMARKET DATA TABLES
-- ===========================================

-- Polymarket events
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

-- Polymarket markets
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

-- Polymarket market data (existing, enhanced)
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

-- Polymarket trades
CREATE TABLE IF NOT EXISTS polymarket_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL UNIQUE,
    taker_order_id TEXT,
    market_id TEXT NOT NULL,
    asset_id TEXT,
    side TEXT NOT NULL, -- 'buy' or 'sell'
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

-- Polymarket order book
CREATE TABLE IF NOT EXISTS polymarket_orderbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    price REAL NOT NULL,
    size REAL NOT NULL,
    side TEXT NOT NULL, -- 'buy' or 'sell'
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id)
);

-- ===========================================
-- AGENT AND TRADING TABLES
-- ===========================================

-- Trading strategies
CREATE TABLE IF NOT EXISTS trading_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL UNIQUE,
    strategy_type TEXT NOT NULL, -- 'weather_based', 'arbitrage', 'momentum', etc.
    description TEXT,
    parameters TEXT, -- JSON string of strategy parameters
    active BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Agent execution logs
CREATE TABLE IF NOT EXISTS agent_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    strategy_id INTEGER,
    market_id TEXT,
    event_id TEXT,
    execution_timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'analyze', 'trade', 'monitor', etc.
    status TEXT NOT NULL, -- 'success', 'failed', 'pending'
    input_data TEXT, -- JSON string of input data
    output_data TEXT, -- JSON string of output data
    error_message TEXT,
    execution_time_ms INTEGER,
    llm_tokens_used INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id),
    FOREIGN KEY (event_id) REFERENCES polymarket_events (event_id)
);

-- Trading history
CREATE TABLE IF NOT EXISTS trading_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL UNIQUE,
    strategy_id INTEGER,
    market_id TEXT NOT NULL,
    outcome TEXT,
    side TEXT NOT NULL, -- 'buy', 'sell'
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total_value REAL NOT NULL,
    fee REAL DEFAULT 0,
    pnl REAL,
    status TEXT NOT NULL, -- 'open', 'closed', 'cancelled'
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

-- Portfolio positions
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    quantity REAL NOT NULL,
    average_price REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL,
    realized_pnl REAL DEFAULT 0,
    status TEXT NOT NULL, -- 'open', 'closed'
    open_timestamp TEXT NOT NULL,
    close_timestamp TEXT,
    strategy_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES polymarket_markets (market_id),
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
    UNIQUE(market_id, outcome, status)
);

-- ===========================================
-- BACKTESTING TABLES
-- ===========================================

-- Backtesting configurations
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
    parameters TEXT, -- JSON string of additional parameters
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id)
);

-- Backtesting results
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
    equity_curve TEXT, -- JSON string of equity curve data
    metrics TEXT, -- JSON string of additional metrics
    execution_time_seconds REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES backtest_configs (id)
);

-- Backtesting trades
CREATE TABLE IF NOT EXISTS backtest_trades (
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

-- Risk analysis results
CREATE TABLE IF NOT EXISTS risk_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL, -- 'var', 'cvar', 'stress_test', etc.
    confidence_level REAL,
    value_at_risk REAL,
    expected_shortfall REAL,
    maximum_drawdown REAL,
    ulcer_index REAL,
    volatility REAL,
    downside_volatility REAL,
    beta REAL,
    stress_test_results TEXT, -- JSON string of stress test results
    risk_adjusted_metrics TEXT, -- JSON string of risk-adjusted metrics
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (backtest_id) REFERENCES backtest_results (backtest_id)
);

-- ===========================================
-- RESOLUTION SUBGRAPH TABLES
-- ===========================================

-- Market resolutions
CREATE TABLE IF NOT EXISTS market_resolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL UNIQUE,
    new_version_q BOOLEAN NOT NULL,
    author TEXT NOT NULL,
    ancillary_data TEXT,
    last_update_timestamp INTEGER NOT NULL,
    status TEXT NOT NULL, -- 'initialized', 'posed', 'proposed', 'challenged', 'reproposed', 'disputed', 'resolved'
    was_disputed BOOLEAN NOT NULL,
    proposed_price INTEGER NOT NULL,
    reproposed_price INTEGER NOT NULL,
    price INTEGER NOT NULL,
    updates TEXT NOT NULL,
    transaction_hash TEXT,
    log_index INTEGER,
    approved BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Ancillary data hash to question ID mapping
CREATE TABLE IF NOT EXISTS ancillary_data_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ancillary_data_hash TEXT NOT NULL UNIQUE,
    question_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES market_resolutions (question_id)
);

-- Moderators
CREATE TABLE IF NOT EXISTS moderators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moderator_address TEXT NOT NULL UNIQUE,
    can_mod BOOLEAN NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Revisions
CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    revision_id TEXT NOT NULL UNIQUE,
    moderator_address TEXT NOT NULL,
    question_id TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    update_text TEXT NOT NULL,
    transaction_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (moderator_address) REFERENCES moderators (moderator_address),
    FOREIGN KEY (question_id) REFERENCES market_resolutions (question_id)
);

-- ===========================================
-- SYSTEM TABLES
-- ===========================================

-- Data quality logs
CREATE TABLE IF NOT EXISTS data_quality_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    quality_check TEXT NOT NULL,
    score REAL,
    issues TEXT, -- JSON string of issues found
    fixed BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- System configuration
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT,
    config_type TEXT DEFAULT 'string', -- 'string', 'number', 'boolean', 'json'
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- API rate limiting
CREATE TABLE IF NOT EXISTS api_rate_limits (
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

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

-- Weather data indexes
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data(location_name);
CREATE INDEX IF NOT EXISTS idx_weather_source_timestamp ON weather_data(source_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_timestamp ON weather_forecasts(forecast_timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_for ON weather_forecasts(forecast_for_timestamp);

-- Polymarket indexes
CREATE INDEX IF NOT EXISTS idx_polymarket_timestamp ON polymarket_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_polymarket_market_id ON polymarket_data(market_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_event_id ON polymarket_events(event_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_market_market_id ON polymarket_markets(market_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_trades_market ON polymarket_trades(market_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_trades_timestamp ON polymarket_trades(match_time);
CREATE INDEX IF NOT EXISTS idx_polymarket_orderbook_market ON polymarket_orderbook(market_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_orderbook_timestamp ON polymarket_orderbook(timestamp);

-- Agent and trading indexes
CREATE INDEX IF NOT EXISTS idx_agent_execution_timestamp ON agent_execution_logs(execution_timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_execution_strategy ON agent_execution_logs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trading_history_market ON trading_history(market_id);
CREATE INDEX IF NOT EXISTS idx_trading_history_timestamp ON trading_history(open_timestamp);
CREATE INDEX IF NOT EXISTS idx_trading_history_strategy ON trading_history(strategy_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_market ON portfolio_positions(market_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_status ON portfolio_positions(status);

-- Backtesting indexes
CREATE INDEX IF NOT EXISTS idx_backtest_results_config ON backtest_results(config_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_date ON backtest_results(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_backtest ON backtest_trades(backtest_id);
CREATE INDEX IF NOT EXISTS idx_risk_analysis_backtest ON risk_analysis(backtest_id);

-- Resolution subgraph indexes
CREATE INDEX IF NOT EXISTS idx_market_resolutions_question ON market_resolutions(question_id);
CREATE INDEX IF NOT EXISTS idx_market_resolutions_status ON market_resolutions(status);
CREATE INDEX IF NOT EXISTS idx_market_resolutions_timestamp ON market_resolutions(last_update_timestamp);
CREATE INDEX IF NOT EXISTS idx_revisions_question ON revisions(question_id);
CREATE INDEX IF NOT EXISTS idx_revisions_moderator ON revisions(moderator_address);

-- System indexes
CREATE INDEX IF NOT EXISTS idx_data_quality_table ON data_quality_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_data_quality_created ON data_quality_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_rate_limits_source ON api_rate_limits(source_name);

-- ===========================================
-- DEFAULT DATA INSERTION
-- ===========================================

-- Insert default weather sources
INSERT OR IGNORE INTO weather_sources (source_name, description, api_endpoint, api_key_required, rate_limit_per_hour) VALUES
('met_office', 'UK Met Office Weather DataHub', 'https://data.hub.api.metoffice.gov.uk', 1, 1000),
('meteostat', 'Meteostat Historical Weather Data', 'https://dev.meteostat.net', 1, 2000),
('nws', 'US National Weather Service', 'https://api.weather.gov', 0, 1000),
('weather_underground', 'Weather Underground API', 'https://api.weather.com', 1, 500),
('weather2geo', 'Weather2Geo API', 'https://api.weather2geo.com', 1, 1000);

-- Insert default system configuration
INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description) VALUES
('database_version', '1.0.0', 'string', 'Current database schema version'),
('data_retention_days', '365', 'number', 'Number of days to retain historical data'),
('max_parallel_backtests', '4', 'number', 'Maximum number of parallel backtest executions'),
('default_risk_free_rate', '0.02', 'number', 'Default risk-free rate for calculations'),
('enable_data_quality_checks', 'true', 'boolean', 'Enable automatic data quality validation');

-- Insert default trading strategies
INSERT OR IGNORE INTO trading_strategies (strategy_name, strategy_type, description, parameters) VALUES
('weather_arbitrage', 'weather_based', 'Arbitrage between weather predictions and market prices', '{"weather_weight": 0.7, "market_weight": 0.3}'),
('momentum_trading', 'momentum', 'Momentum-based trading strategy', '{"lookback_period": 24, "threshold": 0.05}'),
('mean_reversion', 'mean_reversion', 'Mean reversion trading strategy', '{"reversion_threshold": 0.1, "holding_period": 12}');