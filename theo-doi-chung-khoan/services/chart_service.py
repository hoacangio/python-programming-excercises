# build_candlestick_chart.
# Thiết kế: docs/functions/build_candlestick_chart.md.

import plotly.graph_objects as go


def build_candlestick_chart(df, symbol):

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
