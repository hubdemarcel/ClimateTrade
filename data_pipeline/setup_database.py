#!/usr/bin/env python3
"""
Database Setup Script for ClimateTrade Data Pipeline

This script initializes the SQLite database with the defined schema
for storing Polymarket and weather data.
"""

import sqlite3
import os
import sys
from pathlib import Path

def setup_database(db_path: str = "climatetrade.db"):
    """
    Set up the SQLite database with the schema.

    Args:
        db_path: Path to the database file
    """
    # Ensure data directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # Read schema file
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Connect to database and execute schema
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute schema
        cursor.executescript(schema_sql)

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        print("Database setup completed successfully!")
        print(f"Database location: {db_path}")
        print(f"Created tables: {', '.join(table_names)}")

        # Show table info
        for table in ['polymarket_data', 'weather_data', 'weather_sources']:
            if table in table_names:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                print(f"\n{table.upper()} columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Set up ClimateTrade database")
    parser.add_argument(
        "--db-path",
        default="data/climatetrade.db",
        help="Path to the database file (default: data/climatetrade.db)"
    )

    args = parser.parse_args()

    print("Setting up ClimateTrade database...")
    setup_database(args.db_path)
    print("Database setup complete!")

if __name__ == "__main__":
    main()