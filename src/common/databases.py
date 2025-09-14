"""
FogLAMP Database Access System

Production-ready database access layer following MCP best practices.
Supports sqlite, sqlitelb, postgres, and sqlitememory with connection pooling,
retry logic, query safety, and comprehensive error handling.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    _logger.debug("psycopg2 not available. PostgreSQL support disabled.")

from foglamp.services.mcp.common.config_manager import DatabaseConnectionInfo

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


# ============================================================================
# EXCEPTIONS
# ============================================================================

class DatabaseError(Exception):
    """Base database operation exception."""
    pass


class ConnectionError(DatabaseError):
    """Database connection exception."""
    pass


class QueryError(DatabaseError):
    """Query execution exception."""
    pass


class ValidationError(DatabaseError):
    """Query validation exception."""
    pass


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ConnectionHealth:
    """Represents database connection health.
    
    Args:
        is_healthy: Whether the database connection is healthy
        response_time_ms: Response time in milliseconds
        database_version: Database version string if available
        error_message: Error message if connection failed
        last_check: Unix timestamp of last health check
    """
    
    is_healthy: bool
    response_time_ms: float
    database_version: Optional[str]
    error_message: Optional[str] = None
    last_check: float = 0.0


# ============================================================================
# QUERY VALIDATOR
# ============================================================================

class QueryValidator:
    """Validates SQL queries for safety and correctness."""
    
    # Safe query prefixes (case-insensitive)
    SAFE_PREFIXES = {'select', 'with', 'show', 'describe', 'explain'}
    
    # Dangerous keywords that require validation
    DANGEROUS_KEYWORDS = {
        'drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update'
    }
    
    def validate_query(self, query: str, allow_write: bool = False) -> None:
        """
        Validate SQL query for safety.
        
        Args:
            query: SQL query to validate
            allow_write: Whether to allow write operations
            
        Raises:
            ValidationError: If query is unsafe or invalid
        """
        if not query or not query.strip():
            raise ValidationError("Empty query not allowed")
            
        # Normalize query
        normalized = query.strip().lower()
        
        # Check for multiple statements
        if self._has_multiple_statements(normalized):
            raise ValidationError("Multiple statements not allowed for safety")
            
        # Get first word (command)
        first_word = normalized.split()[0] if normalized.split() else ""
        
        # Check if it's a safe read operation
        if first_word in self.SAFE_PREFIXES:
            return  # Safe query
            
        # Check for dangerous operations
        if not allow_write and any(keyword in normalized for keyword in self.DANGEROUS_KEYWORDS):
            raise ValidationError(f"Write operation not allowed: {first_word}")
            
        # If write operations are allowed, let them through
        if allow_write:
            return
            
        # Unknown operation - be safe and reject
        raise ValidationError(f"Unsupported query type: {first_word}")
    
    def _has_multiple_statements(self, query: str) -> bool:
        """Check if query contains multiple statements."""
        # Simple check for semicolons (could be enhanced for quoted strings)
        semicolon_count = query.count(';')
        if semicolon_count == 0:
            return False
        if semicolon_count == 1 and query.rstrip().endswith(';'):
            return False
        return semicolon_count > 1


# ============================================================================
# CONNECTION POOL BASE
# ============================================================================

class ConnectionPool(ABC):
    """Abstract base class for database connection pools."""
    
    def __init__(self, connection_info: DatabaseConnectionInfo, pool_size: int = 5):
        """Initialize connection pool."""
        self.connection_info = connection_info
        self.pool_size = pool_size
        self._pool = []
        self._lock = threading.Lock()
        self._created_connections = 0
        self._health = ConnectionHealth(False, 0.0, None)
        self._validator = QueryValidator()
    
    @abstractmethod
    def _create_connection(self):
        """Create new database connection."""
        pass
    
    @abstractmethod
    def _test_connection(self, conn) -> bool:
        """Test if connection is healthy."""
        pass
    
    @abstractmethod
    def _execute_query(self, conn, query: str) -> Tuple[List[Dict], float]:
        """Execute query and return results with execution time."""
        pass
    
    @abstractmethod
    def _get_database_version(self, conn) -> str:
        """Get database version."""
        pass
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with automatic return."""
        conn = None
        try:
            conn = self._acquire_connection()
            yield conn
        finally:
            if conn:
                self._return_connection(conn)
    
    def _acquire_connection(self):
        """Acquire connection from pool."""
        with self._lock:
            # Try to get existing connection
            while self._pool:
                conn = self._pool.pop(0)
                if self._test_connection(conn):
                    return conn
                else:
                    self._close_connection(conn)
            
            # Create new connection if under limit
            if self._created_connections < self.pool_size:
                try:
                    conn = self._create_connection()
                    self._created_connections += 1
                    return conn
                except Exception as e:
                    raise ConnectionError(f"Failed to create connection: {e}")
            
            raise ConnectionError("Connection pool exhausted")
    
    def _return_connection(self, conn):
        """Return connection to pool."""
        with self._lock:
            if len(self._pool) < self.pool_size and self._test_connection(conn):
                self._pool.append(conn)
            else:
                self._close_connection(conn)
                self._created_connections -= 1
    
    def _close_connection(self, conn):
        """Close database connection."""
        try:
            if hasattr(conn, 'close'):
                conn.close()
        except:
            pass
    
    def execute_query(self, query: str, allow_write: bool = False) -> Dict[str, Any]:
        """
        Execute SQL query with validation and error handling.
        
        Args:
            query: SQL query to execute
            allow_write: Whether to allow write operations
            
        Returns:
            Dict containing: rows, column_names, row_count
            
        Raises:
            ValidationError: If query is invalid
            QueryError: If execution fails
        """
        # Validate query
        self._validator.validate_query(query, allow_write)
        
        # Execute with retry logic
        for attempt in range(3):
            try:
                with self.get_connection() as conn:
                    rows, exec_time = self._execute_query(conn, query)
                    
                    # Extract column names
                    column_names = list(rows[0].keys()) if rows else []
                    
                    return {
                        "rows": rows,
                        "column_names": column_names,
                        "row_count": len(rows)
                    }
                    
            except ConnectionError:
                if attempt == 2:  # Last attempt
                    raise
                _logger.warning(f"Connection failed, retrying... (attempt {attempt + 1}/3)")
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                raise QueryError(f"Query execution failed: {e}")
    
    def health_check(self) -> ConnectionHealth:
        """Check database health."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                if self._test_connection(conn):
                    response_time = (time.time() - start_time) * 1000
                    version = self._get_database_version(conn)
                    
                    self._health = ConnectionHealth(
                        is_healthy=True,
                        response_time_ms=response_time,
                        database_version=version,
                        last_check=time.time()
                    )
                else:
                    self._health = ConnectionHealth(
                        is_healthy=False,
                        response_time_ms=0.0,
                        database_version=None,
                        error_message="Connection test failed",
                        last_check=time.time()
                    )
                    
        except Exception as e:
            self._health = ConnectionHealth(
                is_healthy=False,
                response_time_ms=0.0,
                database_version=None,
                error_message=str(e),
                last_check=time.time()
            )
        
        return self._health

    def close(self):
        """Close all connections in pool."""
        with self._lock:
            while self._pool:
                conn = self._pool.pop(0)
                self._close_connection(conn)
            self._created_connections = 0


# ============================================================================
# DATABASES CONNECTION POOL
# ============================================================================

class SQLitePool(ConnectionPool):
    """SQLite connection pool implementation."""
    
    def _create_connection(self):
        """Create SQLite connection."""
        db_path = str(self.connection_info.database)
        
        if db_path == ":memory:":
            conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            if not os.path.exists(db_path):
                raise ConnectionError(f"Database file not found: {db_path}")
            conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Configure connection
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        return conn
    
    def _test_connection(self, conn) -> bool:
        """Test SQLite connection."""
        try:
            conn.execute("SELECT 1")
            return True
        except:
            return False
    
    def _execute_query(self, conn, query: str) -> Tuple[List[Dict], float]:
        """Execute SQLite query."""
        start_time = time.time()
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Convert rows to dictionaries
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            rows = []
        
        exec_time = (time.time() - start_time) * 1000
        return rows, exec_time
    
    def _get_database_version(self, conn) -> str:
        """Get SQLite version."""
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        return f"SQLite {cursor.fetchone()[0]}"


class PostgreSQLPool(ConnectionPool):
    """PostgreSQL connection pool implementation."""
    
    def __init__(self, connection_info: DatabaseConnectionInfo, pool_size: int = 5):
        """Initialize PostgreSQL pool."""
        if not POSTGRES_AVAILABLE:
            raise ConnectionError("PostgreSQL support not available (psycopg2 not installed)")
        super().__init__(connection_info, pool_size)
    
    def _create_connection(self):
        """Create PostgreSQL connection."""
        conn_params = {
            "dbname": self.connection_info.database,
            "host": self.connection_info.host,
            "port": self.connection_info.port,
            "connect_timeout": 10
        }
        
        if self.connection_info.user:
            conn_params["user"] = self.connection_info.user
        if self.connection_info.password:
            conn_params["password"] = self.connection_info.password
            
        return psycopg2.connect(**conn_params)
    
    def _test_connection(self, conn) -> bool:
        """Test PostgreSQL connection."""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except:
            return False
    
    def _execute_query(self, conn, query: str) -> Tuple[List[Dict], float]:
        """Execute PostgreSQL query."""
        start_time = time.time()
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query)
            
            if cursor.description:
                rows = [dict(row) for row in cursor.fetchall()]
            else:
                rows = []
        
        exec_time = (time.time() - start_time) * 1000
        return rows, exec_time
    
    def _get_database_version(self, conn) -> str:
        """Get PostgreSQL version."""
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            return cursor.fetchone()[0]


# ============================================================================
# DATABASE FACTORY
# ============================================================================

class DatabaseFactory:
    """Factory for creating database connection pools."""
    
    _pools: Dict[str, ConnectionPool] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_pool(cls, connection_info: DatabaseConnectionInfo) -> ConnectionPool:
        """
        Get or create connection pool for database.
        
        Args:
            connection_info: Database connection configuration
            
        Returns:
            Connection pool instance
            
        Raises:
            ConnectionError: If database type is not supported
        """
        # Create unique key for pool
        pool_key = f"{connection_info.plugin}:{connection_info.database}:{connection_info.host}:{connection_info.port}"
        
        with cls._lock:
            if pool_key not in cls._pools:
                cls._pools[pool_key] = cls._create_pool(connection_info)
            
            return cls._pools[pool_key]
    
    @classmethod
    def _create_pool(cls, connection_info: DatabaseConnectionInfo) -> ConnectionPool:
        """Create appropriate connection pool."""
        plugin = connection_info.plugin.lower()
        
        if plugin in ["sqlite", "sqlitelb", "sqlitememory"]:
            return SQLitePool(connection_info)
        elif plugin == "postgres":
            return PostgreSQLPool(connection_info)
        else:
            raise ConnectionError(f"Unsupported database plugin: {plugin}")
    
    @classmethod
    def close_all_pools(cls):
        """Close all connection pools."""
        with cls._lock:
            for pool in cls._pools.values():
                pool.close()
            cls._pools.clear()
