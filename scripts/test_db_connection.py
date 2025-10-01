#!/usr/bin/env python3
"""
Simple test script to verify database connection and meteostat functionality
"""

import sqlite3
import sys
import os

# Add meteostat-python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'meteostat-python'))

def test_db_connection():
    """Test database connection and table access."""
    try:
        conn = sqlite3.connect('../data/climatetrade.db')
        cursor = conn.cursor()

        # Test weather_sources table
        cursor.execute("SELECT id, source_name FROM weather_sources WHERE source_name = 'meteostat'")
        result = cursor.fetchone()
        print(f"[SUCCESS] Database connection successful. Meteostat source: {result}")

        # Test weather_data table structure
        cursor.execute("PRAGMA table_info(weather_data)")
        columns = cursor.fetchall()
        print(f"[SUCCESS] Weather data table has {len(columns)} columns")

        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return False

def test_meteostat_import():
    """Test meteostat library import."""
    try:
        from meteostat import Point, Hourly
        print("[SUCCESS] Meteostat library import successful")
        return True
    except ImportError as e:
        print(f"[ERROR] Meteostat import error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Database and Meteostat Setup ===")

    db_ok = test_db_connection()
    meteostat_ok = test_meteostat_import()

    if db_ok and meteostat_ok:
        print("\n[SUCCESS] All tests passed! Ready to run weather collection scripts.")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed. Please check the setup.")
        sys.exit(1)