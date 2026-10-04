# Fixture dùng chung: mỗi test chạy trên một database SQLite tạm (tạo từ schema
# của setup_database.py), không đụng tới data/portfolio.db.

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import setup_database
from database import session
from repositories import user_repository


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Tạo database tạm và trỏ kết nối dùng chung của ứng dụng vào đó."""
    db_file = tmp_path / "test_portfolio.db"
    monkeypatch.setattr(setup_database, "DB_PATH", db_file)
    assert setup_database.create_database()

    session._db_connection.close()
    monkeypatch.setattr(session._db_connection, "db_path", db_file)
    yield db_file
    session._db_connection.close()


@pytest.fixture
def user_id():
    """Người dùng có Telegram chat ID."""
    return user_repository.get_or_create_user("tester", "123456789")


@pytest.fixture
def other_user_id():
    """Người dùng thứ hai, dùng cho kiểm tra quyền sở hữu."""
    return user_repository.get_or_create_user("other", "987654321")


@pytest.fixture
def insert_price():
    """Ghi một giá đóng cửa vào bảng market_prices."""
    def _insert(symbol: str, close: float, trade_date: str = "2026-10-02 14:45:00"):
        conn = session.get_db_connection()
        conn.execute(
            """
            INSERT INTO market_prices (symbol, trade_date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol, trade_date, close, close, close, close, 1000)
        )
        conn.commit()
    return _insert
