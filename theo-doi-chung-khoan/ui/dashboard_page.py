# Màn hình "Xem danh mục": metrics, bảng danh mục, biểu đồ nến.
# Gọi bởi ui/main.py qua display_dashboard_page()

import streamlit as st
import pandas as pd

from services.portfolio_service import get_portfolio_summary
from services.chart_service import build_candlestick_chart
from services.dashboard_service import get_market_data_for_symbol

# Giả sử user_id = 1 (cần thay thế bằng session state thực tế)
USER_ID = 1


def display_dashboard_page():
    """Render dashboard page: portfolio metrics, holdings table, candlestick chart."""
    st.subheader("📊 Danh mục đầu tư")
    
    try:
        # Lấy tóm tắt danh mục
        portfolio_df = get_portfolio_summary(USER_ID)
        
        if portfolio_df.empty:
            st.info("Bạn chưa có cổ phiếu nào trong danh mục. Hãy thêm giao dịch đầu tiên!")
            return
        
        # Hiển thị metrics tổng quan
        st.subheader("Tổng quan danh mục")
        
        total_cost = portfolio_df["cost_value"].sum()
        total_market_value = portfolio_df["market_value"].sum()
        total_unrealized_profit = portfolio_df["unrealized_profit"].sum()
        total_realized_profit = portfolio_df["realized_profit"].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Tổng vốn",
                f"{total_cost:,.0f} VND"
            )
        
        with col2:
            st.metric(
                "Giá trị thị trường",
                f"{total_market_value:,.0f} VND",
                f"{total_unrealized_profit:,.0f}"
            )
        
        with col3:
            if total_cost > 0:
                pct = (total_unrealized_profit / total_cost) * 100
            else:
                pct = 0
            st.metric(
                "Lợi nhuận %",
                f"{pct:.2f}%"
            )
        
        with col4:
            st.metric(
                "Lợi nhuận đã nhận",
                f"{total_realized_profit:,.0f} VND"
            )
        
        # Hiển thị bảng danh mục
        st.subheader("Chi tiết danh mục")
        
        # Format DataFrame để hiển thị
        display_df = portfolio_df.copy()
        display_df = display_df[[
            "symbol", "quantity", "average_price", "current_price",
            "cost_value", "market_value", "unrealized_profit", "unrealized_percent"
        ]].round(2)
        
        display_df.columns = [
            "Mã CP", "Số lượng", "Giá vốn TB", "Giá hiện tại",
            "Tổng vốn", "Giá trị TT", "Lợi nhuận", "LN %"
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Hiển thị biểu đồ cho mã được chọn
        st.subheader("Biểu đồ nến")
        
        symbols = portfolio_df["symbol"].tolist()
        selected_symbol = st.selectbox("Chọn mã cổ phiếu để xem biểu đồ", symbols)
        
        if selected_symbol:
            try:
                market_df = get_market_data_for_symbol(selected_symbol)
                if not market_df.empty:
                    fig = build_candlestick_chart(market_df, selected_symbol)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Không có dữ liệu cho {selected_symbol}")
            except Exception as e:
                st.error(f"Lỗi khi lấy dữ liệu: {e}")
    
    except Exception as e:
        st.error(f"Lỗi khi hiển thị danh mục: {e}")


