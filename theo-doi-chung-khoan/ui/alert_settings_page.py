# Màn hình "Cài đặt cảnh báo": form tạo cảnh báo và danh sách cảnh báo đang hoạt động.
# Gọi bởi ui/main.py qua display_alert_settings_page()

import streamlit as st
import pandas as pd

from services.alert_service import (
    add_price_alert,
    list_price_alerts,
    deactivate_price_alert
)
from services.dashboard_service import get_available_symbols

# Giả sử user_id = 1 (cần thay thế bằng session state thực tế)
USER_ID = 1


def display_alert_settings_page():
    """Render alert settings page: add alerts and manage existing ones."""
    st.subheader("🔔 Cài đặt cảnh báo giá")
    
    # Section 1: Add new alert
    render_add_alert_form()
    
    st.divider()
    
    # Section 2: List alerts
    render_alerts_list()


def render_add_alert_form():
    """Render form để thêm cảnh báo mới."""
    try:
        symbols = get_available_symbols()
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách mã cổ phiếu: {e}")
        return
    
    if not symbols:
        st.warning("Không có mã cổ phiếu nào. Vui lòng kiểm tra dữ liệu.")
        return
    
    st.subheader("➕ Thêm cảnh báo mới")
    
    with st.form("alert_form"):
        symbol = st.selectbox("Mã cổ phiếu", symbols)
        
        target_price = st.number_input(
            "Giá mục tiêu (VND)",
            min_value=0.01,
            value=100.0,
            step=0.01
        )
        
        condition = st.radio(
            "Điều kiện",
            ["Giá >= Mục tiêu", "Giá <= Mục tiêu"],
            horizontal=True,
            label_visibility="visible"
        )
        condition_value = "GREATER_THAN_OR_EQUAL" if condition.startswith("Giá >=") else "LESS_THAN_OR_EQUAL"
        
        alert_type = st.radio(
            "Loại cảnh báo",
            ["Chốt lời (Take-profit)", "Cắt lỗ (Stop-loss)"],
            horizontal=True
        )
        alert_type_value = "TAKE_PROFIT" if "Chốt lời" in alert_type else "STOP_LOSS"
        
        submitted = st.form_submit_button("Thêm cảnh báo", use_container_width=True)
        
        if submitted:
            try:
                alert_id = add_price_alert(
                    user_id=USER_ID,
                    symbol=symbol,
                    target_price=float(target_price),
                    condition=condition_value,
                    alert_type=alert_type_value
                )
                st.success(
                    f"✅ Cảnh báo thêm thành công! (ID: {alert_id})\n"
                    f"Mã: {symbol} | Giá mục tiêu: {target_price:,.0f} VND | "
                    f"Loại: {alert_type_value}"
                )
                st.rerun()
            except ValueError as e:
                st.error(f"❌ Dữ liệu không hợp lệ: {e}")
            except Exception as e:
                st.error(f"❌ Lỗi khi thêm cảnh báo: {e}")


def render_alerts_list():
    """Render danh sách các cảnh báo hiện tại."""
    st.subheader("📋 Danh sách cảnh báo")
    
    try:
        # Lấy tất cả cảnh báo (active và inactive)
        alerts_df = list_price_alerts(USER_ID, active_only=False)
        
        if alerts_df.empty:
            st.info("Bạn chưa có cảnh báo nào.")
            return
        
        # Format DataFrame
        display_df = alerts_df[[
            "id", "symbol", "target_price", "condition", "alert_type", "is_active"
        ]].copy()
        
        display_df["condition_text"] = display_df["condition"].apply(
            lambda x: "Giá >= mục tiêu" if x == "GREATER_THAN_OR_EQUAL" else "Giá <= mục tiêu"
        )
        
        display_df["alert_type_text"] = display_df["alert_type"].apply(
            lambda x: "Chốt lời" if x == "TAKE_PROFIT" else "Cắt lỗ"
        )
        
        display_df["status"] = display_df["is_active"].apply(
            lambda x: "✅ Đang hoạt động" if x else "❌ Đã vô hiệu"
        )
        
        display_df = display_df[[
            "id", "symbol", "target_price", "condition_text",
            "alert_type_text", "status"
        ]].round(2)
        
        display_df.columns = [
            "ID", "Mã CP", "Giá mục tiêu", "Điều kiện", "Loại", "Trạng thái"
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Nút vô hiệu hóa cảnh báo
        st.subheader("Quản lý cảnh báo")
        
        active_alerts = alerts_df[alerts_df["is_active"]].copy()
        
        if not active_alerts.empty:
            alert_to_deactivate = st.selectbox(
                "Chọn cảnh báo để vô hiệu hóa",
                options=active_alerts["id"].tolist(),
                format_func=lambda x: f"ID {x}: {active_alerts[active_alerts['id'] == x]['symbol'].values[0]}"
            )
            
            if st.button("Vô hiệu hóa cảnh báo", use_container_width=True):
                try:
                    deactivate_price_alert(alert_to_deactivate)
                    st.success(f"✅ Cảnh báo {alert_to_deactivate} đã vô hiệu hóa")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
        else:
            st.info("Không có cảnh báo đang hoạt động để vô hiệu hóa")
    
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách cảnh báo: {e}")


