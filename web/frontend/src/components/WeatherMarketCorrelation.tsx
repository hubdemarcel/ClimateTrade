import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import './WeatherMarketCorrelation.css';

interface WeatherDataPoint {
  timestamp: string;
  temperature: number;
  feels_like: number;
  humidity: number;
  precipitation: number;
  weather_description: string;
  data_type: string;
}

interface MarketDataPoint {
  timestamp: string;
  price: number;
  volume: number;
  outcome: string;
}

interface CorrelationData {
  weather: {
    city: string;
    timeline: WeatherDataPoint[];
    summary: {
      temperature_avg: number;
      temperature_min: number;
      temperature_max: number;
      total_precipitation: number;
    };
  };
  market?: {
    market_id: string;
    question: string;
    timeline: MarketDataPoint[];
  };
}

const WeatherMarketCorrelation: React.FC = () => {
  const [selectedCity, setSelectedCity] = useState<'London,UK' | 'New York,NY'>('London,UK');
  const [correlationData, setCorrelationData] = useState<CorrelationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'combined' | 'weather' | 'market'>('combined');

  useEffect(() => {
    fetchWeatherData();
  }, [selectedCity]);

  const fetchWeatherData = async () => {
    console.log(`Fetching weather data for: ${selectedCity}`);
    try {
      setLoading(true);
      // FIX: Use the documented endpoint `/api/weather/data` with query parameters.
      // This also requires processing the raw data to calculate the summary.
      const encodedCity = encodeURIComponent(selectedCity);
      const response = await fetch(`/api/weather/data?hours=24&location=${encodedCity}`);
      console.log(`API response status for ${selectedCity}: ${response.status}`);
      if (response.ok) {
        const rawData: any[] = await response.json();
        // Deep copy for logging to avoid showing mutated data
        console.log(`Received raw data for ${selectedCity}:`, JSON.parse(JSON.stringify(rawData)));

        // Normalize data to handle inconsistencies from different sources (e.g., Met Office, WU)
        const timelineData: WeatherDataPoint[] = rawData.map(p => ({
          timestamp: p.timestamp,
          temperature: typeof p.temperature === 'number' ? p.temperature : (null as any),
          feels_like: typeof p.feels_like === 'number' ? p.feels_like : (null as any),
          humidity: typeof p.humidity === 'number' ? p.humidity : (null as any),
          // Handle alternative keys like 'precipitation_1h' from Weather Underground
          precipitation: typeof p.precipitation === 'number' ? p.precipitation : 
                         (typeof p.precipitation_1h === 'number' ? p.precipitation_1h : (null as any)),
          weather_description: p.weather_description || p.condition || p.weather_type || 'N/A',
          // These fields might not be present in all sources, provide defaults
          data_type: p.data_type || 'observation',
        })).filter(p => p.timestamp); // Ensure entry has a timestamp

        console.log(`Normalized data for ${selectedCity}:`, timelineData);

        if (timelineData && timelineData.length > 0) {
          // Manually calculate summary stats as the API returns a flat array
          // Use a more robust filter to ensure we only process valid numbers
          const temperatures = timelineData.map(p => p.temperature).filter((t): t is number => typeof t === 'number' && !isNaN(t));
          const precipitations = timelineData.map(p => p.precipitation).filter((p): p is number => typeof p === 'number' && !isNaN(p));

          const summary = {
            temperature_avg: temperatures.length > 0 ? temperatures.reduce((a, b) => a + b, 0) / temperatures.length : 0,
            temperature_min: temperatures.length > 0 ? Math.min(...temperatures) : 0,
            temperature_max: temperatures.length > 0 ? Math.max(...temperatures) : 0,
            total_precipitation: precipitations.reduce((a, b) => a + b, 0),
          };

          setCorrelationData({
            weather: {
              city: selectedCity,
              timeline: timelineData,
              summary: summary,
            },
          });
        } else {
          console.log(`No weather data returned for ${selectedCity}`);
          setCorrelationData(null);
        }
      } else {
        console.error(`Failed to fetch weather data for ${selectedCity}. Status: ${response.status}`);
        setCorrelationData(null);
      }
    } catch (error) {
      console.error('Error fetching weather data:', error);
      setCorrelationData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatChartData = () => {
    if (!correlationData?.weather?.timeline) return [];

    return correlationData.weather.timeline.map((point, index) => ({
      time: new Date(point.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }),
      temperature: point.temperature,
      feels_like: point.feels_like,
      humidity: point.humidity,
      precipitation: point.precipitation,
      weather: point.weather_description,
      hour: index
    }));
  };

  const getTemperatureStats = () => {
    if (!correlationData?.weather?.summary) return null;

    const { temperature_avg, temperature_min, temperature_max, total_precipitation } =
      correlationData.weather.summary;

    return { temperature_avg, temperature_min, temperature_max, total_precipitation };
  };

  const chartData = formatChartData();
  const stats = getTemperatureStats();

  return (
    <div className="weather-market-correlation">
      <div className="correlation-header">
        <h1>🌦️ Weather & Market Correlation Analysis</h1>
        <p>24-hour weather data with market prediction correlation</p>
      </div>

      {/* City Selection */}
      <div className="city-selector">
        <h3>Select City:</h3>
        <div className="city-buttons">
          <button
            className={`city-btn ${selectedCity === 'London,UK' ? 'active' : ''}`}
            onClick={() => setSelectedCity('London,UK')}
          >
            🇬🇧 London, UK
          </button>
          <button
            className={`city-btn ${selectedCity === 'New York,NY' ? 'active' : ''}`}
            onClick={() => setSelectedCity('New York,NY')}
          >
            🇺🇸 New York
          </button>
        </div>
      </div>

      {/* View Mode Selector */}
      <div className="view-selector">
        <h3>View Mode:</h3>
        <div className="view-buttons">
          <button
            className={`view-btn ${viewMode === 'combined' ? 'active' : ''}`}
            onClick={() => setViewMode('combined')}
          >
            📊 Combined View
          </button>
          <button
            className={`view-btn ${viewMode === 'weather' ? 'active' : ''}`}
            onClick={() => setViewMode('weather')}
          >
            🌡️ Weather Only
          </button>
          <button
            className={`view-btn ${viewMode === 'market' ? 'active' : ''}`}
            onClick={() => setViewMode('market')}
          >
            📈 Market Only
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading 24-hour weather data...</p>
        </div>
      )}

      {!loading && !correlationData && (
        <div className="no-data-message" style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
          <h3>No Data Available</h3>
          <p>Could not load weather data for {selectedCity}.</p>
          <p>Please ensure the backend is running and the API is responsive.</p>
        </div>
      )}

      {correlationData && !loading && (
        <>
          {/* Weather Summary Cards */}
          <div className="summary-cards">
            <div className="summary-card">
              <h4>🌡️ Temperature</h4>
              <div className="metric">
                <span className="value">{stats?.temperature_avg?.toFixed(1)}°F</span>
                <span className="label">Average</span>
              </div>
              <div className="range">
                <span>Min: {stats?.temperature_min?.toFixed(1)}°F</span>
                <span>Max: {stats?.temperature_max?.toFixed(1)}°F</span>
              </div>
            </div>

            <div className="summary-card">
              <h4>🌧️ Precipitation</h4>
              <div className="metric">
                <span className="value">{stats?.total_precipitation?.toFixed(1)}mm</span>
                <span className="label">24h Total</span>
              </div>
            </div>

            <div className="summary-card">
              <h4>💨 Conditions</h4>
              <div className="conditions">
                {Array.from(new Set(chartData.map(d => d.weather))).map(condition => (
                  <span key={condition} className="condition-tag">
                    {condition}
                  </span>
                ))}
              </div>
            </div>

            <div className="summary-card">
              <h4>📊 Data Points</h4>
              <div className="metric">
                <span className="value">{chartData.length}</span>
                <span className="label">Hours</span>
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="charts-container">
            {(viewMode === 'combined' || viewMode === 'weather') && (
              <div className="chart-section">
                <h3>🌡️ Temperature & Humidity (24 Hours)</h3>
                <div className="chart-wrapper">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="time"
                        interval="preserveStartEnd"
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis yAxisId="temp" orientation="left" />
                      <YAxis yAxisId="humidity" orientation="right" />
                      <Tooltip
                        labelFormatter={(label) => `Time: ${label}`}
                        formatter={(value: any, name: string) => [
                          `${value}${name === 'humidity' ? '%' : '°F'}`,
                          name === 'temperature' ? 'Temperature' :
                          name === 'feels_like' ? 'Feels Like' : 'Humidity'
                        ]}
                      />
                      <Legend />
                      <Line
                        yAxisId="temp"
                        type="monotone"
                        dataKey="temperature"
                        stroke="#ff7300"
                        strokeWidth={2}
                        name="temperature"
                      />
                      <Line
                        yAxisId="temp"
                        type="monotone"
                        dataKey="feels_like"
                        stroke="#ff0000"
                        strokeWidth={1}
                        strokeDasharray="5 5"
                        name="feels_like"
                      />
                      <Line
                        yAxisId="humidity"
                        type="monotone"
                        dataKey="humidity"
                        stroke="#0088fe"
                        strokeWidth={2}
                        name="humidity"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {(viewMode === 'combined' || viewMode === 'weather') && (
              <div className="chart-section">
                <h3>🌧️ Precipitation (24 Hours)</h3>
                <div className="chart-wrapper">
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="time"
                        interval="preserveStartEnd"
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis />
                      <Tooltip
                        labelFormatter={(label) => `Time: ${label}`}
                        formatter={(value: any) => [`${value}mm`, 'Precipitation']}
                      />
                      <Bar dataKey="precipitation" fill="#00ff88" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          {/* Weather Timeline Table */}
          <div className="timeline-section">
            <h3>📅 24-Hour Weather Timeline</h3>
            <div className="timeline-table">
              <div className="table-header">
                <span>Time</span>
                <span>Temperature</span>
                <span>Feels Like</span>
                <span>Humidity</span>
                <span>Precipitation</span>
                <span>Conditions</span>
              </div>
              {chartData.slice(0, 12).map((point, index) => (
                <div key={index} className="table-row">
                  <span className="time">{point.time}</span>
                  <span className="temp">{point.temperature?.toFixed(1)}°F</span>
                  <span className="feels">{point.feels_like?.toFixed(1)}°F</span>
                  <span className="humidity">{point.humidity}%</span>
                  <span className="precip">{point.precipitation?.toFixed(1)}mm</span>
                  <span className="weather">{point.weather}</span>
                </div>
              ))}
            </div>
            {chartData.length > 12 && (
              <p className="more-data">... and {chartData.length - 12} more hours</p>
            )}
          </div>
        </>
      )}

      {/* Market Correlation Section (Future Enhancement) */}
      <div className="correlation-insights">
        <h3>🔍 Market Correlation Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>📈 Market Efficiency</h4>
            <p>Compare weather predictions vs actual outcomes</p>
            <span className="coming-soon">Coming Soon</span>
          </div>
          <div className="insight-card">
            <h4>🎯 Prediction Accuracy</h4>
            <p>Track how well markets forecast weather</p>
            <span className="coming-soon">Coming Soon</span>
          </div>
          <div className="insight-card">
            <h4>⚡ Real-time Alerts</h4>
            <p>Get notified of significant weather changes</p>
            <span className="coming-soon">Coming Soon</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherMarketCorrelation;