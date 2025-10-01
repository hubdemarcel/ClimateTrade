import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, BarChart, Bar } from 'recharts';
import { Cloud, Thermometer, Droplets, Wind, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown, Filter, BarChart3, Clock, MapPin } from 'lucide-react';
import axios from 'axios';
import { useRefresh } from '../contexts/RefreshContext';

interface WeatherDataPoint {
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
  data_count?: number;
  last_update?: string;
  avg_quality_score?: number;
}

interface ComparisonMetrics {
  temperature_variance: number;
  humidity_variance: number;
  data_completeness: number;
  update_frequency: number;
  quality_consistency: number;
}

// Utility functions - API already returns Fahrenheit, so no conversion needed
const celsiusToFahrenheit = (fahrenheit: number): number => {
  return fahrenheit; // API already provides Fahrenheit values
};

const formatGuadalajaraTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  // Convert to UTC-6 (Guadalajara time)
  const guadalajaraTime = new Date(date.getTime() - (6 * 60 * 60 * 1000));
  return guadalajaraTime.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
};

const getSourceStats = (sourceData: WeatherDataPoint[]) => {
  if (sourceData.length === 0) return null;

  const temperatures = sourceData.map(item => item.temperature).filter(temp => temp !== null && temp !== undefined);
  const humidities = sourceData.map(item => item.humidity).filter(hum => hum !== null && hum !== undefined);
  const windSpeeds = sourceData.map(item => item.wind_speed).filter(wind => wind !== null && wind !== undefined);

  const tempFahrenheit = temperatures.map(celsiusToFahrenheit);

  // Find highest temperature and its timestamp
  let highestTemp = null;
  let highestTempTimestamp = null;
  if (sourceData.length > 0) {
    const maxTempItem = sourceData.reduce((max, item) => {
      const tempF = celsiusToFahrenheit(item.temperature);
      const maxTempF = celsiusToFahrenheit(max.temperature);
      return tempF > maxTempF ? item : max;
    });
    highestTemp = celsiusToFahrenheit(maxTempItem.temperature);
    highestTempTimestamp = maxTempItem.timestamp;
  }

  return {
    latestTemp: temperatures.length > 0 ? celsiusToFahrenheit(temperatures[temperatures.length - 1]) : null,
    latestTimestamp: sourceData.length > 0 ? sourceData[sourceData.length - 1].timestamp : null,
    highestTemp,
    highestTempTimestamp,
    avgTemp: tempFahrenheit.length > 0 ? tempFahrenheit.reduce((a, b) => a + b, 0) / tempFahrenheit.length : null,
    avgHumidity: humidities.length > 0 ? humidities.reduce((a, b) => a + b, 0) / humidities.length : null,
    avgWindSpeed: windSpeeds.length > 0 ? windSpeeds.reduce((a, b) => a + b, 0) / windSpeeds.length : null,
    dataPoints: sourceData.length
  };
};

const SourceComparison: React.FC = () => {
  const { refreshTrigger } = useRefresh();
  const [weatherData, setWeatherData] = useState<WeatherDataPoint[]>([]);
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'comparison' | 'quality' | 'timeline'>('comparison');
  const [comparisonMetrics, setComparisonMetrics] = useState<ComparisonMetrics | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    fetchSources();
    fetchWeatherData();
  }, []);

  // Listen to global refresh trigger
  useEffect(() => {
    fetchSources();
    fetchWeatherData();
  }, [refreshTrigger]);

  const fetchSources = async () => {
    try {
      console.log('Fetching weather sources from /api/weather/sources');
      const response = await axios.get('/api/weather/sources');
      console.log('Sources API response:', response.data);
      setSources(response.data);
      // Auto-select all active sources
      const activeSources = response.data.filter((s: SourceInfo) => s.active).map((s: SourceInfo) => s.name);
      setSelectedSources(activeSources);
      console.log('Auto-selected active sources:', activeSources);
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    }
  };

  const fetchWeatherData = async () => {
    try {
      setLoading(true);
      console.log('Fetching weather data from /api/weather/data?hours=24');
      const response = await axios.get('/api/weather/data?hours=24');
      console.log('Weather data API response:', response.data);
      setWeatherData(response.data);
      setLastUpdate(new Date());

      // Extract unique locations
      const uniqueLocations = [...new Set(response.data.map((item: WeatherDataPoint) => item.location))].filter((loc): loc is string => loc !== null && loc !== undefined);
      console.log('Unique locations found:', uniqueLocations);
      setLocations(uniqueLocations);
      if (uniqueLocations.length > 0) {
        // Set to first available location if not already set
        if (!selectedLocation) {
          setSelectedLocation(uniqueLocations[0]);
          console.log('Set selected location to:', uniqueLocations[0]);
        }
        // If selectedLocation doesn't match any available locations, reset it
        else if (!uniqueLocations.includes(selectedLocation)) {
          console.warn(`Selected location "${selectedLocation}" not found in available locations, resetting to "${uniqueLocations[0]}"`);
          setSelectedLocation(uniqueLocations[0]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch weather data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = (sourceName: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceName)
        ? prev.filter(s => s !== sourceName)
        : [...prev, sourceName]
    );
  };

  const filteredData = weatherData.filter(item =>
    selectedSources.includes(item.source) &&
    (!selectedLocation || item.location === selectedLocation)
  );
  console.log('Filtered data:', {
    totalItems: filteredData.length,
    selectedSources,
    selectedLocation,
    sourcesCount: selectedSources.length,
    weatherDataCount: weatherData.length
  });

  const calculateComparisonMetrics = (): ComparisonMetrics => {
    const sourceGroups = selectedSources.map(source => ({
      source,
      data: filteredData.filter(item => item.source === source)
    }));

    // Calculate temperature variance across sources (in Fahrenheit)
    const tempValues = sourceGroups.flatMap(group =>
      group.data.map(item => celsiusToFahrenheit(item.temperature)).filter(temp => temp !== null && temp !== undefined)
    );

    const tempVariance = tempValues.length > 1 ?
      tempValues.reduce((sum, temp, _, arr) => {
        const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
        return sum + Math.pow(temp - mean, 2);
      }, 0) / tempValues.length : 0;

    // Calculate data completeness
    const totalExpected = sourceGroups.length * 24; // 24 hours per source
    const totalActual = sourceGroups.reduce((sum, group) => sum + group.data.length, 0);
    const dataCompleteness = totalExpected > 0 ? (totalActual / totalExpected) * 100 : 0;

    return {
      temperature_variance: Math.sqrt(tempVariance),
      humidity_variance: 0, // Would calculate similarly
      data_completeness: dataCompleteness,
      update_frequency: 95, // Mock value - would calculate from timestamps
      quality_consistency: 88 // Mock value - would calculate from quality scores
    };
  };

  useEffect(() => {
    console.log('Filtered data changed, length:', filteredData.length);
    if (filteredData.length > 0) {
      const metrics = calculateComparisonMetrics();
      console.log('Calculated comparison metrics:', metrics);
      setComparisonMetrics(metrics);
    } else {
      console.log('No filtered data available for metrics calculation');
    }
  }, [filteredData, selectedSources]);

  const formatComparisonData = () => {
    const timeMap: { [time: string]: { [source: string]: number } } = {};

    filteredData.forEach(item => {
      // Use Guadalajara time (UTC-6)
      const guadalajaraTime = formatGuadalajaraTime(item.timestamp);

      if (!timeMap[guadalajaraTime]) timeMap[guadalajaraTime] = {};
      timeMap[guadalajaraTime][item.source] = celsiusToFahrenheit(item.temperature);
    });

    return Object.keys(timeMap).sort().map(time => ({
      time,
      ...timeMap[time]
    }));
  };

  const formatQualityData = () => {
    return sources.map(source => {
      const sourceData = filteredData.filter(item => item.source === source.name);
      const avgQuality = sourceData.length > 0 ?
        sourceData.reduce((sum, item) => sum + (item.data_quality_score || 0), 0) / sourceData.length : 0;

      return {
        source: source.name,
        dataPoints: sourceData.length,
        avgQuality: Math.round(avgQuality * 100) / 100,
        completeness: sourceData.length > 0 ? (sourceData.length / 24) * 100 : 0
      };
    });
  };

  const getSourceColor = (sourceName: string): string => {
    const colors: { [key: string]: string } = {
      'meteostat': '#3b82f6',
      'openmeteo': '#10b981',
      'nws': '#8b5cf6',
      'weather2geo': '#f59e0b',
      'met_office': '#ef4444'
    };
    return colors[sourceName] || '#6b7280';
  };

  const getSourceStatusIcon = (source: SourceInfo) => {
    if (!source.active) return <XCircle className="w-4 h-4 text-red-500" />;
    if (source.data_count && source.data_count > 0) return <CheckCircle className="w-4 h-4 text-green-500" />;
    return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Weather Source Comparison
          </h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">UTC-6 (Guadalajara)</span>
            </div>
            {lastUpdate && (
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  Date.now() - lastUpdate.getTime() < 300000 ? 'bg-green-500' :
                  Date.now() - lastUpdate.getTime() < 600000 ? 'bg-yellow-500' : 'bg-red-500'
                } animate-pulse`} />
                <span className="text-sm text-gray-600">
                  Updated: {formatGuadalajaraTime(lastUpdate.toISOString())}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Location Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {locations.map(location => (
            <button
              key={location}
              onClick={() => setSelectedLocation(location)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedLocation === location
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
              }`}
            >
              <MapPin className="w-4 h-4 mr-2" />
              {location}
            </button>
          ))}
        </div>
      </div>

      {/* Individual Source Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {sources.map(source => {
          const sourceData = filteredData.filter(item => item.source === source.name);
          const stats = getSourceStats(sourceData);

          return (
            <div key={source.id} className="bg-white p-4 rounded-lg shadow border">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  {getSourceStatusIcon(source)}
                  <span className={`font-medium ${source.active ? 'text-gray-900' : 'text-gray-400'}`}>
                    {source.name}
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={selectedSources.includes(source.name)}
                  onChange={() => toggleSource(source.name)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>

              {stats && (
                <div className="space-y-3">
                  {/* Latest Temperature */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Thermometer className="w-4 h-4 text-red-500" />
                      <span className="text-sm text-gray-600">Latest</span>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-red-600">
                        {stats.latestTemp ? `${stats.latestTemp.toFixed(1)}°F` : 'N/A'}
                      </div>
                      {stats.latestTimestamp && (
                        <div className="text-xs text-gray-500">
                          {formatGuadalajaraTime(stats.latestTimestamp)}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Highest Temperature */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-orange-500" />
                      <span className="text-sm text-gray-600">Highest</span>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-orange-600">
                        {stats.highestTemp ? `${stats.highestTemp.toFixed(1)}°F` : 'N/A'}
                      </div>
                      {stats.highestTempTimestamp && (
                        <div className="text-xs text-gray-500">
                          {formatGuadalajaraTime(stats.highestTempTimestamp)}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Average Temperature */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-gray-600">Average</span>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-blue-600">
                        {stats.avgTemp ? `${stats.avgTemp.toFixed(1)}°F` : 'N/A'}
                      </div>
                      <div className="text-xs text-gray-500">{stats.dataPoints} points</div>
                    </div>
                  </div>

                  {/* Wind Speed in Meters */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Wind className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-gray-600">Wind</span>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-600">
                        {stats.avgWindSpeed ? `${stats.avgWindSpeed.toFixed(1)} m/s` : 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {!stats && (
                <div className="text-center py-4 text-gray-500 text-sm">
                  No data available
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* View Mode Selector */}
      <div className="flex space-x-2">
        {[
          { id: 'comparison', label: 'Data Comparison', icon: TrendingUp },
          { id: 'quality', label: 'Quality Analysis', icon: CheckCircle },
          { id: 'timeline', label: 'Timeline View', icon: BarChart3 }
        ].map(mode => (
          <button
            key={mode.id}
            onClick={() => setViewMode(mode.id as any)}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium ${
              viewMode === mode.id
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <mode.icon className="w-4 h-4 mr-2" />
            {mode.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {!loading && (
        <>
          {/* Comparison Metrics */}
          {comparisonMetrics && viewMode === 'comparison' && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <Thermometer className="w-5 h-5 text-blue-600 mr-2" />
                  <span className="text-sm font-medium text-blue-600">Temp Variance</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">
                  {comparisonMetrics.temperature_variance.toFixed(2)}°F
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <span className="text-sm font-medium text-green-600">Data Completeness</span>
                </div>
                <div className="text-2xl font-bold text-green-900">
                  {comparisonMetrics.data_completeness.toFixed(1)}%
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <TrendingUp className="w-5 h-5 text-purple-600 mr-2" />
                  <span className="text-sm font-medium text-purple-600">Update Frequency</span>
                </div>
                <div className="text-2xl font-bold text-purple-900">
                  {comparisonMetrics.update_frequency}%
                </div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <BarChart3 className="w-5 h-5 text-orange-600 mr-2" />
                  <span className="text-sm font-medium text-orange-600">Quality Consistency</span>
                </div>
                <div className="text-2xl font-bold text-orange-900">
                  {comparisonMetrics.quality_consistency}%
                </div>
              </div>
            </div>
          )}

          {/* Charts */}
          <div className="space-y-6">
            {viewMode === 'comparison' && (
              <div className="h-96">
                <h4 className="text-lg font-medium text-gray-900 mb-4">
                  Temperature Comparison Across Sources (°F - Guadalajara Time)
                </h4>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={formatComparisonData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                      formatter={(value: any, name: string) => [`${value.toFixed(1)}°F`, name]}
                      labelFormatter={(label) => `Time: ${label}`}
                    />
                    <Legend />
                    {selectedSources.map(source => (
                      <Line
                        key={source}
                        type="monotone"
                        dataKey={source}
                        stroke={getSourceColor(source)}
                        strokeWidth={2}
                        name={source}
                        connectNulls={false}
                        dot={{ r: 3 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {viewMode === 'quality' && (
              <div className="h-96">
                <h4 className="text-lg font-medium text-gray-900 mb-4">
                  Data Quality Analysis by Source
                </h4>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={formatQualityData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="source" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="dataPoints" fill="#3b82f6" name="Data Points" />
                    <Bar dataKey="completeness" fill="#10b981" name="Completeness %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {viewMode === 'timeline' && (
              <div className="space-y-4">
                <h4 className="text-lg font-medium text-gray-900">
                  Source Timeline Coverage (Guadalajara Time)
                </h4>
                {selectedSources.map(source => {
                  const sourceData = filteredData.filter(item => item.source === source);
                  const latestUpdate = sourceData.length > 0 ?
                    Math.max(...sourceData.map(item => new Date(item.timestamp).getTime())) : null;

                  return (
                    <div key={source} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: getSourceColor(source) }}
                          />
                          <span className="font-medium">{source}</span>
                        </div>
                        <div className="text-sm text-gray-600">
                          {sourceData.length} data points
                          {latestUpdate && (
                            <span className="ml-2">
                              • Last update: {formatGuadalajaraTime(new Date(latestUpdate).toISOString())}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${(sourceData.length / 24) * 100}%`,
                            backgroundColor: getSourceColor(source)
                          }}
                        />
                      </div>
                      {/* Data freshness indicator */}
                      {latestUpdate && (
                        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                          <span>Data freshness:</span>
                          <span className={`font-medium ${
                            Date.now() - latestUpdate < 3600000 ? 'text-green-600' :
                            Date.now() - latestUpdate < 7200000 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {Math.floor((Date.now() - latestUpdate) / 60000)} min ago
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Source Details Table */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h4 className="text-lg font-medium mb-4">Source Details</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data Points
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Update
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sources.map(source => {
                    const sourceData = filteredData.filter(item => item.source === source.name);
                    const latestUpdate = sourceData.length > 0 ?
                      new Date(Math.max(...sourceData.map(item => new Date(item.timestamp).getTime()))) : null;
                    const stats = getSourceStats(sourceData);

                    return (
                      <tr key={source.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div
                              className="w-3 h-3 rounded-full mr-2"
                              style={{ backgroundColor: getSourceColor(source.name) }}
                            />
                            <span className="text-sm font-medium text-gray-900">
                              {source.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {getSourceStatusIcon(source)}
                            <span className={`ml-2 text-sm ${source.active ? 'text-green-600' : 'text-red-600'}`}>
                              {source.active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div>
                            <div>{sourceData.length} points</div>
                            {stats && (
                              <div className="text-xs text-gray-500">
                                Avg: {stats.avgTemp ? `${stats.avgTemp.toFixed(1)}°F` : 'N/A'}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {latestUpdate ? formatGuadalajaraTime(latestUpdate.toISOString()) : 'No data'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          <div>
                            <div>{source.description}</div>
                            {stats && stats.highestTemp && (
                              <div className="text-xs text-orange-600 mt-1">
                                Peak: {stats.highestTemp.toFixed(1)}°F
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {weatherData.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          No weather data available. Check API keys and data sources.
        </div>
      )}
      
      {weatherData.length > 0 && filteredData.length === 0 && !loading && (
        <div className="text-center py-8 text-yellow-600 bg-yellow-50 rounded-lg">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <h4 className="font-medium">No data matches current filters</h4>
          <p className="text-sm">
            Selected sources: {selectedSources.join(', ') || 'none'} |
            Selected location: {selectedLocation || 'none'}
          </p>
          <p className="text-xs mt-2">
            Available locations: {locations.join(', ')}
          </p>
        </div>
      )}
    </div>
  );
};

export default SourceComparison;