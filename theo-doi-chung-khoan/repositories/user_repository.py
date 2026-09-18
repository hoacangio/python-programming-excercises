# Truy vấn/ghi bảng users (bao gồm telegram_chat_id).
# Schema: docs/requirements.md mục 4, bảng "users".

import logging
from datetime import datetime
from typing import Optional

from database import get_db_connection, User

logger = logging.getLogger(__name__)


def get_or_create_user(username: str, telegram_chat_id: Optional[str] = None) -> int:
    """
    Lấy hoặc tạo người dùng.
    
    Args:
        username: Tên người dùng (unique)
        telegram_chat_id: Telegram chat ID (tùy chọn)
    
    Returns:
        ID người dùng
    
    Raises:
        ValueError: Nếu username không hợp lệ (từ User model)
    """
    # Validate using User model (basic validation)
    user = User(
        id=0,  # Temporary ID for validation
        username=username,
        telegram_chat_id=telegram_chat_id
    )  # Raises ValueError if basic validation fails
    
    # Use normalized values from model
    username = user.username
    telegram_chat_id = user.telegram_chat_id
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Kiểm tra nếu người dùng đã tồn tại
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row:
            user_id = row[0]
            # Cập nhật telegram_chat_id nếu có
            if telegram_chat_id:
                cursor.execute(
                    "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
                    (telegram_chat_id, user_id)
                )
                conn.commit()
            return user_id
        
        # Tạo người dùng mới
        cursor.execute(
            "INSERT INTO users (username, telegram_chat_id) VALUES (?, ?)",
            (username, telegram_chat_id)
        )
        conn.commit()
        user_id = cursor.lastrowid
        logger.info("Tạo người dùng mới: %s (id=%s)", username, user_id)
        return user_id
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        conn.rollback()
        logger.exception("Lỗi khi tạo hoặc lấy người dùng")
        if "UNIQUE constraint failed" in str(e):
            raise ValueError(f"username '{username}' đã tồn tại") from e
        raise


def get_user(user_id: int) -> Optional[User]:
    """
    Lấy thông tin người dùng theo ID.
    
    Args:
        user_id: ID người dùng
    
    Returns:
        User object nếu tìm thấy, None nếu không
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, telegram_chat_id, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        created_at = None
        if row[3]:
            created_at = datetime.fromisoformat(row[3])
        
        return User(
            id=row[0],
            username=row[1],
            telegram_chat_id=row[2],
            created_at=created_at
        )
    except Exception as e:
        logger.exception("Lỗi khi lấy thông tin người dùng id=%s", user_id)
        raise


def update_telegram_chat_id(user_id: int, telegram_chat_id: str) -> None:
    """
    Cập nhật Telegram chat ID cho người dùng.
    
    Args:
        user_id: ID người dùng
        telegram_chat_id: Chat ID mới
    
    Raises:
        ValueError: Nếu user_id không tồn tại hoặc telegram_chat_id rỗng
    """
    if not telegram_chat_id or not str(telegram_chat_id).strip():
        raise ValueError("telegram_chat_id không được rỗng")
    
    telegram_chat_id = str(telegram_chat_id).strip()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
            (telegram_chat_id, user_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Người dùng id={user_id} không tồn tại")
        
        logger.info("Cập nhật Telegram chat ID cho user_id=%s", user_id)
    except ValueError:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Lỗi khi cập nhật Telegram chat ID")
        raise

