# Test cho market_data_service (get_current_prices).
# Kịch bản kiểm thử tham khảo: docs/assignments.md giai đoạn 6.

import math

import pandas as pd
import pytest

from repositories import market_repository
from services import market_data_service


def _ohlcv(closes):
    index = pd.date_range("2026-10-02 09:15", periods=len(closes), freq="1min")
    return pd.DataFrame(
        {"Open": closes, "High": closes, "Low": closes, "Close": closes, "Volume": [100] * len(closes)},
        index=index,
    )


@pytest.fixture
def fake_yf(monkeypatch):
    """Giả lập yf.download: trả dữ liệu theo ticker, ghi lại ticker đã gọi."""
    class FakeYF:
        data = {}
        tickers = []
    def download(tickers, **kwargs):
        FakeYF.tickers.append(tickers)
        return FakeYF.data.get(tickers, pd.DataFrame())
    monkeypatch.setattr(market_data_service.yf, "download", download)
    FakeYF.tickers = []
    return FakeYF


@pytest.mark.parametrize("symbol,expected", [
    ("VNM", "VNM.VN"),
    (" fpt ", "FPT.VN"),
    ("SHS.HN", "SHS.HN"),   # đã có hậu tố thì giữ nguyên
])
def test_to_yahoo_ticker(symbol, expected):
    assert market_data_service.to_yahoo_ticker(symbol) == expected


def test_uses_vn_suffix_and_returns_latest_close(fake_yf):
    fake_yf.data = {"VNM.VN": _ohlcv([57_000, 57_200, 57_300])}

    prices = market_data_service.get_current_prices(["vnm", "VNM"])

    assert fake_yf.tickers == ["VNM.VN"]          # loại trùng, gọi một lần
    assert prices == {"VNM": 57_300}


def test_caches_under_plain_symbol(fake_yf):
    fake_yf.data = {"VNM.VN": _ohlcv([57_000, 57_300])}

    market_data_service.get_current_prices(["VNM"])

    latest = market_repository.get_latest_price("VNM")
    assert float(latest.iloc[0]["close"]) == 57_300


def test_skips_nan_and_non_positive_prices(fake_yf):
    fake_yf.data = {
        "AAA.VN": _ohlcv([10_000, float("nan")]),   # NaN cuối bị bỏ, lấy giá trước đó
        "BBB.VN": _ohlcv([0, 0]),                   # giá không dương
    }

    prices = market_data_service.get_current_prices(["AAA", "BBB", "CCC"])

    assert prices == {"AAA": 10_000}


def test_empty_symbols_rejected():
    with pytest.raises(ValueError):
        market_data_service.get_current_prices([])


def test_source_error_wrapped(monkeypatch):
    def broken(tickers, **kwargs):
        raise TimeoutError("timeout")
    monkeypatch.setattr(market_data_service.yf, "download", broken)
    with pytest.raises(market_data_service.MarketDataError):
        market_data_service.get_current_prices(["VNM"])
