# add_transaction, get_portfolio_summary.
# Thiết kế: docs/functions/add_transaction.md, docs/functions/get_portfolio_summary.md.

import logging
from typing import Optional

import pandas as pd

from repositories import transaction_repository, market_repository

logger = logging.getLogger(__name__)


def add_transaction(
    user_id: int,
    symbol: str,
    transaction_type: str,
    quantity: int,
    price: float,
    notes: Optional[str] = None
) -> int:
    """
    Thêm một giao dịch (BUY/SELL) cho người dùng.
    
    Validation được xử lý bởi Transaction model trong repository layer.
    Repository cũng kiểm tra SELL không vượt quá số lượng sở hữu.
    
    Args:
        user_id: ID người dùng
        symbol: Mã cổ phiếu
        transaction_type: 'BUY' hoặc 'SELL'
        quantity: Số lượng (phải > 0)
        price: Giá/cổ phiếu (phải > 0)
        notes: Ghi chú tùy chọn
    
    Returns:
        ID của giao dịch vừa thêm
    
    Raises:
        ValueError: Nếu dữ liệu không hợp lệ (từ Transaction model hoặc DB-dependent)
    """
    try:
        transaction_id = transaction_repository.add_transaction(
            user_id=user_id,
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=int(quantity),
            price=float(price),
            notes=notes or ""
        )
        logger.info(
            "Giao dịch thêm thành công: user_id=%s, symbol=%s, type=%s, qty=%s",
            user_id, symbol, transaction_type, quantity
        )
        return transaction_id
    except ValueError as e:
        logger.warning("Dữ liệu giao dịch không hợp lệ: %s", e)
        raise
    except Exception as e:
        logger.exception("Lỗi khi thêm giao dịch")
        raise


_SUMMARY_COLUMNS = [
    "symbol", "quantity", "average_price", "current_price",
    "cost_value", "market_value", "unrealized_profit",
    "unrealized_percent", "realized_profit"
]


def get_portfolio_summary(user_id: int) -> pd.DataFrame:
    """
    Lấy tóm tắt danh mục hiện tại của người dùng.
    
    Tính toán từ lịch sử giao dịch (transactions) theo phương pháp giá vốn
    bình quân gia quyền và giá thị trường đã lưu. Với mỗi mã đang sở hữu
    (quantity > 0), tính:
    - Giá vốn bình quân và vốn của phần đang giữ
    - Giá thị trường hiện tại
    - Giá trị thị trường
    - Lợi nhuận chưa nhận và tỷ lệ (%)
    - Lợi nhuận đã nhận từ các lệnh SELL
    
    Nếu chưa có giá của một mã, current_price, market_value,
    unrealized_profit và unrealized_percent là NaN (chưa định giá),
    không gán 0 để tránh hiển thị lỗ giả.
    
    Args:
        user_id: ID người dùng
    
    Returns:
        DataFrame với cột:
        - symbol: Mã cổ phiếu
        - quantity: Số lượng sở hữu
        - average_price: Giá vốn bình quân
        - current_price: Giá đóng cửa gần nhất (NaN nếu chưa có giá)
        - cost_value: Vốn của phần đang giữ (quantity * average_price)
        - market_value: Giá trị thị trường hiện tại (quantity * current_price)
        - unrealized_profit: Lợi nhuận chưa nhận (market_value - cost_value)
        - unrealized_percent: Tỷ lệ lợi nhuận chưa nhận (%)
        - realized_profit: Lợi nhuận đã nhận từ SELL
    """
    portfolio_dict = transaction_repository.get_portfolio(user_id)
    
    result = []
    
    for symbol, item in portfolio_dict.items():
        quantity = item["quantity"]
        
        # Bỏ qua nếu không sở hữu
        if quantity <= 0:
            continue
        
        average_price = item["average_price"]
        cost_value = item["cost_value"]
        
        # Lấy giá thị trường hiện tại từ repository
        current_price = float("nan")
        try:
            latest_df = market_repository.get_latest_price(symbol)
            if not latest_df.empty:
                current_price = float(latest_df.iloc[0]["close"])
        except Exception as e:
            logger.warning("Không thể lấy giá hiện tại cho %s: %s", symbol, e)
        
        market_value = quantity * current_price
        unrealized_profit = market_value - cost_value
        unrealized_percent = (
            unrealized_profit / cost_value * 100 if cost_value > 0 else float("nan")
        )
        
        result.append({
            "symbol": symbol,
            "quantity": quantity,
            "average_price": average_price,
            "current_price": current_price,
            "cost_value": cost_value,
            "market_value": market_value,
            "unrealized_profit": unrealized_profit,
            "unrealized_percent": unrealized_percent,
            "realized_profit": item["realized_profit"]
        })
    
    if not result:
        return pd.DataFrame(columns=_SUMMARY_COLUMNS)
    
    df = pd.DataFrame(result, columns=_SUMMARY_COLUMNS)
    logger.info("Danh mục tóm tắt cho user_id=%s: %d mã", user_id, len(df))
    return df


def get_total_realized_profit(user_id: int) -> float:
    """
    Tổng lợi nhuận đã nhận của người dùng, gồm cả các mã đã bán hết
    (không còn xuất hiện trong get_portfolio_summary).
    
    Args:
        user_id: ID người dùng
    
    Returns:
        Tổng lợi nhuận đã nhận (VND)
    """
    portfolio_dict = transaction_repository.get_portfolio(user_id)
    return float(sum(item["realized_profit"] for item in portfolio_dict.values()))
