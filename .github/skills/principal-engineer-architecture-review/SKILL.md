---
name: principal-engineer-architecture-review
description: "Principal Engineer code review: Verify layered architecture (UI → Services → Repositories), check separation of concerns, compare implementation against requirements.md. Use when reviewing feature completeness, refactoring, or ensuring code adheres to 3-layer architecture pattern."
argument-hint: "Describe the code changes or module to review"
user-invocable: true
---

# Principal Engineer Architecture Review

## When to Use

- **Code review before merging**: Verify new code follows 3-layer architecture
- **Refactoring validation**: Ensure layer responsibilities are not violated
- **Architecture enforcement**: Check that UI, Services, and Repositories have proper boundaries
- **Requirements alignment**: Validate implementation matches technical specifications in `requirements.md`
- **Cross-file impact analysis**: Understand how changes affect architectural layers
- **Onboarding guidance**: Help team members understand proper layer responsibilities

## The 3-Layer Architecture

```
┌─────────────────────────────────────┐
│   UI Layer (app.py, pages/*.py)     │ Streamlit components, forms, charts
│   ✓ User interaction only           │
│   ✗ No business logic, no SQL       │
└──────────────┬──────────────────────┘
               │ imports only
┌──────────────▼──────────────────────┐
│  Services Layer (services/*.py)     │ Business logic, data orchestration
│  ✓ No Streamlit imports             │ No direct SQLite queries
│  ✗ No UI, no database access        │
└──────────────┬──────────────────────┘
               │ imports only
┌──────────────▼──────────────────────┐
│  Repository Layer (repositories/*..) │ Data access, SQL queries, DB transactions
│  ✓ All database logic               │
│  ✓ Transaction management           │
│  ✗ No Streamlit, no business logic  │
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### UI Layer (`app.py`, `pages/*.py`)
- **Responsibility**: Handle user interaction, display data, render forms
- **Imports from**: Services layer only
- **Imports services to**: Get data, add data, trigger actions
- **Forbidden**: Direct repository/database access, business logic calculations, Streamlit imports in services
- **Pattern**: `result = service.get_portfolio_summary(user_id)` → `st.dataframe(result)`

#### Services Layer (`services/*.py`)
- **Responsibility**: Business logic, data validation, orchestration between repositories
- **Imports from**: Repositories, external APIs (yfinance), utility libraries
- **Forbidden**: Streamlit, direct database connections
- **Pattern**: Validate input → Call repos → Transform data → Return result
- **Example**: `get_portfolio_summary()` queries transaction repo + market repo + formats result

#### Repositories Layer (`repositories/*.py`)
- **Responsibility**: All data access, SQL queries, transaction management
- **Imports from**: Only database/utility libraries (`sqlite3`, `sqlalchemy`, logging)
- **Forbidden**: Streamlit, services, business logic
- **Pattern**: One function = one focused database operation (SELECT, INSERT, UPDATE)
- **Transaction safety**: Rollback on error, context managers for connections

---

## Review Procedure

### Step 1: Layer Boundary Audit
For each Python file, classify it as UI, Service, or Repository:

1. **Check import statements**
   - ✓ UI imports services only: `from services.X import Y`
   - ✓ Services import repos: `from repositories.X import Y`
   - ✗ Red flag: UI importing repositories directly
   - ✗ Red flag: Services importing Streamlit (`import streamlit as st`)

2. **Check for forbidden patterns**
   - ✗ Services with SQL queries: `cursor.execute()`, `sqlite3.connect()`
   - ✗ Services with `st.` calls (Streamlit)
   - ✗ Repositories with business logic or calculations
   - ✗ UI with `sqlite3.connect()` or database queries

### Step 2: Feature-to-Layer Mapping
Review each business requirement and trace its implementation:

1. **Map the feature** from `requirements.md` section 3 (core functions)
   - Example: `add_transaction(user_id, symbol, quantity, price, notes)`

2. **Verify existence** in three layers:
   ```
   UI Layer:        st.form() to collect user input → Call add_transaction service
   Services Layer:  add_transaction() validates + calls repo → Returns status
   Repositories:    add_transaction() executes INSERT + handles transaction
   ```

3. **Check data flow** (UI → Service → Repo → DB → Service → UI)
   - No shortcuts or skipped layers
   - Each layer transforms only what's its responsibility

### Step 3: Service-Level Validations
For each function in `services/`:

1. **Type hints**: Does every function have type annotations?
   - Parameters: `def get_portfolio(user_id: int) -> dict:`
   - Return types: All functions should declare return type
   - Collections: Use `list[str]`, `dict[str, float]`, not bare `list`, `dict`
   - Optional: Use `Optional[str]` or `str | None` for nullable values
   - Union: Use `bool | int` for multiple return types

2. **Input validation**: Does it validate user input before repo calls?
   - Check for `ValueError`, `TypeError` raises
   - Normalization: `symbol.strip().upper()`
   - Validate types match hints

3. **Error handling**: Does it handle and log downstream errors?
   - Try/except around API/repo calls
   - Custom exceptions (e.g., `MarketDataError`)
   - Proper logging: `logger.exception()`, `logger.info()`

4. **Transaction safety**: Does it use repos correctly?
   - No direct SQLite connections
   - No complex SQL — push to repository

### Step 4: Repository Quality Checks
For each function in `repositories/`:

1. **Type hints**: Does every function have type annotations?
   - Parameters with types: `def add_transaction(user_id: int, symbol: str, ...) -> int:`
   - Return types must be explicit (dict, list, DataFrame, or custom types)
   - SQLAlchemy models: Type hint as `Transaction` not bare `object`
   - Cursor results: Type as `list[tuple]` or appropriate structure

2. **Focused responsibility**: Does it do ONE thing?
   - ✓ Get one entity: `get_transaction(id: int) -> dict`
   - ✓ Add one type: `add_transaction(...) -> int` (returns ID)
   - ✗ Mixed logic: Multiple unrelated selects/inserts

3. **Connection safety**:
   - ✓ Context manager: `with sqlite3.connect(...)`
   - ✓ Proper closing: `.close()` or context exit
   - ✗ Connection leak: No cleanup on exception

4. **Index awareness**: Do queries use indexed columns?
   - Check schema in `requirements.md` section 4
   - Indexes exist: `idx_transactions_user_symbol`, `idx_price_alerts_active_symbol`

### Step 5: Cross-File Consistency
Check for repeated patterns that should be unified:

1. **Duplicate SQL queries**: Should be moved to shared repo function
2. **Duplicate validation**: Should be in service or shared utility
3. **Duplicate imports**: Consolidate or explain why separate

---

## Common Anti-Patterns & Fixes

### ❌ Anti-Pattern 1: Service with Direct SQL
```python
# WRONG (in services/portfolio_service.py)
import sqlite3
def get_portfolio(user_id):
    conn = sqlite3.connect("data/portfolio.db")
    cursor.execute("SELECT ...")  # ← Direct SQL in service!
```

**Why it's wrong**: Violates separation of concerns; database logic leaks into business layer.

**Fix**: Move SQL to repository
```python
# CORRECT (in repositories/transaction_repository.py)
def get_portfolio(user_id):
    # All SQL here
    
# CORRECT (in services/portfolio_service.py)
from repositories.transaction_repository import get_portfolio as repo_get_portfolio
def get_portfolio_summary(user_id):
    holdings = repo_get_portfolio(user_id)
    # Add business logic (formatting, calculations, enrichment)
    return summary_data
```

### ❌ Anti-Pattern 2: UI Importing Repositories
```python
# WRONG (in app.py)
from repositories.market_repository import get_symbols, get_market_data
```

**Why it's wrong**: UI should consume services only, not reach into data layer.

**Fix**: Create/use service layer
```python
# CORRECT (in services/market_data_service.py or new dashboard_service.py)
def get_dashboard_symbols():
    return get_symbols()  # From repo

# CORRECT (in app.py)
from services.dashboard_service import get_dashboard_symbols
symbols = get_dashboard_symbols()
```

### ❌ Anti-Pattern 3: Repository with Business Logic
```python
# WRONG (in repositories/portfolio_repository.py)
def calculate_portfolio_pnl(user_id):  # ← Business logic!
    # Fetch holdings
    # Fetch current prices
    # Calculate PnL
    # Format result
```

**Why it's wrong**: Business calculations belong in services, repo does data access only.

**Fix**: Split responsibilities
```python
# CORRECT (in repositories/)
def get_holdings(user_id):
    # Pure data access: return holdings
    
def get_transaction_history(user_id):
    # Pure data access: return transactions

# CORRECT (in services/portfolio_service.py)
def calculate_portfolio_pnl(user_id):
    holdings = repo_get_holdings(user_id)
    current_prices = market_service.get_current_prices(symbols)
    # Calculate PnL, format, return
```

### ❌ Anti-Pattern 4: Streamlit in Services
```python
# WRONG (in services/alert_service.py)
import streamlit as st
def process_alerts():
    if condition:
        st.success("Alert triggered!")  # ← Streamlit in service!
```

**Why it's wrong**: Services are pure Python; Streamlit is UI only. Makes testing impossible, couples service to UI.

**Fix**: Return data, let UI handle display
```python
# CORRECT (in services/alert_service.py)
def process_alerts() -> dict[str, str]:
    return {"status": "success", "message": "Alert triggered"}

# CORRECT (in app.py or pages/*.py)
result = alert_service.process_alerts()
st.success(result["message"])
```

### ❌ Anti-Pattern 5: Missing Type Hints
```python
# WRONG (in services/portfolio_service.py)
def get_portfolio(user_id):
    """Missing type hints makes function contract unclear."""
    conn = sqlite3.connect("db.sqlite")
    data = cursor.execute("SELECT ...")  # ← What type is data?
    return data

# WRONG (in repositories/transaction_repository.py)
def add_transaction(user_id, symbol, qty, price):
    # Unclear: does this return int (ID), bool (success), or None?
    cursor.execute("INSERT INTO ...")
```

**Why it's wrong**: 
- Makes code harder to understand and maintain
- Type errors caught only at runtime, not during review
- IDE can't provide autocomplete or catch mistakes
- Makes testing harder (unclear what to mock)
- Future developers don't know expected types

**Fix**: Add comprehensive type hints
```python
# CORRECT (in repositories/transaction_repository.py)
from typing import Optional
import pandas as pd

def add_transaction(
    user_id: int,
    symbol: str,
    qty: int,
    price: float,
    notes: Optional[str] = None
) -> int:  # ← Returns transaction ID
    """Add a transaction and return its ID."""
    try:
        with sqlite3.connect("db.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, qty, price, notes) VALUES (?, ?, ?, ?, ?)",
                (user_id, symbol, qty, price, notes)
            )
            conn.commit()
            return cursor.lastrowid  # ← Clear: returns int ID
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Invalid data: {e}")

def get_portfolio(user_id: int) -> pd.DataFrame:
    """Fetch portfolio holdings as DataFrame with columns: symbol, quantity, total_buy_value."""
    with sqlite3.connect("db.sqlite") as conn:
        df = pd.read_sql_query(
            "SELECT symbol, SUM(...) FROM transactions WHERE user_id = ? GROUP BY symbol",
            conn,
            params=(user_id,)
        )
    return df

# CORRECT (in services/portfolio_service.py)
from repositories.transaction_repository import get_portfolio as repo_get_portfolio
from services.market_data_service import get_current_prices

def get_portfolio_summary(user_id: int) -> dict[str, float | int]:
    """Calculate portfolio summary: total value, PnL, holdings count."""
    holdings = repo_get_portfolio(user_id)  # ← Type: pd.DataFrame
    if holdings.empty:
        return {"total_value": 0.0, "pnl": 0.0, "holdings": 0}
    
    symbols = holdings["symbol"].tolist()  # ← Type: list[str]
    prices = get_current_prices(symbols)  # ← Type: dict[str, float]
    
    total_value = 0.0
    for _, row in holdings.iterrows():
        total_value += row["quantity"] * prices.get(row["symbol"], 0.0)
    
    return {
        "total_value": total_value,  # ← Type: float
        "pnl": calculate_pnl(holdings, prices),  # ← Type: float
        "holdings": len(holdings)  # ← Type: int
    }
```

**Type Hints Cheat Sheet**:
```python
# Basic types
def func(name: str, age: int, height: float, active: bool) -> None:
    pass

# Collections
def func(items: list[str], mapping: dict[str, int], unique: set[int]) -> tuple[str, int]:
    pass

# Optional (nullable)
from typing import Optional
def func(optional_value: Optional[str]) -> str | None:  # Both syntaxes valid
    pass

# Union types
def func(value: int | float) -> int | str:  # Python 3.10+
    pass

# For DataFrames
import pandas as pd
def func(df: pd.DataFrame) -> pd.Series:
    pass

# Custom return dict with structure
def func() -> dict[str, float | int | str]:
    return {"price": 100.5, "qty": 10, "symbol": "AAPL"}
```

---

## Review Checklist

Use this checklist when reviewing code against requirements.md:

### Architecture
- [ ] **UI Layer**: Only imports from services, no Streamlit imports in services
- [ ] **Services Layer**: No Streamlit, no direct SQL, business logic only
- [ ] **Repositories Layer**: SQL queries only, no business logic, proper transaction safety
- [ ] **No Shortcuts**: No UI→Repo, Services→SQLite direct connections

### Features (from requirements.md Section 3)
- [ ] `get_current_prices()` — Service logic, repo for any caching
- [ ] `get_price_history()` — Service logic, yfinance integration
- [ ] `get_portfolio_summary()` — Service aggregates holdings + prices
- [ ] `add_transaction()` — Service validates, repo executes INSERT
- [ ] `add_price_alert()` — Service validates, repo executes INSERT
- [ ] `list_price_alerts()` — Repo queries, service formats
- [ ] `deactivate_price_alert()` — Repo updates, service manages state
- [ ] `process_price_alerts()` — Service orchestrates repo + market_data
- [ ] `build_candlestick_chart()` — Service transforms, UI renders

### Code Quality
- [ ] **Type Hints**: All functions have parameter and return type annotations
- [ ] **Error Handling**: Services catch exceptions, log with context
- [ ] **Input Validation**: Services validate before repo calls (`.strip().upper()`)
- [ ] **Transaction Safety**: Repos use context managers, rollback on failure
- [ ] **Logging**: Key operations logged (fetch, insert, error)
- [ ] **Index Awareness**: Queries use indexed columns from schema

### Database (from requirements.md Section 4)
- [ ] **Schema matches**: users, transactions, price_alerts tables exist
- [ ] **Indexes used**: `idx_transactions_user_symbol`, `idx_price_alerts_active_symbol` exist
- [ ] **Foreign keys**: Proper cascading deletes configured
- [ ] **Constraints**: Check constraints on enum fields (transaction_type, condition, alert_type)

---

## How to Execute a Review

1. **Scope**: Identify files/PR to review
   - Single file: Focus on its layer and immediate dependencies
   - Multiple files: Trace full data flow UI → Service → Repo → DB

2. **Layer Audit** (Step 1)
   - List imports in each file
   - Mark violations (e.g., `import sqlite3 in service file`)

3. **Feature Mapping** (Step 2)
   - Pick 1-2 key features from requirements
   - Trace code path through all three layers
   - Verify each layer handles its responsibility

4. **Validation** (Steps 3-5)
   - Check service error handling
   - Verify repo transaction safety
   - Look for duplicate code that should be unified

5. **Provide Suggestions**
   - Reference anti-patterns above
   - Propose concrete refactorings (see examples)
   - Recommend layer to move code to

---

## References

- **Architecture**: `requirements.md` Section 2 (Architecture Diagram)
- **Core Functions**: `requirements.md` Section 3 (Detailed Specs)
- **Database Schema**: `requirements.md` Section 4 (SQL Schema)
- **Implementation Guidelines**: `requirements.md` Section 5 (Conventions)
- **Current Services**: `services/*.py`
- **Current Repositories**: `repositories/*.py`
