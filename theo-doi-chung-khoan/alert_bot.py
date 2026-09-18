# Entrypoint cho Cron: gọi services.alert_service.process_price_alerts() và ghi log.
# Không import Streamlit. Thiết kế: docs/functions/process_price_alerts.md,
# docs/requirements.md mục 2 (Lưu ý kỹ thuật).

import logging
import sys
from datetime import datetime

from services.alert_service import process_price_alerts

# CẤU HÌNH LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("alert_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Entrypoint chính của alert_bot.
    
    Gọi process_price_alerts() mỗi khi script chạy (thường mỗi 5 phút qua cron).
    Ghi log chi tiết về các cảnh báo được kích hoạt.
    """
    logger.info("=" * 80)
    logger.info(f"Alert bot khởi động lúc {datetime.now()}")
    logger.info("=" * 80)
    
    try:
        # Xử lý tất cả cảnh báo đang hoạt động
        result = process_price_alerts()
        
        # Ghi log kết quả
        logger.info(f"Tổng cảnh báo được kiểm tra: {result['total_alerts']}")
        logger.info(f"Cảnh báo được kích hoạt: {result['triggered']}")
        
        if result['details']:
            logger.info("Chi tiết cảnh báo được kích hoạt:")
            for alert_detail in result['details']:
                logger.info(
                    f"  - Alert ID {alert_detail['alert_id']}: "
                    f"{alert_detail['symbol']} @ {alert_detail['current_price']} VND "
                    f"(target: {alert_detail['target_price']} VND, "
                    f"condition: {alert_detail['condition']}, "
                    f"type: {alert_detail['alert_type']}, "
                    f"user_id: {alert_detail['user_id']})"
                )
        
        logger.info("Alert bot hoàn tất thành công")
    
    except Exception as e:
        logger.exception("Lỗi trong quá trình xử lý cảnh báo!")
        sys.exit(1)


if __name__ == "__main__":
    main()

