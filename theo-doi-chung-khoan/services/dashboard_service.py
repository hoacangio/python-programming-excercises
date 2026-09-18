# Dashboard service: các hàm phục vụ UI (app.py, pages/*.py).
# Tầng Service - không import Streamlit, chỉ orchestrate repositories và các service khác.

import logging
from typing import Optional

import pandas as pd

from repositories import market_repository, transaction_repository

logger = logging.getLogger(__name__)


def get_available_symbols() -> list[str]:
    """
    Lấy danh sách tất cả các mã cổ phiếu có dữ liệu giá.
    
    Dùng bởi UI để hiển thị dropdown chọn mã cổ phiếu.
    
    Returns:
        Danh sách mã cổ phiếu (list[str])
    """
    try:
        symbols = market_repository.get_symbols()
        logger.info("Lấy %d mã cổ phiếu", len(symbols))
        return symbols
    except Exception as e:
        logger.exception("Lỗi khi lấy danh sách mã cổ phiếu")
        raise


def get_market_data_for_symbol(symbol: str) -> pd.DataFrame:
    """
    Lấy dữ liệu giá lịch sử (OHLCV) của một mã cổ phiếu.
    
    Dùng bởi UI để vẽ biểu đồ.
    
    Args:
        symbol: Mã cổ phiếu
    
    Returns:
        DataFrame với cột: trade_date, open, high, low, close, volume
    """
    try:
        df = market_repository.get_market_data(symbol)
        logger.info("Lấy dữ liệu giá cho %s: %d hàng", symbol, len(df))
        return df
    except Exception as e:
        logger.exception("Lỗi khi lấy dữ liệu giá cho %s", symbol)
        raise


def get_latest_price_for_symbol(symbol: str) -> pd.DataFrame:
    """
    Lấy giá gần nhất của một mã cổ phiếu (1 dòng).
    
    Dùng bởi UI để hiển thị thông tin giá mới nhất (close, open, high, volume).
    
    Args:
        symbol: Mã cổ phiếu
    
    Returns:
        DataFrame với 1 dòng: symbol, trade_date, open, high, low, close, volume
    """
    try:
        df = market_repository.get_latest_price(symbol)
        if not df.empty:
            logger.info("Lấy giá gần nhất cho %s: %s", symbol, df.iloc[0]["close"])
        else:
            logger.warning("Không tìm thấy dữ liệu giá cho %s", symbol)
        return df
    except Exception as e:
        logger.exception("Lỗi khi lấy giá gần nhất cho %s", symbol)
        raise
