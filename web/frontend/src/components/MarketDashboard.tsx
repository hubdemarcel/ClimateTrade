import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, Activity, AlertTriangle } from 'lucide-react';

interface MarketOverview {
  market_id: string;
  question: string;
  volume: number;
  liquidity: number;
  data_points: number;
  last_update: string;
}

interface MarketData {
  timestamp: string;
  outcome: string;
  probability: number;
  volume: number;
}

interface MarketDashboardProps {
  refreshTrigger: Date;
}

const MarketDashboard: React.FC<MarketDashboardProps> = ({ refreshTrigger }) => {
  const [markets, setMarkets] = useState<MarketOverview[]>([]);
  const [selectedMarket, setSelectedMarket] = useState<string>('');
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);


  // Helper function to render values with missing data indicators
  const renderValue = (value: number | undefined | null, prefix: string = '', suffix: string = '') => {
    if (value === undefined || value === null || isNaN(value)) {
      return (
        <div className="flex items-center space-x-1">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          <span className="text-gray-400 text-sm">No data</span>
        </div>
      );
    }
    return <span>{prefix}{value.toLocaleString()}{suffix}</span>;
  };

  useEffect(() => {
    fetchMarkets();
  }, [refreshTrigger]);

  useEffect(() => {
    if (selectedMarket) {
      fetchMarketData(selectedMarket);
    }
  }, [selectedMarket, refreshTrigger]);

  const fetchMarkets = async () => {
    try {
      // Fetch market overview from API
      const response = await fetch('/api/markets/overview');
      const data = await response.json();
      setMarkets(data);
      if (data.length > 0 && !selectedMarket) {
        setSelectedMarket(data[0].market_id);
      }
    } catch (error) {
      console.error('Failed to fetch markets from API:', error);
      // Fallback to empty data
      setMarkets([]);
    }
  };

  const fetchMarketData = async (marketId: string) => {
    try {
      // Fetch market data from API
      const response = await fetch(`/api/markets/${marketId}/data`);
      const data = await response.json();
      setMarketData(data);
    } catch (error) {
      console.error('Failed to fetch market data from API:', error);
      // Fallback data
      setMarketData([]);
    } finally {
      setLoading(false);
    }
  };


  const selectedMarketInfo = markets.find(m => m.market_id === selectedMarket);

  const chartData = marketData
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(item => ({
      time: new Date(item.timestamp).toLocaleTimeString(),
      probability: item.probability * 100,
      volume: item.volume,
      outcome: item.outcome,
    }));

  // Group by outcome for multiple lines
  const outcomes = [...new Set(marketData.map(item => item.outcome))];
  const outcomeData = outcomes.map(outcome => {
    const outcomePoints = chartData.filter(point => point.outcome === outcome);
    return {
      outcome,
      data: outcomePoints,
    };
  });

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
          <TrendingUp className="w-5 h-5 mr-2" />
          Market Data
        </h3>
        <select
          value={selectedMarket}
          onChange={(e) => setSelectedMarket(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
        >
          {markets.map(market => (
            <option key={market.market_id} value={market.market_id}>
              {market.question.substring(0, 50)}...
            </option>
          ))}
        </select>
      </div>

      {/* Data Freshness Indicator */}
      {selectedMarketInfo && selectedMarketInfo.last_update && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Market Data Freshness</span>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                new Date().getTime() - new Date(selectedMarketInfo.last_update).getTime() < 3600000
                  ? 'bg-green-500'
                  : 'bg-yellow-500'
              }`}></div>
              <span className="text-xs text-gray-600">
                {Math.floor((new Date().getTime() - new Date(selectedMarketInfo.last_update).getTime()) / 60000)} min ago
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Market Stats */}
      {selectedMarketInfo && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <DollarSign className="w-5 h-5 text-green-600 mr-2" />
              <span className="text-sm font-medium text-green-600">Volume</span>
            </div>
            <div className="text-2xl font-bold text-green-900">
              {renderValue(selectedMarketInfo.volume, '$')}
            </div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <Activity className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-blue-600">Liquidity</span>
            </div>
            <div className="text-2xl font-bold text-blue-900">
              {renderValue(selectedMarketInfo.liquidity, '$')}
            </div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center">
              <TrendingUp className="w-5 h-5 text-purple-600 mr-2" />
              <span className="text-sm font-medium text-purple-600">Data Points</span>
            </div>
            <div className="text-2xl font-bold text-purple-900">
              {renderValue(selectedMarketInfo.data_points)}
            </div>
          </div>
        </div>
      )}

      {/* Probability Chart */}
      <div className="h-64">
        <h4 className="text-lg font-medium text-gray-900 mb-4">Probability Trends</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[0, 100]} />
            <Tooltip
              formatter={(value: any, name: string) => [
                name === 'probability' ? `${value.toFixed(1)}%` : value,
                name === 'probability' ? 'Probability' : name
              ]}
            />
            {outcomes.map((outcome, index) => (
              <Line
                key={outcome}
                type="monotone"
                dataKey="probability"
                data={outcomeData.find(d => d.outcome === outcome)?.data}
                stroke={`hsl(${index * 137.5 % 360}, 70%, 50%)`}
                strokeWidth={2}
                name={outcome}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Market Question */}
      {selectedMarketInfo && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">Market Question</h4>
          <p className="text-gray-700">{selectedMarketInfo.question}</p>
        </div>
      )}

      {markets.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No market data available. Check Polymarket integration.
        </div>
      )}
    </div>
  );
};

export default MarketDashboard;