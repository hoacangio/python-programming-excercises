#!/usr/bin/env python3
"""
Database setup script: Create tables and seed with sample data.
Run this once before testing the app: python setup_database.py

Strategy:
- Fetch real market data from yfinance for primary symbols (VNM, ACB, BID, etc.)
- Generate synthetic but realistic data for secondary VNINDEX symbols
- Supports any VNINDEX component without hardcoding restrictions
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
import time
import random

import pandas as pd
import yfinance as yf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "portfolio.db"

# VNINDEX Components - All major Vietnamese stocks
# Source: VNIndex components (30 stocks typical)
VNINDEX_SYMBOLS = [
    "VNM",   # Vinamilk
    "ACB",   # ACB Bank
    "BID",   # BIDV Bank
    "FPT",   # FPT Corporation
    "VIC",   # Vingroup
    "BVH",   # BVH Holdings
    "GAS",   # PV Gas
    "STB",   # Sacombank
    "TCB",   # Techcombank
    "TPB",   # TPBank
    "MBB",   # MB Bank
    "SBV",   # SBV Holdings
    "VCB",   # Vietcombank
    "HDB",   # HD Bank
    "CTG",   # Vietinbank
    "ALF",   # Allianz Vietnam
    "MSN",   # Massan Group
    "SSH",   # Saigon Sunbelt
    "KDC",   # Kinh Do
    "HPG",   # Hoa Phat Steel
    "HSG",   # Hoa Sen Group
    "NLG",   # Nha Long Group
    "PDR",   # Petro Dragon
    "PNJ",   # PNJ Jewelry
    "PVD",   # PV Drilling
    "SAB",   # Sabeco
    "SJS",   # Sorimachi
    "SSB",   # Seabank
    "TCH",   # Techcombank
    "VJC",   # Vietjet
]

# Realistic base prices for all symbols
SYMBOL_BASE_PRICES = {
    "VNM": 85.0, "ACB": 24.0, "BID": 42.0, "FPT": 68.0,
    "VIC": 55.0, "BVH": 48.0, "GAS": 35.0, "STB": 28.0,
    "TCB": 30.0, "TPB": 25.0, "MBB": 32.0, "SBV": 22.0,
    "VCB": 72.0, "HDB": 45.0, "CTG": 26.0, "ALF": 18.0,
    "MSN": 38.0, "SSH": 15.0, "KDC": 20.0, "HPG": 32.0,
    "HSG": 15.0, "NLG": 28.0, "PDR": 12.0, "PNJ": 52.0,
    "PVD": 18.0, "SAB": 48.0, "SJS": 45.0, "SSB": 22.0,
    "TCH": 30.0, "VJC": 95.0,
}


def create_database():
    """Create database file and tables."""
    # Create data directory if not exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database to start fresh
    if DB_PATH.exists():
        logger.info(f"Xóa database cũ: {DB_PATH}")
        DB_PATH.unlink()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 1. Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                telegram_chat_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Tạo bảng 'users'")
        
        # 2. Create transactions table
        cursor.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                price DECIMAL(15, 2) NOT NULL CHECK (price > 0),
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE INDEX idx_transactions_user_symbol 
            ON transactions(user_id, symbol)
        """)
        logger.info("✓ Tạo bảng 'transactions'")
        
        # 3. Create price_alerts table
        cursor.execute("""
            CREATE TABLE price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                target_price DECIMAL(15, 2) NOT NULL,
                condition VARCHAR(25) NOT NULL CHECK (condition IN ('GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL')),
                alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('TAKE_PROFIT', 'STOP_LOSS')),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE INDEX idx_price_alerts_active_symbol 
            ON price_alerts(is_active, symbol)
        """)
        cursor.execute("""
            CREATE INDEX idx_price_alerts_user 
            ON price_alerts(user_id)
        """)
        logger.info("✓ Tạo bảng 'price_alerts'")
        
        # 4. Create market_prices table (for caching OHLCV data)
        cursor.execute("""
            CREATE TABLE market_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(10) NOT NULL,
                trade_date TIMESTAMP NOT NULL,
                open DECIMAL(15, 2) NOT NULL,
                high DECIMAL(15, 2) NOT NULL,
                low DECIMAL(15, 2) NOT NULL,
                close DECIMAL(15, 2) NOT NULL,
                volume INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, trade_date)
            )
        """)
        cursor.execute("""
            CREATE INDEX idx_market_prices_symbol_date 
            ON market_prices(symbol, trade_date DESC)
        """)
        logger.info("✓ Tạo bảng 'market_prices'")
        
        conn.commit()
        logger.info("✅ Tất cả bảng được tạo thành công!")
        return True
    
    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo bảng: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def _fetch_real_market_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Fetch real market data from yfinance.
    
    Returns DataFrame with normalized columns or None if fetch fails.
    """
    try:
        ticker = f"{symbol}.VN"
        df = yf.download(
            tickers=ticker,
            period=f"{days}d",
            interval="1d",
            progress=False,
            timeout=15
        )
        
        if df is None or df.empty:
            return None
        
        # Flatten MultiIndex columns if present (yfinance returns MultiIndex for single ticker)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)
        
        # Rename to lowercase for consistency
        df.columns = df.columns.str.lower()
        
        return df
    except Exception:
        return None


def _generate_synthetic_market_data(symbol: str, base_price: float, days: int = 30) -> pd.DataFrame:
    """
    Generate realistic synthetic OHLCV data.
    
    Uses deterministic random seed based on symbol for reproducibility.
    """
    random.seed(hash(symbol) % 10000)
    data = []
    
    for day_offset in range(days):
        trade_date = datetime.now() - timedelta(days=days - day_offset)
        
        # Simulate realistic price movement
        daily_change = random.uniform(-0.03, 0.03)  # ±3% daily
        open_price = base_price * (1 + daily_change)
        high = open_price * (1 + random.uniform(0, 0.03))
        low = open_price * (1 - random.uniform(0, 0.02))
        close = (high + low) / 2 + random.uniform(-0.5, 0.5)
        volume = random.randint(500000, 5000000)
        
        data.append({
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volume
        })
        
        base_price = close  # Next day's base is today's close
    
    df = pd.DataFrame(data)
    df.index = pd.date_range(
        end=datetime.now().date(),
        periods=days,
        freq='D'
    )
    df.index.name = 'Date'
    return df


def _insert_market_data_to_db(cursor: sqlite3.Cursor, symbol: str, df: pd.DataFrame) -> int:
    """
    Insert market data DataFrame into database.
    
    Returns number of rows inserted.
    """
    # Clear old data
    cursor.execute("DELETE FROM market_prices WHERE symbol = ?", (symbol.upper(),))
    
    # Ensure columns are lowercase
    df = df.copy()
    df.columns = df.columns.str.lower() if hasattr(df.columns, 'str') else [col.lower() for col in df.columns]
    
    # Prepare data
    rows = []
    for trade_date, row in df.iterrows():
        try:
            # Convert pandas Timestamp to datetime if needed
            if hasattr(trade_date, 'to_pydatetime'):
                trade_date = trade_date.to_pydatetime()
            
            close_val = float(row.get('close', 0))
            if close_val > 0:
                rows.append((
                    symbol.upper(),
                    trade_date,
                    float(row.get('open', 0)),
                    float(row.get('high', 0)),
                    float(row.get('low', 0)),
                    close_val,
                    int(row.get('volume', 0))
                ))
        except (ValueError, TypeError) as e:
            # Skip malformed rows
            logger.debug(f"Skipped malformed row for {symbol}: {e}")
            continue
    
    # Insert
    if rows:
        cursor.executemany("""
            INSERT INTO market_prices (symbol, trade_date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows)
    
    return len(rows)


def populate_market_data(symbols: list[str], days: int = 30) -> dict:
    """
    Populate market data with hybrid strategy:
    1. Try to fetch real data for primary symbols
    2. Fall back to synthetic data if fetch fails or for secondary symbols
    
    Args:
        symbols: List of stock symbols
        days: Number of days of historical data
    
    Returns:
        Statistics dict with success/failure counts
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    stats = {
        "real_data": 0,
        "synthetic_data": 0,
        "failed": 0,
        "total_rows": 0
    }
    
    # Primary symbols - try real data first
    primary = ["VNM", "ACB", "BID", "FPT", "VCB", "TCB", "TPB", "MBB", "CTG"]
    
    logger.info(f"\n📊 Đang tải dữ liệu thị trường cho {len(symbols)} mã...")
    logger.info(f"   • Ưu tiên (real data): {len([s for s in primary if s in symbols])}")
    logger.info(f"   • Phụ (synthetic data): {len([s for s in symbols if s not in primary])}")
    
    # Process all symbols
    for idx, symbol in enumerate(symbols, 1):
        try:
            is_primary = symbol in primary
            base_price = SYMBOL_BASE_PRICES.get(symbol, 35.0)
            
            # Try real data for primary symbols
            if is_primary:
                logger.info(f"   [{idx}/{len(symbols)}] {symbol:6} (attempting real fetch)...")
                df = _fetch_real_market_data(symbol, days)
                
                if df is not None and not df.empty:
                    logger.info(f"      → Real data fetched: {len(df)} rows")
                    rows = _insert_market_data_to_db(cursor, symbol, df)
                    logger.info(f"      → Inserted: {rows} rows")
                    stats["real_data"] += 1
                    stats["total_rows"] += rows
                    logger.info(f"      → ✓ Success with real data")
                    time.sleep(0.3)  # Rate limit
                    continue
                else:
                    logger.info(f"      → Real data fetch returned empty, using synthetic")
            elif idx % 5 == 0 or idx <= 3:
                logger.info(f"   [{idx}/{len(symbols)}] {symbol:6} (synthetic)...")
            
            # Use synthetic data
            df = _generate_synthetic_market_data(symbol, base_price, days)
            if df is None or df.empty:
                raise ValueError(f"Failed to generate synthetic data")
            
            rows = _insert_market_data_to_db(cursor, symbol, df)
            if rows == 0:
                raise ValueError(f"No rows inserted (got 0)")
            
            stats["synthetic_data"] += 1
            stats["total_rows"] += rows
            
            if idx % 5 == 0 or idx <= 3 or is_primary:
                logger.info(f"      → ✓ Success with synthetic data ({rows} rows)")
            
        except Exception as e:
            stats["failed"] += 1
            logger.exception(f"   [{idx}/{len(symbols)}] {symbol:6} ❌ {type(e).__name__}")
    
    conn.commit()
    conn.close()
    
    # Summary
    logger.info(f"\n✅ Hoàn tất:")
    logger.info(f"   • Real data: {stats['real_data']} mã")
    logger.info(f"   • Synthetic data: {stats['synthetic_data']} mã")
    logger.info(f"   • Thất bại: {stats['failed']} mã")
    logger.info(f"   • Tổng: {stats['total_rows']} dòng dữ liệu")
    
    return stats


def seed_data():
    """Seed database with sample user, transactions, and alerts."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 1. Insert sample user
        cursor.execute("""
            INSERT INTO users (username, telegram_chat_id)
            VALUES (?, ?)
        """, ("user1", "123456789"))
        user_id = cursor.lastrowid
        logger.info(f"✓ Tạo user mẫu: user1 (ID: {user_id})")
        
        # 2. Insert sample transactions
        transactions = [
            # Giao dịch mua VNM
            (user_id, "VNM", "BUY", 100, 85.5, datetime.now() - timedelta(days=30), "Mua VNM"),
            (user_id, "VNM", "BUY", 50, 86.0, datetime.now() - timedelta(days=20), "Mua thêm VNM"),
            (user_id, "VNM", "SELL", 30, 87.5, datetime.now() - timedelta(days=10), "Bán 1 phần"),
            
            # Giao dịch mua ACB
            (user_id, "ACB", "BUY", 200, 24.5, datetime.now() - timedelta(days=25), "Mua ACB"),
            (user_id, "ACB", "BUY", 100, 24.8, datetime.now() - timedelta(days=15), "Mua thêm ACB"),
            
            # Giao dịch mua BID
            (user_id, "BID", "BUY", 50, 42.0, datetime.now() - timedelta(days=20), "Mua BID"),
            (user_id, "BID", "SELL", 20, 43.5, datetime.now() - timedelta(days=5), "Bán BID"),
        ]
        
        cursor.executemany("""
            INSERT INTO transactions 
            (user_id, symbol, transaction_type, quantity, price, transaction_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, transactions)
        logger.info(f"✓ Thêm {len(transactions)} giao dịch mẫu")
        
        # 3. Insert sample price alerts
        alerts = [
            (user_id, "VNM", 90.0, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT"),
            (user_id, "VNM", 80.0, "LESS_THAN_OR_EQUAL", "STOP_LOSS"),
            (user_id, "ACB", 26.0, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT"),
            (user_id, "ACB", 23.0, "LESS_THAN_OR_EQUAL", "STOP_LOSS"),
            (user_id, "BID", 45.0, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT"),
        ]
        
        cursor.executemany("""
            INSERT INTO price_alerts 
            (user_id, symbol, target_price, condition, alert_type, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, alerts)
        logger.info(f"✓ Thêm {len(alerts)} cảnh báo giá mẫu")
        
        conn.commit()
        logger.info("✅ Seed data thành công!")
        return True
    
    except Exception as e:
        logger.error(f"❌ Lỗi khi seed data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_database():
    """Verify database was created correctly."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"\n📊 Bảng trong database: {[t[0] for t in tables]}")
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        logger.info(f"   • Users: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        trans_count = cursor.fetchone()[0]
        logger.info(f"   • Transactions: {trans_count}")
        
        cursor.execute("SELECT COUNT(*) FROM price_alerts")
        alert_count = cursor.fetchone()[0]
        logger.info(f"   • Price Alerts: {alert_count}")
        
        cursor.execute("SELECT COUNT(*) FROM market_prices")
        market_count = cursor.fetchone()[0]
        logger.info(f"   • Market Prices: {market_count}")
        
        # Sample symbols
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM market_prices")
        symbol_count = cursor.fetchone()[0]
        logger.info(f"   • Distinct Symbols: {symbol_count}")
        
        # Transactions by symbol
        cursor.execute("SELECT symbol, COUNT(*) as cnt FROM transactions GROUP BY symbol")
        trans_by_symbol = cursor.fetchall()
        logger.info(f"\n💱 Giao dịch theo mã cổ phiếu:")
        for symbol, count in trans_by_symbol:
            logger.info(f"   • {symbol}: {count} giao dịch")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Lỗi khi verify: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main setup flow."""
    logger.info("=" * 70)
    logger.info("🗄️  Theo dõi chứng khoán - Database Setup")
    logger.info("=" * 70)
    
    # Step 1: Create database and tables
    if not create_database():
        logger.error("Không thể tạo database. Dừng!")
        return False
    
    # Step 2: Seed user and transaction data
    if not seed_data():
        logger.error("Không thể seed data. Dừng!")
        return False
    
    # Step 3: Populate market data (all VNINDEX symbols)
    populate_market_data(VNINDEX_SYMBOLS, days=30)
    
    # Step 4: Verify
    if not verify_database():
        logger.error("Không thể verify database. Dừng!")
        return False
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Database setup hoàn tất!")
    logger.info("=" * 70)
    logger.info(f"📍 Database location: {DB_PATH}")
    logger.info("\n🚀 Để chạy app, sử dụng:")
    logger.info("   streamlit run ui/main.py")
    logger.info("\n📝 Tính năng:")
    logger.info("   • Hỗ trợ tất cả ~30 mã VNINDEX")
    logger.info("   • Thêm bất kỳ mã nào vào danh sách giao dịch")
    logger.info("   • Dữ liệu giá được cập nhật tự động")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
