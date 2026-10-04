"""
Test script to send a message to Telegram chat ID 791360434 using the bot token from .env
"""

import sys
import os
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.messaging_service import send_alert_notification, get_bot_token
from dotenv import load_dotenv
import pytest


# Gửi tin nhắn thật qua Telegram: chỉ chạy khi đặt RUN_TELEGRAM_TEST=1.


@pytest.mark.skipif(
    os.getenv("RUN_TELEGRAM_TEST") != "1",
    reason="Gửi tin nhắn thật; đặt RUN_TELEGRAM_TEST=1 để chạy"
)
def test_send_message_to_chat_id():
    """
    Test sending a message to Telegram chat ID 791360434
    """
    # Load environment variables
    load_dotenv()
    
    # Verify bot token is available
    token = get_bot_token()
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not configured in .env")
        return False
    
    print(f"✓ Bot token loaded (starting with: {token[:10]}...)")
    
    # Test parameters
    chat_id = "791360434"
    symbol = "VNM"
    current_price = 85500.00
    target_price = 90000.00
    condition = "GREATER_THAN_OR_EQUAL"
    alert_type = "TAKE_PROFIT"
    
    print(f"\n📤 Sending test message to chat ID: {chat_id}")
    print(f"   Symbol: {symbol}")
    print(f"   Current Price: {current_price:,.2f} VND")
    print(f"   Target Price: {target_price:,.2f} VND")
    print(f"   Condition: {condition}")
    print(f"   Alert Type: {alert_type}")
    
    # Send the message
    result = send_alert_notification(
        telegram_chat_id=chat_id,
        symbol=symbol,
        current_price=current_price,
        target_price=target_price,
        condition=condition,
        alert_type=alert_type
    )
    
    if result:
        print(f"\n✅ Message sent successfully!")
        return True
    else:
        print(f"\n❌ Failed to send message. Check logs for details.")
        return False


if __name__ == "__main__":
    success = test_send_message_to_chat_id()
    exit(0 if success else 1)
