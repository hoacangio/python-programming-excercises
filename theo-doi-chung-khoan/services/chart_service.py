# build_candlestick_chart.
# Thiết kế: docs/functions/build_candlestick_chart.md.

import plotly.graph_objects as go
import pandas as pd


def build_candlestick_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """
    Xây dựng biểu đồ nến (Candlestick) từ dữ liệu OHLC.
    
    Args:
        df: DataFrame chứa cột: trade_date, open, high, low, close
        symbol: Mã cổ phiếu (dùng để hiển thị tiêu đề)
    
    Returns:
        Plotly Figure (Candlestick chart)
    """
    if df is None or df.empty:
        raise ValueError("DataFrame không được rỗng")
    
    required_columns = ["trade_date", "open", "high", "low", "close"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"DataFrame thiếu cột: {missing}")

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["trade_date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name=symbol
            )
        ]
    )

    fig.update_layout(
        title=f"Biểu đồ nến {symbol}",
        xaxis_title="Ngày",
        yaxis_title="Giá (VND)",
        height=550,
        xaxis_rangeslider_visible=False
    )

    return fig

