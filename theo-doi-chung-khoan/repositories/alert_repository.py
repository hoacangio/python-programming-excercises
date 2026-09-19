# Truy vấn/ghi bảng price_alerts, phục vụ add_price_alert/list_price_alerts/
# deactivate_price_alert/process_price_alerts.
# Thiết kế: docs/functions/add_price_alert.md, docs/functions/list_price_alerts.md,
# docs/functions/deactivate_price_alert.md, docs/functions/process_price_alerts.md.
# Schema: docs/requirements.md mục 4.

import logging
from datetime import datetime
from typing import Optional

from database import get_db_connection, PriceAlert

logger = logging.getLogger(__name__)


def add_price_alert(
    user_id: int,
    symbol: str,
    target_price: float,
    condition: str,
    alert_type: str
) -> int:
    """
    Thêm cảnh báo giá mới.
    
    Args:
        user_id: ID người dùng
        symbol: Mã cổ phiếu
        target_price: Giá mục tiêu (phải > 0)
        condition: 'GREATER_THAN_OR_EQUAL' hoặc 'LESS_THAN_OR_EQUAL'
        alert_type: 'TAKE_PROFIT' hoặc 'STOP_LOSS'
    
    Returns:
        ID của cảnh báo vừa thêm
    
    Raises:
        ValueError: Nếu dữ liệu không hợp lệ
    """
    # Validate using PriceAlert model (basic validation + normalization)
    alert = PriceAlert(
        id=0,  # Temporary ID for validation
        user_id=user_id,
        symbol=symbol,
        target_price=target_price,
        condition=condition,
        alert_type=alert_type
    )  # Raises ValueError if basic validation fails
    
    # Use normalized values from model
    symbol = alert.symbol
    condition = alert.condition
    alert_type = alert.alert_type
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO price_alerts
            (user_id, symbol, target_price, condition, alert_type, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (user_id, symbol, float(target_price), condition, alert_type)
        )
        conn.commit()
        alert_id = cursor.lastrowid
        logger.info(
            "Cảnh báo mới: user_id=%s, symbol=%s, target_price=%s, condition=%s, alert_type=%s",
            user_id, symbol, target_price, condition, alert_type
        )
        return alert_id
    except Exception as e:
        conn.rollback()
        logger.exception("Lỗi khi thêm cảnh báo giá")
        raise


def list_price_alerts(user_id: int, active_only: bool = True) -> list[PriceAlert]:
    """
    Liệt kê các cảnh báo của một người dùng.
    
    Args:
        user_id: ID người dùng
        active_only: Chỉ lấy cảnh báo đang hoạt động (is_active=1)
    
    Returns:
        Danh sách PriceAlert objects
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute(
                """
                SELECT
                    id, user_id, symbol, target_price, condition, alert_type, is_active, created_at
                FROM price_alerts
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
        else:
            cursor.execute(
                """
                SELECT
                    id, user_id, symbol, target_price, condition, alert_type, is_active, created_at
                FROM price_alerts
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            created_at = None
            if row[7]:
                created_at = datetime.fromisoformat(row[7])
            
            result.append(PriceAlert(
                id=row[0],
                user_id=row[1],
                symbol=row[2],
                target_price=row[3],
                condition=row[4],
                alert_type=row[5],
                is_active=bool(row[6]),
                created_at=created_at
            ))
        return result
    except Exception as e:
        logger.exception("Lỗi khi lấy danh sách cảnh báo")
        raise


def deactivate_price_alert(alert_id: int) -> None:
    """
    Vô hiệu hóa một cảnh báo (set is_active=0).
    
    Args:
        alert_id: ID cảnh báo
    
    Raises:
        ValueError: Nếu alert_id không tồn tại
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE price_alerts SET is_active = 0 WHERE id = ?",
            (alert_id,)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise ValueError(f"Cảnh báo id={alert_id} không tồn tại")
        
        logger.info("Vô hiệu hóa cảnh báo id=%s", alert_id)
    except ValueError:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Lỗi khi vô hiệu hóa cảnh báo")
        raise


def reactivate_price_alert(alert_id: int, user_id: int) -> None:
    """
    Kích hoạt lại một cảnh báo đã vô hiệu hóa (set is_active=1).
    
    Kiểm tra rằng cảnh báo thuộc về người dùng (bảo mật).
    
    Args:
        alert_id: ID cảnh báo
        user_id: ID người dùng (để xác thực quyền sở hữu)
    
    Raises:
        ValueError: Nếu alert_id không tồn tại hoặc không thuộc về user_id
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Kiểm tra cảnh báo tồn tại và thuộc về người dùng
        cursor.execute(
            "SELECT id FROM price_alerts WHERE id = ? AND user_id = ?",
            (alert_id, user_id)
        )
        
        if cursor.fetchone() is None:
            raise ValueError(
                f"Cảnh báo id={alert_id} không tồn tại hoặc không thuộc về user_id={user_id}"
            )
        
        # Kích hoạt lại cảnh báo
        cursor.execute(
            "UPDATE price_alerts SET is_active = 1 WHERE id = ?",
            (alert_id,)
        )
        conn.commit()
        
        logger.info("Kích hoạt lại cảnh báo id=%s của user_id=%s", alert_id, user_id)
    except ValueError:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.exception("Lỗi khi kích hoạt lại cảnh báo")
        raise


def get_active_alerts_by_symbol(symbol: str) -> list[PriceAlert]:
    """
    Lấy tất cả cảnh báo đang hoạt động cho một mã cổ phiếu.
    
    Dùng bởi process_price_alerts() để kiểm tra mỗi 5 phút.
    
    Args:
        symbol: Mã cổ phiếu
    
    Returns:
        Danh sách PriceAlert objects
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, user_id, symbol, target_price, condition, alert_type, is_active, created_at
            FROM price_alerts
            WHERE symbol = ? AND is_active = 1
            ORDER BY created_at ASC
            """,
            (symbol.upper(),)
        )
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            created_at = None
            if row[7]:
                created_at = datetime.fromisoformat(row[7])
            
            result.append(PriceAlert(
                id=row[0],
                user_id=row[1],
                symbol=row[2],
                target_price=row[3],
                condition=row[4],
                alert_type=row[5],
                is_active=bool(row[6]),
                created_at=created_at
            ))
        return result
    except Exception as e:
        logger.exception("Lỗi khi lấy cảnh báo đang hoạt động cho %s", symbol)
        raise


def get_all_active_alerts() -> list[PriceAlert]:
    """
    Lấy tất cả cảnh báo đang hoạt động (dùng bởi process_price_alerts).
    
    Returns:
        Danh sách PriceAlert objects
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, user_id, symbol, target_price, condition, alert_type, is_active, created_at
            FROM price_alerts
            WHERE is_active = 1
            ORDER BY symbol ASC, created_at ASC
            """
        )
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            created_at = None
            if row[7]:
                created_at = datetime.fromisoformat(row[7])
            
            result.append(PriceAlert(
                id=row[0],
                user_id=row[1],
                symbol=row[2],
                target_price=row[3],
                condition=row[4],
                alert_type=row[5],
                is_active=bool(row[6]),
                created_at=created_at
            ))
        return result
    except Exception as e:
        logger.exception("Lỗi khi lấy tất cả cảnh báo đang hoạt động")
        raise

