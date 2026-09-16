import sqlite3
import pandas as pd
from pathlib import Path


# Đường dẫn đến database
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "portfolio.db"


def get_connection():
    """Kết nối SQLite database."""
    return sqlite3.connect(DB_PATH)


def get_symbols():
    """Lấy danh sách mã cổ phiếu."""
    conn = get_connection()

    query = """
        SELECT DISTINCT symbol
        FROM market_prices
        ORDER BY symbol
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df["symbol"].tolist()


def get_market_data(symbol):
    """Lấy toàn bộ dữ liệu giá của một mã cổ phiếu."""
    conn = get_connection()

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
        params=(symbol,)
    )

    conn.close()

    if not df.empty:
        df["trade_date"] = pd.to_datetime(df["trade_date"])

    return df


def get_latest_price(symbol):
    """Lấy giá gần nhất."""
    conn = get_connection()

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
        params=(symbol,)
    )

    conn.close()

    return df