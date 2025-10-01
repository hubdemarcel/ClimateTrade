# ClimaTrade AI - Frontend Documentation

## Overview

This comprehensive documentation covers the ClimaTrade AI web frontend, including architecture, components, data handling, API integration, and recent enhancements. The application provides advanced weather data analysis, market intelligence, and trading performance monitoring with multi-source data comparison capabilities.

**Key Features:**

- Multi-source weather data comparison and analysis
- Real-time market data visualization
- Trading performance monitoring
- Advanced data quality indicators and missing data handling
- Responsive design with mobile-first approach
- Comprehensive error handling and user feedback

## Table of Contents

1. [Architecture](#architecture)
2. [Components](#components)
3. [Data Handling](#data-handling)
4. [API Integration](#api-integration)
5. [Recent Enhancements](#recent-enhancements)
6. [Configuration & Deployment](#configuration--deployment)
7. [Testing & Performance](#testing--performance)
8. [Security & Monitoring](#security--monitoring)

## Architecture

### Technology Stack

- **Framework**: React 18.2.0 with TypeScript
- **Build Tool**: Vite 4.4.5
- **Styling**: Tailwind CSS 3.3.5
- **Charts**: Recharts 2.8.0
- **Icons**: Lucide React 0.294.0
- **HTTP Client**: Axios 1.6.0

### Application Structure

```
web/frontend/
├── src/
│   ├── components/
│   │   ├── ApiConfig.tsx          # API key configuration
│   │   ├── Dashboard.tsx          # Main dashboard layout
│   │   ├── MarketDashboard.tsx    # Market data visualization
│   │   ├── SystemHealth.tsx       # System health monitoring
│   │   ├── TradingDashboard.tsx   # Trading performance
│   │   ├── WeatherDashboard.tsx   # Weather data visualization
│   │   ├── SourceComparison.tsx   # Multi-source comparison
│   │   └── ErrorBoundary.tsx      # Error handling component
│   ├── App.tsx                    # Main application component
│   ├── App.css                    # Global styles
│   ├── index.css                  # Tailwind imports
│   └── main.tsx                   # Application entry point
├── public/                        # Static assets
├── package.json                   # Dependencies and scripts
├── vite.config.ts                 # Build configuration
└── Dockerfile                     # Container configuration
```

### Component Hierarchy

```
App
├── Header (Navigation Tabs)
├── Dashboard (Main Content)
│   ├── WeatherDashboard
│   │   ├── Data Freshness Indicator
│   │   ├── Active Sources Indicator
│   │   ├── Current Weather Stats
│   │   └── Weather Charts (5-min resolution)
│   ├── MarketDashboard
│   │   ├── Data Freshness Indicator
│   │   ├── Market Stats
│   │   └── Market Charts
│   ├── TradingDashboard
│   │   ├── Performance Metrics
│   │   ├── Current Positions
│   │   └── Trading Charts
│   └── SourceComparison
│       ├── Comparison View
│       ├── Quality Analysis View
│       └── Timeline Coverage View
├── SystemHealth
└── ApiConfig
```

## Components

### Core Components

#### WeatherDashboard

**Purpose**: Display weather data with advanced source comparison and quality indicators

**Key Features:**

- 5-minute interval temperature resolution for detailed benchmarking
- Multi-source data visualization with color-coded lines
- Data freshness indicators (green < 1hr, yellow > 1hr)
- Missing data indicators with yellow warning triangles
- Interactive charts with hover tooltips
- Source attribution for all data points

**Data Requirements:**

```typescript
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
```

#### SourceComparison

**Purpose**: Advanced multi-source weather data comparison and analysis

**Key Features:**

- Three view modes: Comparison, Quality Analysis, Timeline Coverage
- Interactive source filtering with multi-select checkboxes
- Real-time metrics: temperature variance, data completeness, update frequency
- Visual analytics with interactive charts
- Responsive design adapting to screen size (2-5 columns)

**View Modes:**

1. **Comparison View**: Side-by-side temperature comparison across sources
2. **Quality Analysis View**: Data completeness and quality metrics
3. **Timeline Coverage View**: Visual timeline with data availability indicators

#### MarketDashboard & TradingDashboard

**Purpose**: Market data visualization and trading performance monitoring

**Key Features:**

- Real-time market data with freshness indicators
- Trading performance metrics with missing data handling
- Interactive charts for market trends and positions
- Error boundaries for robust error handling

### Utility Components

#### ErrorBoundary

**Purpose**: Comprehensive error handling and user feedback

**Features:**

- Catches React component errors
- Displays user-friendly error messages
- Provides refresh functionality
- Logs errors for debugging

#### SystemHealth

**Purpose**: Monitor overall system status and API connectivity

**Features:**

- Backend service health checks
- API endpoint status indicators
- Real-time connectivity monitoring
- Configuration validation

## Data Handling

### Data Flow Patterns

#### Weather Data Flow

```typescript
// 1. Component mounts → fetchWeatherData()
fetchWeatherData = async () => {
  try {
    const response = await axios.get('/api/weather/data?hours=24');
    const data = response.data;

    // 2. Process and validate data
    const processedData = processWeatherData(data);

    // 3. Update component state
    setWeatherData(processedData);
    setLocations(extractLocations(processedData));
    setActiveSources(extractSources(processedData));

    // 4. Set default filters
    if (locations.length > 0 && !selectedLocation) {
      setSelectedLocation(locations[0]);
    }
  } catch (error) {
    handleApiError(error, 'fetchWeatherData');
  }
};
```

#### Market Data Flow

```typescript
// 1. Fetch markets overview
const fetchMarkets = async () => {
  try {
    const response = await fetch('/api/markets/overview');
    const markets = await response.json();
    setMarkets(markets);

    if (markets.length > 0 && !selectedMarket) {
      setSelectedMarket(markets[0].market_id);
    }
  } catch (error) {
    handleApiError(error, 'fetchMarkets');
  }
};
```

### Data Processing

#### Time Series Processing

```typescript
// Smart timestamp rounding to 5-minute intervals
const roundTo5Minutes = (timestamp: string) => {
  const date = new Date(timestamp);
  const minutes = date.getMinutes();
  const roundedMinutes = Math.round(minutes / 5) * 5;
  date.setMinutes(roundedMinutes, 0, 0);
  return date.toISOString();
};

// Temperature conversion with consistent units
const celsiusToFahrenheit = (celsius: number) => {
  return (celsius * 9) / 5 + 32;
};
```

#### Data Aggregation

```typescript
// Group data by time intervals and average values
const groupByTimeInterval = (data: WeatherData[], intervalMinutes: number) => {
  const grouped: { [key: string]: WeatherData[] } = {};

  data.forEach((item) => {
    const roundedTime = roundTo5Minutes(item.timestamp);
    if (!grouped[roundedTime]) {
      grouped[roundedTime] = [];
    }
    grouped[roundedTime].push(item);
  });

  return grouped;
};
```

### Data Quality & Validation

#### Missing Data Indicators

```typescript
// Helper function for consistent data display
const renderValue = (
  value: number | undefined | null,
  unit: string,
  decimals: number = 1
) => {
  if (value === undefined || value === null || isNaN(value)) {
    return (
      <div className="flex items-center space-x-1">
        <AlertTriangle className="w-4 h-4 text-yellow-500" />
        <span className="text-gray-400 text-sm">No data</span>
      </div>
    );
  }
  return (
    <span>
      {value.toFixed(decimals)}
      {unit}
    </span>
  );
};
```

#### Data Freshness Indicators

```typescript
// Weather data freshness logic
const getDataFreshness = (timestamp: string) => {
  const now = new Date().getTime();
  const dataTime = new Date(timestamp).getTime();
  const minutesAgo = Math.floor((now - dataTime) / 60000);

  if (minutesAgo < 60) {
    return { status: 'fresh', color: 'green', text: `${minutesAgo} min ago` };
  } else {
    return { status: 'stale', color: 'yellow', text: `${minutesAgo} min ago` };
  }
};
```

## API Integration

### Backend API Endpoints

| Component        | Endpoint                           | Method | Purpose                    | Refresh Rate        |
| ---------------- | ---------------------------------- | ------ | -------------------------- | ------------------- |
| WeatherDashboard | `/api/weather/data?hours=24`       | GET    | Fetch weather data         | On refresh trigger  |
| WeatherDashboard | `/api/weather/sources`             | GET    | Fetch source metadata      | On load             |
| MarketDashboard  | `/api/markets/overview`            | GET    | Fetch market overview      | On refresh trigger  |
| MarketDashboard  | `/api/markets/{market_id}/data`    | GET    | Fetch specific market data | On market selection |
| TradingDashboard | `/api/trading/performance?days=30` | GET    | Fetch trading performance  | On refresh trigger  |
| TradingDashboard | `/api/trading/positions`           | GET    | Fetch current positions    | On refresh trigger  |
| SystemHealth     | `/api/system/health`               | GET    | Fetch system health        | On load             |

### Error Handling Patterns

#### Network Error Handling

```typescript
// Generic error handling pattern
const handleApiError = (error: any, context: string) => {
  console.error(`API Error in ${context}:`, error);

  if (error.response) {
    const status = error.response.status;
    switch (status) {
      case 404:
        return { type: 'not_found', message: 'Data not found' };
      case 429:
        return { type: 'rate_limited', message: 'Too many requests' };
      case 500:
        return { type: 'server_error', message: 'Server error' };
      default:
        return {
          type: 'api_error',
          message: error.response.data?.message || 'API error',
        };
    }
  } else if (error.request) {
    return { type: 'network_error', message: 'Network connection failed' };
  } else {
    return { type: 'unknown_error', message: 'Unknown error occurred' };
  }
};
```

#### Loading States

```typescript
// Loading state pattern
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

const fetchData = async () => {
  try {
    setLoading(true);
    setError(null);
    const response = await axios.get('/api/data');
    setData(response.data);
  } catch (err) {
    setError(handleApiError(err, 'fetchData'));
  } finally {
    setLoading(false);
  }
};
```

### State Management

```typescript
// Component state structure
const [weatherData, setWeatherData] = useState<WeatherData[]>([]);
const [selectedLocation, setSelectedLocation] = useState('');
const [locations, setLocations] = useState<string[]>([]);
const [activeSources, setActiveSources] = useState<string[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
const [lastRefresh, setLastRefresh] = useState(new Date());
```

### Refresh Trigger Pattern

```typescript
// Parent component provides refresh trigger
<WeatherDashboard refreshTrigger={lastRefresh} />;

// Child component uses refresh trigger
useEffect(() => {
  fetchWeatherData();
}, [refreshTrigger]);
```

## Recent Enhancements

### Multi-Source Comparison (2025-09-08)

**New Features:**

- SourceComparison component with three view modes
- Interactive filtering with multi-select source checkboxes
- Real-time comparison metrics and quality analysis
- Enhanced WeatherDashboard with source attribution
- 5-minute interval temperature resolution

**Technical Implementation:**

- Added GitCompare icon to navigation
- Integrated SourceComparison component routing
- Enhanced data processing for multi-source handling
- Improved chart visualization with source-specific colors

### Data Quality Improvements (2025-09-05)

**Enhancements:**

- Missing data indicators with yellow warning triangles
- Consistent data display across all components
- Enhanced error handling with user feedback
- Improved data validation and type checking

**Components Updated:**

- WeatherDashboard: Temperature, humidity, precipitation, wind speed
- MarketDashboard: Volume, liquidity, data points
- TradingDashboard: P&L, volume, trades, average trade size

### Temperature Chart Enhancements (2025-09-08)

**Improvements:**

- 5-minute interval resolution for detailed benchmarking
- Smart timestamp rounding to nearest 5-minute mark
- Multi-source data handling with color-coded lines
- Interactive tooltips with source attribution
- Consistent Fahrenheit temperature units

**Benefits:**

- Granular comparison of update frequencies
- Visual identification of data completeness
- Better understanding of source reliability
- Enhanced user experience with detailed insights

### Frontend Connectivity Fixes (2025-09-08)

**Changes Made:**

- Updated all API calls to use relative paths instead of absolute URLs
- Fixed Vite proxy configuration issues
- Improved system health logic with comprehensive checks
- Enhanced error handling and user feedback

**Impact:**

- All API calls now properly route through Vite's proxy
- Frontend-backend connectivity restored
- Dashboard displays data correctly
- System health indicators work accurately

## Configuration & Deployment

### Environment Variables

```bash
# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
VITE_REFRESH_INTERVAL=30000
```

### Vite Configuration

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
});
```

### Build Process

```bash
# Install dependencies
npm install

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Deployment

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "preview"]
```

## Testing & Performance

### Component Testing

```typescript
// Example test for WeatherDashboard
import { render, screen, waitFor } from '@testing-library/react';
import WeatherDashboard from './WeatherDashboard';


test('displays weather data', async () => {
  const mockData = [
    {
      timestamp: '2024-01-01T12:00:00Z',
      location: 'London,UK',
      source: 'met_office',
      temperature: 18.5,
      humidity: 72,
      precipitation: 0.0,
      wind_speed: 3.2,
      description: 'Clear sky',
    },
  ];


  mockedAxios.get.mockResolvedValue({ data: mockData });


  render(<WeatherDashboard refreshTrigger={new Date()} />);


  await waitFor(() => {
    expect(screen.getByText('18.5°C')).toBeInTheDocument();
    expect(screen.getByText('72%')).toBeInTheDocument();
  });
});
```

### Performance Optimizations

#### React Performance Techniques

1. **Memoization**: Use `React.memo` for components with stable props
2. **Lazy Loading**: Dynamic imports for code splitting
3. **Virtual Scrolling**: For large datasets
4. **Efficient Re-renders**: Optimize state updates

#### Bundle Optimization

```typescript
// Dynamic imports for code splitting
const WeatherDashboard = lazy(() => import('./components/WeatherDashboard'));


// Usage
<Suspense fallback={<div>Loading...</div>}>
  <WeatherDashboard />
</Suspense>;
```

### API Testing Results

- ✅ **15/15 tests passed**
- ✅ **All endpoints responding correctly**
- ✅ **Error handling working properly**
- ✅ **CORS functioning correctly**

## Security & Monitoring

### Security Measures

#### Current Security Features

- **CORS Configuration**: Properly configured for localhost:8080
- **API Keys**: Environment variables properly configured
- **Input Validation**: Weather service validates city names
- **HTTPS Ready**: Backend configured for secure connections

#### Security Enhancements Needed

1. **Authentication Middleware**: Add JWT or API key authentication
2. **Rate Limiting**: Implement request rate limiting
3. **Input Sanitization**: Enhanced input validation middleware
4. **Request Logging**: Add logging without sensitive data

### Error Monitoring

#### Error Boundary Implementation

```typescript
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }


  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }


  componentDidCatch(error, errorInfo) {
    console.error('Component error:', error, errorInfo);
  }


  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h3>Something went wrong</h3>
          <p>Please refresh the page or contact support</p>
          <button onClick={() => window.location.reload()}>Refresh</button>
        </div>
      );
    }


    return this.props.children;
  }
}
```

### Performance Monitoring

#### Key Metrics

- **Chart Render Time**: Monitor chart rendering performance
- **Data Processing Time**: Track data aggregation performance
- **Memory Usage**: Monitor memory consumption during data processing
- **API Response Times**: Track backend API performance

### Future Enhancements

#### Planned Features

1. **Real-time Updates**: WebSocket integration for live data updates
2. **Export Functionality**: CSV/JSON export of comparison results
3. **Historical Analysis**: Time-range selection for historical comparisons
4. **Alert System**: Notifications for source quality issues
5. **Custom Metrics**: User-defined comparison metrics

#### Scalability Improvements

1. **Data Partitioning**: Time-based data partitioning for large datasets
2. **Caching Layers**: Add Redis caching for frequently accessed data
3. **Async Processing**: Move heavy data processing to background workers
4. **Database Optimization**: Add indexes for time-series queries