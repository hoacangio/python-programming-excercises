# Main UI coordinator: Navigation and page delegation.
# This module handles all UI navigation and coordinates between pages.

import streamlit as st

from ui.dashboard_page import display_dashboard_page
from ui.add_transaction_page import display_add_transaction_page
from ui.alert_settings_page import display_alert_settings_page


def render_sidebar_navigation() -> str:
    """
    Render sidebar navigation menu.
    
    Returns:
        Selected page name: 'dashboard', 'add_transaction', 'alert_settings'
    """
    st.sidebar.title("📊 Điều hướng")
    
    page = st.sidebar.radio(
        "Chọn trang",
        ["📈 Dashboard", "➕ Thêm giao dịch", "🔔 Cảnh báo"],
        label_visibility="collapsed"
    )
    
    # Map display names to page identifiers
    page_map = {
        "📈 Dashboard": "dashboard",
        "➕ Thêm giao dịch": "add_transaction",
        "🔔 Cảnh báo": "alert_settings"
    }
    
    return page_map.get(page, "dashboard")


def run():
    """
    Main UI entry point.
    
    Handles page routing and displays the selected page.
    """
    # Configure page
    st.set_page_config(
        page_title="Theo dõi chứng khoán",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Hệ thống theo dõi chứng khoán")
    st.caption("Dữ liệu được đọc từ SQLite - portfolio.db")
    
    # Get selected page from navigation
    selected_page = render_sidebar_navigation()
    
    # Route to appropriate page
    if selected_page == "dashboard":
        display_dashboard_page()
    elif selected_page == "add_transaction":
        display_add_transaction_page()
    elif selected_page == "alert_settings":
        display_alert_settings_page()
    else:
        st.error("Trang không tìm thấy")
