import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import ApiConfig from './components/ApiConfig';
import SystemHealth from './components/SystemHealth';
import WeatherTrading from './components/WeatherTrading';
import WeatherMarketCorrelation from './components/WeatherMarketCorrelation';
import SourceComparison from './components/SourceComparison';
import { RefreshProvider } from './contexts/RefreshContext';
import { Activity, Settings, BarChart3, Cloud, TrendingUp, GitCompare } from 'lucide-react';
import axios from 'axios';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [systemHealth, setSystemHealth] = useState<any>(null);

  useEffect(() => {
    // Fetch system health on load
    fetchSystemHealth();
  }, []);

  const fetchSystemHealth = async () => {
    try {
      const response = await axios.get('/api/system/health');
      setSystemHealth(response.data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'trading', label: 'Weather Trading', icon: Cloud },
    { id: 'correlation', label: 'Weather & Markets', icon: TrendingUp },
    { id: 'sources', label: 'Source Comparison', icon: GitCompare },
    { id: 'health', label: 'System Health', icon: Activity },
    { id: 'config', label: 'API Config', icon: Settings },
  ];

  return (
    <RefreshProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">ClimaTrade AI Dashboard</h1>
                {systemHealth && (
                  <span className={`ml-4 px-2 py-1 text-xs rounded-full ${
                    systemHealth.weather_data_count > 0 || systemHealth.polymarket_data_count > 0 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {systemHealth.weather_data_count > 0 || systemHealth.polymarket_data_count > 0 ? 'System Active' : 'System Inactive'}
                  </span>
                )}
              </div>
              <div className="flex space-x-4">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center px-4 py-2 rounded-md text-sm font-medium ${
                        activeTab === tab.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'trading' && <WeatherTrading />}
          {activeTab === 'correlation' && <WeatherMarketCorrelation />}
          {activeTab === 'sources' && <SourceComparison />}
          {activeTab === 'health' && <SystemHealth healthData={systemHealth} />}
          {activeTab === 'config' && <ApiConfig />}
        </main>
      </div>
    </RefreshProvider>
  );
}

export default App;