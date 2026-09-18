import logging
import sqlite3
from pathlib import Path

import pandas as pd

from database import get_db_connection

# LOGGING

logger = logging.getLogger(__name__)

# Đường dẫn đến database
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "portfolio.db"


def get_connection() -> sqlite3.Connection:
    """Kết nối SQLite database (sử dụng centralized connection)."""
    return get_db_connection()


def get_symbols() -> list[str]:
    """
    Lấy danh sách mã cổ phiếu từ bảng market_prices.
    
    Returns:
        Danh sách các mã cổ phiếu (list[str])
    """
    conn = get_connection()
    try:
        query = """
            SELECT DISTINCT symbol
            FROM market_prices
            ORDER BY symbol
        """
        df = pd.read_sql_query(query, conn)
        return df["symbol"].tolist() if not df.empty else []
    finally:
        conn.close()


def get_market_data(symbol: str) -> pd.DataFrame:
    """
    Lấy toàn bộ dữ liệu giá (OHLCV) của một mã cổ phiếu.
    
    Args:
        symbol: Mã cổ phiếu (chuẩn hóa thành uppercase)
    
    Returns:
        DataFrame với cột: trade_date, open, high, low, close, volume
    """
    conn = get_connection()
    try:
        query = """
            SELECT
                trade_date,
                open,
                high,
                low,
                close,
                volume
            FROM market_prices
            WHERE symbol = ?
            ORDER BY trade_date ASC
        """
        df = pd.read_sql_query(
            query,
            conn,
            params=(symbol.upper() if isinstance(symbol, str) else symbol,)
        )
        if not df.empty:
            df["trade_date"] = pd.to_datetime(df["trade_date"])
        return df
    finally:
        conn.close()


def get_latest_price(symbol: str) -> pd.DataFrame:
    """
    Lấy giá gần nhất (1 dòng) của một mã cổ phiếu.
    
    Args:
        symbol: Mã cổ phiếu
    
    Returns:
        DataFrame với 1 dòng chứa: symbol, trade_date, open, high, low, close, volume
    """
    conn = get_connection()
    try:
        query = """
            SELECT
                symbol,
                trade_date,
                open,
                high,
                low,
                close,
                volume
            FROM market_prices
            WHERE symbol = ?
            ORDER BY trade_date DESC
            LIMIT 1
        """
        df = pd.read_sql_query(
            query,
            conn,
            params=(symbol.upper() if isinstance(symbol, str) else symbol,)
        )
        return df
    finally:
        conn.close()


def upsert_market_data(symbol: str, df: pd.DataFrame) -> None:
    """
    Cập nhật hoặc chèn dữ liệu giá (OHLCV) vào bảng market_prices.
    
    Dữ liệu được lấy từ yfinance hoặc các nguồn khác và cache vào SQLite.
    Nếu dòng đã tồn tại (cùng symbol + trade_date), sẽ cập nhật; ngược lại thêm mới.
    
    Args:
        symbol: Mã cổ phiếu
        df: DataFrame chứa OHLCV data với index là datetime
        
    Raises:
        ValueError: Nếu DataFrame rỗng hoặc thiếu cột bắt buộc
    """
    if df is None or df.empty:
        logger.warning("DataFrame rỗng cho %s, bỏ qua upsert", symbol)
        return
    
    # Kiểm tra cột bắt buộc
    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error("DataFrame thiếu cột %s cho %s", missing, symbol)
        raise ValueError(f"DataFrame thiếu cột bắt buộc: {missing}")
    
    # Chuẩn bị dữ liệu
    df_copy = df.copy()
    df_copy["symbol"] = symbol.upper()
    
    # Nếu index là datetime, đặt tên là trade_date
    if isinstance(df_copy.index, pd.DatetimeIndex):
        df_copy["trade_date"] = df_copy.index
    elif "trade_date" not in df_copy.columns:
        logger.error("Không tìm thấy trade_date hoặc datetime index cho %s", symbol)
        raise ValueError("DataFrame phải có cột trade_date hoặc datetime index")
    
    # Chỉ giữ các cột cần thiết
    df_copy = df_copy[[
        "symbol",
        "trade_date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]].copy()
    
    # Đổi tên cột để khớp với schema database
    df_copy.columns = [
        "symbol",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]
    
    # Loại giá không hợp lệ
    df_copy = df_copy[
        (df_copy["open"] > 0)
        & (df_copy["high"] > 0)
        & (df_copy["low"] > 0)
        & (df_copy["close"] > 0)
    ]
    
    if df_copy.empty:
        logger.warning("Không có dữ liệu hợp lệ để upsert cho %s", symbol)
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Xóa dữ liệu cũ của mã này
        cursor.execute("DELETE FROM market_prices WHERE symbol = ?", (symbol.upper(),))
        
        # Chèn dữ liệu mới
        df_copy.to_sql(
            "market_prices",
            conn,
            if_exists="append",
            index=False
        )
        
        conn.commit()
        logger.info("Đã upsert %d hàng dữ liệu cho %s", len(df_copy), symbol)
        
    except Exception as e:
        conn.rollback()
        logger.exception("Lỗi khi upsert dữ liệu cho %s", symbol)
        raise
    finally:
        conn.close()