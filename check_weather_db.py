#!/usr/bin/env python3
"""
Check weather data in database
"""

import sqlite3
import os

def main():
    db_path = 'data/climatetrade.db'

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    if 'weather_data' in tables:
        # Count records
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        count = cursor.fetchone()[0]
        print(f"Weather data records: {count}")

        # Sample data
        cursor.execute("""
            SELECT wd.location_name, ws.source_name, wd.timestamp, wd.temperature
            FROM weather_data wd
            JOIN weather_sources ws ON wd.source_id = ws.id
            ORDER BY wd.timestamp DESC
            LIMIT 10
        """)
        print("Sample weather data:")
        for row in cursor.fetchall():
            print(f"  {row}")

    if 'weather_sources' in tables:
        cursor.execute("SELECT source_name FROM weather_sources")
        sources = [row[0] for row in cursor.fetchall()]
        print(f"Weather sources: {sources}")

    conn.close()

if __name__ == "__main__":
    main()