# Test cho portfolio_service (add_transaction, get_portfolio_summary).
# Kịch bản kiểm thử tham khảo: docs/assignments.md giai đoạn 6.

import math

import pytest

from services import portfolio_service


def _add(user_id, symbol, txn_type, quantity, price):
    return portfolio_service.add_transaction(user_id, symbol, txn_type, quantity, price)


def _row(df, symbol):
    return df[df["symbol"] == symbol].iloc[0]


# --- add_transaction ---

def test_buy_normalizes_symbol(user_id):
    txn_id = _add(user_id, "fpt", "BUY", 100, 100_000)
    assert txn_id > 0
    df = portfolio_service.get_portfolio_summary(user_id)
    assert df["symbol"].tolist() == ["FPT"]


def test_sell_within_holding(user_id):
    _add(user_id, "FPT", "BUY", 100, 100_000)
    assert _add(user_id, "FPT", "SELL", 40, 110_000) > 0


def test_sell_more_than_holding_rejected(user_id):
    _add(user_id, "FPT", "BUY", 100, 100_000)
    _add(user_id, "FPT", "SELL", 40, 110_000)
    with pytest.raises(ValueError, match="Không đủ cổ phiếu"):
        _add(user_id, "FPT", "SELL", 100, 110_000)


@pytest.mark.parametrize("txn_type,quantity,price", [
    ("BUY", 0, 100_000),     # số lượng bằng 0
    ("BUY", 10, -1),         # giá âm
    ("HOLD", 10, 100_000),   # loại giao dịch không hợp lệ
])
def test_invalid_transaction_rejected(user_id, txn_type, quantity, price):
    with pytest.raises(ValueError):
        _add(user_id, "FPT", txn_type, quantity, price)


# --- get_portfolio_summary ---

def test_cost_reduced_after_sell(user_id, insert_price):
    """Bán 40/100: vốn còn lại phải là 60 x giá vốn, không phải tổng tiền mua."""
    insert_price("FPT", 120_000)
    _add(user_id, "FPT", "BUY", 100, 100_000)
    _add(user_id, "FPT", "SELL", 40, 110_000)

    row = _row(portfolio_service.get_portfolio_summary(user_id), "FPT")
    assert row["quantity"] == 60
    assert row["average_price"] == pytest.approx(100_000)
    assert row["cost_value"] == pytest.approx(6_000_000)
    assert row["realized_profit"] == pytest.approx(400_000)
    assert row["unrealized_profit"] == pytest.approx(60 * 20_000)


def test_weighted_average_example_from_report(user_id, insert_price):
    """Chuỗi giao dịch ở Bảng 2.1 của báo cáo, giá thị trường 125.000."""
    insert_price("VNM", 125_000)
    _add(user_id, "VNM", "BUY", 100, 100_000)
    _add(user_id, "VNM", "BUY", 100, 120_000)
    _add(user_id, "VNM", "SELL", 50, 130_000)
    _add(user_id, "VNM", "BUY", 50, 140_000)

    row = _row(portfolio_service.get_portfolio_summary(user_id), "VNM")
    assert row["quantity"] == 200
    assert row["average_price"] == pytest.approx(117_500)
    assert row["cost_value"] == pytest.approx(23_500_000)
    assert row["market_value"] == pytest.approx(25_000_000)
    assert row["unrealized_profit"] == pytest.approx(1_500_000)
    assert row["unrealized_percent"] == pytest.approx(6.383, abs=1e-3)
    assert row["realized_profit"] == pytest.approx(1_000_000)


def test_missing_price_is_nan_not_zero(user_id):
    """Chưa có giá: không được hiển thị lỗ giả bằng toàn bộ vốn."""
    _add(user_id, "ACB", "BUY", 100, 25_000)

    row = _row(portfolio_service.get_portfolio_summary(user_id), "ACB")
    assert row["cost_value"] == pytest.approx(2_500_000)
    assert math.isnan(row["current_price"])
    assert math.isnan(row["market_value"])
    assert math.isnan(row["unrealized_profit"])


def test_fully_sold_symbol_hidden_but_realized_kept(user_id):
    _add(user_id, "BID", "BUY", 50, 40_000)
    _add(user_id, "BID", "SELL", 50, 44_000)

    df = portfolio_service.get_portfolio_summary(user_id)
    assert df.empty
    assert portfolio_service.get_total_realized_profit(user_id) == pytest.approx(200_000)


def test_rebuy_after_selling_out_starts_new_cost(user_id):
    _add(user_id, "BID", "BUY", 50, 40_000)
    _add(user_id, "BID", "SELL", 50, 44_000)
    _add(user_id, "BID", "BUY", 10, 50_000)

    row = _row(portfolio_service.get_portfolio_summary(user_id), "BID")
    assert row["average_price"] == pytest.approx(50_000)
    assert row["realized_profit"] == pytest.approx(200_000)


def test_empty_portfolio_has_schema(user_id):
    df = portfolio_service.get_portfolio_summary(user_id)
    assert df.empty
    assert "unrealized_profit" in df.columns
