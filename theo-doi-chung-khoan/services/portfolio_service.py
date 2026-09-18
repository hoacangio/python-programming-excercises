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


def get_portfolio_summary(user_id: int) -> pd.DataFrame:
    """
    Lấy tóm tắt danh mục hiện tại của người dùng.
    
    Tính toán từ lịch sử giao dịch (transactions) và giá thị trường hiện tại.
    Với mỗi mã cổ phiếu đang sở hữu (quantity > 0), tính:
    - Giá vốn trung bình
    - Giá thị trường hiện tại
    - Giá trị thị trường
    - Lợi nhuận chưa nhận
    - Tỷ lệ lợi nhuận (%)
    - Lợi nhuận đã nhận
    
    Args:
        user_id: ID người dùng
    
    Returns:
        DataFrame với cột:
        - symbol: Mã cổ phiếu
        - quantity: Số lượng sở hữu
        - average_price: Giá vốn trung bình
        - current_price: Giá đóng cửa gần nhất
        - cost_value: Tổng giá vốn
        - market_value: Giá trị thị trường hiện tại (quantity * current_price)
        - unrealized_profit: Lợi nhuận chưa nhận (market_value - cost_value)
        - unrealized_percent: Tỷ lệ lợi nhuận chưa nhận (%)
        - realized_profit: Lợi nhuận đã nhận từ SELL
    """
    # Lấy portfolio từ repository (chỉ tính từ transactions)
    portfolio_dict = transaction_repository.get_portfolio(user_id)
    
    if not portfolio_dict:
        # Trả về DataFrame rỗng theo schema
        return pd.DataFrame(columns=[
            "symbol", "quantity", "average_price", "current_price",
            "cost_value", "market_value", "unrealized_profit",
            "unrealized_percent", "realized_profit"
        ])
    
    result = []
    
    for symbol, item in portfolio_dict.items():
        quantity = item["quantity"]
        total_buy_value = item["total_buy_value"]
        total_buy_quantity = item["total_buy_quantity"]
        
        # Bỏ qua nếu không sở hữu
        if quantity <= 0:
            continue
        
        # Tính giá vốn trung bình
        if total_buy_quantity > 0:
            average_price = total_buy_value / total_buy_quantity
        else:
            average_price = 0.0
        
        # Lấy giá thị trường hiện tại từ repository
        try:
            latest_df = market_repository.get_latest_price(symbol)
            if latest_df.empty:
                current_price = 0.0
            else:
                current_price = float(latest_df.iloc[0]["close"])
        except Exception as e:
            logger.warning("Không thể lấy giá hiện tại cho %s: %s", symbol, e)
            current_price = 0.0
        
        # Tính giá trị thị trường
        market_value = quantity * current_price
        
        # Tính lợi nhuận chưa nhận
        unrealized_profit = market_value - total_buy_value
        
        # Tính tỷ lệ lợi nhuận
        if total_buy_value > 0:
            unrealized_percent = (unrealized_profit / total_buy_value) * 100
        else:
            unrealized_percent = 0.0
        
        # Lợi nhuận đã nhận (từ SELL)
        realized_profit = item.get("realized_profit", 0.0)
        
        result.append({
            "symbol": symbol,
            "quantity": quantity,
            "average_price": average_price,
            "current_price": current_price,
            "cost_value": total_buy_value,
            "market_value": market_value,
            "unrealized_profit": unrealized_profit,
            "unrealized_percent": unrealized_percent,
            "realized_profit": realized_profit
        })
    
    if not result:
        return pd.DataFrame(columns=[
            "symbol", "quantity", "average_price", "current_price",
            "cost_value", "market_value", "unrealized_profit",
            "unrealized_percent", "realized_profit"
        ])
    
    df = pd.DataFrame(result)
    logger.info("Danh mục tóm tắt cho user_id=%s: %d mã", user_id, len(df))
    return df
