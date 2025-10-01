import sqlite3

def check_database():
    conn = sqlite3.connect('data/climatetrade.db')
    cursor = conn.cursor()

    # Check weather sources
    cursor.execute('SELECT * FROM weather_sources')
    sources = cursor.fetchall()
    print('Weather Sources:')
    for s in sources:
        print(f'  {s}')

    # Check weather data count
    cursor.execute('SELECT COUNT(*) FROM weather_data')
    count = cursor.fetchone()[0]
    print(f'Weather data records: {count}')

    # Check market data
    cursor.execute('SELECT COUNT(*) FROM polymarket_data')
    market_count = cursor.fetchone()[0]
    print(f'Market data records: {market_count}')

    # Check recent weather data
    cursor.execute('SELECT location_name, timestamp, temperature FROM weather_data ORDER BY timestamp DESC LIMIT 5')
    recent_weather = cursor.fetchall()
    print('Recent weather data:')
    for w in recent_weather:
        print(f'  {w}')

    # Check recent market data
    cursor.execute('SELECT market_id, timestamp, probability FROM polymarket_data ORDER BY timestamp DESC LIMIT 5')
    recent_market = cursor.fetchall()
    print('Recent market data:')
    for m in recent_market:
        print(f'  {m}')

    conn.close()

if __name__ == '__main__':
    check_database()