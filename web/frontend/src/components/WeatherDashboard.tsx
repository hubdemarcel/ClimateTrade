import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Cloud, Thermometer, Droplets, Wind, AlertTriangle } from 'lucide-react';
import axios from 'axios';

interface WeatherData {
  timestamp: string;
  location: string;
  source: string;
  temperature: number;
  humidity: number;
  precipitation: number;
  wind_speed: number;
  description: string;
  data_quality_score?: number;
}

interface SourceInfo {
  id: number;
  name: string;
  description: string;
  requires_key: boolean;
  active: boolean;
}

interface WeatherDashboardProps {
  refreshTrigger: Date;
}

const WeatherDashboard: React.FC<WeatherDashboardProps> = ({ refreshTrigger }) => {
  const [weatherData, setWeatherData] = useState<WeatherData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [locations, setLocations] = useState<string[]>([]);
  const [activeSources, setActiveSources] = useState<string[]>([]);
  const [availableSources, setAvailableSources] = useState<SourceInfo[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [showSourceFilter, setShowSourceFilter] = useState(false);

  // Helper function to render values with missing data indicators
  const renderValue = (value: number | undefined | null, unit: string, decimals: number = 1) => {
    if (value === undefined || value === null || isNaN(value)) {
      return (
        <div className="flex items-center space-x-1">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          <span className="text-gray-400 text-sm">No data</span>
        </div>
      );
    }
    return <span>{value.toFixed(decimals)}{unit}</span>;
  };

  // Helper function to round minutes to nearest 5-minute interval
  const roundToNearest5Minutes = (date: Date): Date => {
    const minutes = date.getMinutes();
    const roundedMinutes = Math.round(minutes / 5) * 5;
    const newDate = new Date(date);
    newDate.setMinutes(roundedMinutes, 0, 0); // Set seconds and milliseconds to 0
    return newDate;
  };

  useEffect(() => {
    fetchWeatherData();
  }, [refreshTrigger]);

  const fetchSources = async () => {
    try {
      const response = await axios.get('/api/weather/sources');
      setAvailableSources(response.data);
      // Auto-select all active sources
      const activeSourceNames = response.data.filter((s: SourceInfo) => s.active).map((s: SourceInfo) => s.name);
      setSelectedSources(activeSourceNames);
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    }
  };

  const fetchWeatherData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/weather/data?hours=24');
      setWeatherData(response.data);

      // Extract unique locations
      const uniqueLocations = [...new Set(response.data.map((item: WeatherData) => item.location))].filter((loc): loc is string => loc !== null && loc !== undefined);
      setLocations(uniqueLocations);
      if (uniqueLocations.length > 0 && !selectedLocation) {
        setSelectedLocation(uniqueLocations[0]);
      }

      // Extract active sources
      const uniqueSources = [...new Set(response.data.map((item: WeatherData) => item.source))].filter((src): src is string => src !== null && src !== undefined);
      setActiveSources(uniqueSources);
    } catch (error) {
      console.error('Failed to fetch weather data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, [refreshTrigger]);

  const toggleSource = (sourceName: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceName)
        ? prev.filter(s => s !== sourceName)
        : [...prev, sourceName]
    );
  };

  const filteredData = weatherData.filter(item => {
    const locationMatch = !selectedLocation || item.location === selectedLocation;
    const sourceMatch = selectedSources.length === 0 || selectedSources.includes(item.source);
    return locationMatch && sourceMatch;
  });

  // Data for humidity and precipitation chart
  const chartData = filteredData
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(item => ({
      time: new Date(item.timestamp).toLocaleTimeString(),
      temperature: item.temperature,
      humidity: item.humidity,
      precipitation: item.precipitation,
      windSpeed: item.wind_speed,
    }));

  // Filter for current day temperature data
  const today = new Date().toDateString();
  const todayData = filteredData.filter(item => new Date(item.timestamp).toDateString() === today);

  // Group temperature data by time and source for comparison (5-minute intervals)
  const timeMap: { [time: string]: { [source: string]: number[] } } = {};
  todayData.forEach(item => {
    const roundedDate = roundToNearest5Minutes(new Date(item.timestamp));
    const time = roundedDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (!timeMap[time]) timeMap[time] = {};
    if (!timeMap[time][item.source]) timeMap[time][item.source] = [];
    timeMap[time][item.source].push(item.temperature);
  });

  // Average temperatures for each source in each time interval
  const averagedTimeMap: { [time: string]: { [source: string]: number } } = {};
  Object.keys(timeMap).forEach(time => {
    averagedTimeMap[time] = {};
    Object.keys(timeMap[time]).forEach(source => {
      const temps = timeMap[time][source];
      const avg = temps.reduce((sum, temp) => sum + temp, 0) / temps.length;
      averagedTimeMap[time][source] = avg;
    });
  });

  const tempChartData = Object.keys(averagedTimeMap).sort().map(time => ({
    time,
    ...averagedTimeMap[time]
  }));

  const latestData = filteredData[filteredData.length - 1];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-gray-900 flex items-center">
          <Cloud className="w-5 h-5 mr-2" />
          Weather Data
        </h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowSourceFilter(!showSourceFilter)}
            className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Filter Sources
          </button>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Locations</option>
            {locations.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Source Filter Panel */}
      {showSourceFilter && (
        <div className="bg-white p-4 rounded-lg shadow border">
          <h4 className="text-lg font-medium mb-3">Filter by Weather Sources</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {availableSources.map(source => (
              <div key={source.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`dashboard-source-${source.id}`}
                  checked={selectedSources.includes(source.name)}
                  onChange={() => toggleSource(source.name)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor={`dashboard-source-${source.id}`} className="flex items-center space-x-2 text-sm">
                  <div
                    className={`w-2 h-2 rounded-full ${source.active ? 'bg-green-500' : 'bg-red-500'}`}
                  />
                  <span className={source.active ? 'text-gray-900' : 'text-gray-400'}>
                    {source.name}
                  </span>
                </label>
              </div>
            ))}
          </div>
          <div className="mt-3 flex justify-between items-center">
            <span className="text-sm text-gray-600">
              {selectedSources.length} of {availableSources.length} sources selected
            </span>
            <div className="space-x-2">
              <button
                onClick={() => setSelectedSources(availableSources.filter(s => s.active).map(s => s.name))}
                className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded"
              >
                Select Active
              </button>
              <button
                onClick={() => setSelectedSources([])}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Data Indicators */}
      <div className="mb-4 space-y-3">
        {/* Data Freshness Indicator */}
        {latestData && (
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Data Freshness</span>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  new Date().getTime() - new Date(latestData.timestamp).getTime() < 3600000
                    ? 'bg-green-500'
                    : 'bg-yellow-500'
                }`}></div>
                <span className="text-xs text-gray-600">
                  {Math.floor((new Date().getTime() - new Date(latestData.timestamp).getTime()) / 60000)} min ago
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Active Data Sources */}
        {activeSources.length > 0 && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-700">Active Sources</span>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-blue-600">
                  {activeSources.join(', ')}
                </span>
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Current Weather Stats */}
      {latestData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <Thermometer className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-blue-600">Temperature</span>
            </div>
            <div className="text-2xl font-bold text-blue-900">
              {renderValue(latestData.temperature, '°F', 1)}
            </div>
            <div className="text-xs text-blue-600 mt-1">
              Source: {latestData.source}
              {latestData.data_quality_score && (
                <span className="ml-2 px-1 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                  Quality: {Math.round(latestData.data_quality_score * 100)}%
                </span>
              )}
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <Droplets className="w-5 h-5 text-green-600 mr-2" />
              <span className="text-sm font-medium text-green-600">Humidity</span>
            </div>
            <div className="text-2xl font-bold text-green-900">
              {renderValue(latestData.humidity, '%', 0)}
            </div>
            <div className="text-xs text-green-600 mt-1">
              Source: {latestData.source}
              {latestData.data_quality_score && (
                <span className="ml-2 px-1 py-0.5 bg-green-100 text-green-800 rounded text-xs">
                  Quality: {Math.round(latestData.data_quality_score * 100)}%
                </span>
              )}
            </div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center">
              <Cloud className="w-5 h-5 text-purple-600 mr-2" />
              <span className="text-sm font-medium text-purple-600">Precipitation</span>
            </div>
            <div className="text-2xl font-bold text-purple-900">
              {renderValue(latestData.precipitation, 'mm', 1)}
            </div>
            <div className="text-xs text-purple-600 mt-1">
              Source: {latestData.source}
              {latestData.data_quality_score && (
                <span className="ml-2 px-1 py-0.5 bg-purple-100 text-purple-800 rounded text-xs">
                  Quality: {Math.round(latestData.data_quality_score * 100)}%
                </span>
              )}
            </div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="flex items-center">
              <Wind className="w-5 h-5 text-orange-600 mr-2" />
              <span className="text-sm font-medium text-orange-600">Wind Speed</span>
            </div>
            <div className="text-2xl font-bold text-orange-900">
              {renderValue(latestData.wind_speed, 'm/s', 1)}
            </div>
            <div className="text-xs text-orange-600 mt-1">
              Source: {latestData.source}
              {latestData.data_quality_score && (
                <span className="ml-2 px-1 py-0.5 bg-orange-100 text-orange-800 rounded text-xs">
                  Quality: {Math.round(latestData.data_quality_score * 100)}%
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Weather Charts */}
      <div className="space-y-6">
        <div className="h-64">
          <h4 className="text-lg font-medium text-gray-900 mb-4">24-Hour Temperature Comparison (5-Minute Intervals)</h4>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={tempChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              {activeSources.map(source => (
                <Line key={source} type="monotone" dataKey={source} stroke={source === 'meteostat' ? '#3b82f6' : source === 'openmeteo' ? '#10b981' : '#8884d8'} strokeWidth={2} name={source} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="h-64">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Humidity & Precipitation</h4>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="humidity" stroke="#10b981" strokeWidth={2} name="Humidity (%)" />
              <Line yAxisId="right" type="monotone" dataKey="precipitation" stroke="#8b5cf6" strokeWidth={2} name="Precipitation (mm)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {weatherData.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No weather data available. Check API keys and data sources.
        </div>
      )}
    </div>
  );
};

export default WeatherDashboard;