#!/usr/bin/env python3
"""
Data Querying Script for ClimateTrade Database

This script provides basic querying capabilities for Polymarket and weather data.
"""

import sqlite3
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import sys
from pathlib import Path

class ClimateTradeQuerier:
    """Handles querying of ClimateTrade database."""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self.ensure_db_exists()

    def ensure_db_exists(self):
        """Ensure the database file exists."""
        if not Path(self.db_path).exists():
            print(f"Error: Database not found at {self.db_path}")
            sys.exit(1)

    def connect_db(self):
        """Connect to the database."""
        return sqlite3.connect(self.db_path)

    def get_polymarket_summary(self) -> Dict:
        """Get summary statistics for Polymarket data."""
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            # Total records
            cursor.execute("SELECT COUNT(*) FROM polymarket_data")
            total_records = cursor.fetchone()[0]

            # Unique markets
            cursor.execute("SELECT COUNT(DISTINCT market_id) FROM polymarket_data")
            unique_markets = cursor.fetchone()[0]

            # Unique events
            cursor.execute("SELECT COUNT(DISTINCT event_title) FROM polymarket_data")
            unique_events = cursor.fetchone()[0]

            # Date range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM polymarket_data")
            date_range = cursor.fetchone()

            # Recent records (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM polymarket_data WHERE timestamp > ?", (yesterday,))
            recent_records = cursor.fetchone()[0]

            return {
                'total_records': total_records,
                'unique_markets': unique_markets,
                'unique_events': unique_events,
                'date_range': date_range,
                'recent_records_24h': recent_records
            }

        finally:
            conn.close()

    def get_weather_summary(self) -> Dict:
        """Get summary statistics for weather data."""
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            # Total records
            cursor.execute("SELECT COUNT(*) FROM weather_data")
            total_records = cursor.fetchone()[0]

            # Sources
            cursor.execute("""
                SELECT ws.source_name, COUNT(wd.id) as count
                FROM weather_sources ws
                LEFT JOIN weather_data wd ON ws.id = wd.source_id
                GROUP BY ws.id, ws.source_name
            """)
            sources = cursor.fetchall()

            # Locations
            cursor.execute("SELECT COUNT(DISTINCT location_name) FROM weather_data")
            unique_locations = cursor.fetchone()[0]

            # Date range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM weather_data")
            date_range = cursor.fetchone()

            return {
                'total_records': total_records,
                'sources': dict(sources),
                'unique_locations': unique_locations,
                'date_range': date_range
            }

        finally:
            conn.close()

    def query_polymarket_data(self,
                            market_id: Optional[str] = None,
                            event_title: Optional[str] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            limit: int = 100) -> List[Dict]:
        """Query Polymarket data with filters."""
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            query = """
                SELECT event_title, event_url, market_id, outcome_name,
                       probability, volume, timestamp, scraped_at
                FROM polymarket_data
                WHERE 1=1
            """
            params = []

            if market_id:
                query += " AND market_id = ?"
                params.append(market_id)

            if event_title:
                query += " AND event_title LIKE ?"
                params.append(f"%{event_title}%")

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

        finally:
            conn.close()

    def query_weather_data(self,
                          location: Optional[str] = None,
                          source: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """Query weather data with filters."""
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            query = """
                SELECT wd.*, ws.source_name
                FROM weather_data wd
                JOIN weather_sources ws ON wd.source_id = ws.id
                WHERE 1=1
            """
            params = []

            if location:
                query += " AND wd.location_name LIKE ?"
                params.append(f"%{location}%")

            if source:
                query += " AND ws.source_name = ?"
                params.append(source)

            if start_date:
                query += " AND wd.timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND wd.timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY wd.timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

        finally:
            conn.close()

    def get_market_probability_trends(self, market_id: str, days: int = 30) -> List[Dict]:
        """Get probability trends for a specific market."""
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
                SELECT outcome_name, probability, timestamp
                FROM polymarket_data
                WHERE market_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """

            cursor.execute(query, (market_id, start_date))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

        finally:
            conn.close()

    def get_weather_correlation_data(self,
                                   location: str,
                                   start_date: str,
                                   end_date: str) -> Dict:
        """Get weather and market data for correlation analysis."""
        weather_data = self.query_weather_data(
            location=location,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        # Get market data for the same period
        market_data = self.query_polymarket_data(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        return {
            'weather_data': weather_data,
            'market_data': market_data,
            'period': {'start': start_date, 'end': end_date}
        }

def print_summary(querier: ClimateTradeQuerier):
    """Print database summary."""
    print("=== ClimateTrade Database Summary ===\n")

    # Polymarket summary
    pm_summary = querier.get_polymarket_summary()
    print("Polymarket Data:")
    print(f"  Total records: {pm_summary['total_records']}")
    print(f"  Unique markets: {pm_summary['unique_markets']}")
    print(f"  Unique events: {pm_summary['unique_events']}")
    print(f"  Date range: {pm_summary['date_range']}")
    print(f"  Recent records (24h): {pm_summary['recent_records_24h']}\n")

    # Weather summary
    weather_summary = querier.get_weather_summary()
    print("Weather Data:")
    print(f"  Total records: {weather_summary['total_records']}")
    print(f"  Unique locations: {weather_summary['unique_locations']}")
    print(f"  Date range: {weather_summary['date_range']}")
    print("  Sources:")
    for source, count in weather_summary['sources'].items():
        print(f"    {source}: {count} records")

def main():
    parser = argparse.ArgumentParser(description="Query ClimateTrade database")
    parser.add_argument(
        "--db-path",
        default="data/climatetrade.db",
        help="Path to the database file"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Summary command
    subparsers.add_parser('summary', help='Show database summary')

    # Query polymarket
    pm_parser = subparsers.add_parser('polymarket', help='Query Polymarket data')
    pm_parser.add_argument('--market-id', help='Filter by market ID')
    pm_parser.add_argument('--event-title', help='Filter by event title (partial match)')
    pm_parser.add_argument('--start-date', help='Start date (ISO format)')
    pm_parser.add_argument('--end-date', help='End date (ISO format)')
    pm_parser.add_argument('--limit', type=int, default=100, help='Limit results')

    # Query weather
    weather_parser = subparsers.add_parser('weather', help='Query weather data')
    weather_parser.add_argument('--location', help='Filter by location (partial match)')
    weather_parser.add_argument('--source', help='Filter by source')
    weather_parser.add_argument('--start-date', help='Start date (ISO format)')
    weather_parser.add_argument('--end-date', help='End date (ISO format)')
    weather_parser.add_argument('--limit', type=int, default=100, help='Limit results')

    # Market trends
    trends_parser = subparsers.add_parser('trends', help='Get market probability trends')
    trends_parser.add_argument('market_id', help='Market ID to analyze')
    trends_parser.add_argument('--days', type=int, default=30, help='Number of days to look back')

    # Correlation data
    corr_parser = subparsers.add_parser('correlation', help='Get weather-market correlation data')
    corr_parser.add_argument('--location', required=True, help='Location for weather data')
    corr_parser.add_argument('--start-date', required=True, help='Start date (ISO format)')
    corr_parser.add_argument('--end-date', required=True, help='End date (ISO format)')

    args = parser.parse_args()

    querier = ClimateTradeQuerier(args.db_path)

    if args.command == 'summary':
        print_summary(querier)

    elif args.command == 'polymarket':
        results = querier.query_polymarket_data(
            market_id=args.market_id,
            event_title=args.event_title,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit
        )
        print(json.dumps(results, indent=2, default=str))

    elif args.command == 'weather':
        results = querier.query_weather_data(
            location=args.location,
            source=args.source,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit
        )
        print(json.dumps(results, indent=2, default=str))

    elif args.command == 'trends':
        results = querier.get_market_probability_trends(args.market_id, args.days)
        print(json.dumps(results, indent=2, default=str))

    elif args.command == 'correlation':
        results = querier.get_weather_correlation_data(
            args.location, args.start_date, args.end_date
        )
        print(json.dumps(results, indent=2, default=str))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()