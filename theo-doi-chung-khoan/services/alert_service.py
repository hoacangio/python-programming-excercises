import os
import re
import sqlite3
import logging
from typing import Callable, Optional

import pandas as pd
import requests

from ..repository.alert_repository import AlertRepository
from alert_process_result import AlertProcessResult, AlertError

logger = logging.getLogger(__name__)


class AlertService:
    """Business logic cho việc tạo price alert."""

    # Schema chuẩn của DataFrame trả về bởi list_price_alerts
    ALERT_COLUMNS = [
        "id",
        "symbol",
        "target_price",
        "condition",
        "alert_type",
        "is_active",
        "created_at",
    ]

    VALID_CONDITIONS = {"GREATER_THAN_OR_EQUAL", "LESS_THAN_OR_EQUAL"}
    VALID_ALERT_TYPES = {"TAKE_PROFIT", "STOP_LOSS"}
    # Symbol: chữ cái/số, dấu chấm, dấu gạch ngang (vd: AAPL, BTC-USD, VNM.VN)
    SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.\-]{1,20}$")

    TELEGRAM_API_BASE = "https://api.telegram.org"
    DEFAULT_TELEGRAM_TIMEOUT_SECONDS = 10

    def __init__(
        self,
        repository: AlertRepository,
        get_current_prices: Optional[Callable[[list[str]], dict[str, float]]] = None,
    ):
        """
        repository: AlertRepository dùng chung cho mọi thao tác DB.
        get_current_prices: hàm nhận list symbol duy nhất, trả về
            dict[str, float]. Mặc định trỏ tới MarketDataService.get_current_prices
            nếu không truyền vào, để tiện inject mock khi test.
        """
        self.repository = repository
        self._get_current_prices = get_current_prices or self._default_get_current_prices

    @staticmethod
    def _default_get_current_prices(symbols: list[str]) -> dict[str, float]:
        """Import trễ để tránh vòng lặp import / phụ thuộc cứng vào MarketDataService."""
        from market_data_service import get_current_prices  # type: ignore

        return get_current_prices(symbols)

    def add_price_alert(
        self,
        user_id: int,
        symbol: str,
        target_price: float,
        condition: str,
        alert_type: str,
    ) -> tuple[bool, str]:
        # --- 1. Normalize ---
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_condition = condition.strip().upper() if condition else ""
        normalized_alert_type = alert_type.strip().upper() if alert_type else ""

        # --- 2. Validate input ---
        if not normalized_symbol or not self.SYMBOL_PATTERN.match(normalized_symbol):
            return False, f"Symbol không hợp lệ: '{symbol}'."

        if target_price is None or target_price <= 0:
            return False, "target_price phải lớn hơn 0."

        if normalized_condition not in self.VALID_CONDITIONS:
            return False, (
                f"condition không hợp lệ: '{condition}'. "
                f"Chỉ chấp nhận {sorted(self.VALID_CONDITIONS)}."
            )

        if normalized_alert_type not in self.VALID_ALERT_TYPES:
            return False, (
                f"alert_type không hợp lệ: '{alert_type}'. "
                f"Chỉ chấp nhận {sorted(self.VALID_ALERT_TYPES)}."
            )

        # --- 3. Verify user exists ---
        try:
            if not self.repository.user_exists(user_id):
                return False, f"User id {user_id} không tồn tại."
        except sqlite3.Error as e:
            return False, f"Lỗi database khi kiểm tra user: {e}"

        # --- 4. Insert alert ---
        try:
            alert_id = self.repository.insert_price_alert(
                user_id=user_id,
                symbol=normalized_symbol,
                target_price=target_price,
                condition=normalized_condition,
                alert_type=normalized_alert_type,
            )
        except sqlite3.Error as e:
            return False, f"Lỗi database khi tạo alert: {e}"

        return True, (
            f"Đã tạo alert #{alert_id} cho {normalized_symbol} "
            f"({normalized_alert_type}, {normalized_condition} {target_price})."
        )

    @staticmethod
    def _normalize_symbol(symbol: Optional[str]) -> str:
        if not symbol:
            return ""
        return symbol.strip().upper()

    def list_price_alerts(
        self,
        user_id: int,
        active_only: bool = False,
    ) -> pd.DataFrame:
        """
        Trả về DataFrame các price alert của user_id, mới nhất trước.
        active_only=True chỉ lấy alert đang active (is_active = 1).

        Nếu user_id không hợp lệ hoặc DB lỗi, trả về DataFrame rỗng
        với đúng schema thay vì raise exception, vì đây là hàm đọc dữ liệu
        dùng cho hiển thị/worker.
        """
        if user_id is None or user_id <= 0:
            return self._empty_alerts_dataframe()

        try:
            rows = self.repository.select_alerts_by_user(
                user_id=user_id,
                active_only=active_only,
            )
        except sqlite3.Error:
            return self._empty_alerts_dataframe()

        if not rows:
            return self._empty_alerts_dataframe()

        df = pd.DataFrame(rows, columns=self.ALERT_COLUMNS)

        # Chuẩn hóa kiểu dữ liệu
        df["id"] = df["id"].astype(int)
        df["target_price"] = df["target_price"].astype(float)
        df["is_active"] = df["is_active"].astype(bool)
        df["symbol"] = df["symbol"].astype(str)
        df["condition"] = df["condition"].astype(str)
        df["alert_type"] = df["alert_type"].astype(str)
        df["created_at"] = pd.to_datetime(df["created_at"])

        return df.sort_values("created_at", ascending=False).reset_index(drop=True)

    def _empty_alerts_dataframe(self) -> pd.DataFrame:
        """DataFrame rỗng nhưng đúng schema, dùng khi không có dữ liệu hoặc lỗi."""
        return pd.DataFrame(columns=self.ALERT_COLUMNS)

    def deactivate_price_alert(
        self,
        user_id: int,
        alert_id: int,
    ) -> tuple[bool, str]:
        """
        Tắt một price alert đang active. Chỉ chủ sở hữu (user_id đúng)
        mới tắt được alert của chính mình.
        """
        # --- 1. Validate input ---
        if user_id is None or user_id <= 0:
            return False, "user_id không hợp lệ."

        if alert_id is None or alert_id <= 0:
            return False, "alert_id không hợp lệ."

        # --- 2. Update và kiểm tra affected_rows ---
        try:
            affected_rows = self.repository.deactivate_alert(
                user_id=user_id,
                alert_id=alert_id,
            )
        except sqlite3.Error as e:
            return False, f"Lỗi database khi tắt alert: {e}"

        if affected_rows == 1:
            return True, f"Đã tắt alert #{alert_id}."

        return False, (
            f"Không thể tắt alert #{alert_id}: "
            "alert không tồn tại, không thuộc user này hoặc đã tắt."
        )

    def process_price_alerts(self) -> AlertProcessResult:
        """
        Worker chạy nền: kiểm tra tất cả active alert, gửi Telegram cho alert
        nào thỏa điều kiện, và chỉ tắt alert sau khi Telegram xác nhận thành công.

        Database URL (repository đã cấu hình sẵn), TELEGRAM_BOT_TOKEN và
        timeout được lấy từ biến môi trường. Hàm không nhận input từ Streamlit.
        """
        result = AlertProcessResult()

        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        timeout = self._get_telegram_timeout()

        if not telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN chưa được cấu hình, dừng xử lý alert.")
            result.errors.append(
                AlertError(alert_id=0, message="TELEGRAM_BOT_TOKEN chưa được cấu hình.")
            )
            return result

        # --- 1. Lấy active alerts kèm chat_id ---
        try:
            alert_rows = self.repository.select_active_alerts_with_chat_id()
        except sqlite3.Error as e:
            logger.error("Lỗi database khi lấy active alerts: %s", e)
            result.errors.append(
                AlertError(alert_id=0, message=f"Lỗi database khi lấy active alerts: {e}")
            )
            return result

        result.checked_count = len(alert_rows)
        if not alert_rows:
            return result

        # --- 2. Lấy giá hiện tại cho các symbol duy nhất ---
        unique_symbols = sorted({row["symbol"] for row in alert_rows})
        try:
            current_prices = self._get_current_prices(unique_symbols)
        except Exception as e:
            logger.error("Lỗi khi lấy current prices: %s", e)
            result.errors.append(
                AlertError(alert_id=0, message=f"Lỗi khi lấy current prices: {e}")
            )
            return result

        # --- 3. Duyệt từng alert đủ dữ liệu giá ---
        for row in alert_rows:
            alert_id = row["alert_id"]
            symbol = row["symbol"]
            current_price = current_prices.get(symbol)

            if current_price is None:
                # Không có giá cho symbol này -> bỏ qua, không tính là lỗi xử lý alert
                continue

            if not self._is_condition_met(
                condition=row["condition"],
                current_price=current_price,
                target_price=row["target_price"],
            ):
                continue

            result.triggered_count += 1

            text = self._build_alert_message(
                symbol=symbol,
                alert_type=row["alert_type"],
                condition=row["condition"],
                target_price=row["target_price"],
                current_price=current_price,
            )

            sent_ok, send_error = self._send_telegram_message(
                token=telegram_token,
                chat_id=row["chat_id"],
                text=text,
                timeout=timeout,
            )

            if not sent_ok:
                result.failed_count += 1
                logger.error("Gửi Telegram thất bại cho alert #%s: %s", alert_id, send_error)
                result.errors.append(AlertError(alert_id=alert_id, message=send_error))
                continue

            # --- 4. Chỉ deactivate sau khi Telegram xác nhận thành công ---
            try:
                affected_rows = self.repository.deactivate_alert_by_id(alert_id)
            except sqlite3.Error as e:
                result.failed_count += 1
                message = f"Gửi thành công nhưng lỗi DB khi tắt alert: {e}"
                logger.error("Alert #%s: %s", alert_id, message)
                result.errors.append(AlertError(alert_id=alert_id, message=message))
                continue

            if affected_rows == 1:
                result.sent_count += 1
            else:
                # Đã gửi Telegram nhưng không update được (vd: đã bị tắt bởi tiến trình khác)
                result.failed_count += 1
                message = "Gửi thành công nhưng affected_rows != 1 khi tắt alert."
                logger.error("Alert #%s: %s", alert_id, message)
                result.errors.append(AlertError(alert_id=alert_id, message=message))

        return result

    @staticmethod
    def _get_telegram_timeout() -> float:
        raw_timeout = os.environ.get("TELEGRAM_TIMEOUT_SECONDS")
        if not raw_timeout:
            return AlertService.DEFAULT_TELEGRAM_TIMEOUT_SECONDS
        try:
            return float(raw_timeout)
        except ValueError:
            logger.warning(
                "TELEGRAM_TIMEOUT_SECONDS='%s' không hợp lệ, dùng mặc định %ss.",
                raw_timeout,
                AlertService.DEFAULT_TELEGRAM_TIMEOUT_SECONDS,
            )
            return AlertService.DEFAULT_TELEGRAM_TIMEOUT_SECONDS

    @staticmethod
    def _is_condition_met(
        condition: str,
        current_price: float,
        target_price: float,
    ) -> bool:
        if condition == "GREATER_THAN_OR_EQUAL":
            return current_price >= target_price
        if condition == "LESS_THAN_OR_EQUAL":
            return current_price <= target_price
        # Condition không xác định (dữ liệu DB hỏng) -> coi như không thỏa
        logger.warning("Condition không xác định: %s", condition)
        return False

    @staticmethod
    def _build_alert_message(
        symbol: str,
        alert_type: str,
        condition: str,
        target_price: float,
        current_price: float,
    ) -> str:
        readable_condition = (
            ">=" if condition == "GREATER_THAN_OR_EQUAL" else "<="
        )
        return (
            f"🔔 {alert_type} - {symbol}\n"
            f"Điều kiện: giá {readable_condition} {target_price}\n"
            f"Giá hiện tại: {current_price}"
        )

    def _send_telegram_message(
        self,
        token: str,
        chat_id: str,
        text: str,
        timeout: float,
    ) -> tuple[bool, Optional[str]]:
        """
        Gửi tin nhắn qua Telegram Bot API.
        Trả về (True, None) nếu HTTP 200 và JSON ok=true.
        Trả về (False, error_message) cho mọi trường hợp còn lại
        (lỗi mạng, timeout, HTTP lỗi, ok=false).
        """
        url = f"{self.TELEGRAM_API_BASE}/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        try:
            response = requests.post(url, json=payload, timeout=timeout)
        except requests.RequestException as e:
            return False, f"Lỗi kết nối Telegram: {e}"

        if response.status_code != 200:
            return False, f"Telegram trả HTTP {response.status_code}: {response.text}"

        try:
            data = response.json()
        except ValueError:
            return False, "Telegram trả về JSON không hợp lệ."

        if not data.get("ok"):
            return False, f"Telegram ok=false: {data}"

        return True, None