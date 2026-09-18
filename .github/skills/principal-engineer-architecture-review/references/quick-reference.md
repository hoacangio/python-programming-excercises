# Quick Reference: 3-Layer Architecture

One-page cheat sheet for instant reference during code review.

## Layer Responsibilities

```
┌──────────────────────────────┐
│ UI: app.py, pages/*.py       │ Input forms, display, st.* calls
├──────────────────────────────┤
│ SERVICE: services/*.py       │ Business logic, no SQL, no st.*
├──────────────────────────────┤
│ REPOSITORY: repositories/*.py│ SQL queries, transactions, DB access
└──────────────────────────────┘
```

## Import Pyramid

```
UI imports: services.*  ✓
Service imports: repositories.*, external APIs  ✓
Repo imports: sqlite3, logging  ✓

FORBIDDEN:
UI → repositories ❌
Service → streamlit ❌
Repo → streamlit, services ❌
```

## Responsibility Map

| Task | Layer | Pattern |
|------|-------|---------|
| Validate input | Service | `if not symbol: raise ValueError` |
| Normalize input | Service | `symbol.strip().upper()` |
| Query database | Repository | `cursor.execute(sql)` |
| Call API | Service | `yfinance.download()` |
| Calculate business logic | Service | `revenue - costs` |
| Commit transaction | Repository | `conn.commit()` |
| Format for display | Service/UI | `st.dataframe()`, formatting |
| Show to user | UI | `st.write()`, `st.form()` |
| Handle errors | Service | `try/except` + log |
| Manage connections | Repository | `with sqlite3.connect()` |

## Red Flags

| Pattern | Layer | Severity |
|---------|-------|----------|
| `import streamlit` in services/ | Service | 🔴 BLOCK |
| `sqlite3.connect()` in services/ | Service | 🔴 BLOCK |
| `from repositories` in app.py | UI | 🔴 BLOCK |
| `st.error()` in services/ | Service | 🔴 BLOCK |
| Business logic in repositories/ | Repo | 🟡 FIX |
| `cursor.execute()` not in `with` | Repo | 🟡 FIX |
| No error handling in service | Service | 🟡 FIX |
| No logging in repo | Repo | 🟡 FIX |

## Fix Templates

### Moving SQL from Service to Repo

**Before** (WRONG):
```python
# services/portfolio_service.py
import sqlite3
def get_portfolio(user_id):
    conn = sqlite3.connect("db.sqlite")
    cursor.execute("SELECT ...")
```

**After** (RIGHT):
```python
# repositories/portfolio_repository.py
def get_portfolio(user_id):
    with sqlite3.connect("db.sqlite") as conn:
        return pd.read_sql_query("SELECT ...", conn)

# services/portfolio_service.py
from repositories.portfolio_repository import get_portfolio as repo_get
def get_portfolio_summary(user_id):
    holdings = repo_get(user_id)
    # Add business logic here
    return formatted_data
```

### Fixing UI→Repo Imports

**Before** (WRONG):
```python
# app.py
from repositories.market_repo import get_symbols
symbols = get_symbols()
```

**After** (RIGHT):
```python
# services/dashboard_service.py
from repositories.market_repo import get_symbols as repo_get
def get_symbols():
    return repo_get()  # Can add business logic if needed

# app.py
from services.dashboard_service import get_symbols
symbols = get_symbols()
```

### Adding Error Handling to Service

**Before**:
```python
def add_alert(user_id, symbol, price):
    return repo_add_alert(user_id, symbol, price)
```

**After**:
```python
def add_alert(user_id, symbol, price):
    try:
        validate_positive_int(user_id)
        symbol = normalize_symbol(symbol)
        price = float(price)
        if price <= 0:
            raise ValueError("price must be positive")
        
        result = repo_add_alert(user_id, symbol, price)
        logger.info(f"Alert added: {symbol} @ {price}")
        return {"status": "success", "alert_id": result}
    except ValueError as e:
        logger.warning(f"Invalid alert input: {e}")
        raise
    except Exception as e:
        logger.exception(f"Failed to add alert: {e}")
        raise MarketDataError(f"Database error: {e}")
```

### Transaction Safety in Repo

**Before** (RISKY):
```python
def add_transaction(user_id, symbol, qty, price):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ...")
    conn.commit()
    conn.close()
    # ← Fails if INSERT throws; connection leaked
```

**After** (SAFE):
```python
def add_transaction(user_id, symbol, qty, price):
    try:
        with sqlite3.connect("db.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, qty, price) VALUES (?, ?, ?, ?)",
                (user_id, symbol, qty, price)
            )
            conn.commit()
            logger.info(f"Transaction: {user_id} {symbol} x{qty}")
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        logger.error(f"Duplicate/constraint: {e}")
        raise ValueError(f"Invalid data: {e}")
    except Exception as e:
        logger.exception(f"DB error: {e}")
        raise
    # ← Connection auto-closes even on exception
```

## Decision Tree

```
Found SQL query?
├─ In services/ ? → Move to repositories/
├─ In app.py ? → Move to repositories/, call from services/
└─ In repositories/ ✓

Found `import streamlit`?
├─ In services/ ? → REMOVE (services are pure Python)
├─ In repositories/ ? → REMOVE (repo is data-only)
└─ In app.py or pages/ ✓

Found business calculation?
├─ In UI layer ? → Move to services/
├─ In repositories/ ? → Move to services/
└─ In services/ ✓

Found database query?
├─ In UI ? → Should be in service → repo chain
├─ In services ? → Move to repositories/
└─ In repositories/ ✓

Error handling?
├─ In service ? ✓ (validate input, try/catch repo calls)
├─ In repo ? ✓ (protect DB operations)
└─ In UI ? ✓ (display to user)

Missing type hints?
├─ Every function should have: def func(param: Type) -> ReturnType
├─ Use list[str], dict[str, int], not bare list, dict
├─ Use Optional[str] or str | None for nullable
└─ Document data structure with type hints
```

## Type Hints Quick Reference

Add these to EVERY function signature:

```python
# Basic types
def func(name: str, count: int, price: float, active: bool) -> None:
    pass

# Collections - use modern syntax (Python 3.9+)
def func(items: list[str], prices: dict[str, float], ids: set[int]) -> tuple[str, int]:
    pass

# Optional/nullable - either syntax works
from typing import Optional
def func(value: Optional[str]) -> str | None:  # Both valid
    pass

# Union types (Python 3.10+)
def func(value: int | float | str) -> list[dict[str, int]]:
    pass

# DataFrames
import pandas as pd
def func(df: pd.DataFrame) -> pd.Series:
    pass

# SQLite/repo functions
def add_transaction(user_id: int, symbol: str, qty: int, price: float) -> int:
    """Returns transaction ID."""
    pass

def get_portfolio(user_id: int) -> pd.DataFrame:
    """Returns portfolio with columns: symbol, quantity, total_buy_value."""
    pass

# Services with structured return
def get_portfolio_summary(user_id: int) -> dict[str, float | int]:
    """Returns {'total_value': float, 'pnl': float, 'holdings': int}."""
    pass

def process_alerts() -> dict[str, str]:
    """Returns {'status': 'success', 'message': 'Alert triggered'}."""
    pass
```

**Benefits of Type Hints**:
- IDE catches errors before runtime ✓
- Code is self-documenting ✓
- Easier to test and mock ✓
- Makes refactoring safer ✓
- Future developers know contracts ✓

## Metrics

Track these during review:

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| Functions with type hints | 90-100% | 50-89% | <50% |
| Services with `sqlite3` imports | 0 | 1-2 | 3+ |
| Services with `streamlit` imports | 0 | 0 | 1+ |
| UI files importing repos | 0 | 0 | 1+ |
| Repos using context managers | 90-100% | 50-89% | <50% |
| Services with error handling | 90-100% | 50-89% | <50% |
| Code covered by unit tests | 80%+ | 50-79% | <50% |

## Resources

- Full guide: See main `SKILL.md`
- Real findings: See `references/architecture-findings.md`
- Checklist: See `references/review-checklist.md`
- Requirements: `docs/requirements.md` in workspace
