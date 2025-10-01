"""
ClimaTrade AI Dashboard Backend
FastAPI application serving data for the React dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import json
try:
    from .clob_service import clob_service
    from .weather_service import weather_service
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from clob_service import clob_service
    try:
        from weather_service import weather_service
    except ImportError:
        weather_service = None
        print("WARNING: Weather service not available - weather endpoints will return 404")

app = FastAPI(title="ClimaTrade AI Dashboard API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "climatetrade.db"

def get_db_connection():
    """Get database connection"""
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database not found")
    return sqlite3.connect(str(DB_PATH))

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ClimaTrade AI Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        weather_count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "weather_records": weather_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Enhanced Weather endpoints
@app.get("/api/weather/24h/{city}")
async def get_24h_weather(city: str):
    """Get 24-hour weather history for a city - returns structured data with timeline and summary"""
    try:
        if weather_service is None:
            raise HTTPException(status_code=503, detail="Weather service not available")
        
        weather_data = weather_service.get_24h_weather_history(city)
        return weather_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weather data: {str(e)}")

@app.get("/api/weather/comparison")
async def get_weather_comparison(city1: str = "london", city2: str = "nyc"):
    """Compare weather between two cities"""
    try:
        comparison = weather_service.get_weather_comparison(city1, city2)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare weather: {str(e)}")

@app.get("/api/weather/cities")
async def get_available_cities():
    """Get list of available cities for weather data"""
    cities = {
        "london": {
            "name": "London, UK",
            "coordinates": {"lat": 51.5074, "lon": -0.1278},
            "timezone": "Europe/London"
        },
        "nyc": {
            "name": "New York, NY",
            "coordinates": {"lat": 40.7128, "lon": -74.0060},
            "timezone": "America/New_York"
        }
    }
    return {"cities": cities, "count": len(cities)}

# Weather endpoints
@app.get("/api/weather/sources")
async def get_weather_sources():
    """Get available weather data sources"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, source_name, description, api_key_required, active
            FROM weather_sources
            ORDER BY source_name
        """)
        sources = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "requires_key": bool(row[3]),
                "active": bool(row[4])
            }
            for row in sources
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather/refresh")
async def refresh_weather_data():
    """Refresh weather data by fetching latest from external APIs"""
    try:
        if weather_service is None:
            raise HTTPException(status_code=503, detail="Weather service not available")

        refreshed_cities = []

        # Refresh data for London and NYC
        for city in ['london', 'nyc']:
            try:
                weather_data = weather_service.get_24h_weather_history(city)
                refreshed_cities.append({
                    'city': city,
                    'data_points': weather_data.get('data_points', 0),
                    'source': weather_data.get('source', 'unknown')
                })
            except Exception as e:
                print(f"Failed to refresh {city}: {str(e)}")
                refreshed_cities.append({
                    'city': city,
                    'error': str(e)
                })

        return {
            'status': 'completed',
            'refreshed_cities': refreshed_cities,
            'timestamp': datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh weather data: {str(e)}")

def _map_city_name_to_key(city_name: str) -> str:
    """Map full city name to backend city key"""
    city_mapping = {
        'london,uk': 'london',
        'new york,ny': 'nyc',
        'new york,ny': 'nyc',
        'new york': 'nyc'
    }
    sanitized = city_name.strip().lower()
    return city_mapping.get(sanitized, sanitized)

@app.get("/api/weather/data")
async def get_weather_data(
    location: Optional[str] = None,
    source: Optional[str] = None,
    hours: int = 24
):
    """Get weather data for dashboard - supports both database query and real-time API calls"""
    try:
        # If location parameter is provided, use real-time weather service
        if location and weather_service:
            try:
                # Map frontend city name to backend key
                city_key = _map_city_name_to_key(location)
                print(f"DEBUG: Mapped frontend city '{location}' to backend key '{city_key}'")
                
                # Get real-time data from weather service
                weather_data = weather_service.get_24h_weather_history(city_key)
                
                # Format data for frontend compatibility
                if weather_data and 'timeline' in weather_data:
                    return weather_data['timeline']
                else:
                    # Fall back to database query if real-time data not available
                    print(f"DEBUG: No timeline data from weather service for {city_key}")
                    pass
            except Exception as e:
                print(f"Real-time weather service failed for {location}: {e}")
                # Fall through to database query
        
        # Database query fallback
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        query = """
            SELECT
                wd.timestamp,
                wd.location_name,
                ws.source_name,
                wd.temperature,
                wd.humidity,
                wd.precipitation,
                wd.wind_speed,
                wd.weather_description,
                wd.feels_like,
                wd.pressure,
                wd.wind_direction,
                wd.visibility
            FROM weather_data wd
            JOIN weather_sources ws ON wd.source_id = ws.id
            WHERE wd.timestamp >= ?
            AND wd.timestamp <= ?
        """
        params = [start_time.isoformat(), end_time.isoformat()]

        if location:
            query += " AND wd.location_name LIKE ?"
            params.append(f"%{location}%")

        if source:
            query += " AND ws.source_name = ?"
            params.append(source)

        query += " ORDER BY wd.timestamp DESC LIMIT 1000"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Format data for frontend compatibility
        formatted_data = []
        for row in rows:
            data_point = {
                "timestamp": row[0],
                "temperature": row[3],
                "humidity": row[4],
                "precipitation": row[5],
                "weather_description": row[7],
                "feels_like": row[8],
                "data_type": "historical"
            }
            # Only include fields that are not None
            if row[9] is not None:  # pressure
                data_point["pressure"] = row[9]
            if row[10] is not None:  # wind_direction
                data_point["wind_direction"] = row[10]
            if row[11] is not None:  # visibility
                data_point["visibility"] = row[11]
            formatted_data.append(data_point)

        return formatted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Market endpoints
@app.get("/api/markets/overview")
async def get_markets_overview():
    """Get markets overview for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                m.market_id,
                m.question,
                m.volume,
                m.liquidity,
                COUNT(md.id) as data_points,
                MAX(md.timestamp) as last_update
            FROM polymarket_markets m
            LEFT JOIN polymarket_data md ON m.market_id = md.market_id
            GROUP BY m.market_id, m.question, m.volume, m.liquidity
            ORDER BY m.volume DESC
            LIMIT 50
        """)

        markets = cursor.fetchall()
        conn.close()

        return [
            {
                "market_id": row[0],
                "question": row[1],
                "volume": row[2] or 0,
                "liquidity": row[3] or 0,
                "data_points": row[4],
                "last_update": row[5]
            }
            for row in markets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets/{market_id}/data")
async def get_market_data(market_id: str, hours: int = 24):
    """Get market data for specific market"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        cursor.execute("""
            SELECT
                timestamp,
                outcome_name,
                probability,
                volume
            FROM polymarket_data
            WHERE market_id = ?
            AND timestamp >= ?
            AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1000
        """, [market_id, start_time.isoformat(), end_time.isoformat()])

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "timestamp": row[0],
                "outcome": row[1],
                "probability": row[2],
                "volume": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trading endpoints
@app.get("/api/trading/performance")
async def get_trading_performance(days: int = 30):
    """Get trading performance data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        cursor.execute("""
            SELECT
                DATE(open_timestamp) as date,
                COUNT(*) as trades,
                SUM(total_value) as volume,
                AVG(price) as avg_price,
                SUM(pnl) as total_pnl
            FROM trading_history
            WHERE open_timestamp >= ?
            AND open_timestamp <= ?
            GROUP BY DATE(open_timestamp)
            ORDER BY date
        """, [start_date.isoformat(), end_date.isoformat()])

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "date": row[0],
                "trades": row[1],
                "volume": row[2] or 0,
                "avg_price": row[3] or 0,
                "total_pnl": row[4] or 0
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/positions")
async def get_current_positions():
    """Get current trading positions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pp.market_id,
                pp.outcome,
                pp.quantity,
                pp.average_price,
                pp.current_price,
                pp.unrealized_pnl,
                pm.question
            FROM portfolio_positions pp
            JOIN polymarket_markets pm ON pp.market_id = pm.market_id
            WHERE pp.status = 'open'
            ORDER BY ABS(pp.unrealized_pnl) DESC
        """)

        positions = cursor.fetchall()
        conn.close()

        return [
            {
                "market_id": row[0],
                "outcome": row[1],
                "quantity": row[2],
                "avg_price": row[3],
                "current_price": row[4],
                "unrealized_pnl": row[5],
                "question": row[6]
            }
            for row in positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Polymarket CLOB Trading endpoints
@app.get("/api/clob/status")
async def get_clob_status():
    """Get CLOB connection status"""
    try:
        status = clob_service.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLOB status check failed: {str(e)}")

@app.get("/api/clob/markets")
async def get_clob_markets(limit: int = 50):
    """Get available Polymarket trading markets"""
    try:
        markets = clob_service.get_markets(limit=limit)
        return {"markets": markets, "count": len(markets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get markets: {str(e)}")

@app.get("/api/clob/markets/{market_id}")
async def get_clob_market_details(market_id: str):
    """Get detailed market information"""
    try:
        market = clob_service.get_market_details(market_id)
        return market
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Market not found: {str(e)}")

@app.get("/api/clob/orderbook/{token_id}")
async def get_clob_order_book(token_id: str):
    """Get order book for a specific token"""
    try:
        orderbook = clob_service.get_order_book(token_id)
        return orderbook
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order book: {str(e)}")

@app.get("/api/clob/price/{token_id}")
async def get_clob_price(token_id: str, side: str = "BUY"):
    """Get current market price for a token"""
    try:
        price_data = clob_service.get_price(token_id, side)
        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price: {str(e)}")

@app.get("/api/clob/balance")
async def get_clob_balance():
    """Get user balance and allowance"""
    try:
        balance = clob_service.get_balance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")

@app.get("/api/clob/orders")
async def get_clob_orders():
    """Get user's open orders"""
    try:
        orders = clob_service.get_open_orders()
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")

@app.post("/api/clob/orders/limit")
async def place_limit_order(order_data: dict):
    """Place a limit order"""
    try:
        required_fields = ["token_id", "price", "size", "side"]
        for field in required_fields:
            if field not in order_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        result = clob_service.place_limit_order(
            token_id=order_data["token_id"],
            price=float(order_data["price"]),
            size=float(order_data["size"]),
            side=order_data["side"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place limit order: {str(e)}")

@app.post("/api/clob/orders/market")
async def place_market_order(order_data: dict):
    """Place a market order"""
    try:
        required_fields = ["token_id", "amount", "side"]
        for field in required_fields:
            if field not in order_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        result = clob_service.place_market_order(
            token_id=order_data["token_id"],
            amount=float(order_data["amount"]),
            side=order_data["side"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place market order: {str(e)}")

@app.delete("/api/clob/orders/{order_id}")
async def cancel_clob_order(order_id: str):
    """Cancel a specific order"""
    try:
        result = clob_service.cancel_order(order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

@app.delete("/api/clob/orders")
async def cancel_all_clob_orders():
    """Cancel all open orders"""
    try:
        result = clob_service.cancel_all_orders()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel all orders: {str(e)}")

# System endpoints
@app.get("/api/system/config")
async def get_system_config():
    """Get system configuration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT config_key, config_value FROM system_config")
        configs = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/health")
async def get_system_health():
    """Get system health status"""
    try:
        print("DEBUG: System health check requested")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check various components
        health_status = {}

        # Database tables check
        tables = ['weather_data', 'polymarket_data', 'trading_history']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            health_status[f"{table}_count"] = count
            print(f"DEBUG: {table} count: {count}")

        # API keys check
        api_keys = {}
        env_vars = ['MET_OFFICE_API_KEY', 'POLYGON_WALLET_PRIVATE_KEY']
        for var in env_vars:
            is_set = bool(os.getenv(var))
            api_keys[var] = is_set
            print(f"DEBUG: {var} configured: {is_set}")
        health_status["api_keys"] = api_keys

        # Recent data check
        cursor.execute("""
            SELECT MAX(timestamp) FROM weather_data
            UNION ALL
            SELECT MAX(timestamp) FROM polymarket_data
        """)
        recent_data = cursor.fetchall()
        health_status["latest_weather"] = recent_data[0][0] if recent_data[0][0] else None
        health_status["latest_market"] = recent_data[1][0] if recent_data[1][0] else None
        print(f"DEBUG: Latest weather: {health_status['latest_weather']}")
        print(f"DEBUG: Latest market: {health_status['latest_market']}")

        conn.close()

        print(f"DEBUG: Returning health status: {health_status}")
        return health_status
    except Exception as e:
        print(f"DEBUG: Error in system health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)