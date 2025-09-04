#!/usr/bin/env python3
"""
Polymarket Data Ingestion Script

This script ingests Polymarket market data from CSV files into the database.
"""

import csv
import sqlite3
import argparse
import logging
from pathlib import Path
from datetime import datetime
import sys

# Import data quality modules
try:
    from data_quality_pipeline import process_polymarket_data
    from data_validation import validate_polymarket_data
    DATA_QUALITY_AVAILABLE = True
except ImportError:
    logger.warning("Data quality modules not available. Running without validation/cleaning.")
    DATA_QUALITY_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PolymarketDataIngester:
    """Handles ingestion of Polymarket data into the database."""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self.ensure_db_exists()

    def ensure_db_exists(self):
        """Ensure the database file exists."""
        if not Path(self.db_path).exists():
            logger.error(f"Database not found at {self.db_path}. Please run setup_database.py first.")
            sys.exit(1)

    def connect_db(self):
        """Connect to the database."""
        return sqlite3.connect(self.db_path)

    def validate_csv_row(self, row: dict) -> bool:
        """Validate a CSV row has required fields."""
        required_fields = ['event_title', 'market_id', 'outcome_name', 'timestamp', 'scraped_at']
        return all(field in row and row[field].strip() for field in required_fields)

    def parse_csv_row(self, row: dict) -> dict:
        """Parse and clean a CSV row."""
        return {
            'event_title': row.get('event_title', '').strip(),
            'event_url': row.get('event_url', '').strip(),
            'market_id': row.get('market_id', '').strip(),
            'outcome_name': row.get('outcome_name', '').strip(),
            'probability': float(row.get('probability', 0)) if row.get('probability') else None,
            'volume': float(row.get('volume', 0)) if row.get('volume') else None,
            'timestamp': row.get('timestamp', '').strip(),
            'scraped_at': row.get('scraped_at', '').strip()
        }

    def insert_polymarket_data(self, data: list, conn: sqlite3.Connection) -> int:
        """Insert Polymarket data into the database."""
        cursor = conn.cursor()

        insert_sql = """
        INSERT OR IGNORE INTO polymarket_data
        (event_title, event_url, market_id, outcome_name, probability, volume, timestamp, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted_count = 0
        for record in data:
            try:
                cursor.execute(insert_sql, (
                    record['event_title'],
                    record['event_url'],
                    record['market_id'],
                    record['outcome_name'],
                    record['probability'],
                    record['volume'],
                    record['timestamp'],
                    record['scraped_at']
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            except sqlite3.Error as e:
                logger.error(f"Error inserting record for market {record['market_id']}: {e}")

        return inserted_count

    def ingest_csv_file(self, csv_path: str, enable_quality_pipeline: bool = True) -> dict:
        """Ingest data from a single CSV file with optional quality processing."""
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        data = []
        valid_rows = 0
        invalid_rows = 0

        logger.info(f"Reading CSV file: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                if self.validate_csv_row(row):
                    try:
                        parsed_row = self.parse_csv_row(row)
                        data.append(parsed_row)
                        valid_rows += 1
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing row {row_num}: {e}")
                        invalid_rows += 1
                else:
                    logger.warning(f"Invalid row {row_num}: missing required fields")
                    invalid_rows += 1

        logger.info(f"Parsed {valid_rows} valid rows, {invalid_rows} invalid rows")

        # Apply data quality pipeline if available and enabled
        quality_result = None
        if DATA_QUALITY_AVAILABLE and enable_quality_pipeline and data:
            logger.info("Applying data quality pipeline to Polymarket data")
            try:
                quality_config = {
                    'fail_on_validation_error': False,
                    'fail_on_cleaning_error': False,
                    'generate_reports': True,
                    'quality_threshold': 70.0  # More lenient for initial processing
                }
                quality_result = process_polymarket_data(data, quality_config)

                if quality_result['success']:
                    logger.info(f"Quality pipeline completed. Score: {quality_result['quality_score']}%")
                    # Use cleaned data for database insertion
                    data = quality_result['cleaned_data']
                    logger.info(f"Using {len(data)} cleaned records for database insertion")
                else:
                    logger.warning(f"Quality pipeline failed: {quality_result.get('error', 'Unknown error')}")
                    logger.warning("Proceeding with original data")

            except Exception as e:
                logger.error(f"Error in data quality pipeline: {e}")
                logger.warning("Proceeding with original data")

        # Insert data into database
        conn = self.connect_db()
        try:
            inserted_count = self.insert_polymarket_data(data, conn)
            conn.commit()
            logger.info(f"Successfully inserted {inserted_count} new records")

            result = {
                'file': csv_path,
                'total_rows': len(data),
                'inserted': inserted_count,
                'duplicates': len(data) - inserted_count,
                'quality_processed': quality_result is not None,
                'quality_score': quality_result.get('quality_score') if quality_result else None
            }

            if quality_result:
                result.update({
                    'original_records': quality_result['original_records'],
                    'processed_records': quality_result['processed_records'],
                    'validation_errors': quality_result['validation_result'].get('invalid_records', 0),
                    'cleaning_steps': quality_result['cleaning_result'].get('cleaning_steps', [])
                })

            return result

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def ingest_directory(self, directory_path: str) -> list:
        """Ingest all CSV files from a directory."""
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        csv_files = list(directory.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {directory_path}")
            return []

        results = []
        for csv_file in csv_files:
            try:
                result = self.ingest_csv_file(str(csv_file))
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")

        return results

def main():
    parser = argparse.ArgumentParser(description="Ingest Polymarket data from CSV files")
    parser.add_argument(
        "input",
        help="Path to CSV file or directory containing CSV files"
    )
    parser.add_argument(
        "--db-path",
        default="data/climatetrade.db",
        help="Path to the database file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--enable-quality-pipeline", "-q",
        action="store_true",
        default=True,
        help="Enable data quality pipeline (validation and cleaning)"
    )
    parser.add_argument(
        "--disable-quality-pipeline",
        action="store_true",
        help="Disable data quality pipeline"
    )
    parser.add_argument(
        "--quality-config",
        type=str,
        help="Path to JSON file with quality pipeline configuration"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine if quality pipeline should be enabled
    enable_quality = args.enable_quality_pipeline and not args.disable_quality_pipeline

    # Load quality configuration if provided
    quality_config = None
    if args.quality_config and Path(args.quality_config).exists():
        try:
            import json
            with open(args.quality_config, 'r') as f:
                quality_config = json.load(f)
            logger.info(f"Loaded quality configuration from {args.quality_config}")
        except Exception as e:
            logger.error(f"Error loading quality configuration: {e}")
            quality_config = None

    ingester = PolymarketDataIngester(args.db_path)

    try:
        input_path = Path(args.input)
        if input_path.is_file():
            result = ingester.ingest_csv_file(args.input, enable_quality_pipeline=enable_quality)
            print(f"Processed {result['file']}: {result['inserted']} inserted, {result['duplicates']} duplicates")
            if result.get('quality_processed'):
                print(f"Quality Score: {result.get('quality_score', 'N/A')}%")
                print(f"Validation Errors: {result.get('validation_errors', 0)}")
                if result.get('cleaning_steps'):
                    print(f"Cleaning Steps: {', '.join(result['cleaning_steps'])}")
        elif input_path.is_dir():
            results = ingester.ingest_directory(args.input)
            total_inserted = sum(r['inserted'] for r in results)
            total_duplicates = sum(r['duplicates'] for r in results)
            total_quality_processed = sum(1 for r in results if r.get('quality_processed', False))
            avg_quality_score = None
            if total_quality_processed > 0:
                quality_scores = [r.get('quality_score') for r in results if r.get('quality_score') is not None]
                if quality_scores:
                    avg_quality_score = sum(quality_scores) / len(quality_scores)

            print(f"Processed {len(results)} files: {total_inserted} inserted, {total_duplicates} duplicates")
            if total_quality_processed > 0:
                print(f"Files with quality processing: {total_quality_processed}")
                if avg_quality_score is not None:
                    print(f"Average Quality Score: {avg_quality_score:.1f}%")
        else:
            print(f"Error: {args.input} is not a valid file or directory")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()