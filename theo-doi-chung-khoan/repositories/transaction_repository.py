# Truy vấn/ghi bảng transactions, phục vụ add_transaction/get_portfolio_summary/build_candlestick_chart.
# Thiết kế: docs/functions/add_transaction.md, docs/functions/get_portfolio_summary.md,
# docs/functions/build_candlestick_chart.md. Schema: docs/requirements.md mục 4.


import logging
from datetime import datetime
from typing import Optional

from database import get_db_connection, Transaction

logger = logging.getLogger(__name__)


def get_holding_quantity(user_id: int, symbol: str) -> int:
    """
    Lấy số lượng cổ phiếu hiện đang sở hữu (tính cả BUY và SELL).
    
    Args:
        user_id: ID người dùng
        symbol: Mã cổ phiếu
    
    Returns:
        Số lượng hiện đang sở hữu (0 nếu không có)
    """
    conn = get_db_connection()
    try:
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
        return int(quantity)
    except Exception as e:
        logger.exception("Lỗi khi lấy số lượng sở hữu cho %s (user_id=%s)", symbol, user_id)
        raise


def add_transaction(
    user_id: int,
    symbol: str,
    transaction_type: str,
    quantity: int,
    price: float,
    notes: Optional[str] = None
) -> int:
    """
    Thêm một giao dịch (BUY/SELL) vào database.
    
    Args:
        user_id: ID người dùng
        symbol: Mã cổ phiếu (chuẩn hóa thành uppercase)
        transaction_type: 'BUY' hoặc 'SELL'
        quantity: Số lượng (phải > 0)
        price: Giá/cổ phiếu (phải > 0)
        notes: Ghi chú tùy chọn
    
    Returns:
        ID của giao dịch vừa thêm (cursor.lastrowid)
    
    Raises:
        ValueError: Nếu dữ liệu cơ bản không hợp lệ (từ model)
                   hoặc không đủ cổ phiếu để bán (DB-dependent)
    """
    # Step 1: Validate using Transaction model (basic rules)
    txn = Transaction(
        id=0,  # Temporary ID, will be assigned by database
        user_id=user_id,
        symbol=symbol,
        transaction_type=transaction_type,
        quantity=quantity,
        price=price,
        notes=notes or ""
    )  # Raises ValueError if basic validation fails
    
    # Step 2: Validate database-dependent rule (availability to sell)
    if txn.transaction_type == "SELL":
        current_quantity = get_holding_quantity(user_id, txn.symbol)
        if txn.quantity > current_quantity:
            raise ValueError(
                f"Không đủ cổ phiếu để bán. "
                f"Hiện đang sở hữu {current_quantity} {txn.symbol}."
            )

    # Step 3: Insert into database
    conn = get_db_connection()

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
                txn.user_id,
                txn.symbol,
                txn.transaction_type,
                txn.quantity,
                txn.price,
                txn.notes
            )
        )

        conn.commit()
        transaction_id = cursor.lastrowid
        logger.info("Giao dịch mới: user_id=%s, symbol=%s, type=%s, qty=%s, price=%s", 
                    user_id, txn.symbol, txn.transaction_type, quantity, price)
        return transaction_id

    except Exception as e:
        conn.rollback()
        logger.exception("Lỗi khi thêm giao dịch")
        raise


def get_transactions(user_id: int) -> list[Transaction]:
    """
    Lấy tất cả giao dịch của một người dùng (sắp xếp theo ngày giảm dần).
    
    Args:
        user_id: ID người dùng
    
    Returns:
        Danh sách Transaction objects
    """
    conn = get_db_connection()

    try:
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
        transactions = []
        
        for row in rows:
            txn_date = None
            if row[5]:
                txn_date = datetime.fromisoformat(row[5])
            
            transactions.append(Transaction(
                id=row[0],
                user_id=user_id,
                symbol=row[1],
                transaction_type=row[2],
                quantity=row[3],
                price=row[4],
                transaction_date=txn_date,
                notes=row[6]
            ))
        
        return transactions
    except Exception as e:
        logger.exception("Lỗi khi lấy giao dịch cho user_id=%s", user_id)
        raise


def get_portfolio(user_id: int) -> dict:
    """
    Tính toán danh mục hiện tại (từng mã cổ phiếu).
    
    Args:
        user_id: ID người dùng
    
    Returns:
        Dict: {symbol: {quantity, total_buy_value, total_buy_quantity}, ...}
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                symbol,
                transaction_type,
                quantity,
                price
            FROM transactions
            WHERE user_id = ?
            ORDER BY transaction_date ASC, id ASC
            """,
            (user_id,)
        )
        
        rows = cursor.fetchall()
        portfolio = {}
        
        for symbol, transaction_type, quantity, price in rows:
            if symbol not in portfolio:
                portfolio[symbol] = {
                    "quantity": 0,
                    "total_buy_value": 0.0,
                    "total_buy_quantity": 0
                }
            
            item = portfolio[symbol]
            
            if transaction_type == "BUY":
                item["quantity"] += quantity
                item["total_buy_value"] += quantity * price
                item["total_buy_quantity"] += quantity
            elif transaction_type == "SELL":
                item["quantity"] -= quantity
        
        return portfolio
    except Exception as e:
        logger.exception("Lỗi khi tính toán danh mục cho user_id=%s", user_id)
        raise