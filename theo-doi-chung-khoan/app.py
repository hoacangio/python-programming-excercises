import streamlit as st
import pandas as pd
from services.chart_service import build_candlestick_chart

from repositories.market_repository import (
    get_symbols,
    get_market_data,
    get_latest_price
)


# =========================
# CẤU HÌNH TRANG
# =========================
st.set_page_config(
    page_title="Theo dõi chứng khoán",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Hệ thống theo dõi chứng khoán")
st.caption("Dữ liệu được đọc từ SQLite - portfolio.db")


# =========================
# SIDEBAR
# =========================
st.sidebar.header("Bộ lọc")

symbols = get_symbols()

if not symbols:
    st.error("Không tìm thấy dữ liệu trong bảng market_prices.")
    st.stop()

selected_symbol = st.sidebar.selectbox(
    "Chọn mã cổ phiếu",
    symbols
)

period = st.sidebar.selectbox(
    "Khoảng thời gian",
    ["1 tháng", "3 tháng", "6 tháng", "1 năm", "Tất cả"]
)


# =========================
# ĐỌC DATABASE
# =========================
df = get_market_data(selected_symbol)
latest = get_latest_price(selected_symbol)

if df.empty:
    st.warning(f"Không có dữ liệu cho {selected_symbol}")
    st.stop()

days = {
    "1 tháng": 30,
    "3 tháng": 90,
    "6 tháng": 180,
    "1 năm": 365
}

if period != "Tất cả":
    latest_date = df["trade_date"].max()

    start_date = (
        latest_date -
        pd.Timedelta(days=days[period])
    )

    df = df[df["trade_date"] >= start_date]
# =========================
# BIỂU ĐỒ NẾN
# =========================

st.subheader("🕯 Biểu đồ nến")

fig = build_candlestick_chart(
    df,
    selected_symbol
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================
# THÔNG TIN GIÁ MỚI NHẤT
# =========================
st.subheader(f"Thông tin {selected_symbol}")

latest_row = latest.iloc[0]
previous_close = df.iloc[-2]["close"]

price_change = latest_row["close"] - previous_close

percent_change = (
    price_change / previous_close
) * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Giá đóng cửa",
    f"{latest_row['close']:,.0f} VND",
    f"{price_change:,.0f} ({percent_change:.2f}%)"
)

col2.metric(
    "Giá mở cửa",
    f"{latest_row['open']:,.0f}"
)

col3.metric(
    "Giá cao nhất",
    f"{latest_row['high']:,.0f}"
)

col4.metric(
    "Khối lượng",
    f"{latest_row['volume']:,.0f}"
)

# =========================
# BIỂU ĐỒ
# =========================
st.subheader("Biểu đồ giá đóng cửa")

chart_df = df.set_index("trade_date")

st.line_chart(
    chart_df["close"]
)


# =========================
# VOLUME
# =========================
st.subheader("Khối lượng giao dịch")

st.bar_chart(
    chart_df["volume"]
)


# =========================
# BẢNG DỮ LIỆU
# =========================
st.subheader("Dữ liệu lịch sử")

display_df = df.sort_values(
    "trade_date",
    ascending=False
)

st.dataframe(
    display_df,
    use_container_width=True
)