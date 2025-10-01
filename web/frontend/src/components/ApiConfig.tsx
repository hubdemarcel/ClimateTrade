import React, { useState, useEffect } from 'react';
import { Key, Save, AlertCircle, CheckCircle } from 'lucide-react';

interface ApiKey {
  name: string;
  value: string;
  description: string;
  required: boolean;
}

const ApiConfig: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      name: 'MET_OFFICE_API_KEY',
      value: '',
      description: 'UK Met Office Weather DataHub API Key',
      required: true,
    },
    {
      name: 'POLYGON_WALLET_PRIVATE_KEY',
      value: '',
      description: 'Polygon Wallet Private Key for Trading',
      required: true,
    },
    {
      name: 'METEOSTAT_API_KEY',
      value: '',
      description: 'Meteostat API Key (optional)',
      required: false,
    },
    {
      name: 'WEATHER_UNDERGROUND_API_KEY',
      value: '',
      description: 'Weather Underground API Key (optional)',
      required: false,
    },
    {
      name: 'WEATHER2GEO_API_KEY',
      value: '',
      description: 'Weather2Geo API Key (optional)',
      required: false,
    },
  ]);

  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    loadExistingKeys();
  }, []);

  const loadExistingKeys = async () => {
    try {
      // In a real implementation, this would fetch from backend
      // For now, we'll show placeholder values
      const response = await fetch('http://localhost:8001/api/system/health');
      const data = await response.json();

      setApiKeys(prevKeys =>
        prevKeys.map(key => ({
          ...key,
          value: data.api_keys && data.api_keys[key.name.toLowerCase()] ? '••••••••' : '',
        }))
      );
    } catch (error) {
      console.error('Failed to load API keys:', error);
    }
  };

  const handleKeyChange = (name: string, value: string) => {
    setApiKeys(prevKeys =>
      prevKeys.map(key =>
        key.name === name ? { ...key, value } : key
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveStatus('idle');

    try {
      // In a real implementation, this would save to environment variables
      // For now, we'll simulate the save
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Validate required keys
      const missingRequired = apiKeys.filter(key => key.required && !key.value.trim());
      if (missingRequired.length > 0) {
        throw new Error(`Missing required API keys: ${missingRequired.map(k => k.name).join(', ')}`);
      }

      setSaveStatus('success');
    } catch (error) {
      console.error('Failed to save API keys:', error);
      setSaveStatus('error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold text-gray-900 flex items-center mb-6">
          <Key className="w-5 h-5 mr-2" />
          API Key Configuration
        </h3>

        <div className="space-y-4">
          {apiKeys.map((key) => (
            <div key={key.name} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {key.name}
                    {key.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <p className="text-sm text-gray-500 mb-3">{key.description}</p>
                  <input
                    type="password"
                    value={key.value}
                    onChange={(e) => handleKeyChange(key.name, e.target.value)}
                    placeholder={key.value ? '••••••••' : 'Enter API key...'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="ml-4">
                  {key.value ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : key.required ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <div className="w-5 h-5" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            * Required API keys must be configured for the system to function properly
          </p>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>

        {saveStatus === 'success' && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              <span className="text-sm text-green-800">API keys saved successfully!</span>
            </div>
          </div>
        )}

        {saveStatus === 'error' && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-sm text-red-800">Failed to save API keys. Please try again.</span>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-medium text-gray-900 mb-4">Configuration Instructions</h4>
        <div className="space-y-3 text-sm text-gray-600">
          <p>
            <strong>Environment Variables:</strong> API keys are stored as environment variables.
            You can also set them directly in your system's environment or in a .env file.
          </p>
          <p>
            <strong>Security:</strong> API keys are sensitive information. Never commit them to version control.
            Consider using a password manager or secure credential storage.
          </p>
          <p>
            <strong>Getting API Keys:</strong>
          </p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li><strong>Met Office:</strong> Register at <a href="https://www.metoffice.gov.uk/services/data" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Met Office DataHub</a></li>
            <li><strong>Polygon Wallet:</strong> Create a wallet for blockchain trading</li>
            <li><strong>Other APIs:</strong> Register at respective weather service providers</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ApiConfig;