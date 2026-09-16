import streamlit as st
import pandas as pd
import plotly.express as px

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

    st.info("Bạn chưa có cổ phiếu trong danh mục.")

else:

    # =====================================================
    # TÍNH TOÁN TỔNG QUAN DANH MỤC
    # =====================================================

    total_cost = portfolio["cost_value"].sum()
    total_market = portfolio["market_value"].sum()
    total_unrealized = portfolio["unrealized_profit"].sum()
    total_realized = portfolio["realized_profit"].sum()

    # Tổng lãi/lỗ
    total_profit = total_unrealized + total_realized

    # % lãi/lỗ chưa thực hiện
    total_profit_percent = (
        total_unrealized / total_cost * 100
        if total_cost > 0
        else 0
    )

    # Tỷ trọng từng cổ phiếu
    portfolio["weight"] = (
        portfolio["market_value"] / total_market * 100
        if total_market > 0
        else 0
    )

    # =====================================================
    # METRIC
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "💰 Tổng vốn",
        f"{total_cost:,.0f} ₫"
    )

    c2.metric(
        "📊 Giá trị hiện tại",
        f"{total_market:,.0f} ₫"
    )

    c3.metric(
        "📈 Lãi/lỗ chưa thực hiện",
        f"{total_unrealized:,.0f} ₫",
        delta=f"{total_profit_percent:.2f}%"
    )

    c4.metric(
        "💵 Lãi đã thực hiện",
        f"{total_realized:,.0f} ₫"
    )

    c5.metric(
        "🏆 Tổng lãi/lỗ",
        f"{total_profit:,.0f} ₫"
    )

    # =====================================================
    # BIỂU ĐỒ
    # =====================================================

    st.subheader("📊 Phân tích danh mục")

    chart_col1, chart_col2 = st.columns(2)

    # Biểu đồ tỷ trọng
    with chart_col1:

        st.markdown("#### 🥧 Tỷ trọng danh mục")

        fig_allocation = px.pie(
            portfolio,
            names="symbol",
            values="market_value",
            hole=0.45
        )

        fig_allocation.update_traces(
            textposition="inside",
            textinfo="label+percent"
        )

        st.plotly_chart(
            fig_allocation,
            use_container_width=True
        )

    # Biểu đồ giá trị
    with chart_col2:

        st.markdown("#### 📊 Giá trị từng cổ phiếu")

        fig_value = px.bar(
            portfolio,
            x="symbol",
            y="market_value",
            text="market_value",
            labels={
                "symbol": "Mã cổ phiếu",
                "market_value": "Giá trị hiện tại (VNĐ)"
            }
        )

        fig_value.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside"
        )

        fig_value.update_layout(
            xaxis_title="Mã cổ phiếu",
            yaxis_title="VNĐ"
        )

        st.plotly_chart(
            fig_value,
            use_container_width=True
        )

    # =====================================================
    # BẢNG DANH MỤC
    # =====================================================

    st.subheader("📋 Chi tiết danh mục")

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
            "realized_profit": "Lãi đã thực hiện",
            "weight": "Tỷ trọng %"
        }
    )

    display_df["Giá vốn"] = display_df["Giá vốn"].round(0)
    display_df["Giá hiện tại"] = display_df["Giá hiện tại"].round(0)
    display_df["Tổng vốn"] = display_df["Tổng vốn"].round(0)
    display_df["Giá trị hiện tại"] = display_df["Giá trị hiện tại"].round(0)
    display_df["Lãi/lỗ"] = display_df["Lãi/lỗ"].round(0)
    display_df["Lãi/lỗ %"] = display_df["Lãi/lỗ %"].round(2)
    display_df["Lãi đã thực hiện"] = display_df["Lãi đã thực hiện"].round(0)
    display_df["Tỷ trọng %"] = display_df["Tỷ trọng %"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )