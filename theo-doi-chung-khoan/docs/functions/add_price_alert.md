# `add_price_alert`

## Contract

```python
add_price_alert(
    user_id: int,
    symbol: str,
    target_price: float,
    condition: str,
    alert_type: str,
) -> tuple[bool, str]
```

### Input

`target_price > 0`; `condition` là `GREATER_THAN_OR_EQUAL` hoặc `LESS_THAN_OR_EQUAL`; `alert_type` là `TAKE_PROFIT` hoặc `STOP_LOSS`. Symbol được chuẩn hóa trước khi lưu.

### Output

- Thành công: `(True, message)` sau khi insert và commit.
- Thất bại: `(False, message)` khi validation, user không tồn tại hoặc database lỗi đã dự đoán.

## Downstream: database

Insert vào `price_alerts` với `is_active = 1`; output nội bộ là `alert_id` và trạng thái active. Hàm không gọi `yfinance`.

## Sequence diagram

```mermaid
sequenceDiagram
    participant App as Streamlit app
    participant AS as AlertService
    participant Repo as AlertRepository
    App->>AS: add_price_alert(input)
    AS->>AS: Normalize and validate enum/price
    AS->>Repo: verify user exists
    Repo-->>AS: User exists or not
    alt Valid user and input
        AS->>Repo: insert active price_alert
        Repo-->>AS: alert_id
        AS-->>App: True, message
    else Invalid request
        AS-->>App: False, message
    end
```
