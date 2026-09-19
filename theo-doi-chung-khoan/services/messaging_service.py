# Telegram messaging service để gửi thông báo cảnh báo giá.
# Thiết kế: Intergration với alert_service, sử dụng python-telegram-bot library.

import logging
import os
import asyncio
from typing import Optional, List, Dict, Any

from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

from utils.time_util import setup_local_timezone, format_local_time_for_message

# Set up timezone for local time display
setup_local_timezone()

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def get_bot_token() -> Optional[str]:
    """
    Lấy Telegram bot token từ environment variable.
    
    Returns:
        Bot token hoặc None nếu không được cấu hình
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    return token if token and token.strip() else None


def send_alert_notification(
    telegram_chat_id: str,
    symbol: str,
    current_price: float,
    target_price: float,
    condition: str,
    alert_type: str
) -> bool:
    """
    Gửi thông báo cảnh báo giá tới người dùng qua Telegram (synchronous wrapper).
    
    Args:
        telegram_chat_id: Telegram chat ID của người dùng
        symbol: Mã cổ phiếu (e.g., 'VNM', 'AAPL')
        current_price: Giá hiện tại
        target_price: Giá mục tiêu được cảnh báo
        condition: Điều kiện cảnh báo ('GREATER_THAN_OR_EQUAL' hoặc 'LESS_THAN_OR_EQUAL')
        alert_type: Loại cảnh báo ('TAKE_PROFIT' hoặc 'STOP_LOSS')
    
    Returns:
        True nếu gửi thành công, False nếu lỗi
    """
    # Run async function in synchronous context
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _async_send_alert_notification(
                telegram_chat_id,
                symbol,
                current_price,
                target_price,
                condition,
                alert_type
            )
        )
        loop.close()
        return result
    except Exception as e:
        logger.exception("Lỗi khi chạy async send_alert_notification: %s", e)
        return False


async def _async_send_alert_notification(
    telegram_chat_id: str,
    symbol: str,
    current_price: float,
    target_price: float,
    condition: str,
    alert_type: str
) -> bool:
    
    token = get_bot_token()
    if not token:
        logger.warning(
            "TELEGRAM_BOT_TOKEN không được cấu hình trong .env. "
            "Không thể gửi thông báo cho user (chat_id=%s)",
            telegram_chat_id
        )
        return False
    
    if not telegram_chat_id or not str(telegram_chat_id).strip():
        logger.warning(
            "telegram_chat_id rỗng. Không thể gửi thông báo cho user với symbol=%s",
            symbol
        )
        return False
    
    try:
        # Tạo tin nhắn
        condition_text = "tăng lên" if condition == "GREATER_THAN_OR_EQUAL" else "giảm xuống"
        alert_type_text = "Lấy lợi nhuận" if alert_type == "TAKE_PROFIT" else "Cắt lỗ"
        local_time_str = format_local_time_for_message()
        
        message = (
            f"🚨 <b>Cảnh báo giá: {symbol}</b>\n\n"
            f"📊 Giá hiện tại: <code>{current_price:,.2f}</code> VND\n"
            f"🎯 Giá mục tiêu: <code>{target_price:,.2f}</code> VND\n"
            f"📈 Điều kiện: {condition_text}\n"
            f"🏷️ Loại: {alert_type_text}\n"
            f"⏰ Thời gian: {local_time_str}\n\n"
        )
        
        # Gửi tin nhắn (async)
        async with Bot(token=token) as bot:
            await bot.send_message(
                chat_id=int(telegram_chat_id.strip().strip("'")),  # Remove quotes if present
                text=message,
                parse_mode="HTML"
            )
        
        logger.info(
            "Gửi thông báo Telegram thành công: "
            "chat_id=%s, symbol=%s, current_price=%s, target_price=%s",
            telegram_chat_id, symbol, current_price, target_price
        )
        return True
    
    except TelegramError as e:
        logger.error(
            "Lỗi Telegram khi gửi thông báo cho chat_id=%s: %s",
            telegram_chat_id, e
        )
        return False
    except Exception as e:
        logger.exception(
            "Lỗi không mong đợi khi gửi thông báo Telegram cho chat_id=%s",
            telegram_chat_id
        )
        return False


def send_bulk_alert_notifications(triggered_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Gửi thông báo cho tất cả các cảnh báo được kích hoạt.
    
    Args:
        triggered_alerts: Danh sách các cảnh báo được kích hoạt từ process_price_alerts()
                         Mỗi phần tử: {
                             "alert_id": int,
                             "symbol": str,
                             "current_price": float,
                             "target_price": float,
                             "condition": str,
                             "alert_type": str,
                             "user_id": int,
                             "telegram_chat_id": str (optional)
                         }
    
    Returns:
        Dict kết quả: {
            "total": số cảnh báo được gửi,
            "successful": số cảnh báo gửi thành công,
            "failed": số cảnh báo gửi thất bại,
            "details": [{alert_id, status}]
        }
    """
    result = {
        "total": len(triggered_alerts),
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    if not triggered_alerts:
        return result
    
    for alert in triggered_alerts:
        telegram_chat_id = alert.get("telegram_chat_id")
        
        if not telegram_chat_id:
            logger.warning(
                "Không có telegram_chat_id cho user_id=%s (alert_id=%s). "
                "Bỏ qua gửi Telegram.",
                alert.get("user_id"), alert.get("alert_id")
            )
            result["failed"] += 1
            result["details"].append({
                "alert_id": alert.get("alert_id"),
                "status": "skipped_no_telegram_chat_id"
            })
            continue
        
        success = send_alert_notification(
            telegram_chat_id=telegram_chat_id,
            symbol=alert.get("symbol"),
            current_price=alert.get("current_price"),
            target_price=alert.get("target_price"),
            condition=alert.get("condition"),
            alert_type=alert.get("alert_type")
        )
        
        if success:
            result["successful"] += 1
            result["details"].append({
                "alert_id": alert.get("alert_id"),
                "status": "sent"
            })
        else:
            result["failed"] += 1
            result["details"].append({
                "alert_id": alert.get("alert_id"),
                "status": "failed"
            })
    
    logger.info(
        "Gửi bulk notifications hoàn tất: %d/%d thành công",
        result["successful"], result["total"]
    )
    
    return result
