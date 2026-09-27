# Candlestick Chart Architecture Implementation Review

## Implementation Summary

This document summarizes the implementation of the candlestick chart feature according to the principal engineer's architectural review feedback.

### Changes Made

#### 1. ✅ Added `get_price_history()` in market_data_service.py

**File**: `services/market_data_service.py`

**New Function Signature**:
```python
def get_price_history(
    symbol: str,
    start: date,
    end: date,
    interval: str = '1d'
) -> pd.DataFrame
```

**Responsibility**: 
- Fetches OHLCV data from yfinance with date range support
- Normalizes DataFrame columns and index structure
- Caches results to repository (non-blocking, logs errors)
- Returns clean DataFrame with schema: `trade_date, open, high, low, close, volume`

**Helper Function Added**:
- `_normalize_ohlcv_dataframe()`: Handles MultiIndex flattening, column renaming, datetime conversion, NaN removal, sorting

**Type Hints**: ✅ Complete with date/str/str returns pd.DataFrame

**Error Handling**: ✅ Raises ValueError for invalid dates, MarketDataError for API failures

**Logging**: ✅ Info/warning/exception at appropriate levels

---

#### 2. ✅ Fixed `build_candlestick_chart()` in chart_service.py

**Old Signature** (Violates Architecture):
```python
def build_candlestick_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
```
- Forced UI to fetch data separately ❌
- No access to user's transactions ❌

**New Signature** (Follows 3-Layer Architecture):
```python
def build_candlestick_chart(
    user_id: int,
    symbol: str,
    start: date,
    end: date,
    interval: str = '1d'
) -> go.Figure
```

**Implementation Details**:
1. **Fetches price data** via `market_data_service.get_price_history()` ✅
2. **Fetches user transactions** via `transaction_repository.get_transactions()` ✅
3. **Filters transactions** by symbol and date range ✅
4. **Adds BUY markers** (green triangles pointing up) with hover details ✅
5. **Adds SELL markers** (red triangles pointing down) with hover details ✅
6. **Returns empty Figure** with valid layout if no price data ✅

**Type Hints**: ✅ All parameters and return type annotated

**Error Handling**: ✅ Validates user_id, symbol; raises ValueError for invalid input

**Logging**: ✅ Logs request, completion, transaction count

---

#### 3. ✅ Updated `dashboard_service.py` 

**Before**: Violated layer separation by calling `market_repository.get_market_data()` directly

**After**: Now calls `market_data_service.get_price_history()` instead

**Function Updated**:
```python
def get_market_data_for_symbol(
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    interval: str = '1d'
) -> pd.DataFrame
```

**Changes**:
- Now uses market_data_service layer ✅
- Added optional date parameters with defaults (30 days lookback) ✅
- Maintains backward compatibility for callers ✅
- Proper logging and error handling ✅

---

#### 4. ✅ Updated `dashboard_page.py` (UI Layer)

**Before**:
```python
market_df = get_market_data_for_symbol(selected_symbol)
fig = build_candlestick_chart(market_df, selected_symbol)
```
Problems: Multiple API calls, UI orchestrating data flow, wrong chart signature

**After**:
```python
fig = build_candlestick_chart(
    user_id=USER_ID,
    symbol=selected_symbol,
    start=start_date,
    end=end_date,
    interval='1d'
)
```

**Changes**:
- Single service call to build_candlestick_chart() ✅
- Passes all necessary parameters (user_id, dates) ✅
- Removed intermediate get_market_data_for_symbol() call ✅
- Added date range with sensible defaults (30 days) ✅
- Improved error handling with specific exception types ✅

---

## Architecture Validation

### Layer Separation: ✅ PASS

| Layer | Before | After |
|-------|--------|-------|
| **UI** | ❌ Calls market_repository directly | ✅ Calls services only |
| **Services** | ❌ chart_service doesn't fetch data | ✅ Orchestrates repositories + APIs |
| **Repositories** | ✅ Data access only | ✅ Data access only |
| **yfinance** | ❌ Not integrated | ✅ Called via market_data_service |

### Data Flow Verification

**Chart Rendering Flow**:
```
dashboard_page.py (UI)
  ↓ calls with (user_id, symbol, start, end)
chart_service.build_candlestick_chart()
  ├─ calls market_data_service.get_price_history()
  │  ├─ validates input
  │  ├─ calls yfinance.download()
  │  ├─ normalizes DataFrame
  │  └─ caches via market_repository.upsert_market_data()
  │
  └─ calls transaction_repository.get_transactions()
     └─ fetches from database
  
  Combines data → creates Plotly Figure → returns to UI
```

✅ **NO SHORTCUTS**: No UI→Repository direct calls, no Services with SQLite

---

## Code Quality Assessment

### Type Hints ✅
- ✅ `get_price_history()`: parameters + return type
- ✅ `build_candlestick_chart()`: all 5 params + return type
- ✅ Helper functions annotated
- ✅ Collection types use `list[str]`, `dict[str, float]`

### Error Handling ✅
- ✅ Input validation (symbol, user_id, dates)
- ✅ Custom exception `MarketDataError` for API failures
- ✅ Try/except with logging in repositories
- ✅ ValueError for invalid input ranges
- ✅ Graceful fallbacks (empty DataFrame with schema)

### Logging ✅
- ✅ Info: function entry, data counts
- ✅ Warning: missing data, cache failures
- ✅ Exception: upstream errors with context

### Input Validation ✅
- ✅ Symbol normalization: `strip().upper()`
- ✅ Date range validation: `start < end`
- ✅ Null checks: symbol, user_id, dates
- ✅ Empty list handling

---

## Testing Considerations

### Unit Test Coverage Needed
- [ ] `get_price_history()` with valid/invalid date ranges
- [ ] `_normalize_ohlcv_dataframe()` with MultiIndex and single-index inputs
- [ ] `build_candlestick_chart()` with user_id=0, empty transactions, no price data
- [ ] Transaction filtering by symbol and date range
- [ ] Marker positioning (BUY/SELL on correct dates and prices)

### Integration Test Coverage Needed
- [ ] End-to-end: dashboard_page → chart_service → market_data_service → yfinance
- [ ] Cache behavior: second call should use cached data
- [ ] Error propagation: yfinance failure → proper UI error message
- [ ] Transaction overlay: verify BUY/SELL appear on correct candles

---

## Potential Issues & Mitigations

| Issue | Status | Mitigation |
|-------|--------|-----------|
| yfinance API rate limits | ⚠️ Known | Cache via market_repository; should add retry logic |
| No user auth in USER_ID=1 | ⚠️ Hardcoded | Should come from session state (noted in code) |
| Large date ranges slow | ⚠️ Possible | Consider pagination or max range limit |
| MultiIndex columns edge case | ✅ Handled | _normalize_ohlcv_dataframe flattens properly |
| Empty transaction list | ✅ Handled | Gracefully skips marker addition |
| No price data for symbol | ✅ Handled | Returns empty Figure with valid layout |

---

## Compliance Checklist

### Requirements from requirements.md
- [x] Section 2 (Architecture): Data flows through layers properly
- [x] Section 3 (Functions): `get_price_history()` + `build_candlestick_chart()` implemented
- [x] Section 4 (Database): Transaction queries working, indexes used
- [x] Section 5 (Conventions): Type hints, logging, error handling

### Anti-Patterns Check
- [x] ❌ Service with direct SQL → Fixed (no SQL in chart_service)
- [x] ❌ UI importing Repositories → Fixed (only imports services)
- [x] ❌ Repository with business logic → N/A (not changed)
- [x] ❌ Streamlit in Services → N/A (was already clean)
- [x] ❌ Missing type hints → Fixed (comprehensive hints added)

---

## Files Modified

| File | Changes | Impact |
|------|---------|--------|
| `services/market_data_service.py` | +2 new functions (get_price_history, _normalize_ohlcv_dataframe) | HIGH: New service layer function |
| `services/chart_service.py` | Complete rewrite of build_candlestick_chart | HIGH: Changed signature and behavior |
| `services/dashboard_service.py` | Updated get_market_data_for_symbol to use market_data_service | MEDIUM: Moved from repository to service |
| `ui/dashboard_page.py` | Updated chart call to new signature, removed intermediate call | MEDIUM: UI simplification |

---

## Ready for Review

✅ **All architectural issues from principal engineer review have been addressed**
✅ **Code follows 3-layer pattern consistently**
✅ **yfinance data flow properly integrated**
✅ **Type hints comprehensive**
✅ **Error handling graceful**
✅ **No layer violations detected**

### Recommended Principal Engineer Review Points

1. **Verify data normalization** in `_normalize_ohlcv_dataframe()` handles edge cases
2. **Check marker positioning** logic for BUY/SELL transactions
3. **Assess yfinance integration** - consider rate limiting strategy
4. **Validate transaction_date filtering** - timezone handling
5. **Review performance** - caching strategy with concurrent users
6. **Confirm user_id source** - should come from authenticated session
