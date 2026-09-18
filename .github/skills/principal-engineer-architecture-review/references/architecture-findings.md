# Architecture Review Findings

Real architectural issues found in this codebase, with concrete fixes.

## Finding 1: UI Importing Repositories Directly ❌

**File**: `app.py` (Lines 5-9)

```python
# WRONG
from repositories.market_repository import (
    get_symbols,
    get_market_data,
    get_latest_price
)
```

**Issue**: The UI layer (`app.py`) imports directly from the repository layer, bypassing services. This violates the 3-layer architecture.

**Consequence**: 
- UI becomes tightly coupled to data access patterns
- Business logic changes force UI changes
- Services become orphaned/unused
- Harder to test or mock data

**Fix**: Create a dashboard service
```python
# NEW FILE: services/dashboard_service.py
from repositories.market_repository import (
    get_symbols,
    get_market_data as repo_get_market_data,
    get_latest_price as repo_get_latest_price
)

def get_symbols():
    """Return available symbols for dashboard."""
    return get_symbols()

def get_market_data(symbol):
    """Get market data with any business logic."""
    return repo_get_market_data(symbol)

def get_latest_price(symbol):
    """Get latest price with any business logic."""
    return repo_get_latest_price(symbol)
```

**Then in app.py**:
```python
# CORRECT
from services.dashboard_service import (
    get_symbols,
    get_market_data,
    get_latest_price
)
```

---

## Finding 2: Services with Direct SQL Queries ❌

**File**: `services/portfolio_service.py` (Lines 7+)

```python
# WRONG
import sqlite3
import pandas as pd

DB_PATH = "data/portfolio.db"

def get_portfolio(user_id):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT symbol, SUM(...) FROM transactions
        WHERE user_id = ? GROUP BY symbol
    """
    df = pd.read_sql_query(query, conn, ...)
```

**Issue**: The service layer directly executes SQL queries, which should belong in the repository layer.

**Consequence**:
- Services are not "pure business logic"
- Database changes require service changes
- SQL logic scattered across services
- Duplicate SQL queries in multiple services

**Fix**: Move SQL to repository
```python
# FILE: repositories/portfolio_repository.py (NEW or updated)
import sqlite3
import pandas as pd

DB_PATH = "data/portfolio.db"

def get_portfolio(user_id):
    """Repository: fetch portfolio holdings from DB."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT symbol, 
               SUM(CASE WHEN transaction_type = 'BUY' 
                       THEN quantity ELSE -quantity END) AS quantity,
               SUM(CASE WHEN transaction_type = 'BUY' 
                       THEN quantity * price ELSE 0 END) AS total_buy_value
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
    """
    df = pd.read_sql_query(query, conn, ...)
    conn.close()
    return df
```

**Then in services/portfolio_service.py**:
```python
# CORRECT
from repositories.portfolio_repository import get_portfolio as repo_get_portfolio

def get_portfolio_summary(user_id):
    """Service: business logic for portfolio summary."""
    holdings = repo_get_portfolio(user_id)
    # Any enrichment, calculation, or transformation here
    return holdings
```

---

## Finding 3: No Transaction Safety in Repository ❌

**File**: `repositories/transaction_repository.py` (Lines 34+)

```python
# PROBLEMATIC
def add_transaction(user_id, symbol, transaction_type, quantity, price, notes=""):
    symbol = symbol.upper()
    transaction_type = transaction_type.upper()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""INSERT INTO transactions ...""")
    conn.commit()
    conn.close()
    # ← No error handling! If insert fails, connection not closed properly
```

**Issue**: No try/except around the transaction. If an exception occurs, the connection is not closed.

**Fix**: Use context manager
```python
# CORRECT
def add_transaction(user_id, symbol, transaction_type, quantity, price, notes=""):
    symbol = symbol.upper()
    transaction_type = transaction_type.upper()
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO transactions 
                   (user_id, symbol, transaction_type, quantity, price, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, symbol, transaction_type, quantity, price, notes)
            )
            conn.commit()
            logger.info(f"Transaction added: {user_id} {symbol} {transaction_type} x{quantity}")
            return {"status": "success", "transaction_id": cursor.lastrowid}
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error: {e}")
        raise ValueError(f"Invalid transaction data: {e}")
    except Exception as e:
        logger.exception(f"Failed to add transaction: {e}")
        raise
```

---

## Finding 4: Services Missing Validation ❌

**File**: `services/market_data_service.py` (Lines 39-47)

```python
# CURRENT
def get_current_prices(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        raise ValueError("symbols cannot be empty")
    
    # Normalization exists ✓
    normalized = []
    seen = set()
    for symbol in symbols:
        sym = str(symbol).strip().upper()
        if sym and sym not in seen:
            seen.add(sym)
            normalized.append(sym)
    # ...
```

**Good**: Normalization exists. But check that ALL services validate input similarly.

**Best Practice**: Create a shared validation utility
```python
# FILE: services/validation_utils.py (NEW)
def normalize_symbol(symbol: str) -> str:
    """Normalize stock symbol: strip, uppercase, validate non-empty."""
    sym = str(symbol).strip().upper()
    if not sym:
        raise ValueError("Symbol cannot be empty after normalization")
    return sym

def normalize_symbols(symbols: list[str]) -> list[str]:
    """Normalize list of symbols, remove duplicates."""
    if not symbols:
        raise ValueError("Symbols list cannot be empty")
    
    normalized = []
    seen = set()
    for symbol in symbols:
        sym = normalize_symbol(symbol)
        if sym not in seen:
            seen.add(sym)
            normalized.append(sym)
    return normalized

def validate_positive_int(value, name="value"):
    """Validate positive integer."""
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be positive integer, got {value}")
    return value
```

**Then in services**:
```python
# CORRECT (in any service)
from services.validation_utils import normalize_symbols, validate_positive_int

def add_price_alert(user_id, symbol, target_price, condition):
    user_id = validate_positive_int(user_id, "user_id")
    symbol = normalize_symbol(symbol)
    target_price = float(target_price)
    if target_price <= 0:
        raise ValueError("target_price must be positive")
    # ... call repo
```

---

## Finding 5: Missing Error Handling in Services ❌

**File**: `services/market_data_service.py` (Lines 74+)

```python
# CURRENT (lines 74-84)
try:
    logger.info("Fetching current price for %s", symbol)
    df = yf.download(...)
except Exception as exc:
    logger.exception("Error fetching from yfinance for %s", symbol)
    # ← Exception is logged but not re-raised or handled!
    # Result: partial data returned silently
```

**Issue**: Exception is swallowed. Caller doesn't know if data is complete or partial.

**Fix**: Return structured result
```python
# CORRECT
def get_current_prices(symbols: list[str]) -> dict[str, float]:
    """
    Returns: dict[str, float] = {"SYMBOL": price}
    Raises: MarketDataError if all symbols fail; logs partial failures
    """
    normalized = normalize_symbols(symbols)
    result = {}
    failed = []
    
    for symbol in normalized:
        try:
            logger.info("Fetching current price for %s", symbol)
            df = yf.download(
                tickers=symbol,
                period="1d",
                interval="1m",
                auto_adjust=False,
                progress=False,
                timeout=_REQUEST_TIMEOUT
            )
            if df.empty:
                logger.warning("No data for %s", symbol)
                failed.append(symbol)
            else:
                price = float(df["Close"].iloc[-1])
                result[symbol] = price
                logger.info("Got price for %s: %s", symbol, price)
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", symbol, exc)
            failed.append(symbol)
    
    if not result:  # All failed
        raise MarketDataError(
            f"Could not fetch prices for any symbols: {symbols}"
        )
    
    if failed:  # Partial failure
        logger.warning("Partial failure for symbols: %s", failed)
    
    return result
```

---

## Finding 6: Missing Type Hints on Functions ❌

**Files**: Multiple across services, repositories, and UI

```python
# WRONG (services/portfolio_service.py)
def get_portfolio(user_id):
    """Fetch portfolio - but what type is user_id? What is the return type?"""
    conn = sqlite3.connect(DB_PATH)
    # ...

# WRONG (repositories/transaction_repository.py)
def add_transaction(user_id, symbol, transaction_type, quantity, price, notes=""):
    """Add a transaction - does this return int? bool? None?"""
    # ...

# WRONG (app.py)
def get_symbols():
    """Get symbols for dropdown - returns what exactly?"""
    return get_symbols()
```

**Issue**: Functions lack type annotations on parameters and return values.

**Consequence**:
- IDE cannot provide autocomplete or catch type errors
- Code is harder to understand (unclear contracts)
- Refactoring is risky (changing types breaks callers silently)
- Testing is harder (unclear what to mock/expect)
- Type errors only caught at runtime, not during review

**Fix**: Add comprehensive type hints
```python
# CORRECT (repositories/transaction_repository.py)
from typing import Optional
import pandas as pd

def add_transaction(
    user_id: int,
    symbol: str,
    transaction_type: str,
    quantity: int,
    price: float,
    notes: Optional[str] = None
) -> int:  # ← Returns transaction ID
    """Add a transaction and return its ID."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO transactions 
                   (user_id, symbol, transaction_type, quantity, price, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, symbol, transaction_type, quantity, price, notes)
            )
            conn.commit()
            return cursor.lastrowid  # ← Clear: returns int
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Invalid transaction: {e}")

def get_portfolio(user_id: int) -> pd.DataFrame:
    """Fetch portfolio holdings as DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT symbol, SUM(...) FROM transactions WHERE user_id = ? GROUP BY symbol",
            conn,
            params=(user_id,)
        )
    return df

# CORRECT (services/portfolio_service.py)
from repositories.transaction_repository import get_portfolio as repo_get_portfolio
from services.market_data_service import get_current_prices

def get_portfolio_summary(user_id: int) -> dict[str, float | int]:
    """Calculate portfolio summary with PnL.
    
    Returns:
        dict with keys: total_value (float), pnl (float), holdings (int)
    """
    holdings = repo_get_portfolio(user_id)  # Type: pd.DataFrame
    if holdings.empty:
        return {"total_value": 0.0, "pnl": 0.0, "holdings": 0}
    
    symbols: list[str] = holdings["symbol"].tolist()
    prices: dict[str, float] = get_current_prices(symbols)
    
    total_value = sum(row["quantity"] * prices.get(row["symbol"], 0.0) 
                      for _, row in holdings.iterrows())
    
    return {
        "total_value": total_value,
        "pnl": calculate_pnl(holdings, prices),
        "holdings": len(holdings)
    }

# CORRECT (app.py)
from services.dashboard_service import get_symbols

symbols: list[str] = get_symbols()
selected_symbol: str = st.selectbox("Choose symbol", symbols)
```

**Type Hints Cheat Sheet**:
```python
from typing import Optional, Union
import pandas as pd

# Basic types
def func(name: str, age: int, price: float, active: bool) -> None:
    pass

# Collections (Python 3.9+)
def func(items: list[str], mapping: dict[str, int], ids: set[int]) -> tuple[str, int]:
    pass

# Optional/nullable
def func(optional_value: Optional[str]) -> str | None:
    pass

# Union (Python 3.10+)
def func(value: int | float | str) -> list[dict[str, int]]:
    pass

# DataFrames
def func(df: pd.DataFrame) -> pd.Series:
    pass

# Structured return dict
def func() -> dict[str, float | int]:
    return {"price": 100.5, "qty": 10}
```

---

## Finding 7: Inconsistent Repository Transaction Pattern ❌

**Files**: Multiple repository files

Some use `conn.close()` explicitly, some rely on garbage collection. This is inconsistent and risky.

**Fix**: Use context managers everywhere
```python
# CONSISTENT PATTERN (across all repository files)
with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    # Your query here
    # Connection auto-closes at end of with block
```

---

## Refactoring Priority

1. **High Priority** (Breaking architecture):
   - [ ] Move all SQL from `services/*.py` to `repositories/*.py`
   - [ ] Update `app.py` to import from services, not repositories
   - [ ] Add transaction safety (context managers) to all repos

2. **Medium Priority** (Code quality):
   - [ ] **Add type hints to ALL functions** (parameters + return types)
   - [ ] Consolidate validation logic into `services/validation_utils.py`
   - [ ] Improve error handling in market_data_service (structured returns)
   - [ ] Add logging to all repository operations

3. **Low Priority** (Polish):
   - [ ] Consolidate duplicate SQL queries
   - [ ] Consistent docstring format across services/repos

---

## Testing Implications

Once architecture is fixed, these tests become possible:

```python
# TEST: Service layer (mocked repos)
def test_get_portfolio_summary():
    with patch('repositories.portfolio_repository.get_portfolio') as mock_repo:
        mock_repo.return_value = DataFrame(...)
        result = portfolio_service.get_portfolio_summary(user_id=1)
        assert result["total_value"] == 10000

# TEST: Repository layer (real DB)
def test_add_transaction_commits():
    repo.add_transaction(user_id=1, symbol="AAPL", ...)
    result = repo.get_portfolio(user_id=1)
    assert "AAPL" in result["symbol"].values

# TEST: UI layer (mocked services)
def test_dashboard_renders():
    with patch('services.dashboard_service.get_symbols') as mock:
        mock.return_value = ["AAPL", "GOOGL"]
        # Render page and verify
```

Currently, these tests are hard/impossible because layers are mixed.
