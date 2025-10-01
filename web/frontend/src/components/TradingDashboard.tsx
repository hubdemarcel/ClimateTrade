import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, AlertTriangle } from 'lucide-react';

interface TradingData {
  date: string;
  trades: number;
  volume: number;
  avg_price: number;
  total_pnl: number;
}

interface Position {
  market_id: string;
  outcome: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  unrealized_pnl: number;
  question: string;
}

interface TradingDashboardProps {
  refreshTrigger: Date;
}

const TradingDashboard: React.FC<TradingDashboardProps> = ({ refreshTrigger }) => {
  const [tradingData, setTradingData] = useState<TradingData[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  // Helper function to render values with missing data indicators
  const renderValue = (value: number | undefined | null, prefix: string = '', decimals: number = 0) => {
    if (value === undefined || value === null || isNaN(value)) {
      return (
        <div className="flex items-center space-x-1">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          <span className="text-gray-400 text-sm">No data</span>
        </div>
      );
    }
    return <span>{prefix}{value.toFixed(decimals)}{decimals > 0 ? '' : ''}</span>;
  };

  useEffect(() => {
    fetchTradingData();
    fetchPositions();
  }, [refreshTrigger]);

  const fetchTradingData = async () => {
    try {
      const response = await fetch('/api/trading/performance?days=30');
      const data = await response.json();
      setTradingData(data);
    } catch (error) {
      console.error('Failed to fetch trading data:', error);
    }
  };

  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/trading/positions');
      const data = await response.json();
      setPositions(data);
    } catch (error) {
      console.error('Failed to fetch positions:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalPnL = tradingData.reduce((sum, day) => sum + day.total_pnl, 0);
  const totalVolume = tradingData.reduce((sum, day) => sum + day.volume, 0);
  const totalTrades = tradingData.reduce((sum, day) => sum + day.trades, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900 flex items-center">
        <BarChart3 className="w-5 h-5 mr-2" />
        Trading Performance
      </h3>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`p-4 rounded-lg ${totalPnL >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex items-center">
            {totalPnL >= 0 ? (
              <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-600 mr-2" />
            )}
            <span className={`text-sm font-medium ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              Total P&L
            </span>
          </div>
          <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-900' : 'text-red-900'}`}>
            {renderValue(totalPnL, '$', 2)}
          </div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center">
            <DollarSign className="w-5 h-5 text-blue-600 mr-2" />
            <span className="text-sm font-medium text-blue-600">Total Volume</span>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {renderValue(totalVolume, '$', 2)}
          </div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="flex items-center">
            <BarChart3 className="w-5 h-5 text-purple-600 mr-2" />
            <span className="text-sm font-medium text-purple-600">Total Trades</span>
          </div>
          <div className="text-2xl font-bold text-purple-900">
            {renderValue(totalTrades)}
          </div>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-orange-600 mr-2" />
            <span className="text-sm font-medium text-orange-600">Avg Trade Size</span>
          </div>
          <div className="text-2xl font-bold text-orange-900">
            {renderValue(totalTrades > 0 ? totalVolume / totalTrades : null, '$', 2)}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* P&L Chart */}
        <div className="h-64">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Daily P&L</h4>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tradingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip
                formatter={(value: any) => [`$${value?.toFixed(2)}`, 'P&L']}
              />
              <Bar
                dataKey="total_pnl"
                fill={(entry: any) => entry.total_pnl >= 0 ? '#10b981' : '#ef4444'}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Volume Chart */}
        <div className="h-64">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Trading Volume</h4>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={tradingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip
                formatter={(value: any) => [`$${value?.toFixed(2)}`, 'Volume']}
              />
              <Line type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Current Positions */}
      <div>
        <h4 className="text-lg font-medium text-gray-900 mb-4">Current Positions</h4>
        {positions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Market
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Outcome
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unrealized P&L
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {positions.map((position, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {position.question.substring(0, 50)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.outcome}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {position.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${position.avg_price?.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${position.current_price?.toFixed(4)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                      position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      ${position.unrealized_pnl?.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No open positions
          </div>
        )}
      </div>

      {tradingData.length === 0 && positions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No trading data available. Start trading to see performance metrics.
        </div>
      )}
    </div>
  );
};

export default TradingDashboard;