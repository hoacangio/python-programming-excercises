"""
Centralized database connection instance for the entire application.

This module provides a singleton database connection that is shared across
all repositories. This ensures:
- Efficient resource usage (single connection pool)
- Consistent transaction handling
- Easy testing and mocking

Quy ước transaction/commit/rollback: docs/requirements.md mục 5 (Quy ước triển khai).
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Database path - accessible from any working directory
DB_PATH = Path(__file__).parent.parent / "data" / "portfolio.db"


class DatabaseConnection:
    """
    Centralized database connection singleton.
    
    Provides a single, reusable connection to the SQLite database.
    Handles connection lifecycle and ensures proper resource cleanup.
    
    Usage:
        db = DatabaseConnection()
        conn = db.get_connection()
        # Use connection
        conn.close()  # Or use context manager
    """
    
    _instance: Optional['DatabaseConnection'] = None
    
    def __new__(cls) -> 'DatabaseConnection':
        """Ensure singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the database connection (called only once per singleton)."""
        if self._initialized:
            return
        
        self.db_path = DB_PATH
        self._connection: Optional[sqlite3.Connection] = None
        self._initialized = True
        logger.debug(f"DatabaseConnection initialized with path: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create database connection.
        
        Creates a new connection if one doesn't exist or if the existing
        connection is closed.
        
        Returns:
            sqlite3.Connection: Active database connection
            
        Raises:
            FileNotFoundError: If database file does not exist
            sqlite3.DatabaseError: If connection fails
        """
        if self._connection is None or self._is_connection_closed():
            if not self.db_path.exists():
                raise FileNotFoundError(
                    f"Database file not found at {self.db_path}. "
                    "Run setup_database.py first."
                )
            
            try:
                self._connection = sqlite3.connect(str(self.db_path))
                # Enable foreign key constraints
                self._connection.execute("PRAGMA foreign_keys = ON")
                logger.debug(f"Database connection established: {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        
        return self._connection
    
    def _is_connection_closed(self) -> bool:
        """
        Check if the current connection is closed.
        
        Returns:
            bool: True if connection is closed or invalid, False otherwise
        """
        if self._connection is None:
            return True
        
        try:
            self._connection.execute("SELECT 1")
            return False
        except sqlite3.ProgrammingError:
            return True
    
    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.debug("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
    
    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        self.close()


# Global singleton instance
_db_connection = DatabaseConnection()


def get_db_connection() -> sqlite3.Connection:
    """
    Get the centralized database connection.
    
    This is the main entry point for accessing the database.
    Should be used instead of creating new connections directly.
    
    Returns:
        sqlite3.Connection: The shared database connection
        
    Example:
        from database import get_db_connection
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
        finally:
            conn.close()
    """
    return _db_connection.get_connection()
