import sqlite3
import sys

def check_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('data/climatetrade.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if weather_sources table exists
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='weather_sources';")
        weather_sources_exists = cursor.fetchone()[0] > 0
        
        # Check if weather_data table exists
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='weather_data';")
        weather_data_exists = cursor.fetchone()[0] > 0
        
        print(f"\nweather_sources table exists: {weather_sources_exists}")
        print(f"weather_data table exists: {weather_data_exists}")
        
        # If tables exist, check for data
        if weather_sources_exists:
            cursor.execute("SELECT COUNT(*) FROM weather_sources;")
            sources_count = cursor.fetchone()[0]
            print(f"Number of records in weather_sources: {sources_count}")
            
            if sources_count > 0:
                cursor.execute("SELECT * FROM weather_sources LIMIT 5;")
                sources_data = cursor.fetchall()
                print("\nSample weather_sources data:")
                for row in sources_data:
                    print(f"  {row}")
        
        if weather_data_exists:
            cursor.execute("SELECT COUNT(*) FROM weather_data;")
            data_count = cursor.fetchone()[0]
            print(f"Number of records in weather_data: {data_count}")
            
            if data_count > 0:
                cursor.execute("SELECT * FROM weather_data LIMIT 5;")
                data_records = cursor.fetchall()
                print("\nSample weather_data data:")
                for row in data_records:
                    print(f"  {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_database()