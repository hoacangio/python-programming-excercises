# Truy vấn/ghi bảng transactions, phục vụ add_transaction/get_portfolio_summary/build_candlestick_chart.
# Thiết kế: docs/functions/add_transaction.md, docs/functions/get_portfolio_summary.md,
# docs/functions/build_candlestick_chart.md. Schema: docs/requirements.md mục 4.


import sqlite3

DB_PATH = "data/portfolio.db"


def get_holding_quantity(user_id, symbol):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COALESCE(
            SUM(
                CASE
                    WHEN transaction_type = 'BUY' THEN quantity
                    WHEN transaction_type = 'SELL' THEN -quantity
                    ELSE 0
                END
            ),
            0
        )
        FROM transactions
        WHERE user_id = ?
          AND symbol = ?
        """,
        (user_id, symbol.upper())
    )

    quantity = cursor.fetchone()[0]

    conn.close()

    return int(quantity)


def add_transaction(
    user_id,
    symbol,
    transaction_type,
    quantity,
    price,
    notes=""
):
    symbol = symbol.upper()
    transaction_type = transaction_type.upper()

    if transaction_type not in ("BUY", "SELL"):
        raise ValueError("Loại giao dịch phải là BUY hoặc SELL.")

    if quantity <= 0:
        raise ValueError("Số lượng phải lớn hơn 0.")

    if price <= 0:
        raise ValueError("Giá giao dịch phải lớn hơn 0.")

    if transaction_type == "SELL":

        current_quantity = get_holding_quantity(
            user_id,
            symbol
        )

        if quantity > current_quantity:
            raise ValueError(
                f"Không đủ cổ phiếu để bán. "
                f"Hiện đang sở hữu {current_quantity} {symbol}."
            )

    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute(
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
                user_id,
                symbol,
                transaction_type,
                int(quantity),
                float(price),
                notes
            )
        )

        conn.commit()

        return cursor.lastrowid

    finally:
        conn.close()


def get_transactions(user_id):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            symbol,
            transaction_type,
            quantity,
            price,
            transaction_date,
            notes
        FROM transactions
        WHERE user_id = ?
        ORDER BY transaction_date DESC, id DESC
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows