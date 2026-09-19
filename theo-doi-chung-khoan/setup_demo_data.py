#!/usr/bin/env python3
"""
Demo data setup script for Telegram messaging feature.
Run this after setup_database.py to populate demo data with telegram_chat_id.

This script:
1. Creates demo users with telegram_chat_id
2. Adds sample transactions
3. Creates price alerts that can be triggered for demo
4. Enables testing of Telegram notification workflow
"""

import logging
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from repositories import user_repository, transaction_repository, alert_repository
from database import get_db_connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Demo Telegram chat IDs for testing
DEMO_USERS = [
    {
        "username": "demo_trader_1",
        "telegram_chat_id": "791360434",  # Demo chat ID
        "description": "Trader cơ bản"
    },
    {
        "username": "demo_trader_2",
        "telegram_chat_id": "987654321",  # Demo chat ID
        "description": "Trader nâng cao"
    },
    {
        "username": "demo_no_telegram",
        "telegram_chat_id": None,
        "description": "Không có Telegram (kiểm tra xử lý lỗi)"
    },
]

# Sample transactions
DEMO_TRANSACTIONS = {
    "demo_trader_1": [
        {"symbol": "VNM", "transaction_type": "BUY", "quantity": 100, "price": 85.0},
        {"symbol": "ACB", "transaction_type": "BUY", "quantity": 200, "price": 24.0},
        {"symbol": "BID", "transaction_type": "BUY", "quantity": 150, "price": 42.0},
    ],
    "demo_trader_2": [
        {"symbol": "FPT", "transaction_type": "BUY", "quantity": 50, "price": 68.0},
        {"symbol": "VIC", "transaction_type": "BUY", "quantity": 75, "price": 55.0},
        {"symbol": "TCB", "transaction_type": "BUY", "quantity": 100, "price": 30.0},
    ],
    "demo_no_telegram": [
        {"symbol": "GAS", "transaction_type": "BUY", "quantity": 80, "price": 35.0},
    ],
}

# Demo price alerts
DEMO_ALERTS = {
    "demo_trader_1": [
        {
            "symbol": "VNM",
            "target_price": 90.0,
            "condition": "GREATER_THAN_OR_EQUAL",
            "alert_type": "TAKE_PROFIT",
            "description": "Lấy lợi khi VNM >= 90"
        },
        {
            "symbol": "VNM",
            "target_price": 80.0,
            "condition": "LESS_THAN_OR_EQUAL",
            "alert_type": "STOP_LOSS",
            "description": "Cắt lỗ khi VNM <= 80"
        },
        {
            "symbol": "ACB",
            "target_price": 26.0,
            "condition": "GREATER_THAN_OR_EQUAL",
            "alert_type": "TAKE_PROFIT",
            "description": "Lấy lợi khi ACB >= 26"
        },
    ],
    "demo_trader_2": [
        {
            "symbol": "FPT",
            "target_price": 70.0,
            "condition": "GREATER_THAN_OR_EQUAL",
            "alert_type": "TAKE_PROFIT",
            "description": "Lấy lợi khi FPT >= 70"
        },
        {
            "symbol": "VIC",
            "target_price": 50.0,
            "condition": "LESS_THAN_OR_EQUAL",
            "alert_type": "STOP_LOSS",
            "description": "Cắt lỗ khi VIC <= 50"
        },
    ],
    "demo_no_telegram": [
        {
            "symbol": "GAS",
            "target_price": 40.0,
            "condition": "GREATER_THAN_OR_EQUAL",
            "alert_type": "TAKE_PROFIT",
            "description": "Lấy lợi khi GAS >= 40"
        },
    ],
}


def setup_demo_users():
    """Create demo users with telegram_chat_id."""
    logger.info("\n" + "="*80)
    logger.info("BƯỚC 1: Tạo người dùng demo")
    logger.info("="*80)
    
    user_ids = {}
    for user_data in DEMO_USERS:
        try:
            user_id = user_repository.get_or_create_user(
                username=user_data["username"],
                telegram_chat_id=user_data["telegram_chat_id"]
            )
            user_ids[user_data["username"]] = user_id
            telegram_info = (
                f"Telegram ID: {user_data['telegram_chat_id']}" 
                if user_data["telegram_chat_id"] 
                else "Không có Telegram"
            )
            logger.info(
                f"✓ Tạo user: {user_data['username']} (ID: {user_id}) - "
                f"{user_data['description']} - {telegram_info}"
            )
        except ValueError as e:
            logger.warning(f"⚠ User {user_data['username']} có thể đã tồn tại: {e}")
            # Try to get existing user
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (user_data["username"],))
                row = cursor.fetchone()
                if row:
                    user_id = row[0]
                    user_ids[user_data["username"]] = user_id
                    logger.info(f"✓ Sử dụng user hiện có: {user_data['username']} (ID: {user_id})")
                    # Update telegram_chat_id if provided
                    if user_data["telegram_chat_id"]:
                        cursor.execute(
                            "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
                            (user_data["telegram_chat_id"], user_id)
                        )
                        conn.commit()
                        logger.info(f"✓ Cập nhật Telegram ID cho user {user_data['username']}")
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"❌ Lỗi tạo user {user_data['username']}: {e}")
    
    return user_ids


def setup_demo_transactions(user_ids):
    """Create sample transactions for demo users."""
    logger.info("\n" + "="*80)
    logger.info("BƯỚC 2: Thêm giao dịch mẫu")
    logger.info("="*80)
    
    for username, transactions in DEMO_TRANSACTIONS.items():
        if username not in user_ids:
            logger.warning(f"⚠ User {username} không tìm thấy, bỏ qua giao dịch")
            continue
        
        user_id = user_ids[username]
        for trans_data in transactions:
            try:
                trans_id = transaction_repository.add_transaction(
                    user_id=user_id,
                    symbol=trans_data["symbol"],
                    transaction_type=trans_data["transaction_type"],
                    quantity=trans_data["quantity"],
                    price=trans_data["price"]
                )
                logger.info(
                    f"✓ Giao dịch: {username} - "
                    f"{trans_data['transaction_type']} {trans_data['quantity']} "
                    f"{trans_data['symbol']} @ {trans_data['price']} VND (ID: {trans_id})"
                )
            except Exception as e:
                logger.error(
                    f"❌ Lỗi thêm giao dịch {username} - {trans_data['symbol']}: {e}"
                )


def setup_demo_alerts(user_ids):
    """Create sample price alerts for demo users."""
    logger.info("\n" + "="*80)
    logger.info("BƯỚC 3: Tạo cảnh báo giá mẫu")
    logger.info("="*80)
    
    for username, alerts in DEMO_ALERTS.items():
        if username not in user_ids:
            logger.warning(f"⚠ User {username} không tìm thấy, bỏ qua cảnh báo")
            continue
        
        user_id = user_ids[username]
        for alert_data in alerts:
            try:
                alert_id = alert_repository.add_price_alert(
                    user_id=user_id,
                    symbol=alert_data["symbol"],
                    target_price=alert_data["target_price"],
                    condition=alert_data["condition"],
                    alert_type=alert_data["alert_type"]
                )
                logger.info(
                    f"✓ Cảnh báo: {username} - "
                    f"{alert_data['symbol']} {alert_data['condition']} "
                    f"{alert_data['target_price']} VND - "
                    f"{alert_data['alert_type']} (ID: {alert_id}) - "
                    f"{alert_data['description']}"
                )
            except Exception as e:
                logger.error(
                    f"❌ Lỗi tạo cảnh báo {username} - {alert_data['symbol']}: {e}"
                )


def verify_telegram_config():
    """Verify Telegram configuration."""
    logger.info("\n" + "="*80)
    logger.info("BƯỚC 4: Kiểm tra cấu hình Telegram")
    logger.info("="*80)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("⚠ TELEGRAM_BOT_TOKEN không được cấu hình trong .env")
        logger.info("  Để sử dụng tính năng Telegram:")
        logger.info("  1. Nhận token từ @BotFather trên Telegram")
        logger.info("  2. Thêm vào file .env: TELEGRAM_BOT_TOKEN=<your-token>")
        logger.info("  3. Nhận chat ID từ demo users bằng cách:")
        logger.info("     - Gửi tin nhắn tới bot: /start")
        logger.info("     - Copy chat ID vào DEMO_USERS trong script này")
    else:
        logger.info(f"✓ TELEGRAM_BOT_TOKEN được cấu hình (token: {token[:10]}...)")
    
    logger.info("\n📝 Demo Telegram Chat IDs (dùng trong ví dụ):")
    for user_data in DEMO_USERS:
        if user_data["telegram_chat_id"]:
            logger.info(f"  - {user_data['username']}: {user_data['telegram_chat_id']}")
        else:
            logger.info(f"  - {user_data['username']}: (không có)")


def main():
    """Main setup function."""
    logger.info("\n" + "="*80)
    logger.info("🚀 SETUP DỮ LIỆU DEMO CHO TELEGRAM MESSAGING")
    logger.info("="*80)
    
    try:
        # Step 1: Setup demo users
        user_ids = setup_demo_users()
        
        # Step 2: Setup transactions
        setup_demo_transactions(user_ids)
        
        # Step 3: Setup alerts
        setup_demo_alerts(user_ids)
        
        # Step 4: Verify Telegram config
        verify_telegram_config()
        
        logger.info("\n" + "="*80)
        logger.info("✅ SETUP DEMO DỮ LIỆU HOÀN TẤT!")
        logger.info("="*80)
        logger.info("\n📌 Các bước tiếp theo:")
        logger.info("  1. Cấu hình TELEGRAM_BOT_TOKEN trong .env (nếu chưa có)")
        logger.info("  2. Cập nhật telegram_chat_id thực tế trong database:")
        logger.info("     SELECT id, username, telegram_chat_id FROM users;")
        logger.info("  3. Chạy alert_bot.py để kiểm tra cảnh báo được kích hoạt:")
        logger.info("     python alert_bot.py")
        logger.info("  4. Kiểm tra log để xem Telegram messages đã được gửi hay không")
        logger.info("\n💡 Ghi chú:")
        logger.info("  - Demo sử dụng mock telegram_chat_id (123456789, 987654321)")
        logger.info("  - Để nhận messages thực tế, cập nhật bằng chat ID thực của bạn")
        logger.info("  - Chat ID có thể lấy bằng cách gửi /start tới @your_bot_username")
        logger.info("")
    
    except Exception as e:
        logger.error(f"❌ Lỗi trong quá trình setup: {e}")
        logger.exception("Chi tiết lỗi:")
        sys.exit(1)


if __name__ == "__main__":
    main()
