# Truy vấn/ghi bảng price_alerts, phục vụ add_price_alert/list_price_alerts/
# deactivate_price_alert/process_price_alerts.
# Thiết kế: docs/functions/add_price_alert.md, docs/functions/list_price_alerts.md,
# docs/functions/deactivate_price_alert.md, docs/functions/process_price_alerts.md.
# Schema: docs/requirements.md mục 4.
import sqlite3


class AlertRepository:
    def __init__(self, db_path: str = "data/portfolio.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def user_exists(self, user_id: int) -> bool:
        """Kiểm tra user_id có tồn tại trong bảng users hay không."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM users WHERE id = ? LIMIT 1",
                (user_id,),
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def insert_price_alert(
        self,
        user_id: int,
        symbol: str,
        target_price: float,
        condition: str,
        alert_type: str,
    ) -> int:
        """
        Insert một price alert đang active (is_active = 1).
        Trả về alert_id vừa tạo. Ném sqlite3.Error nếu DB lỗi.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO price_alerts
                    (user_id, symbol, target_price, condition, alert_type, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (user_id, symbol, target_price, condition, alert_type),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def select_alerts_by_user(
        self,
        user_id: int,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Lấy các price_alerts của user_id, mới nhất trước.
        active_only=True sẽ thêm điều kiện is_active = 1.
        Trả về list[dict], rỗng nếu không có dòng nào. Ném sqlite3.Error nếu DB lỗi.
        """
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            query = (
                "SELECT id, symbol, target_price, condition, alert_type, "
                "is_active, created_at "
                "FROM price_alerts WHERE user_id = ?"
            )
            params: list[Any] = [user_id]
 
            if active_only:
                query += " AND is_active = 1"
 
            query += " ORDER BY created_at DESC"
 
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def deactivate_alert(self, user_id: int, alert_id: int) -> int:
        """
        Tắt một alert đang active thuộc về user_id.
        Chỉ update khi id khớp, user_id khớp và is_active = 1.
        Trả về số dòng bị ảnh hưởng (0 hoặc 1). Ném sqlite3.Error nếu DB lỗi.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                UPDATE price_alerts
                SET is_active = 0
                WHERE id = ?
                  AND user_id = ?
                  AND is_active = 1
                """,
                (alert_id, user_id),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def select_active_alerts_with_chat_id(self) -> list[dict[str, Any]]:
        """
        Lấy toàn bộ active alerts (is_active = 1) kèm chat_id của user sở hữu,
        dùng cho worker process_price_alerts. Join price_alerts với users.
        Trả về list[dict] với keys: alert_id, symbol, target_price, condition,
        alert_type, chat_id. Ném sqlite3.Error nếu DB lỗi.
        """
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT
                    pa.id AS alert_id,
                    pa.symbol AS symbol,
                    pa.target_price AS target_price,
                    pa.condition AS condition,
                    pa.alert_type AS alert_type,
                    u.chat_id AS chat_id
                FROM price_alerts pa
                JOIN users u ON u.id = pa.user_id
                WHERE pa.is_active = 1
                """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
 
    def deactivate_alert_by_id(self, alert_id: int) -> int:
        """
        Tắt một alert theo alert_id, dùng sau khi Telegram xác nhận gửi thành công.
        Không cần user_id vì worker chạy nền, không có "current user".
        Trả về số dòng bị ảnh hưởng (0 hoặc 1). Ném sqlite3.Error nếu DB lỗi.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                UPDATE price_alerts
                SET is_active = 0
                WHERE id = ?
                  AND is_active = 1
                """,
                (alert_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
 