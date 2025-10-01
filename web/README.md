# ClimaTrade AI Dashboard

A comprehensive web dashboard for monitoring and controlling the ClimaTrade AI weather-informed trading system. Built with React + FastAPI for real-time data visualization and system management.

## 🎯 Overview

The ClimaTrade AI Dashboard provides a unified interface to monitor all aspects of your weather-informed trading system, including:

- **Weather Data Analysis**: Real-time weather patterns and historical trends
- **Market Monitoring**: Polymarket probability changes and trading opportunities
- **Performance Tracking**: P&L analysis, position management, and trade history
- **System Health**: API connectivity, data quality, and component status
- **Configuration Management**: API key setup and system settings

## 🏗️ Architecture

### Backend (FastAPI)

- **Framework**: FastAPI with automatic API documentation
- **Database**: SQLite integration with existing ClimaTrade database
- **CORS**: Configured for React frontend communication
- **Port**: 8001 (to avoid conflicts with other services)

### Frontend (React + TypeScript)

- **UI Framework**: React 18 with TypeScript
- **Charts**: Recharts for interactive data visualization
- **Styling**: Tailwind CSS for responsive design
- **Icons**: Lucide React for consistent iconography
- **Port**: 3000 (standard React development port)

### Database Integration

- Connects to existing `data/climatetrade.db`
- Reads from all major tables: weather_data, polymarket_data, trading_history, etc.
- Real-time data updates with manual refresh capability

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- Existing ClimaTrade database (`data/climatetrade.db`)

### Installation & Setup

1. **Backend Dependencies**:

   ```bash
   cd web/backend
   pip install -r requirements.txt
   ```

2. **Frontend Dependencies**:
   ```bash
   cd web/frontend
   npm install
   ```

### Running the Dashboard

#### Option 1: Integrated Startup (Recommended)

```bash
python scripts/start_system.py --mode dashboard
```

#### Option 2: Manual Startup

```bash
# Terminal 1: Start Backend
cd web/backend
python main.py

# Terminal 2: Start Frontend
cd web/frontend
npm start
```

#### Option 3: Docker Deployment

```bash
cd web
docker-compose up --build
```

### Access URLs

- **Dashboard**: http://localhost:3000
- **API Backend**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## 📊 Dashboard Features

### 1. Weather Data Dashboard

- **Interactive Charts**: Temperature, humidity, precipitation trends
- **Location Filtering**: Select specific geographic areas
- **Real-time Stats**: Current weather conditions summary
- **Historical Data**: 24-hour rolling window with zoom/pan

### 2. Market Data Dashboard

- **Probability Trends**: Time-series charts of market probabilities
- **Market Selection**: Browse and analyze different Polymarket events
- **Volume Analysis**: Trading volume and liquidity metrics
- **Outcome Tracking**: Multi-outcome probability visualization

### 3. Trading Performance Dashboard

- **P&L Analysis**: Daily and cumulative profit/loss charts
- **Position Management**: Current holdings with unrealized P&L
- **Trade History**: Complete transaction log with filtering
- **Performance Metrics**: Win rate, average trade size, total volume

### 4. System Health Monitor

- **API Status**: Real-time connectivity checks for all services
- **Data Quality**: Record counts and freshness indicators
- **Component Health**: Database, backend, and external service status
- **Alert System**: Automated notifications for issues

### 5. API Configuration Panel

- **Key Management**: Secure input for all required API keys
- **Status Indicators**: Visual feedback for configured vs missing keys
- **Validation**: Real-time validation and setup instructions
- **Security**: Password-masked input with confirmation

## 🔧 API Reference

### Weather Endpoints

```
GET /api/weather/data?hours=24&location=London&source=met_office
GET /api/weather/sources
```

### Market Endpoints

```
GET /api/markets/overview
GET /api/markets/{market_id}/data?hours=24
```

### Trading Endpoints

```
GET /api/trading/performance?days=30
GET /api/trading/positions
```

### System Endpoints

```
GET /api/system/health
GET /api/system/config
```

### Request Parameters

- `hours`: Time window for data (default: 24)
- `location`: Geographic filter for weather data
- `source`: Data source filter
- `days`: Time window for trading data
- `market_id`: Specific market identifier

## ⚙️ Configuration

### Environment Variables

Set these in your environment or `.env` file:

```bash
# Required API Keys
MET_OFFICE_API_KEY=your_met_office_key
POLYGON_WALLET_PRIVATE_KEY=your_polygon_key

# Optional API Keys
METEOSTAT_API_KEY=your_meteostat_key
WEATHER_UNDERGROUND_API_KEY=your_wunderground_key
WEATHER2GEO_API_KEY=your_weather2geo_key
```

### Database Configuration

- **Path**: `../data/climatetrade.db` (relative to backend)
- **Tables**: All existing ClimaTrade tables are supported
- **Connection**: Automatic SQLite connection with error handling

## 🎨 UI Components

### Dashboard Layout

- **Navigation**: Tab-based navigation (Dashboard, Health, Config)
- **Responsive**: Mobile-friendly design with Tailwind CSS
- **Real-time**: Manual refresh with loading indicators
- **Status**: System health indicators in header

### Data Visualization

- **Charts**: Interactive Recharts components
- **Filtering**: Dropdown selectors and date ranges
- **Export**: Data export capabilities (future feature)
- **Themes**: Light/dark mode support (future feature)

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. Database Connection Issues

**Symptoms**: "Database not found" errors
**Solutions**:

- Verify `data/climatetrade.db` exists
- Check file permissions
- Ensure correct relative path

#### 2. API Key Problems

**Symptoms**: Missing data, authentication errors
**Solutions**:

- Check environment variables are set
- Verify API keys are valid and active
- Use dashboard's API Config tab to update

#### 3. Port Conflicts

**Symptoms**: "Port already in use" errors
**Current Configuration**:

- Backend: 8001
- Frontend: 3000
  **Solutions**:
- Modify ports in respective configuration files
- Kill conflicting processes

#### 4. CORS Issues

**Symptoms**: Frontend can't connect to backend
**Solutions**:

- Verify backend is running on correct port
- Check CORS settings in `backend/main.py`
- Ensure frontend is accessing correct URL

#### 5. Missing Dependencies

**Symptoms**: Import errors, missing modules
**Solutions**:

- Run `pip install -r requirements.txt` in backend
- Run `npm install` in frontend
- Check Python/Node versions match requirements

### Debug Information

- **Backend Logs**: Console output from FastAPI
- **Frontend Logs**: Browser developer tools
- **API Testing**: Visit http://localhost:8001/docs for interactive API testing
- **Database Inspection**: Use SQLite browser to check data

## 🛠️ Development

### Backend Development

```bash
cd web/backend
pip install -r requirements.txt
python main.py  # With auto-reload
```

### Frontend Development

```bash
cd web/frontend
npm install
npm start  # Hot reload enabled
```

### Testing

```bash
# Backend tests
cd web/backend
python -m pytest

# Frontend tests
cd web/frontend
npm test
```

### Building for Production

```bash
# Frontend build
cd web/frontend
npm run build

# Backend deployment
# Use gunicorn or similar for production
```

## 📁 Project Structure

```
web/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── WeatherDashboard.tsx
│   │   │   ├── MarketDashboard.tsx
│   │   │   ├── TradingDashboard.tsx
│   │   │   ├── SystemHealth.tsx
│   │   │   └── ApiConfig.tsx
│   │   ├── App.tsx         # Main application
│   │   ├── index.tsx       # Entry point
│   │   └── index.css       # Global styles
│   ├── package.json        # Node dependencies
│   └── Dockerfile          # Frontend container
├── docker-compose.yml      # Container orchestration
└── README.md              # This documentation
```

## 🤝 Contributing

### Code Standards

1. **TypeScript**: Strict typing for all React components
2. **Python**: Type hints and docstrings for API endpoints
3. **Styling**: Tailwind CSS classes with consistent naming
4. **Error Handling**: Comprehensive error boundaries and API error handling

### Adding New Features

1. Create feature branch from `main`
2. Implement backend API endpoints first
3. Build corresponding React components
4. Update documentation
5. Test integration thoroughly

### Component Guidelines

- Use functional components with hooks
- Implement proper TypeScript interfaces
- Include loading states and error handling
- Follow existing naming conventions
- Add comprehensive comments

## 📈 Future Enhancements

### Planned Features

- **Real-time WebSocket Updates**: Live data streaming
- **Advanced Filtering**: Date range pickers, multi-select filters
- **Data Export**: CSV/PDF export capabilities
- **Alert System**: Email/SMS notifications for critical events
- **Dark Mode**: Theme switching capability
- **Mobile App**: React Native companion app

### Performance Optimizations

- **Data Caching**: Redis integration for faster queries
- **Lazy Loading**: Component-based code splitting
- **Database Indexing**: Query optimization for large datasets
- **CDN Integration**: Static asset optimization

## 📄 License

This dashboard is part of the ClimaTrade AI project and follows the same licensing terms.

## 🆘 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review API documentation at `/docs`
3. Check system logs for error details
4. Verify all prerequisites are met

---

**Last Updated**: September 5, 2025
**Version**: 1.0.0
**Authors**: ClimaTrade AI Development Team
