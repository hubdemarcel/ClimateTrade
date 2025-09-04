#!/usr/bin/env python3
"""
Database Migration Manager for ClimateTrade AI
Handles database schema migrations and version control
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import importlib.util
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations and schema versioning"""

    def __init__(self, db_path: str = "data/climatetrade.db"):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent
        self.ensure_migration_table()

    def ensure_migration_table(self):
        """Ensure the migrations tracking table exists"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create migrations table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT NOT NULL UNIQUE,
                    version TEXT NOT NULL,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT,
                    success BOOLEAN DEFAULT 0,
                    error_message TEXT
                );
            """)

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT migration_name FROM schema_migrations WHERE success = 1 ORDER BY id;")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migration files"""
        applied = set(self.get_applied_migrations())

        migration_files = []
        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name != "__init__.py" and file_path.name != "migration_manager.py":
                migration_files.append(file_path.stem)

        return [m for m in sorted(migration_files) if m not in applied]

    def apply_migration(self, migration_name: str) -> bool:
        """Apply a specific migration"""
        migration_file = self.migrations_dir / f"{migration_name}.py"

        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False

        # Import the migration module
        spec = importlib.util.spec_from_file_location(migration_name, migration_file)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load migration: {migration_name}")
            return False

        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)

        # Check if migration has required functions
        if not hasattr(migration_module, 'upgrade') or not hasattr(migration_module, 'downgrade'):
            logger.error(f"Migration {migration_name} missing upgrade/downgrade functions")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info(f"Applying migration: {migration_name}")

            # Start transaction
            cursor.execute("BEGIN;")

            # Apply the migration
            migration_module.upgrade(cursor)

            # Record the migration
            cursor.execute("""
                INSERT INTO schema_migrations (migration_name, version, success)
                VALUES (?, ?, 1);
            """, (migration_name, getattr(migration_module, 'version', '1.0.0')))

            conn.commit()
            logger.info(f"Successfully applied migration: {migration_name}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to apply migration {migration_name}: {e}")

            # Record failed migration
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO schema_migrations (migration_name, version, success, error_message)
                    VALUES (?, ?, 0, ?);
                """, (migration_name, getattr(migration_module, 'version', '1.0.0'), str(e)))
                conn.commit()
            except sqlite3.Error:
                pass

            return False
        finally:
            if conn:
                conn.close()

    def rollback_migration(self, migration_name: str) -> bool:
        """Rollback a specific migration"""
        migration_file = self.migrations_dir / f"{migration_name}.py"

        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False

        # Import the migration module
        spec = importlib.util.spec_from_file_location(migration_name, migration_file)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load migration: {migration_name}")
            return False

        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)

        if not hasattr(migration_module, 'downgrade'):
            logger.error(f"Migration {migration_name} missing downgrade function")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info(f"Rolling back migration: {migration_name}")

            # Start transaction
            cursor.execute("BEGIN;")

            # Rollback the migration
            migration_module.downgrade(cursor)

            # Remove from migrations table
            cursor.execute("DELETE FROM schema_migrations WHERE migration_name = ?;", (migration_name,))

            conn.commit()
            logger.info(f"Successfully rolled back migration: {migration_name}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to rollback migration {migration_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def apply_pending_migrations(self) -> bool:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return True

        logger.info(f"Found {len(pending)} pending migrations")

        success_count = 0
        for migration in pending:
            if self.apply_migration(migration):
                success_count += 1
            else:
                logger.error(f"Failed to apply migration: {migration}")
                break

        if success_count == len(pending):
            logger.info(f"Successfully applied all {success_count} migrations")
            return True
        else:
            logger.error(f"Applied {success_count}/{len(pending)} migrations before failure")
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "applied_migrations": applied,
            "pending_migrations": pending,
            "total_applied": len(applied),
            "total_pending": len(pending),
            "current_version": applied[-1] if applied else None
        }

    def create_migration_template(self, name: str, description: str = "") -> str:
        """Create a migration template file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = f"{timestamp}_{name}"

        template = f'''"""
Migration: {migration_name}
Description: {description}
Version: 1.0.0
"""

def upgrade(cursor):
    """
    Upgrade function - apply the migration

    Args:
        cursor: SQLite cursor object
    """
    # Add your upgrade SQL here
    pass


def downgrade(cursor):
    """
    Downgrade function - rollback the migration

    Args:
        cursor: SQLite cursor object
    """
    # Add your downgrade SQL here
    pass
'''

        migration_file = self.migrations_dir / f"{migration_name}.py"
        with open(migration_file, 'w') as f:
            f.write(template)

        logger.info(f"Created migration template: {migration_file}")
        return str(migration_file)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ClimateTrade Database Migration Manager")
    parser.add_argument(
        "--db-path",
        default="data/climatetrade.db",
        help="Path to the database file"
    )
    parser.add_argument(
        "action",
        choices=["status", "apply", "rollback", "create"],
        help="Migration action to perform"
    )
    parser.add_argument(
        "--migration",
        help="Migration name for rollback or specific apply"
    )
    parser.add_argument(
        "--name",
        help="Name for new migration (used with create action)"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Description for new migration"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    manager = MigrationManager(args.db_path)

    if args.action == "status":
        status = manager.get_migration_status()
        print("\n=== MIGRATION STATUS ===")
        print(f"Applied: {status['total_applied']}")
        print(f"Pending: {status['total_pending']}")
        print(f"Current version: {status['current_version'] or 'None'}")

        if status['applied_migrations']:
            print("\nApplied migrations:")
            for migration in status['applied_migrations']:
                print(f"  ✓ {migration}")

        if status['pending_migrations']:
            print("\nPending migrations:")
            for migration in status['pending_migrations']:
                print(f"  ○ {migration}")

    elif args.action == "apply":
        if args.migration:
            success = manager.apply_migration(args.migration)
        else:
            success = manager.apply_pending_migrations()

        if success:
            print("Migration(s) applied successfully")
        else:
            print("Migration(s) failed")
            sys.exit(1)

    elif args.action == "rollback":
        if not args.migration:
            print("Migration name required for rollback")
            sys.exit(1)

        success = manager.rollback_migration(args.migration)
        if success:
            print(f"Successfully rolled back migration: {args.migration}")
        else:
            print(f"Failed to rollback migration: {args.migration}")
            sys.exit(1)

    elif args.action == "create":
        if not args.name:
            print("Migration name required for create action")
            sys.exit(1)

        migration_file = manager.create_migration_template(args.name, args.description)
        print(f"Created migration template: {migration_file}")


if __name__ == "__main__":
    main()