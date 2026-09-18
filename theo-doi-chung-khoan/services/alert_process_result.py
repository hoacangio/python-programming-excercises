from dataclasses import dataclass, field


@dataclass
class AlertError:
    """Lỗi xảy ra khi xử lý một alert cụ thể."""

    alert_id: int
    message: str


@dataclass
class AlertProcessResult:
    """Kết quả tổng hợp của một lần chạy process_price_alerts."""

    checked_count: int = 0
    triggered_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    errors: list[AlertError] = field(default_factory=list)