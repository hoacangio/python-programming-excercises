# Architecture Review Checklist Template

Copy this template when conducting a Principal Engineer architecture review.

---

## Review Session: [Feature/PR Name]

**Date**: ___________  
**Reviewer**: ___________  
**Files Under Review**: ___________  

---

## Layer Classification

For each file, mark its layer and list violations:

| File | Layer | Imports | Violations Found |
|------|-------|---------|------------------|
| app.py | UI | `services.*` | ❌ Also imports `repositories.*` |
| services/market_data_service.py | Service | `repositories.*`, `yfinance` | ✓ No Streamlit imports |
| repositories/transaction_repository.py | Repository | `sqlite3`, `logging` | ⚠️ No context managers |
| ... | ... | ... | ... |

---

## Feature Mapping

Pick 1-3 features from `requirements.md` Section 3 and trace implementation:

### Feature: `add_transaction(user_id, symbol, quantity, price, notes)`

- [ ] **UI Layer exists**
  - File: `pages/*.py` or `app.py`
  - Pattern: Form input → Calls service
  - Status: ✓ Found in `pages/3_Giao_dich.py`

- [ ] **Service Layer exists**
  - File: `services/portfolio_service.py`
  - Responsibility: Validate input, call repo, format response
  - Status: ❌ Missing — currently direct SQL in service

- [ ] **Repository Layer exists**
  - File: `repositories/transaction_repository.py`
  - Responsibility: Execute INSERT, manage transaction
  - Status: ⚠️ Exists but lacks error handling

- [ ] **Data Flow**
  - UI → Service ✓
  - Service → Repo ❌ (Service has direct SQL)
  - Repo → DB ✓

### Feature: `get_portfolio_summary(user_id)`

- [ ] **UI Layer**: Calls service to get summary
- [ ] **Service Layer**: Queries holdings + current prices, calculates metrics
- [ ] **Repository Layer**: Returns raw data (holdings, prices separately)
- [ ] **Data Flow**: Complete? Y/N

---

## Code Quality Assessment

### Services (`services/*.py`)

| Aspect | Status | Evidence | Action |
|--------|--------|----------|--------|
| Type hints | ✓/⚠️/❌ | All functions have parameter + return types | |
| No Streamlit imports | ✓/⚠️/❌ | `grep -l "import streamlit" services/` | |
| No direct SQL | ✓/⚠️/❌ | `grep -l "sqlite3\|cursor.execute" services/` | |
| Input validation | ✓/⚠️/❌ | Example from `market_data_service.py` line X | |
| Error handling | ✓/⚠️/❌ | Try/except + logging around repo calls | |
| Docstrings | ✓/⚠️/❌ | All functions documented | |

**Summary**: ________________________________________________________________________

### Repositories (`repositories/*.py`)

| Aspect | Status | Evidence | Action |
|--------|--------|----------|--------|
| Type hints | ✓/⚠️/❌ | All functions have parameter + return types | |
| SQL queries only | ✓/⚠️/❌ | No business logic calculations | |
| Context managers | ✓/⚠️/❌ | `with sqlite3.connect()` pattern used | |
| Error handling | ✓/⚠️/❌ | Try/except on DB operations | |
| Logging | ✓/⚠️/❌ | Info logs for operations, error logs on failure | |
| Index usage | ✓/⚠️/❌ | Queries use indexed columns | |
| Transaction safety | ✓/⚠️/❌ | Rollback on error, ACID guarantees | |

**Summary**: ________________________________________________________________________

### UI (`app.py`, `pages/*.py`)

| Aspect | Status | Evidence | Action |
|--------|--------|----------|--------|
| Type hints (where applicable) | ✓/⚠️/❌ | Local variables/returns have types | |
| Services only | ✓/⚠️/❌ | No `from repositories` imports | |
| User interaction | ✓/⚠️/❌ | Forms, filters, display logic only | |
| Error display | ✓/⚠️/❌ | `st.error()`, `st.warning()` for failures | |

**Summary**: ________________________________________________________________________

---

## Anti-Pattern Detection

Scan for these common violations:

- [ ] ❌ **SQL in Service**: `grep -n "sqlite3\|cursor.execute\|SQL" services/`
  - Found in: ________________
  - Severity: 🔴 High

- [ ] ❌ **Repository in UI**: `grep -n "from repositories" app.py pages/`
  - Found in: ________________
  - Severity: 🔴 High

- [ ] ❌ **Streamlit in Service**: `grep -n "import streamlit\|st\." services/`
  - Found in: ________________
  - Severity: 🔴 High

- [ ] ⚠️ **No Transaction Manager**: `grep -n "sqlite3.connect" repositories/ | grep -v "with"`
  - Found in: ________________
  - Severity: 🟡 Medium

- [ ] ⚠️ **Duplicate SQL**: Are same queries defined in multiple repos?
  - Found: ________________
  - Severity: 🟡 Medium

- [ ] ⚠️ **Business Logic in Repo**: Do repo functions calculate/transform data?
  - Found: ________________
  - Severity: 🟡 Medium

---

## Requirements Alignment

Check implementation against `requirements.md`:

### Section 3: Core Functions

| Function | Designed In Docs | Exists In Code | Status |
|----------|------------------|----------------|--------|
| `get_current_prices()` | Yes | services/market_data_service.py | ✓ |
| `get_price_history()` | Yes | ⚠️ Partial | Missing repo layer |
| `get_portfolio_summary()` | Yes | services/portfolio_service.py | ⚠️ Has SQL |
| `add_transaction()` | Yes | repositories/transaction_repository.py | ⚠️ No service wrapper |
| `add_price_alert()` | Yes | services/alert_service.py | ✓ |
| `list_price_alerts()` | Yes | services/alert_service.py | ✓ |
| `deactivate_price_alert()` | Yes | services/alert_service.py | ✓ |
| `process_price_alerts()` | Yes | alert_bot.py | ⚠️ In wrong place |
| `build_candlestick_chart()` | Yes | services/chart_service.py | ✓ |

**Coverage**: ___% complete, __% properly architected

### Section 4: Database Schema

- [ ] All tables exist: `users`, `transactions`, `price_alerts`
- [ ] All indexes exist: `idx_transactions_user_symbol`, `idx_price_alerts_active_symbol`
- [ ] Check constraints on enums: `transaction_type`, `condition`, `alert_type`
- [ ] Foreign key cascade: `ON DELETE CASCADE` configured

**Status**: ✓/⚠️/❌

### Section 5: Implementation Guidelines

- [ ] Type hints: All functions have parameter and return type annotations
- [ ] Input normalization: `symbol.strip().upper()`
- [ ] Error handling: Custom exceptions (e.g., `MarketDataError`)
- [ ] Logging: Key operations logged
- [ ] Transactions: Using context managers

**Status**: ___% compliant

---

## Recommendations

### Immediate (Blocking)
1. [ ] **Move SQL from services to repositories**
   - Impact: _____ files affected
   - Effort: ⏱️ X hours
   - Benefit: Fixes core architectural violation
   - Recommended fix: See `references/architecture-findings.md` Finding 2

2. [ ] **Update UI imports**
   - Change: `repositories.*` → `services.*`
   - Files: app.py (lines 5-9)
   - Effort: ⏱️ 1 hour

3. [ ] **Add transaction safety**
   - Pattern: `with sqlite3.connect():`
   - Impact: All repository files
   - Effort: ⏱️ 2 hours
   - Benefit: Prevents connection leaks

### Important (Next Sprint)
1. [ ] **Add type hints to all functions**
   - Scope: services/*.py, repositories/*.py, pages/*.py
   - Impact: Every function needs parameter + return types
   - Effort: ⏱️ 6-8 hours
   - Benefit: IDE support, safer refactoring, clearer contracts
   - Reference: See `references/architecture-findings.md` Finding 6

2. [ ] **Consolidate validation**
   - Create: `services/validation_utils.py`
   - Benefit: DRY, consistency
   - Effort: ⏱️ 3 hours

2. [ ] **Improve error handling**
   - Enhance: Services should return structured results
   - Reference: `references/architecture-findings.md` Finding 5
   - Effort: ⏱️ 4 hours

3. [ ] **Create dashboard service**
   - New: `services/dashboard_service.py`
   - Effort: ⏱️ 2 hours

### Nice-to-Have (Polish)
1. [ ] Add comprehensive logging
2. [ ] Add type hints to all repository functions
3. [ ] Add docstrings to all service functions

---

## Test Coverage Implications

After refactoring, new tests become possible:

- [ ] **Service tests** (with mocked repos): `tests/test_*_service.py`
- [ ] **Repository tests** (with real SQLite): `tests/test_repositories.py`
- [ ] **UI tests** (with mocked services): `tests/test_pages.py`

Current blocker: Tight coupling makes mocking impossible.

---

## Sign-Off

**Architecture Status**: 
- [ ] ✓ Compliant with 3-layer architecture
- [ ] ⚠️ Mostly compliant with minor violations
- [ ] ❌ Needs significant refactoring

**Reviewer Sign-Off**: _________________ **Date**: _________

**Recommended Next Step**:
```
[ ] Approve as-is
[ ] Approve with conditional fixes (list below)
[ ] Request refactoring before merge
[ ] Schedule architecture retrospective

Conditions:
- ________________________
- ________________________
```

---

## Notes

________________________________________________________________________________________

________________________________________________________________________________________

________________________________________________________________________________________
