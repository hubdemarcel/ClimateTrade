#!/usr/bin/env python3
"""
Database Setup Script for ClimateTrade AI
Comprehensive database initialization for the complete schema
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Optional
import logging

# Import centralized logging
try:
    # Add project root to path for utils
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logging import setup_logging, get_logger
    # Setup centralized logging
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging if centralized system not available
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles comprehensive database setup and initialization"""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self.schema_path = Path(__file__).parent / "schema.sql"
        self.ensure_schema_exists()

    def ensure_schema_exists(self):
        """Ensure the schema file exists"""
        if not self.schema_path.exists():
            logger.error(f"Schema file not found at {self.schema_path}")
            sys.exit(1)

    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def setup_database(self, force_recreate: bool = False) -> bool:
        """
        Set up the database with the comprehensive schema

        Args:
            force_recreate: If True, drop existing database and recreate

        Returns:
            True if setup successful, False otherwise
        """
        self.ensure_db_directory()

        if force_recreate and Path(self.db_path).exists():
            logger.info(f"Removing existing database: {self.db_path}")
            Path(self.db_path).unlink()

        # Read schema file
        logger.info(f"Reading schema from: {self.schema_path}")
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Connect to database and execute schema
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info("Executing database schema...")
            cursor.executescript(schema_sql)

            # Verify tables were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]

            logger.info(f"Database setup completed successfully!")
            logger.info(f"Database location: {self.db_path}")
            logger.info(f"Created {len(table_names)} tables")

            # Show table summary
            self._display_table_summary(cursor, table_names)

            # Run post-setup validations
            self._run_post_setup_validations(cursor)

            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Database setup failed: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def _display_table_summary(self, cursor: sqlite3.Cursor, table_names: list):
        """Display a summary of created tables"""
        logger.info("\n=== DATABASE TABLES SUMMARY ===")

        # Group tables by category
        categories = {
            'Weather Data': [t for t in table_names if t.startswith('weather')],
            'Polymarket Data': [t for t in table_names if t.startswith('polymarket')],
            'Agent & Trading': [t for t in ['trading_strategies', 'agent_execution_logs',
                                          'trading_history', 'portfolio_positions']],
            'Backtesting': [t for t in table_names if t.startswith(('backtest', 'risk'))],
            'Resolution': [t for t in table_names if t in ['market_resolutions', 'ancillary_data_mappings',
                                                         'moderators', 'revisions']],
            'System': [t for t in ['data_quality_logs', 'system_config', 'api_rate_limits']]
        }

        for category, tables in categories.items():
            if tables:
                logger.info(f"\n{category}:")
                for table in sorted(tables):
                    if table in table_names:
                        cursor.execute(f"PRAGMA table_info({table});")
                        columns = cursor.fetchall()
                        logger.info(f"  - {table}: {len(columns)} columns")

    def _run_post_setup_validations(self, cursor: sqlite3.Cursor):
        """Run post-setup validations"""
        logger.info("\n=== POST-SETUP VALIDATIONS ===")

        # Check weather sources
        cursor.execute("SELECT COUNT(*) FROM weather_sources;")
        weather_sources_count = cursor.fetchone()[0]
        logger.info(f"Weather sources initialized: {weather_sources_count}")

        # Check system config
        cursor.execute("SELECT COUNT(*) FROM system_config;")
        config_count = cursor.fetchone()[0]
        logger.info(f"System configuration entries: {config_count}")

        # Check trading strategies
        cursor.execute("SELECT COUNT(*) FROM trading_strategies;")
        strategies_count = cursor.fetchone()[0]
        logger.info(f"Default trading strategies: {strategies_count}")

        # Check indexes
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index';")
        index_count = cursor.fetchone()[0]
        logger.info(f"Database indexes created: {index_count}")

    def get_database_info(self) -> dict:
        """Get information about the database"""
        if not Path(self.db_path).exists():
            return {"error": "Database does not exist"}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]

            # Get total records across all tables
            total_records = 0
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                    count = cursor.fetchone()[0]
                    total_records += count
                except sqlite3.Error:
                    pass  # Skip tables that might have issues

            # Get database size
            db_size = Path(self.db_path).stat().st_size

            return {
                "database_path": self.db_path,
                "table_count": table_count,
                "total_records": total_records,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            }

        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of the database"""
        if not Path(self.db_path).exists():
            logger.error("Source database does not exist")
            return False

        if backup_path is None:
            timestamp = Path(self.db_path).stat().st_mtime
            backup_path = f"{self.db_path}.backup_{int(timestamp)}"

        try:
            # SQLite backup
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)

            with backup_conn:
                source_conn.backup(backup_conn)

            logger.info(f"Database backup created: {backup_path}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Backup failed: {e}")
            return False
        finally:
            if source_conn:
                source_conn.close()
            if backup_conn:
                backup_conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Set up ClimateTrade comprehensive database")
    parser.add_argument(
        "--db-path",
        default="data/climatetrade.db",
        help="Path to the database file (default: data/climatetrade.db)"
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Force recreation of database (removes existing)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show database information instead of setup"
    )
    parser.add_argument(
        "--backup",
        type=str,
        help="Create backup of existing database to specified path"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        # Update logging level for verbose output
        try:
            from utils.logging import update_logging_config, LogConfig
            config = LogConfig(level='DEBUG', console_level='DEBUG')
            update_logging_config(config)
        except ImportError:
            logging.getLogger().setLevel(logging.DEBUG)

    setup = DatabaseSetup(args.db_path)

    if args.info:
        info = setup.get_database_info()
        if "error" in info:
            logger.error(info["error"])
            sys.exit(1)
        else:
            print("\n=== DATABASE INFORMATION ===")
            for key, value in info.items():
                print(f"{key}: {value}")
    elif args.backup:
        success = setup.backup_database(args.backup)
        if not success:
            sys.exit(1)
    else:
        print("Setting up ClimateTrade comprehensive database...")
        success = setup.setup_database(force_recreate=args.force_recreate)
        if success:
            print("\nDatabase setup completed successfully!")
            # Show info after setup
            info = setup.get_database_info()
            if "error" not in info:
                print(f"Database: {info['database_path']}")
                print(f"Tables: {info['table_count']}")
                print(f"Size: {info['database_size_mb']} MB")
        else:
            print("\nDatabase setup failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()