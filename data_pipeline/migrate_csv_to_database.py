#!/usr/bin/env python3
"""
CSV to Database Migration Script for ClimateTrade AI
Migrates existing CSV files to the polymarket_data table in SQLite database
"""

import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Add project root to path for database utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import centralized logging if available
try:
    from utils.logging import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)


class CSVDataMigrator:
    """Handles migration of CSV data to SQLite database"""

    def __init__(self, db_path: str = "../data/climatetrade.db", csv_dir: str = "data/"):
        self.db_path = Path(__file__).parent / db_path
        self.csv_dir = Path(__file__).parent / csv_dir
        self.migration_stats = {
            'files_processed': 0,
            'records_migrated': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

    def ensure_database_exists(self) -> bool:
        """Ensure the database exists before migration"""
        if not self.db_path.exists():
            logger.error(f"Database not found at {self.db_path}")
            logger.info("Please run database setup first: cd database && python setup_database.py")
            return False
        return True

    def get_csv_files(self) -> List[Path]:
        """Get all CSV files in the data directory"""
        if not self.csv_dir.exists():
            logger.error(f"CSV directory not found: {self.csv_dir}")
            return []

        csv_files = list(self.csv_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files in {self.csv_dir}")
        return sorted(csv_files)

    def validate_csv_structure(self, df: pd.DataFrame, filename: str) -> bool:
        """Validate CSV structure matches expected format"""
        required_columns = ['event_title', 'event_url', 'market_id', 'outcome_name',
                          'probability', 'volume', 'timestamp', 'scraped_at']

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns in {filename}: {missing_columns}")
            return False

        # Check for empty dataframe
        if df.empty:
            logger.warning(f"Empty CSV file: {filename}")
            return False

        return True

    def clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types for database insertion"""
        # Convert numeric columns
        df['probability'] = pd.to_numeric(df['probability'], errors='coerce').fillna(0.0)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0.0)

        # Ensure timestamps are strings
        df['timestamp'] = df['timestamp'].astype(str)
        df['scraped_at'] = df['scraped_at'].astype(str)

        # Handle NaN values
        df = df.fillna('')

        return df

    def migrate_csv_file(self, csv_file: Path, conn: sqlite3.Connection) -> bool:
        """Migrate a single CSV file to database"""
        try:
            logger.info(f"Processing: {csv_file.name}")

            # Read CSV file
            df = pd.read_csv(csv_file)

            # Validate structure
            if not self.validate_csv_structure(df, csv_file.name):
                self.migration_stats['errors'] += 1
                return False

            # Clean data types
            df = self.clean_data_types(df)

            # Prepare data for insertion
            records = []
            duplicates_skipped = 0

            for _, row in df.iterrows():
                # Check for duplicates (market_id, outcome_name, timestamp combination)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM polymarket_data
                    WHERE market_id = ? AND outcome_name = ? AND timestamp = ?
                """, (row['market_id'], row['outcome_name'], row['timestamp']))

                if cursor.fetchone():
                    duplicates_skipped += 1
                    continue

                records.append((
                    row['market_id'],
                    row['event_title'],
                    row['event_url'],
                    row['outcome_name'],
                    float(row['probability']),
                    float(row['volume']),
                    row['timestamp'],
                    row['scraped_at']
                ))

            # Insert records in batches
            if records:
                cursor.executemany("""
                    INSERT INTO polymarket_data
                    (market_id, event_title, event_url, outcome_name, probability, volume, timestamp, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, records)

                logger.info(f"Migrated {len(records)} records from {csv_file.name}")
                self.migration_stats['records_migrated'] += len(records)
            else:
                logger.info(f"No new records to migrate from {csv_file.name}")

            if duplicates_skipped > 0:
                logger.info(f"Skipped {duplicates_skipped} duplicate records")
                self.migration_stats['duplicates_skipped'] += duplicates_skipped

            self.migration_stats['files_processed'] += 1
            return True

        except Exception as e:
            logger.error(f"Error migrating {csv_file.name}: {e}")
            self.migration_stats['errors'] += 1
            return False

    def run_migration(self, dry_run: bool = False) -> bool:
        """Run the complete migration process"""
        logger.info("Starting CSV to Database Migration")
        logger.info("=" * 50)

        if not self.ensure_database_exists():
            return False

        csv_files = self.get_csv_files()
        if not csv_files:
            logger.error("No CSV files found to migrate")
            return False

        try:
            conn = sqlite3.connect(str(self.db_path))

            if dry_run:
                logger.info("DRY RUN MODE - No changes will be made to database")
                conn = None  # Don't actually connect for dry run
            else:
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")

            success_count = 0
            for csv_file in csv_files:
                if conn:
                    if self.migrate_csv_file(csv_file, conn):
                        success_count += 1
                else:
                    # Dry run - just validate files
                    try:
                        df = pd.read_csv(csv_file)
                        if self.validate_csv_structure(df, csv_file.name):
                            logger.info(f"Would migrate: {csv_file.name} ({len(df)} records)")
                            success_count += 1
                        else:
                            self.migration_stats['errors'] += 1
                    except Exception as e:
                        logger.error(f"Error reading {csv_file.name}: {e}")
                        self.migration_stats['errors'] += 1

            if conn and not dry_run:
                if success_count == len(csv_files):
                    conn.commit()
                    logger.info("Migration completed successfully!")
                else:
                    conn.rollback()
                    logger.error("Migration failed - rolling back changes")
                    return False

            # Display migration summary
            self._display_migration_summary()

            return success_count == len(csv_files)

        except sqlite3.Error as e:
            logger.error(f"Database error during migration: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _display_migration_summary(self):
        """Display migration statistics"""
        logger.info("\n" + "=" * 50)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Files processed: {self.migration_stats['files_processed']}")
        logger.info(f"Records migrated: {self.migration_stats['records_migrated']}")
        logger.info(f"Duplicates skipped: {self.migration_stats['duplicates_skipped']}")
        logger.info(f"Errors: {self.migration_stats['errors']}")
        logger.info("=" * 50)

    def verify_migration(self) -> Dict:
        """Verify migration by checking database contents"""
        if not self.db_path.exists():
            return {"error": "Database not found"}

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get total records in polymarket_data table
            cursor.execute("SELECT COUNT(*) FROM polymarket_data")
            total_records = cursor.fetchone()[0]

            # Get records by source file (if we stored that info)
            cursor.execute("""
                SELECT COUNT(DISTINCT market_id) as markets,
                       COUNT(DISTINCT event_title) as events,
                       MIN(timestamp) as earliest_timestamp,
                       MAX(timestamp) as latest_timestamp
                FROM polymarket_data
            """)
            stats = cursor.fetchone()

            return {
                "total_records": total_records,
                "unique_markets": stats[0],
                "unique_events": stats[1],
                "date_range": f"{stats[2]} to {stats[3]}" if stats[2] and stats[3] else "N/A"
            }

        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate CSV data to ClimateTrade database")
    parser.add_argument(
        "--db-path",
        default="../data/climatetrade.db",
        help="Path to the database file (relative to script location)"
    )
    parser.add_argument(
        "--csv-dir",
        default="data/",
        help="Directory containing CSV files to migrate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files without making database changes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify migration results after completion"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    migrator = CSVDataMigrator(args.db_path, args.csv_dir)

    if args.verify:
        logger.info("Verifying migration results...")
        results = migrator.verify_migration()
        if "error" in results:
            logger.error(f"Verification failed: {results['error']}")
            sys.exit(1)
        else:
            print("\n=== MIGRATION VERIFICATION ===")
            for key, value in results.items():
                print(f"{key}: {value}")
        return

    success = migrator.run_migration(dry_run=args.dry_run)

    if success:
        print("\nMigration completed successfully!")
        if not args.dry_run:
            print("You can verify the migration with: python migrate_csv_to_database.py --verify")
    else:
        print("\nMigration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()