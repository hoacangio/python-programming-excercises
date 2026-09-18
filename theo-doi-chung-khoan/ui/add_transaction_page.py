# Màn hình "Thêm giao dịch": form BUY/SELL gọi add_transaction.
# Gọi bởi ui/main.py qua display_add_transaction_page()

import streamlit as st

from services.portfolio_service import add_transaction
from services.dashboard_service import get_available_symbols

# Giả sử user_id = 1 (cần thay thế bằng session state thực tế)
USER_ID = 1


def display_add_transaction_page():
    """Render add transaction form page."""
    st.subheader("➕ Thêm giao dịch")
    st.write("Nhập thông tin giao dịch mua/bán cổ phiếu")
    
    try:
        symbols = get_available_symbols()
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách mã cổ phiếu: {e}")
        return
    
    if not symbols:
        st.warning("Không có mã cổ phiếu nào. Vui lòng kiểm tra dữ liệu.")
        return
    
    with st.form("transaction_form"):
        st.subheader("Thông tin giao dịch")
        
        # Chọn loại giao dịch
        transaction_type = st.radio(
            "Loại giao dịch",
            ["BUY", "SELL"],
            horizontal=True
        )
        
        # Chọn mã cổ phiếu
        symbol = st.selectbox(
            "Mã cổ phiếu",
            symbols
        )
        
        # Số lượng
        quantity = st.number_input(
            "Số lượng",
            min_value=1,
            value=10,
            step=1
        )
        
        # Giá
        price = st.number_input(
            "Giá (VND)",
            min_value=0.01,
            value=100.0,
            step=0.01
        )
        
        # Ghi chú (tùy chọn)
        notes = st.text_input(
            "Ghi chú (tùy chọn)",
            ""
        )
        
        # Nút submit
        submitted = st.form_submit_button(
            f"Thêm giao dịch {transaction_type}",
            use_container_width=True
        )
        
        if submitted:
            try:
                # Kiểm tra input
                if not symbol:
                    st.error("Vui lòng chọn mã cổ phiếu")
                    return
                
                if quantity <= 0:
                    st.error("Số lượng phải lớn hơn 0")
                    return
                
                if price <= 0:
                    st.error("Giá phải lớn hơn 0")
                    return
                
                # Gọi service
                transaction_id = add_transaction(
                    user_id=USER_ID,
                    symbol=symbol,
                    transaction_type=transaction_type,
                    quantity=int(quantity),
                    price=float(price),
                    notes=notes
                )
                
                # Hiển thị thành công
                st.success(
                    f"✅ Giao dịch thêm thành công! (ID: {transaction_id})\n"
                    f"Loại: {transaction_type} | Mã: {symbol} | "
                    f"Số lượng: {quantity} | Giá: {price:,.0f} VND"
                )
                
                # Reload page để cập nhật danh mục
                st.rerun()
            
            except ValueError as e:
                st.error(f"❌ Dữ liệu không hợp lệ: {e}")
            except Exception as e:
                st.error(f"❌ Lỗi khi thêm giao dịch: {e}")


