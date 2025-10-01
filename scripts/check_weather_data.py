#!/usr/bin/env python3
"""
Check weather data in the database
"""

import sqlite3
import sys
import os

def main():
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "climatetrade.db")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check meteostat data
        cursor.execute("""
            SELECT location_name, temperature, humidity, timestamp, source_id
            FROM weather_data
            WHERE source_id = 2
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        results = cursor.fetchall()

        print("Recent meteostat weather data:")
        print("-" * 50)

        for row in results:
            location, temp, humidity, timestamp, source_id = row
            print(f"Location: {location}")
            print(f"Temperature: {temp} C")
            print(f"Humidity: {humidity}%")
            print(f"Timestamp: {timestamp}")
            print(f"Source ID: {source_id}")
             print("-" * 30)

        # Count total records
        cursor.execute("SELECT COUNT(*) FROM weather_data WHERE source_id = 2")
        count = cursor.fetchone()[0]
        print(f"\nTotal meteostat records: {count}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()