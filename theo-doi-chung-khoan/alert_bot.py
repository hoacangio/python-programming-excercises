# Entrypoint cho Cron: gọi services.alert_service.process_price_alerts() và ghi log.
# Không import Streamlit. Thiết kế: docs/functions/process_price_alerts.md,
# docs/requirements.md mục 2 (Lưu ý kỹ thuật).

import logging
import os
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler
from services.alert_service import process_price_alerts
from utils.time_util import setup_local_timezone, format_local_time_for_log, format_next_schedule

# Set up timezone for local time display
setup_local_timezone()

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
scheduler = BackgroundScheduler()


def check_alerts():
    """
    Kiểm tra cảnh báo giá và kích hoạt nếu cần.
    Hàm này được gọi định kỳ bởi scheduler.
    """
    try:
        logger.debug(f"Kiểm tra cảnh báo lúc {format_local_time_for_log()}")
        
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
    
    except Exception as e:
        logger.exception("Lỗi trong quá trình xử lý cảnh báo!")


def main():
    """
    Entrypoint chính của alert_bot.
    
    Khởi động BackgroundScheduler để kiểm tra cảnh báo mỗi 1 phút.
    Scheduler chạy liên tục trong background cho đến khi nhận tín hiệu dừng.
    """
    global scheduler
    
    logger.info("=" * 80)
    logger.info(f"Alert bot khởi động lúc {format_local_time_for_log()}")
    logger.info("=" * 80)
    
    try:
        bot_interval_minutes = int(os.getenv("BOT_INTERVAL_MINUTES", 1))
        
        # Cấu hình scheduler
        scheduler.add_job(
            check_alerts,
            'interval',
            minutes=bot_interval_minutes,
            id='check_price_alerts',
            name='Kiểm tra cảnh báo giá',
            replace_existing=True
        )
        
        logger.info(f'Scheduler được cấu hình: kiểm tra cảnh báo mỗi {bot_interval_minutes} phút')
        
        # Chạy job đầu tiên ngay lập tức
        logger.info("Chạy kiểm tra cảnh báo lần đầu tiên...")
        check_alerts()
        
        # Khởi động scheduler
        logger.info("Khởi động scheduler...")
        scheduler.start()
        logger.info("Alert bot đang chạy. Nhấn Ctrl+C để dừng.")
        logger.info(f"Lịch kiểm tra tiếp theo: {format_next_schedule(bot_interval_minutes)}")
        
        # Giữ scheduler chạy
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            raise
    
    except (KeyboardInterrupt, SystemExit):
        logger.info("Nhận tín hiệu dừng. Đang tắt scheduler...")
        scheduler.shutdown()
        logger.info("Alert bot đã dừng")
    except Exception as e:
        logger.exception("Lỗi nghiêm trọng trong alert bot!")
        if scheduler.running:
            scheduler.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()

