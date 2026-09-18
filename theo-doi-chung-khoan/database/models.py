"""
Data model classes for the stock tracking application.

Provides type-safe representations of database entities:
- User: Individual user with optional Telegram integration
- Transaction: Buy/Sell transactions for stocks
- PriceAlert: Price threshold alerts for automated notifications

These models serve as the single source of truth for entity structure
and are used throughout the application for type hints and validation.

Schema thiết kế tại docs/requirements.md mục 4 (Đặc Tả Database).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


@dataclass
class User:
    """
    Represents a user in the system.
    
    Attributes:
        id: Unique user identifier (from database)
        username: Unique username for login/identification
        telegram_chat_id: Optional Telegram chat ID for bot notifications
        created_at: Timestamp when user was created
    """
    id: int
    username: str
    telegram_chat_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.username or not str(self.username).strip():
            raise ValueError("username không được rỗng")
        
        self.username = str(self.username).strip()
        if self.telegram_chat_id:
            self.telegram_chat_id = str(self.telegram_chat_id).strip() or None
    
    def to_dict(self) -> dict:
        """Convert User to dictionary for serialization."""
        return {
            "id": self.id,
            "username": self.username,
            "telegram_chat_id": self.telegram_chat_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Transaction:
    """
    Represents a buy/sell transaction for a stock.
    
    Attributes:
        id: Unique transaction identifier (from database)
        user_id: ID of the user who made the transaction
        symbol: Stock symbol (e.g., 'AAPL', 'VNM'), normalized to uppercase
        transaction_type: Either 'BUY' or 'SELL'
        quantity: Number of shares (must be > 0)
        price: Price per share in currency units (must be > 0)
        transaction_date: When the transaction occurred
        notes: Optional notes about the transaction
    """
    id: int
    user_id: int
    symbol: str
    transaction_type: Literal['BUY', 'SELL']
    quantity: int
    price: float
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate transaction data after initialization."""
        # Normalize symbol
        self.symbol = str(self.symbol).strip().upper()
        if not self.symbol:
            raise ValueError("symbol không được rỗng")
        
        # Validate transaction type
        self.transaction_type = str(self.transaction_type).strip().upper()
        if self.transaction_type not in ('BUY', 'SELL'):
            raise ValueError("transaction_type phải là 'BUY' hoặc 'SELL'")
        
        # Validate quantity
        if self.quantity <= 0:
            raise ValueError("quantity phải > 0")
        
        # Validate price
        if self.price <= 0:
            raise ValueError("price phải > 0")
    
    def get_amount(self) -> float:
        """Calculate total amount for this transaction (quantity * price)."""
        return self.quantity * self.price
    
    def to_dict(self) -> dict:
        """Convert Transaction to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "price": self.price,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "notes": self.notes
        }


@dataclass
class PriceAlert:
    """
    Represents a price alert configuration.
    
    Used to monitor stock prices and trigger notifications when conditions are met.
    
    Attributes:
        id: Unique alert identifier (from database)
        user_id: ID of the user who created this alert
        symbol: Stock symbol to monitor, normalized to uppercase
        target_price: Price threshold to monitor
        condition: Trigger condition:
            - 'GREATER_THAN_OR_EQUAL': Alert when price >= target_price
            - 'LESS_THAN_OR_EQUAL': Alert when price <= target_price
        alert_type: Purpose of the alert:
            - 'TAKE_PROFIT': Profit-taking alert
            - 'STOP_LOSS': Stop-loss alert
        is_active: Whether this alert is currently active (monitoring enabled)
        created_at: When the alert was created
    """
    id: int
    user_id: int
    symbol: str
    target_price: float
    condition: Literal['GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL']
    alert_type: Literal['TAKE_PROFIT', 'STOP_LOSS']
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    VALID_CONDITIONS = ('GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL')
    VALID_ALERT_TYPES = ('TAKE_PROFIT', 'STOP_LOSS')
    
    def __post_init__(self):
        """Validate price alert data after initialization."""
        # Normalize symbol
        self.symbol = str(self.symbol).strip().upper()
        if not self.symbol:
            raise ValueError("symbol không được rỗng")
        
        # Validate target price
        if self.target_price <= 0:
            raise ValueError("target_price phải > 0")
        
        # Normalize and validate condition
        self.condition = str(self.condition).strip().upper()
        if self.condition not in self.VALID_CONDITIONS:
            raise ValueError(
                f"condition phải là: {', '.join(self.VALID_CONDITIONS)}"
            )
        
        # Normalize and validate alert type
        self.alert_type = str(self.alert_type).strip().upper()
        if self.alert_type not in self.VALID_ALERT_TYPES:
            raise ValueError(
                f"alert_type phải là: {', '.join(self.VALID_ALERT_TYPES)}"
            )
    
    def should_trigger(self, current_price: float) -> bool:
        """
        Check if this alert should be triggered based on current price.
        
        Args:
            current_price: Current price to check against
            
        Returns:
            bool: True if condition is met and alert should trigger
        """
        if not self.is_active:
            return False
        
        if self.condition == 'GREATER_THAN_OR_EQUAL':
            return current_price >= self.target_price
        else:  # LESS_THAN_OR_EQUAL
            return current_price <= self.target_price
    
    def to_dict(self) -> dict:
        """Convert PriceAlert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "target_price": self.target_price,
            "condition": self.condition,
            "alert_type": self.alert_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
