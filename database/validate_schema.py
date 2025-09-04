#!/usr/bin/env python3
"""
Schema Validation Script for ClimateTrade AI
Validates that the new comprehensive schema is compatible with existing data loaders
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates database schema compatibility with existing loaders"""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self.validation_results = []

    def validate_schema_compatibility(self) -> bool:
        """Run comprehensive schema validation"""
        logger.info("Starting schema compatibility validation...")

        if not Path(self.db_path).exists():
            logger.error(f"Database not found: {self.db_path}")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Validate core tables exist
            if not self._validate_core_tables(cursor):
                return False

            # Validate polymarket data compatibility
            if not self._validate_polymarket_compatibility(cursor):
                return False

            # Validate weather data compatibility
            if not self._validate_weather_compatibility(cursor):
                return False

            # Validate indexes
            if not self._validate_indexes(cursor):
                return False

            # Validate foreign keys
            if not self._validate_foreign_keys(cursor):
                return False

            conn.close()

            # Print validation summary
            self._print_validation_summary()

            return len([r for r in self.validation_results if not r['passed']]) == 0

        except sqlite3.Error as e:
            logger.error(f"Database validation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _validate_core_tables(self, cursor: sqlite3.Cursor) -> bool:
        """Validate that all required tables exist"""
        required_tables = [
            'weather_sources', 'weather_data', 'weather_forecasts',
            'polymarket_events', 'polymarket_markets', 'polymarket_data',
            'polymarket_trades', 'polymarket_orderbook',
            'trading_strategies', 'agent_execution_logs', 'trading_history',
            'portfolio_positions', 'backtest_configs', 'backtest_results',
            'backtest_trades', 'risk_analysis', 'market_resolutions',
            'ancillary_data_mappings', 'moderators', 'revisions',
            'data_quality_logs', 'system_config', 'api_rate_limits'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        existing_tables = [row[0] for row in cursor.fetchall()]

        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)

        if missing_tables:
            self.validation_results.append({
                'test': 'Core Tables Existence',
                'passed': False,
                'details': f"Missing tables: {', '.join(missing_tables)}"
            })
            return False
        else:
            self.validation_results.append({
                'test': 'Core Tables Existence',
                'passed': True,
                'details': f"All {len(required_tables)} required tables present"
            })
            return True

    def _validate_polymarket_compatibility(self, cursor: sqlite3.Cursor) -> bool:
        """Validate polymarket table compatibility with existing loaders"""
        # Check polymarket_data table structure
        cursor.execute("PRAGMA table_info(polymarket_data);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = [
            'id', 'market_id', 'outcome_name', 'probability', 'volume',
            'timestamp', 'scraped_at', 'event_title', 'event_url', 'created_at'
        ]

        missing_columns = []
        for col in required_columns:
            if col not in column_names:
                missing_columns.append(col)

        if missing_columns:
            self.validation_results.append({
                'test': 'Polymarket Data Compatibility',
                'passed': False,
                'details': f"Missing columns in polymarket_data: {', '.join(missing_columns)}"
            })
            return False

        # Validate unique constraint
        cursor.execute("PRAGMA index_list(polymarket_data);")
        indexes = cursor.fetchall()
        has_unique_constraint = any('polymarket_data' in idx[1] and idx[2] == '1' for idx in indexes)

        if not has_unique_constraint:
            # Check for unique constraint in table definition
            for col in columns:
                if len(col) > 5 and col[5] and 'UNIQUE' in str(col[5]):
                    has_unique_constraint = True
                    break

        if not has_unique_constraint:
            self.validation_results.append({
                'test': 'Polymarket Data Unique Constraint',
                'passed': False,
                'details': "Missing unique constraint on (market_id, outcome_name, timestamp)"
            })
            return False

        self.validation_results.append({
            'test': 'Polymarket Data Compatibility',
            'passed': True,
            'details': "All required columns and constraints present"
        })
        return True

    def _validate_weather_compatibility(self, cursor: sqlite3.Cursor) -> bool:
        """Validate weather table compatibility with existing loaders"""
        # Check weather_data table structure
        cursor.execute("PRAGMA table_info(weather_data);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = [
            'id', 'source_id', 'location_name', 'latitude', 'longitude',
            'timestamp', 'temperature', 'temperature_min', 'temperature_max',
            'feels_like', 'humidity', 'pressure', 'wind_speed', 'wind_direction',
            'precipitation', 'weather_code', 'weather_description', 'visibility',
            'uv_index', 'alerts', 'raw_data', 'data_quality_score', 'created_at'
        ]

        missing_columns = []
        for col in required_columns:
            if col not in column_names:
                missing_columns.append(col)

        if missing_columns:
            self.validation_results.append({
                'test': 'Weather Data Compatibility',
                'passed': False,
                'details': f"Missing columns in weather_data: {', '.join(missing_columns)}"
            })
            return False

        # Check foreign key to weather_sources
        cursor.execute("PRAGMA foreign_key_list(weather_data);")
        foreign_keys = cursor.fetchall()
        has_source_fk = any(fk[2] == 'weather_sources' and fk[3] == 'id' for fk in foreign_keys)

        if not has_source_fk:
            self.validation_results.append({
                'test': 'Weather Data Foreign Key',
                'passed': False,
                'details': "Missing foreign key constraint to weather_sources"
            })
            return False

        # Validate unique constraint
        has_unique_constraint = False
        for col in columns:
            if len(col) > 5 and col[5] and 'UNIQUE' in str(col[5]):
                has_unique_constraint = True
                break

        if not has_unique_constraint:
            self.validation_results.append({
                'test': 'Weather Data Unique Constraint',
                'passed': False,
                'details': "Missing unique constraint on (source_id, location_name, timestamp)"
            })
            return False

        self.validation_results.append({
            'test': 'Weather Data Compatibility',
            'passed': True,
            'details': "All required columns, constraints, and foreign keys present"
        })
        return True

    def _validate_indexes(self, cursor: sqlite3.Cursor) -> bool:
        """Validate that required indexes exist"""
        required_indexes = [
            'idx_weather_timestamp', 'idx_weather_location', 'idx_weather_source_timestamp',
            'idx_polymarket_timestamp', 'idx_polymarket_market_id',
            'idx_polymarket_event_id', 'idx_polymarket_market_market_id',
            'idx_polymarket_trades_market', 'idx_polymarket_trades_timestamp',
            'idx_polymarket_orderbook_market', 'idx_polymarket_orderbook_timestamp',
            'idx_agent_execution_timestamp', 'idx_agent_execution_strategy',
            'idx_trading_history_market', 'idx_trading_history_timestamp',
            'idx_trading_history_strategy', 'idx_portfolio_positions_market',
            'idx_portfolio_positions_status', 'idx_backtest_results_config',
            'idx_backtest_results_date', 'idx_backtest_trades_backtest',
            'idx_risk_analysis_backtest', 'idx_market_resolutions_question',
            'idx_market_resolutions_status', 'idx_market_resolutions_timestamp',
            'idx_revisions_question', 'idx_revisions_moderator',
            'idx_data_quality_table', 'idx_data_quality_created',
            'idx_api_rate_limits_source'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        existing_indexes = [row[0] for row in cursor.fetchall()]

        missing_indexes = []
        for idx in required_indexes:
            if idx not in existing_indexes:
                missing_indexes.append(idx)

        if missing_indexes:
            self.validation_results.append({
                'test': 'Required Indexes',
                'passed': False,
                'details': f"Missing indexes: {', '.join(missing_indexes)}"
            })
            return False
        else:
            self.validation_results.append({
                'test': 'Required Indexes',
                'passed': True,
                'details': f"All {len(required_indexes)} required indexes present"
            })
            return True

    def _validate_foreign_keys(self, cursor: sqlite3.Cursor) -> bool:
        """Validate foreign key constraints"""
        # Enable foreign key enforcement for validation
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Test foreign key constraints by attempting invalid inserts
        fk_issues = []

        try:
            # Test weather_data -> weather_sources
            cursor.execute("INSERT INTO weather_data (source_id, location_name, timestamp) VALUES (99999, 'test', '2024-01-01');")
            fk_issues.append("weather_data.source_id foreign key constraint not enforced")
        except sqlite3.IntegrityError:
            pass  # This is expected - constraint should prevent invalid insert

        # Clean up test data
        cursor.execute("DELETE FROM weather_data WHERE location_name = 'test';")

        if fk_issues:
            self.validation_results.append({
                'test': 'Foreign Key Constraints',
                'passed': False,
                'details': f"Foreign key issues: {', '.join(fk_issues)}"
            })
            return False
        else:
            self.validation_results.append({
                'test': 'Foreign Key Constraints',
                'passed': True,
                'details': "All foreign key constraints properly enforced"
            })
            return True

    def _print_validation_summary(self):
        """Print validation results summary"""
        logger.info("\n" + "="*60)
        logger.info("SCHEMA VALIDATION SUMMARY")
        logger.info("="*60)

        passed = 0
        failed = 0

        for result in self.validation_results:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            logger.info(f"{status}: {result['test']}")
            if not result['passed']:
                logger.info(f"       {result['details']}")
                failed += 1
            else:
                passed += 1

        logger.info("="*60)
        logger.info(f"Total Tests: {len(self.validation_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")

        if failed == 0:
            logger.info("🎉 All validation tests passed! Schema is compatible.")
        else:
            logger.error(f"❌ {failed} validation test(s) failed. Please review schema.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate ClimateTrade database schema compatibility")
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

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    validator = SchemaValidator(args.db_path)

    if validator.validate_schema_compatibility():
        logger.info("Schema validation completed successfully")
        sys.exit(0)
    else:
        logger.error("Schema validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()