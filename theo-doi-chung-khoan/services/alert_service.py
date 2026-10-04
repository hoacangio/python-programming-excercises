# add_price_alert, list_price_alerts, deactivate_price_alert, process_price_alerts.
# Thiết kế: docs/functions/add_price_alert.md, docs/functions/list_price_alerts.md,
# docs/functions/deactivate_price_alert.md, docs/functions/process_price_alerts.md.

import logging
from typing import Optional

import pandas as pd

from repositories import alert_repository, user_repository
from services import market_data_service, messaging_service

logger = logging.getLogger(__name__)


def add_price_alert(
    user_id: int,
    symbol: str,
    target_price: float,
    condition: str,
    alert_type: str
) -> int:
    """
    Thêm một cảnh báo giá mới cho người dùng.
    
    Validation được xử lý bởi PriceAlert model trong repository layer.
    
    Args:
        user_id: ID người dùng
        symbol: Mã cổ phiếu
        target_price: Giá mục tiêu (phải > 0)
        condition: 'GREATER_THAN_OR_EQUAL' hoặc 'LESS_THAN_OR_EQUAL'
        alert_type: 'TAKE_PROFIT' hoặc 'STOP_LOSS'
    
    Returns:
        ID của cảnh báo vừa thêm
    
    Raises:
        ValueError: Nếu dữ liệu không hợp lệ (từ PriceAlert model)
    """
    try:
        alert_id = alert_repository.add_price_alert(
            user_id=user_id,
            symbol=symbol,
            target_price=float(target_price),
            condition=condition,
            alert_type=alert_type
        )
        logger.info(
            "Cảnh báo thêm thành công: user_id=%s, symbol=%s, target=%s, type=%s",
            user_id, symbol, target_price, alert_type
        )
        return alert_id
    except ValueError as e:
        logger.warning("Dữ liệu cảnh báo không hợp lệ: %s", e)
        raise
    except Exception as e:
        logger.exception("Lỗi khi thêm cảnh báo")
        raise


def list_price_alerts(user_id: int, active_only: bool = True) -> pd.DataFrame:
    """
    Liệt kê các cảnh báo giá của người dùng.
    
    Args:
        user_id: ID người dùng
        active_only: Chỉ lấy cảnh báo đang hoạt động (mặc định: True)
    
    Returns:
        DataFrame với cột: id, user_id, symbol, target_price, condition, alert_type, is_active, created_at
    """
    try:
        alerts = alert_repository.list_price_alerts(user_id, active_only)
        if not alerts:
            return pd.DataFrame(columns=[
                "id", "user_id", "symbol", "target_price",
                "condition", "alert_type", "is_active", "created_at"
            ])
        
        # Convert PriceAlert objects to dicts for DataFrame
        alert_dicts = [alert.to_dict() for alert in alerts]
        df = pd.DataFrame(alert_dicts)
        logger.info("Lấy %d cảnh báo cho user_id=%s", len(df), user_id)
        return df
    except Exception as e:
        logger.exception("Lỗi khi lấy danh sách cảnh báo")
        raise


def deactivate_price_alert(alert_id: int, user_id: int) -> None:
    """
    Vô hiệu hóa một cảnh báo giá.
    
    Người dùng chỉ có thể vô hiệu hóa cảnh báo của chính họ (xác thực qua user_id).
    
    Args:
        alert_id: ID cảnh báo
        user_id: ID người dùng (để xác thực quyền sở hữu)
    
    Raises:
        ValueError: Nếu alert_id không tồn tại hoặc không thuộc về user_id
    """
    try:
        alert_repository.deactivate_price_alert(alert_id, user_id)
        logger.info("Cảnh báo %s đã vô hiệu hóa cho user_id=%s", alert_id, user_id)
    except ValueError as e:
        logger.warning("Không thể vô hiệu hóa cảnh báo: %s", e)
        raise
    except Exception as e:
        logger.exception("Lỗi khi vô hiệu hóa cảnh báo")
        raise


def reactivate_price_alert(alert_id: int, user_id: int) -> None:
    """
    Kích hoạt lại một cảnh báo giá đã vô hiệu hóa.
    
    Người dùng chỉ có thể kích hoạt lại cảnh báo của chính họ (xác thực qua user_id).
    
    Args:
        alert_id: ID cảnh báo
        user_id: ID người dùng (để xác thực quyền sở hữu)
    
    Raises:
        ValueError: Nếu alert_id không tồn tại hoặc không thuộc về user_id
    """
    try:
        alert_repository.reactivate_price_alert(alert_id, user_id)
        logger.info("Cảnh báo %s đã được kích hoạt lại cho user_id=%s", alert_id, user_id)
    except ValueError as e:
        logger.warning("Không thể kích hoạt lại cảnh báo: %s", e)
        raise
    except Exception as e:
        logger.exception("Lỗi khi kích hoạt lại cảnh báo")
        raise


def process_price_alerts() -> dict:
    """
    Xử lý tất cả các cảnh báo giá đang hoạt động.
    
    Kiểm tra giá hiện tại của mỗi mã cổ phiếu và so sánh với các ngưỡng cảnh báo.
    Cảnh báo đạt ngưỡng được gửi qua Telegram trước; chỉ những cảnh báo gửi
    thành công mới bị vô hiệu hóa (đảm bảo "ít nhất một lần"). Cảnh báo gửi lỗi
    vẫn active và được gửi lại ở chu kỳ sau.
    
    Dùng bởi alert_bot.py chạy theo BOT_INTERVAL_MINUTES.
    
    Returns:
        Dict kết quả: {
            "total_alerts": số cảnh báo được kiểm tra,
            "triggered": số cảnh báo đạt ngưỡng,
            "deactivated": số cảnh báo đã gửi thành công và được vô hiệu hóa,
            "details": [{alert_id, symbol, current_price, target_price, condition, ...}],
            "messaging": kết quả gửi Telegram
        }
    """
    empty_messaging = {"total": 0, "successful": 0, "failed": 0, "details": []}
    
    try:
        # Lấy tất cả cảnh báo đang hoạt động
        all_alerts = alert_repository.get_all_active_alerts()
        
        if not all_alerts:
            logger.info("Không có cảnh báo đang hoạt động để kiểm tra")
            return {
                "total_alerts": 0,
                "triggered": 0,
                "deactivated": 0,
                "details": [],
                "messaging": empty_messaging
            }
        
        # Nhóm cảnh báo theo mã cổ phiếu
        symbols_to_check = set(alert.symbol for alert in all_alerts)
        
        # Lấy giá hiện tại
        try:
            current_prices = market_data_service.get_current_prices(list(symbols_to_check))
        except Exception as e:
            logger.exception("Lỗi khi lấy giá hiện tại")
            return {
                "total_alerts": len(all_alerts),
                "triggered": 0,
                "deactivated": 0,
                "details": [],
                "messaging": empty_messaging,
                "error": str(e)
            }
        
        # Bước 1: tìm các cảnh báo đạt ngưỡng
        triggered_alerts = []
        
        for alert in all_alerts:
            current_price = current_prices.get(alert.symbol)
            
            if current_price is None:
                logger.warning("Không tìm thấy giá cho %s", alert.symbol)
                continue
            
            if not alert.should_trigger(current_price):
                continue
            
            user = user_repository.get_user(alert.user_id)
            telegram_chat_id = user.telegram_chat_id if user else None
            
            triggered_alerts.append({
                "alert_id": alert.id,
                "symbol": alert.symbol,
                "current_price": current_price,
                "target_price": alert.target_price,
                "condition": alert.condition,
                "alert_type": alert.alert_type,
                "user_id": alert.user_id,
                "telegram_chat_id": telegram_chat_id
            })
            logger.info(
                "Cảnh báo %s đạt ngưỡng: %s @ %s (target: %s)",
                alert.id, alert.symbol, current_price, alert.target_price
            )
        
        # Bước 2: gửi Telegram
        messaging_result = empty_messaging
        if triggered_alerts:
            try:
                messaging_result = messaging_service.send_bulk_alert_notifications(triggered_alerts)
                logger.info("Gửi Telegram notifications: %s", messaging_result)
            except Exception:
                logger.exception("Lỗi khi gửi Telegram notifications; cảnh báo giữ active để gửi lại")
        
        # Bước 3: chỉ vô hiệu hóa cảnh báo đã gửi thành công
        sent_ids = {
            d["alert_id"] for d in messaging_result["details"] if d["status"] == "sent"
        }
        deactivated_count = 0
        for item in triggered_alerts:
            if item["alert_id"] not in sent_ids:
                continue
            try:
                alert_repository.deactivate_price_alert(item["alert_id"], item["user_id"])
                deactivated_count += 1
            except Exception:
                logger.exception("Lỗi khi vô hiệu hóa cảnh báo %s", item["alert_id"])
        
        result = {
            "total_alerts": len(all_alerts),
            "triggered": len(triggered_alerts),
            "deactivated": deactivated_count,
            "details": triggered_alerts,
            "messaging": messaging_result
        }
        
        logger.info(
            "Xử lý cảnh báo hoàn tất: %d/%d đạt ngưỡng, %d đã gửi và vô hiệu hóa",
            len(triggered_alerts), len(all_alerts), deactivated_count
        )
        
        return result
    
    except Exception as e:
        logger.exception("Lỗi trong quá trình xử lý cảnh báo")
        raise
