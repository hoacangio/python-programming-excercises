# Đo thời gian xử lý của tầng dịch vụ trên database tạm (không đụng data/portfolio.db).
# Chạy: python benchmark.py  (chu kỳ cảnh báo gọi Yahoo Finance thật, cần Internet;
# bước gửi Telegram được thay bằng hàm giả để các lượt đo giống nhau)

import random
import statistics
import tempfile
import time
from pathlib import Path

import setup_database
from database import session
from repositories import market_repository, user_repository
from services import alert_service, messaging_service, portfolio_service
from services.chart_service import build_candlestick_chart

SYMBOLS = list(setup_database.SYMBOL_BASE_PRICES)
SIZES = [100, 1_000, 10_000]


def use_temp_db(path: Path) -> None:
    setup_database.DB_PATH = path
    setup_database.create_database()
    session._db_connection.close()
    session._db_connection.db_path = path


def seed(user_id: int, n_transactions: int) -> None:
    """Sinh n giao dịch hợp lệ (không bán vượt tồn) và 288 nến cho mỗi mã."""
    rng = random.Random(42)
    conn = session.get_db_connection()
    holdings = {s: 0 for s in SYMBOLS}
    rows = []
    for _ in range(n_transactions):
        symbol = rng.choice(SYMBOLS)
        base = setup_database.SYMBOL_BASE_PRICES[symbol]
        price = round(base * rng.uniform(0.8, 1.2), -1)
        if holdings[symbol] >= 100 and rng.random() < 0.3:
            qty = rng.randint(1, holdings[symbol])
            holdings[symbol] -= qty
            rows.append((user_id, symbol, "SELL", qty, price))
        else:
            qty = rng.randint(1, 10) * 100
            holdings[symbol] += qty
            rows.append((user_id, symbol, "BUY", qty, price))
    conn.executemany(
        "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    candles = []
    for symbol in SYMBOLS:
        base = setup_database.SYMBOL_BASE_PRICES[symbol]
        for i in range(288):
            c = base * (1 + rng.uniform(-0.02, 0.02))
            candles.append((symbol, f"2026-10-02 {9 + i // 60:02d}:{i % 60:02d}:00", c, c * 1.01, c * 0.99, c, 1000))
    conn.executemany(
        "INSERT OR REPLACE INTO market_prices (symbol, trade_date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
        candles,
    )
    conn.commit()


def measure(fn, runs: int) -> tuple[float, float, float]:
    fn()  # lượt khởi động, không tính
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times), min(times), max(times)


def report(name: str, runs: int, result: tuple[float, float, float]) -> None:
    med, lo, hi = result
    print(f"| {name} | {runs} | {med:,.1f} ms | {lo:,.1f} – {hi:,.1f} ms |")


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    print("| Thao tác | Số lần đo | Trung vị | Nhỏ nhất – Lớn nhất |")
    print("| --- | :-: | --: | --: |")

    for n in SIZES:
        use_temp_db(tmp / f"bench_{n}.db")
        user_id = user_repository.get_or_create_user("bench", "1")
        seed(user_id, n)
        report(f"Tổng hợp danh mục ({n:,} giao dịch, 30 mã)", 20,
               measure(lambda: portfolio_service.get_portfolio_summary(user_id), 20))

    report("Ghi một giao dịch BUY (10.000 giao dịch sẵn có)", 50,
           measure(lambda: portfolio_service.add_transaction(user_id, "VNM", "BUY", 100, 57_000), 50))
    report("Truy vấn và dựng biểu đồ nến 288 điểm", 50,
           measure(lambda: build_candlestick_chart(market_repository.get_market_data("VNM"), "VNM"), 50))

    # Chu kỳ cảnh báo: gọi Yahoo Finance thật, Telegram giả lập; ngưỡng không bao giờ đạt
    messaging_service.send_alert_notification = lambda **kwargs: True
    for count, runs in [(3, 5), (30, 3)]:
        conn = session.get_db_connection()
        conn.execute("DELETE FROM price_alerts")
        conn.commit()
        for symbol in SYMBOLS[:count]:
            alert_service.add_price_alert(user_id, symbol, 10_000_000, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT")
        report(f"Một chu kỳ kiểm tra cảnh báo ({count} mã, gọi Yahoo Finance)", runs,
               measure(alert_service.process_price_alerts, runs))


if __name__ == "__main__":
    import logging
    logging.disable(logging.CRITICAL)
    main()
