# Test cho chart_service (build_candlestick_chart).
# Kịch bản kiểm thử tham khảo: docs/assignments.md giai đoạn 6.

import pandas as pd
import plotly.graph_objects as go
import pytest

from services.chart_service import build_candlestick_chart


def test_builds_figure_from_ohlc():
    df = pd.DataFrame({
        "trade_date": pd.date_range("2026-10-01", periods=3, freq="D"),
        "open": [1, 2, 3], "high": [2, 3, 4], "low": [0.5, 1.5, 2.5], "close": [1.5, 2.5, 3.5],
    })
    fig = build_candlestick_chart(df, "VNM")
    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "candlestick"


def test_empty_dataframe_rejected():
    with pytest.raises(ValueError):
        build_candlestick_chart(pd.DataFrame(), "VNM")


def test_missing_column_rejected():
    df = pd.DataFrame({"trade_date": [pd.Timestamp("2026-10-01")], "open": [1], "high": [2], "low": [0.5]})
    with pytest.raises(ValueError):
        build_candlestick_chart(df, "VNM")
