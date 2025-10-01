import React, { useState, useEffect } from 'react';
import WeatherDashboard from './WeatherDashboard';
import MarketDashboard from './MarketDashboard';
import TradingDashboard from './TradingDashboard';
import { useRefresh } from '../contexts/RefreshContext';
import { RefreshCw } from 'lucide-react';
import axios from 'axios';

const Dashboard: React.FC = () => {
  const { refreshTrigger, triggerRefresh, isRefreshing, setIsRefreshing } = useRefresh();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // Call the refresh endpoint to fetch latest weather data
      const response = await axios.post('/api/weather/refresh');

      if (response.status === 200) {
        console.log('Weather data refreshed:', response.data);
        // Trigger global refresh for all components
        triggerRefresh();
      } else {
        console.error('Failed to refresh weather data');
      }
    } catch (error) {
      console.error('Error refreshing weather data:', error);
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000);
    }
  };

  return (
    <div className="space-y-8">
      {/* Refresh Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard Overview</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            Last updated: {refreshTrigger.toLocaleTimeString()}
          </span>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Weather Dashboard */}
        <div className="bg-white rounded-lg shadow p-6">
          <WeatherDashboard refreshTrigger={refreshTrigger} />
        </div>

        {/* Market Dashboard */}
        <div className="bg-white rounded-lg shadow p-6">
          <MarketDashboard refreshTrigger={refreshTrigger} />
        </div>
      </div>

      {/* Trading Dashboard - Full Width */}
      <div className="bg-white rounded-lg shadow p-6">
        <TradingDashboard refreshTrigger={refreshTrigger} />
      </div>
    </div>
  );
};

export default Dashboard;