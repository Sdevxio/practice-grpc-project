"""
SQLite Performance Database Handler

Enterprise-grade database handler for performance test results with:
- Connection pooling and thread safety
- Automatic schema migration
- Data validation and integrity constraints
- Comprehensive error handling and logging
- Backup and recovery capabilities

Author: Performance Engineering Team
Version: 1.0.0
"""

import sqlite3
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from test_framework.utils import get_logger


class PerformanceDatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class PerformanceDatabase:
    """
    Enterprise SQLite handler for performance test data with robust
    error handling, connection management, and data integrity features.
    """

    # Database schema version for migration management
    SCHEMA_VERSION = "1.0.0"

    # Default database configuration
    DEFAULT_DB_PATH = os.path.join("C:", "performance-data", "performance.db")
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, db_path: str = None, logger=None, timeout: float = None):
        """
        Initialize database handler with enterprise configuration.

        Args:
            db_path: Database file path (defaults to C:\performance-data\performance.db)
            logger: Logger instance for operation tracking
            timeout: Database connection timeout in seconds
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.logger = logger or get_logger("performance_db")

        # Thread safety
        self._lock = threading.Lock()
        self._connection_pool = {}

        # Ensure database directory exists
        self._ensure_database_directory()

        # Initialize database schema
        self._initialize_database()

        self.logger.info(f"Performance database initialized: {self.db_path}")

    def _ensure_database_directory(self) -> None:
        """Ensure the database directory exists with proper permissions."""
        try:
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                self.logger.info(f"Created database directory: {db_dir}")
        except Exception as e:
            raise PerformanceDatabaseError(f"Failed to create database directory: {e}")

    @contextmanager
    def get_connection(self):
        """
        Thread-safe database connection context manager.

        Yields:
            sqlite3.Connection: Database connection with proper configuration
        """
        thread_id = threading.get_ident()

        try:
            with self._lock:
                if thread_id not in self._connection_pool:
                    conn = sqlite3.connect(
                        self.db_path,
                        timeout=self.timeout,
                        check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.execute("PRAGMA journal_mode = WAL")
                    self._connection_pool[thread_id] = conn

                connection = self._connection_pool[thread_id]

            yield connection

        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise PerformanceDatabaseError(f"Database operation failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected database error: {e}")
            raise PerformanceDatabaseError(f"Unexpected error: {e}")

    def _initialize_database(self) -> None:
        """Initialize database schema with comprehensive table structure."""
        schema_sql = """
        -- Performance test results table
        CREATE TABLE IF NOT EXISTS performance_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name VARCHAR(100) NOT NULL,
            duration REAL NOT NULL,
            success BOOLEAN NOT NULL DEFAULT 1,
            test_date DATE NOT NULL,
            test_time TIME NOT NULL,
            test_run_timestamp TIMESTAMP NOT NULL,
            log_entry_timestamp VARCHAR(50),
            log_entry_message TEXT,
            log_correlation BOOLEAN DEFAULT 0,
            test_type VARCHAR(50),
            tap_timestamp VARCHAR(50),
            session_timestamp VARCHAR(50),
            expected_user VARCHAR(50),
            category VARCHAR(50) DEFAULT 'performance',
            subcategory VARCHAR(50) DEFAULT 'ui_timing',
            additional_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_duration CHECK (duration >= -1000000 AND duration <= 1000000),
            CONSTRAINT chk_test_name CHECK (length(test_name) > 0)
        );

        -- Performance statistics summary table
        CREATE TABLE IF NOT EXISTS performance_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name VARCHAR(100) NOT NULL,
            total_runs INTEGER DEFAULT 0,
            successful_runs INTEGER DEFAULT 0,
            average_duration REAL DEFAULT 0.0,
            min_duration REAL DEFAULT 0.0,
            max_duration REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(test_name)
        );

        -- Database metadata table
        CREATE TABLE IF NOT EXISTS database_metadata (
            key VARCHAR(50) PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for performance optimization
        CREATE INDEX IF NOT EXISTS idx_performance_test_name ON performance_results(test_name);
        CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_results(test_run_timestamp);
        CREATE INDEX IF NOT EXISTS idx_performance_success ON performance_results(success);
        CREATE INDEX IF NOT EXISTS idx_performance_date ON performance_results(test_date);
        """

        try:
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()

                # Set schema version
                conn.execute(
                    "INSERT OR REPLACE INTO database_metadata (key, value) VALUES (?, ?)",
                    ("schema_version", self.SCHEMA_VERSION)
                )
                conn.commit()

            self.logger.info("Database schema initialized successfully")

        except Exception as e:
            raise PerformanceDatabaseError(f"Failed to initialize database schema: {e}")

    def save_performance_result(self, test_data: Dict[str, Any]) -> int:
        """
        Save performance test result with comprehensive data validation.

        Args:
            test_data: Performance test data dictionary

        Returns:
            int: Record ID of saved result

        Raises:
            PerformanceDatabaseError: If save operation fails
        """
        # Validate required fields
        required_fields = ["test_name", "duration", "test_run_timestamp"]
        for field in required_fields:
            if field not in test_data:
                raise PerformanceDatabaseError(f"Missing required field: {field}")

        try:
            # Parse timestamp for date/time fields
            timestamp = datetime.fromisoformat(test_data["test_run_timestamp"])

            insert_sql = """
            INSERT INTO performance_results (
                test_name, duration, success, test_date, test_time, test_run_timestamp,
                log_entry_timestamp, log_entry_message, log_correlation,
                test_type, tap_timestamp, session_timestamp, expected_user,
                category, subcategory, additional_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                test_data["test_name"],
                float(test_data["duration"]),
                test_data.get("success", True),
                timestamp.date().isoformat(),  # Convert to string
                timestamp.time().isoformat(),  # Convert to string
                test_data["test_run_timestamp"],
                test_data.get("log_entry_timestamp"),
                test_data.get("log_entry_message"),
                test_data.get("log_correlation", False),
                test_data.get("test_type"),
                test_data.get("tap_timestamp"),
                test_data.get("session_timestamp"),
                test_data.get("expected_user"),
                test_data.get("category", "performance"),
                test_data.get("subcategory", "ui_timing"),
                json.dumps({k: v for k, v in test_data.items()
                            if k not in ["test_name", "duration", "success", "test_run_timestamp"]})
            )

            with self.get_connection() as conn:
                cursor = conn.execute(insert_sql, values)
                record_id = cursor.lastrowid
                conn.commit()

                # Update statistics
                self._update_performance_stats(conn, test_data["test_name"])

            self.logger.info(f"Saved performance result: {test_data['test_name']} (ID: {record_id})")
            return record_id

        except Exception as e:
            self.logger.error(f"Failed to save performance result: {e}")
            raise PerformanceDatabaseError(f"Save operation failed: {e}")

    def get_performance_history(self, test_name: str = None, limit: int = None,
                                days: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve performance test history with flexible filtering.

        Args:
            test_name: Filter by specific test name
            limit: Maximum number of records to return
            days: Return records from last N days

        Returns:
            List[Dict]: Performance test results
        """
        try:
            base_sql = """
            SELECT * FROM performance_results 
            WHERE 1=1
            """
            params = []

            if test_name:
                base_sql += " AND test_name = ?"
                params.append(test_name)

            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                base_sql += " AND test_run_timestamp >= ?"
                params.append(cutoff_date.isoformat())

            base_sql += " ORDER BY test_run_timestamp DESC"

            if limit:
                base_sql += f" LIMIT {limit}"

            with self.get_connection() as conn:
                cursor = conn.execute(base_sql, params)
                results = []

                for row in cursor.fetchall():
                    result = dict(row)
                    # Parse additional_data JSON
                    if result.get("additional_data"):
                        try:
                            additional = json.loads(result["additional_data"])
                            result.update(additional)
                        except json.JSONDecodeError:
                            pass

                    results.append(result)

                self.logger.debug(f"Retrieved {len(results)} performance records")
                return results

        except Exception as e:
            self.logger.error(f"Failed to retrieve performance history: {e}")
            raise PerformanceDatabaseError(f"Query operation failed: {e}")

    def get_performance_statistics(self, test_name: str = None) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.

        Args:
            test_name: Filter by specific test name

        Returns:
            Dict: Performance statistics
        """
        try:
            with self.get_connection() as conn:
                if test_name:
                    stats_sql = """
                    SELECT 
                        COUNT(*) as total_tests,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_tests,
                        AVG(CASE WHEN success = 1 THEN duration END) as average_duration,
                        MIN(CASE WHEN success = 1 THEN duration END) as min_duration,
                        MAX(CASE WHEN success = 1 THEN duration END) as max_duration,
                        (SELECT duration FROM performance_results WHERE test_name = ? AND success = 1 
                         ORDER BY test_run_timestamp DESC LIMIT 1) as latest_duration
                    FROM performance_results WHERE test_name = ?
                    """
                    cursor = conn.execute(stats_sql, (test_name, test_name))
                else:
                    stats_sql = """
                    SELECT 
                        COUNT(*) as total_tests,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_tests,
                        AVG(CASE WHEN success = 1 THEN duration END) as average_duration,
                        MIN(CASE WHEN success = 1 THEN duration END) as min_duration,
                        MAX(CASE WHEN success = 1 THEN duration END) as max_duration,
                        (SELECT duration FROM performance_results WHERE success = 1 
                         ORDER BY test_run_timestamp DESC LIMIT 1) as latest_duration
                    FROM performance_results
                    """
                    cursor = conn.execute(stats_sql)

                row = cursor.fetchone()

                if row:
                    stats = dict(row)

                    # Calculate trend if we have enough data
                    trend = self._calculate_trend(conn, test_name)
                    stats["trend"] = trend

                    # Ensure no None values
                    for key, value in stats.items():
                        if value is None:
                            stats[key] = 0

                    return stats
                else:
                    return self._empty_stats()

        except Exception as e:
            self.logger.error(f"Failed to calculate statistics: {e}")
            return self._empty_stats()

    def _update_performance_stats(self, conn: sqlite3.Connection, test_name: str) -> None:
        """Update cached performance statistics."""
        try:
            stats_sql = """
            SELECT 
                COUNT(*) as total_runs,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful_runs,
                AVG(CASE WHEN success = 1 THEN duration END) as average_duration,
                MIN(CASE WHEN success = 1 THEN duration END) as min_duration,
                MAX(CASE WHEN success = 1 THEN duration END) as max_duration
            FROM performance_results WHERE test_name = ?
            """

            cursor = conn.execute(stats_sql, (test_name,))
            row = cursor.fetchone()

            if row:
                upsert_sql = """
                INSERT OR REPLACE INTO performance_stats 
                (test_name, total_runs, successful_runs, average_duration, min_duration, max_duration, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """

                conn.execute(upsert_sql, (
                    test_name,
                    row["total_runs"],
                    row["successful_runs"],
                    row["average_duration"] or 0,
                    row["min_duration"] or 0,
                    row["max_duration"] or 0
                ))

        except Exception as e:
            self.logger.warning(f"Failed to update performance stats: {e}")

    def _calculate_trend(self, conn: sqlite3.Connection, test_name: str = None) -> str:
        """Calculate performance trend based on recent vs historical data."""
        try:
            trend_sql = """
            SELECT duration FROM performance_results 
            WHERE success = 1
            """
            params = []

            if test_name:
                trend_sql += " AND test_name = ?"
                params.append(test_name)

            trend_sql += " ORDER BY test_run_timestamp DESC LIMIT 10"

            cursor = conn.execute(trend_sql, params)
            durations = [row["duration"] for row in cursor.fetchall()]

            if len(durations) < 4:
                return "insufficient_data"

            # Compare recent vs earlier averages
            mid = len(durations) // 2
            recent_avg = sum(durations[:mid]) / mid
            earlier_avg = sum(durations[mid:]) / (len(durations) - mid)

            change = ((recent_avg - earlier_avg) / earlier_avg) * 100

            if change < -5:
                return "improving"
            elif change > 5:
                return "degrading"
            else:
                return "stable"

        except Exception:
            return "unknown"

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_tests": 0,
            "successful_tests": 0,
            "average_duration": 0,
            "min_duration": 0,
            "max_duration": 0,
            "latest_duration": 0,
            "trend": "no_data"
        }

    def backup_database(self, backup_path: str = None) -> str:
        """
        Create database backup with timestamp.

        Args:
            backup_path: Custom backup path

        Returns:
            str: Path to backup file
        """
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"performance_backup_{timestamp}.db")

        try:
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()

            self.logger.info(f"Database backup created: {backup_path}")
            return backup_path

        except Exception as e:
            raise PerformanceDatabaseError(f"Backup operation failed: {e}")

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and health metrics."""
        try:
            with self.get_connection() as conn:
                # Get record counts
                cursor = conn.execute("SELECT COUNT(*) as total_records FROM performance_results")
                total_records = cursor.fetchone()["total_records"]

                # Get date range
                cursor = conn.execute("""
                    SELECT 
                        MIN(test_run_timestamp) as earliest_test,
                        MAX(test_run_timestamp) as latest_test
                    FROM performance_results
                """)
                date_info = cursor.fetchone()

                # Get schema version
                cursor = conn.execute("SELECT value FROM database_metadata WHERE key = 'schema_version'")
                schema_row = cursor.fetchone()
                schema_version = schema_row["value"] if schema_row else "unknown"

                # Get database file size
                file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                return {
                    "database_path": self.db_path,
                    "schema_version": schema_version,
                    "total_records": total_records,
                    "earliest_test": date_info["earliest_test"],
                    "latest_test": date_info["latest_test"],
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }

        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}

    def delete_last_record(self, test_name: str = None) -> bool:
        """
        Delete the last record from performance_results table.
        
        :param test_name: Optional filter by test name
        :return: True if record was deleted, False otherwise
        """
        try:
            with self.get_connection() as conn:
                if test_name:
                    # Delete last record for specific test
                    delete_sql = """
                    DELETE FROM performance_results 
                    WHERE id = (
                        SELECT id FROM performance_results 
                        WHERE test_name = ? 
                        ORDER BY id DESC LIMIT 1
                    )
                    """
                    cursor = conn.execute(delete_sql, (test_name,))
                else:
                    # Delete last record overall
                    delete_sql = """
                    DELETE FROM performance_results 
                    WHERE id = (
                        SELECT id FROM performance_results 
                        ORDER BY id DESC LIMIT 1
                    )
                    """
                    cursor = conn.execute(delete_sql)
                
                conn.commit()
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.logger.info(f"Deleted last record{f' for test {test_name}' if test_name else ''}")
                    return True
                else:
                    self.logger.warning(f"No records found to delete{f' for test {test_name}' if test_name else ''}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to delete last record: {e}")
            return False

    def close(self) -> None:
        """Close all database connections."""
        try:
            with self._lock:
                for conn in self._connection_pool.values():
                    conn.close()
                self._connection_pool.clear()

            self.logger.info("Database connections closed")

        except Exception as e:
            self.logger.warning(f"Error closing database connections: {e}")