# Repositories

Tầng repository chịu trách nhiệm truy vấn và ghi database (SQLAlchemy), không chứa business logic. Các service ở `services/` gọi repository để đọc/ghi dữ liệu, sau đó tự xử lý nghiệp vụ (tính PnL, kiểm tra điều kiện alert,...).

Quy ước chung:

- Mỗi repository thao tác trên đúng một bảng và dùng transaction (`commit`/`rollback`) khi ghi dữ liệu.
- Không import Streamlit hoặc gọi API bên ngoài (yfinance, Telegram) trong repository.
- Schema đầy đủ: [docs/requirements.md](../docs/requirements.md) mục 4.

## `user_repository.py`

Truy vấn/ghi bảng `users` (bao gồm `telegram_chat_id`).

```python
from repositories.user_repository import UserRepository

repo = UserRepository(session)
user = repo.get_by_id(user_id=1)          # -> User | None
exists = repo.exists(user_id=1)           # -> bool, dùng khi validate add_price_alert
```

## `transaction_repository.py`

Truy vấn/ghi bảng `transactions`, phục vụ `add_transaction`, `get_portfolio_summary`, `build_candlestick_chart`.

```python
from repositories.transaction_repository import TransactionRepository

repo = TransactionRepository(session)

# Dùng bởi add_transaction để kiểm tra tồn trước khi cho SELL
position = repo.get_position(user_id=1, symbol="FPT")   # -> int (số lượng đang giữ)

# Ghi giao dịch mới, commit/rollback theo docs/functions/add_transaction.md
transaction_id = repo.insert(
    user_id=1, symbol="FPT", transaction_type="BUY",
    quantity=100, price=95_000, notes=None,
)

# Dùng bởi get_portfolio_summary / build_candlestick_chart
rows = repo.list_transactions(user_id=1, ordered=True)  # order by transaction_date, id
```
