import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, AlertTriangle, Database, Cloud, Key } from 'lucide-react';

interface SystemHealthProps {
  healthData?: any;
}

const SystemHealth: React.FC<SystemHealthProps> = ({ healthData }) => {
  const [apiKeys, setApiKeys] = useState<any>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchApiKeysStatus();
  }, []);

  const fetchApiKeysStatus = async () => {
    try {
      // Check environment variables (this would need backend support)
      const response = await fetch('/api/system/health');
      const data = await response.json();
      setApiKeys(data.api_keys || {});
    } catch (error) {
      console.error('Failed to fetch API keys status:', error);
    }
  };

  const getStatusIcon = (status: boolean) => {
    return status ? (
      <CheckCircle className="w-5 h-5 text-green-500" />
    ) : (
      <XCircle className="w-5 h-5 text-red-500" />
    );
  };

  const getStatusColor = (status: boolean) => {
    return status ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50';
  };

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900 flex items-center">
        <Activity className="w-5 h-5 mr-2" />
        System Health & Status
      </h3>

      {/* Database Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Database className="w-5 h-5 mr-2" />
          Database Status
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`p-4 rounded-lg ${getStatusColor((healthData?.weather_data_count || 0) > 0)}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Weather Data</span>
              {getStatusIcon((healthData?.weather_data_count || 0) > 0)}
            </div>
            <p className="text-2xl font-bold mt-2">{healthData?.weather_data_count || 0} records</p>
          </div>
          <div className={`p-4 rounded-lg ${getStatusColor((healthData?.polymarket_data_count || 0) > 0)}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Market Data</span>
              {getStatusIcon((healthData?.polymarket_data_count || 0) > 0)}
            </div>
            <p className="text-2xl font-bold mt-2">{healthData?.polymarket_data_count || 0} records</p>
          </div>
          <div className={`p-4 rounded-lg ${getStatusColor((healthData?.trading_history_count || 0) >= 0)}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Trading History</span>
              {getStatusIcon((healthData?.trading_history_count || 0) >= 0)}
            </div>
            <p className="text-2xl font-bold mt-2">{healthData?.trading_history_count || 0} records</p>
          </div>
        </div>
      </div>

      {/* API Keys Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Key className="w-5 h-5 mr-2" />
          API Keys Configuration
        </h4>
        <div className="space-y-3">
          {Object.entries(apiKeys).map(([key, configured]) => (
            <div key={key} className={`p-4 rounded-lg ${getStatusColor(configured as boolean)}`}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{key.replace(/_/g, ' ').toUpperCase()}</span>
                {getStatusIcon(configured as boolean)}
              </div>
              <p className="text-sm mt-1">
                {configured ? 'Configured' : 'Missing - Please set environment variable'}
              </p>
            </div>
          ))}
          {Object.keys(apiKeys).length === 0 && (
            <div className="text-center py-8 text-gray-500">
              Unable to check API keys status
            </div>
          )}
        </div>
      </div>

      {/* Data Sources Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Cloud className="w-5 h-5 mr-2" />
          Data Sources
        </h4>
        <div className="space-y-3">
          <div className={`p-4 rounded-lg ${getStatusColor(!!healthData?.latest_weather)}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Latest Weather Data</span>
              {getStatusIcon(!!healthData?.latest_weather)}
            </div>
            <p className="text-sm mt-1">
              {healthData?.latest_weather
                ? new Date(healthData.latest_weather).toLocaleString()
                : 'No recent data'
              }
            </p>
          </div>
          <div className={`p-4 rounded-lg ${getStatusColor(!!healthData?.latest_market)}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Latest Market Data</span>
              {getStatusIcon(!!healthData?.latest_market)}
            </div>
            <p className="text-sm mt-1">
              {healthData?.latest_market
                ? new Date(healthData.latest_market).toLocaleString()
                : 'No recent data'
              }
            </p>
          </div>
        </div>
      </div>

      {/* System Alerts */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2" />
          System Alerts
        </h4>
        <div className="space-y-3">
          {(!healthData?.weather_data_count || healthData.weather_data_count === 0) && (
            <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-200">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
                <span className="text-sm font-medium text-yellow-800">No Weather Data</span>
              </div>
              <p className="text-sm text-yellow-700 mt-1">
                Weather data collection may not be running or API keys may be missing.
              </p>
            </div>
          )}
          {(!healthData?.polymarket_data_count || healthData.polymarket_data_count === 0) && (
            <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-200">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
                <span className="text-sm font-medium text-yellow-800">No Market Data</span>
              </div>
              <p className="text-sm text-yellow-700 mt-1">
                Polymarket data collection may not be running or API keys may be missing.
              </p>
            </div>
          )}
          {Object.values(apiKeys).some((configured: any) => !configured) && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200">
              <div className="flex items-center">
                <XCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-sm font-medium text-red-800">Missing API Keys</span>
              </div>
              <p className="text-sm text-red-700 mt-1">
                Some API keys are not configured. Check the API Config tab to set them.
              </p>
            </div>
          )}
          {Object.values(apiKeys).every((configured: any) => configured) &&
           healthData?.weather_data_count > 0 &&
           healthData?.polymarket_data_count > 0 && (
            <div className="p-4 rounded-lg bg-green-50 border border-green-200">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <span className="text-sm font-medium text-green-800">System Healthy</span>
              </div>
              <p className="text-sm text-green-700 mt-1">
                All systems are operational and data is being collected.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;