"""
Database layer - centralized connection and data models.

This package provides:
- DatabaseConnection: Singleton for managing database connections
- get_db_connection(): Function to get the shared connection
- Data model classes: User, Transaction, PriceAlert

Usage:
    # Get database connection
    from database import get_db_connection
    conn = get_db_connection()
    
    # Use data models for type safety
    from database import User, Transaction, PriceAlert
    user = User(id=1, username="john")
    
    # Direct imports
    from database.session import DatabaseConnection
    from database.models import User, Transaction, PriceAlert
"""

from database.session import (
    DatabaseConnection,
    get_db_connection,
    DB_PATH,
)
from database.models import (
    User,
    Transaction,
    PriceAlert,
)

__all__ = [
    # Session/Connection
    'DatabaseConnection',
    'get_db_connection',
    'DB_PATH',
    # Models
    'User',
    'Transaction',
    'PriceAlert',
]
