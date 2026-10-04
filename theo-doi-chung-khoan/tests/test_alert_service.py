# Test cho alert_service (add_price_alert, list_price_alerts, deactivate_price_alert,
# process_price_alerts). Kịch bản kiểm thử tham khảo: docs/assignments.md giai đoạn 6.

import pytest

from database import PriceAlert
from repositories import user_repository
from services import alert_service, market_data_service, messaging_service

GE = "GREATER_THAN_OR_EQUAL"
LE = "LESS_THAN_OR_EQUAL"


def _is_active(user_id, alert_id):
    df = alert_service.list_price_alerts(user_id, active_only=False)
    return bool(df.loc[df["id"] == alert_id, "is_active"].iloc[0])


@pytest.fixture
def prices(monkeypatch):
    """Giả lập nguồn giá: test gán dict giá vào prices.value."""
    class Prices:
        value = {}
    def fake_get_current_prices(symbols):
        return {s: Prices.value[s] for s in symbols if s in Prices.value}
    monkeypatch.setattr(market_data_service, "get_current_prices", fake_get_current_prices)
    return Prices


@pytest.fixture
def telegram(monkeypatch):
    """Giả lập Telegram: ghi lại tin đã gửi, có thể bật chế độ gửi lỗi."""
    class Telegram:
        sent = []
        fail = False
    def fake_send(telegram_chat_id, symbol, **kwargs):
        if Telegram.fail:
            return False
        Telegram.sent.append((telegram_chat_id, symbol))
        return True
    monkeypatch.setattr(messaging_service, "send_alert_notification", fake_send)
    Telegram.sent = []
    return Telegram


# --- Điều kiện kích hoạt ---

@pytest.mark.parametrize("condition,price,expected", [
    (GE, 99_999, False),
    (GE, 100_000, True),    # bằng ngưỡng cũng kích hoạt
    (GE, 100_001, True),
    (LE, 99_999, True),
    (LE, 100_000, True),
    (LE, 100_001, False),
])
def test_should_trigger_boundaries(condition, price, expected):
    alert = PriceAlert(id=1, user_id=1, symbol="VNM", target_price=100_000,
                       condition=condition, alert_type="TAKE_PROFIT")
    assert alert.should_trigger(price) is expected


# --- Tạo và quản lý cảnh báo ---

def test_add_valid_alert(user_id):
    alert_id = alert_service.add_price_alert(user_id, "vnm", 60_000, GE, "TAKE_PROFIT")
    df = alert_service.list_price_alerts(user_id)
    assert df["id"].tolist() == [alert_id]
    assert df["symbol"].iloc[0] == "VNM"


@pytest.mark.parametrize("target,condition", [
    (60_000, "EQUAL"),   # điều kiện không hợp lệ
    (-1, GE),            # giá mục tiêu âm
])
def test_invalid_alert_rejected(user_id, target, condition):
    with pytest.raises(ValueError):
        alert_service.add_price_alert(user_id, "VNM", target, condition, "TAKE_PROFIT")


def test_deactivate_own_alert(user_id):
    alert_id = alert_service.add_price_alert(user_id, "VNM", 60_000, GE, "TAKE_PROFIT")
    alert_service.deactivate_price_alert(alert_id, user_id)
    assert not _is_active(user_id, alert_id)


def test_deactivate_other_users_alert_rejected(user_id, other_user_id):
    alert_id = alert_service.add_price_alert(user_id, "VNM", 60_000, GE, "TAKE_PROFIT")
    with pytest.raises(ValueError):
        alert_service.deactivate_price_alert(alert_id, other_user_id)
    assert _is_active(user_id, alert_id)


def test_reactivate_requires_owner(user_id, other_user_id):
    alert_id = alert_service.add_price_alert(user_id, "VNM", 60_000, GE, "TAKE_PROFIT")
    alert_service.deactivate_price_alert(alert_id, user_id)
    with pytest.raises(ValueError):
        alert_service.reactivate_price_alert(alert_id, other_user_id)
    alert_service.reactivate_price_alert(alert_id, user_id)
    assert _is_active(user_id, alert_id)


# --- process_price_alerts ---

def test_triggered_alert_sent_then_deactivated(user_id, prices, telegram):
    alert_id = alert_service.add_price_alert(user_id, "VNM", 57_000, GE, "TAKE_PROFIT")
    prices.value = {"VNM": 57_300}

    result = alert_service.process_price_alerts()

    assert result["triggered"] == 1
    assert result["deactivated"] == 1
    assert telegram.sent == [("123456789", "VNM")]
    assert not _is_active(user_id, alert_id)


def test_alert_not_reached_stays_active(user_id, prices, telegram):
    alert_id = alert_service.add_price_alert(user_id, "VNM", 60_000, GE, "TAKE_PROFIT")
    prices.value = {"VNM": 57_300}

    result = alert_service.process_price_alerts()

    assert result["triggered"] == 0
    assert telegram.sent == []
    assert _is_active(user_id, alert_id)


def test_send_failure_keeps_alert_and_retries(user_id, prices, telegram):
    """Ít nhất một lần: gửi lỗi thì cảnh báo vẫn active và được gửi lại ở chu kỳ sau."""
    alert_id = alert_service.add_price_alert(user_id, "VNM", 60_000, LE, "STOP_LOSS")
    prices.value = {"VNM": 57_300}

    telegram.fail = True
    result = alert_service.process_price_alerts()
    assert result["triggered"] == 1
    assert result["deactivated"] == 0
    assert _is_active(user_id, alert_id)

    telegram.fail = False
    result = alert_service.process_price_alerts()
    assert result["deactivated"] == 1
    assert telegram.sent == [("123456789", "VNM")]
    assert not _is_active(user_id, alert_id)


def test_missing_chat_id_keeps_alert_active(prices, telegram):
    no_chat_user = user_repository.get_or_create_user("no_chat", None)
    alert_id = alert_service.add_price_alert(no_chat_user, "VNM", 50_000, GE, "TAKE_PROFIT")
    prices.value = {"VNM": 57_300}

    result = alert_service.process_price_alerts()

    assert result["messaging"]["details"][0]["status"] == "skipped_no_telegram_chat_id"
    assert result["deactivated"] == 0
    assert _is_active(no_chat_user, alert_id)


def test_missing_price_keeps_alert_active(user_id, prices, telegram):
    alert_id = alert_service.add_price_alert(user_id, "XYZ", 10_000, GE, "TAKE_PROFIT")
    prices.value = {}

    result = alert_service.process_price_alerts()

    assert result["triggered"] == 0
    assert _is_active(user_id, alert_id)


def test_price_source_error_reported(user_id, monkeypatch, telegram):
    def broken(symbols):
        raise market_data_service.MarketDataError("timeout")
    monkeypatch.setattr(market_data_service, "get_current_prices", broken)
    alert_id = alert_service.add_price_alert(user_id, "VNM", 50_000, GE, "TAKE_PROFIT")

    result = alert_service.process_price_alerts()

    assert "timeout" in result["error"]
    assert _is_active(user_id, alert_id)


def test_each_symbol_priced_once(user_id, monkeypatch, telegram):
    calls = []
    def fake(symbols):
        calls.append(sorted(symbols))
        return {}
    monkeypatch.setattr(market_data_service, "get_current_prices", fake)
    alert_service.add_price_alert(user_id, "VNM", 60_000, GE, "TAKE_PROFIT")
    alert_service.add_price_alert(user_id, "VNM", 50_000, LE, "STOP_LOSS")
    alert_service.add_price_alert(user_id, "FPT", 70_000, GE, "TAKE_PROFIT")

    alert_service.process_price_alerts()

    assert calls == [["FPT", "VNM"]]
