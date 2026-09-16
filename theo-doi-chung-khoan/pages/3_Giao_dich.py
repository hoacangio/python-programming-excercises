import streamlit as st
import sqlite3
from pathlib import Path
from repositories.market_repository import get_symbols


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "portfolio.db"


st.title("💰 Giao dịch cổ phiếu")

symbols = get_symbols()

symbol = st.selectbox(
    "Mã cổ phiếu",
    symbols
)

transaction_type = st.radio(
    "Loại giao dịch",
    ["BUY", "SELL"]
)

quantity = st.number_input(
    "Số lượng",
    min_value=1,
    step=1
)

price = st.number_input(
    "Giá giao dịch",
    min_value=0.0,
    step=100.0
)

notes = st.text_input(
    "Ghi chú"
)

if st.button("Lưu giao dịch"):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO transactions
        (
            user_id,
            symbol,
            transaction_type,
            quantity,
            price,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            symbol,
            transaction_type,
            quantity,
            price,
            notes
        )
    )

    conn.commit()
    conn.close()

    st.success("Đã lưu giao dịch!")