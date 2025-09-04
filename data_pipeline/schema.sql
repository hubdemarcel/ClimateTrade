-- ClimateTrade Data Pipeline Schema
-- SQLite database for storing Polymarket and weather data

-- Polymarket market data table
CREATE TABLE IF NOT EXISTS polymarket_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_title TEXT NOT NULL,
    event_url TEXT,
    market_id TEXT NOT NULL,
    outcome_name TEXT NOT NULL,
    probability REAL,
    volume REAL,
    timestamp TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market_id, outcome_name, timestamp)
);

-- Weather sources table
CREATE TABLE IF NOT EXISTS weather_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    description TEXT,
    api_endpoint TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Unified weather data table
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
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES weather_sources (id),
    UNIQUE(source_id, location_name, timestamp)
);

-- Insert default weather sources
INSERT OR IGNORE INTO weather_sources (source_name, description, api_endpoint) VALUES
('met_office', 'UK Met Office Weather DataHub', 'https://data.hub.api.metoffice.gov.uk'),
('meteostat', 'Meteostat Historical Weather Data', 'https://dev.meteostat.net'),
('nws', 'US National Weather Service', 'https://api.weather.gov'),
('weather_underground', 'Weather Underground API', 'https://api.weather.com');

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_polymarket_timestamp ON polymarket_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_polymarket_market_id ON polymarket_data(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data(location_name);
CREATE INDEX IF NOT EXISTS idx_weather_source_timestamp ON weather_data(source_id, timestamp);