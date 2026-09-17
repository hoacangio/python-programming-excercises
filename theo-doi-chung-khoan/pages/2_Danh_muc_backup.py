import streamlit as st
import pandas as pd

from repositories.transaction_repository import (
    add_transaction,
    get_transactions,
    get_holding_quantity
)

from services.portfolio_service import (
    get_portfolio_summary,
    get_current_market_price
)


st.set_page_config(
    page_title="Danh mục đầu tư",
    page_icon="💼",
    layout="wide"
)

USER_ID = 1


st.title("💼 Danh mục đầu tư")


# =====================================================
# BUY / SELL
# =====================================================

st.subheader("Thực hiện giao dịch")

col1, col2 = st.columns(2)

with col1:

    symbol = st.selectbox(
        "Mã cổ phiếu",
        [
            "FPT.VN",
            "VCB.VN",
            "HPG.VN",
            "MWG.VN",
            "VNM.VN"
        ]
    )

    transaction_type = st.radio(
        "Loại giao dịch",
        ["BUY", "SELL"],
        horizontal=True
    )


with col2:

    current_price = get_current_market_price(symbol)

    st.metric(
        "Giá thị trường gần nhất",
        f"{current_price:,.0f} VNĐ"
    )

    holding = get_holding_quantity(
        USER_ID,
        symbol
    )

    st.metric(
        "Đang sở hữu",
        f"{holding:,} CP"
    )


quantity = st.number_input(
    "Số lượng",
    min_value=1,
    step=1
)


price = st.number_input(
    "Giá giao dịch",
    min_value=1.0,
    value=current_price if current_price > 0 else 1000.0,
    step=100.0
)


total_value = quantity * price

st.info(
    f"💰 Giá trị giao dịch: "
    f"{total_value:,.0f} VNĐ"
)


notes = st.text_input(
    "Ghi chú",
    placeholder="Ví dụ: Mua tích lũy..."
)


if st.button(
    "💾 Lưu giao dịch",
    type="primary",
    use_container_width=True
):

    try:

        transaction_id = add_transaction(
            USER_ID,
            symbol,
            transaction_type,
            quantity,
            price,
            notes
        )

        st.success(
            f"Đã lưu giao dịch #{transaction_id}"
        )

        st.rerun()

    except ValueError as e:

        st.error(str(e))

    except Exception as e:

        st.error(
            f"Không thể lưu giao dịch: {e}"
        )


# =====================================================
# PORTFOLIO
# =====================================================

st.divider()

st.subheader("📊 Danh mục hiện tại")

portfolio = get_portfolio_summary(USER_ID)


if portfolio.empty:

    st.info(
        "Bạn chưa có cổ phiếu trong danh mục."
    )

else:

    total_cost = portfolio["cost_value"].sum()

    total_market = portfolio["market_value"].sum()

    total_unrealized = (
        portfolio["unrealized_profit"].sum()
    )

    total_realized = (
        portfolio["realized_profit"].sum()
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tổng vốn",
        f"{total_cost:,.0f} ₫"
    )

    c2.metric(
        "Giá trị hiện tại",
        f"{total_market:,.0f} ₫"
    )

    c3.metric(
        "Lãi/lỗ chưa thực hiện",
        f"{total_unrealized:,.0f} ₫"
    )

    c4.metric(
        "Lãi đã thực hiện",
        f"{total_realized:,.0f} ₫"
    )

    display_df = portfolio.copy()

    display_df = display_df.rename(
        columns={
            "symbol": "Mã CP",
            "quantity": "Số lượng",
            "average_price": "Giá vốn",
            "current_price": "Giá hiện tại",
            "cost_value": "Tổng vốn",
            "market_value": "Giá trị hiện tại",
            "unrealized_profit": "Lãi/lỗ",
            "unrealized_percent": "Lãi/lỗ %",
            "realized_profit": "Lãi đã thực hiện"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# TRANSACTION HISTORY
# =====================================================

st.divider()

st.subheader("📜 Lịch sử giao dịch")

transactions = get_transactions(USER_ID)

if transactions:

    history = pd.DataFrame(
        transactions,
        columns=[
            "ID",
            "Mã CP",
            "Loại",
            "Số lượng",
            "Giá",
            "Ngày giao dịch",
            "Ghi chú"
        ]
    )

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("Chưa có giao dịch.")