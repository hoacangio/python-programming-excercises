# `process_price_alerts`

## Contract

```python
process_price_alerts() -> AlertProcessResult
```

`AlertProcessResult` gồm `checked_count`, `triggered_count`, `sent_count`, `failed_count` và danh sách lỗi theo `alert_id`.

### Input

Database URL, `TELEGRAM_BOT_TOKEN` và timeout lấy từ biến môi trường. Hàm không nhận input từ Streamlit.

### Output

Kết quả tổng hợp. Mỗi alert chỉ chuyển sang inactive sau khi Telegram xác nhận gửi thành công. Nếu gửi lỗi, alert vẫn active và lỗi được ghi log.

## Downstream contracts

| Downstream           | Input                                                                                   | Output                     |
| -------------------- | --------------------------------------------------------------------------------------- | -------------------------- |
| `AlertRepository`    | Active alerts join users: `alert_id`, `symbol`, `target_price`, `condition`, `chat_id`  | Alert rows                 |
| `get_current_prices` | Danh sách symbol duy nhất                                                               | `dict[str, float]`         |
| Telegram Bot API     | `POST https://api.telegram.org/bot{TOKEN}/sendMessage`, JSON `{chat_id, text}`, timeout | HTTP 200 và JSON `ok=true` |
| `AlertRepository`    | `alert_id` sau khi gửi thành công                                                       | Affected rows = 1, commit  |

## Sequence diagram

```mermaid
sequenceDiagram
    participant Cron as alert_bot.py
    participant AS as AlertService
    participant Repo as AlertRepository
    participant MDS as MarketDataService
    participant TG as Telegram Bot API
    Cron->>AS: process_price_alerts()
    AS->>Repo: list active alerts with chat_id
    Repo-->>AS: Alert rows
    AS->>MDS: get_current_prices(unique_symbols)
    MDS-->>AS: Current prices
    loop Mỗi alert đủ dữ liệu
        AS->>AS: Evaluate condition against current price
        alt Condition is met
            AS->>TG: POST sendMessage(chat_id, text, timeout)
            TG-->>AS: HTTP response ok=true/false
            alt Telegram success
                AS->>Repo: deactivate alert and commit
            else Telegram failure
                AS->>AS: Log failure and keep active
            end
        end
    end
    AS-->>Cron: AlertProcessResult
```
