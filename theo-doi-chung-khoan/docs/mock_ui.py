import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# Cấu hình trang
st.set_page_config(page_title="Portfolio Dashboard", layout="wide")

# --- SIDEBAR MENU ---
st.sidebar.title("Menu Điều Hướng")
menu = st.sidebar.radio("Chọn chức năng:", ["Xem danh mục", "Thêm giao dịch", "Cài đặt cảnh báo"])

# --- MÀN HÌNH 1: XEM DANH MỤC ---
if menu == "Xem danh mục":
    st.header("Dashboard Quản Lý Danh Mục")

    # Tổng quan tài sản (Metrics)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng Vốn Đầu Tư", "150,000,000 đ")
    col2.metric("Tổng Giá Trị Hiện Tại", "165,000,000 đ", "15,000,000 đ")
    col3.metric("% Lời/Lỗ", "+10.0%", "Tăng")

    st.divider()

    # Bảng danh mục
    st.subheader("Danh Sách Cổ Phiếu Đang Giữ")
    df_portfolio = pd.DataFrame({
        "Mã": ["FPT", "VNM"],
        "SL": [1000, 500],
        "Giá vốn": [95000, 70000],
        "Giá TT": [105000, 67200],
        "Giá trị HT": [105000000, 33600000],
        "% Lời/Lỗ": ["+10.53%", "-4.00%"]
    })
    st.dataframe(df_portfolio, use_container_width=True, hide_index=True)

    st.divider()

    # Biểu đồ kỹ thuật
    st.subheader("Biểu Đồ Lịch Sử Giá")
    col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
    col_f1.selectbox("Chọn mã", ["FPT", "VNM"])
    col_f2.date_input("Khoảng thời gian", [])
    col_f3.selectbox("Interval", ["1d", "1h", "15m"])

    # Mockup nến giả lập
    fig = go.Figure(data=[go.Candlestick(
        x=['2026-09-01', '2026-09-02', '2026-09-03', '2026-09-04', '2026-09-05'],
        open=[100, 102, 101, 104, 105],
        high=[103, 104, 105, 106, 107],
        low=[99, 100, 101, 103, 102],
        close=[102, 101, 104, 105, 106]
    )])
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- MÀN HÌNH 2: THÊM GIAO DỊCH ---
elif menu == "Thêm giao dịch":
    st.header("Thêm Giao Dịch Mới")

    with st.form("add_tx_form", border=True):
        symbol = st.text_input("Mã cổ phiếu (Symbol)", placeholder="Ví dụ: FPT")
        tx_type = st.radio("Loại giao dịch", ["BUY", "SELL"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Số lượng", min_value=1, step=100)
        with col2:
            price = st.number_input("Giá giao dịch", min_value=0.0, step=1000.0)

        notes = st.text_area("Ghi chú (Tùy chọn)")

        submitted = st.form_submit_button("Thêm Giao Dịch", type="primary")
        if submitted:
            st.success(f"Giao dịch {tx_type} mã {symbol} đã được thêm thành công!")

# --- MÀN HÌNH 3: CÀI ĐẶT CẢNH BÁO ---
elif menu == "Cài đặt cảnh báo":
    st.header("Quản Lý Cảnh Báo Giá (Telegram)")

    with st.expander("Tạo Cảnh Báo Mới", expanded=True):
        with st.form("add_alert_form", border=False):
            c1, c2 = st.columns(2)
            c1.text_input("Mã cổ phiếu", placeholder="FPT")
            c2.selectbox("Loại", ["TAKE_PROFIT", "STOP_LOSS"])

            c3, c4 = st.columns(2)
            c3.selectbox("Điều kiện", ["GREATER_THAN_OR_EQUAL (>=)", "LESS_THAN_OR_EQUAL (<=)"])
            c4.number_input("Giá mục tiêu", min_value=0, step=1000)

            if st.form_submit_button("Tạo Cảnh Báo", type="primary"):
                st.success("Đã thiết lập cảnh báo!")

    st.divider()

    st.subheader("Danh Sách Cảnh Báo Đang Hoạt Động")
    df_alerts = pd.DataFrame({
        "ID": [1, 2],
        "Mã": ["FPT", "VNM"],
        "Giá Mục Tiêu": [115000, 60000],
        "Điều Kiện": [">=", "<="],
        "Loại": ["TAKE_PROFIT", "STOP_LOSS"],
        "Tắt (Deactivate)": [False, False]
    })

    # Dùng data_editor để giả lập tính năng tick vào checkbox để tắt cảnh báo
    st.data_editor(df_alerts, use_container_width=True, hide_index=True)