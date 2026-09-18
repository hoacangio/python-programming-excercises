# get_current_prices, get_price_history: tích hợp yfinance.
# Thiết kế: docs/functions/get_current_prices.md, docs/functions/get_price_history.md.
import logging
from datetime import date

import pandas as pd
import yfinance as yf
from repositories import market_repository

# LOGGING

logger = logging.getLogger(__name__)

# CONSTANT

_OHLCV_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]

_REQUEST_TIMEOUT = 10


# CUSTOM ERROR

class MarketDataError(Exception):
    """
    Lỗi khi gọi hoặc xử lý dữ liệu
    từ nguồn downstream như API,
    mạng hoặc timeout.
    """
    pass

# get_current_prices
def get_current_prices(
    symbols: list[str]
) -> dict[str, float]:
    """
    Lấy giá hiện tại gần nhất cho danh sách mã.
    """
    # Kiểm tra input
    if not symbols:
        raise ValueError(
            "symbols không được rỗng"
        )

    
    # Chuẩn hóa và loại mã trùng
    normalized = []
    seen = set()

    for symbol in symbols:

        sym = str(symbol).strip().upper()

        if sym and sym not in seen:

            seen.add(sym)
            normalized.append(sym)

    if not normalized:
        raise ValueError(
            "symbols không được rỗng"
        )

    result = {}

    # Lấy giá từng mã

    for symbol in normalized:

        try:

            logger.info(
                "Đang lấy giá hiện tại cho %s",
                symbol
            )
           
            # GỌI YFINANCE

            df = yf.download(
                tickers=symbol,
                period="1d",
                interval="1m",
                auto_adjust=False,
                progress=False,
                timeout=_REQUEST_TIMEOUT,
                multi_level_index=False
            )

        except Exception as exc:

            logger.exception(
                "Lỗi yfinance cho %s",
                symbol
            )

            raise MarketDataError(
                f"Lỗi khi lấy giá hiện tại "
                f"cho {symbol}: {exc}"
            ) from exc

        # Lấy giá Close gần nhất

        price = _extract_latest_close(
            df,
            symbol
        )

        # Không có dữ liệu

        if price is None:

            logger.warning(
                "Không có dữ liệu giá cho mã %s, bỏ qua.",
                symbol
            )

            continue

        # Lưu kết quả

        result[symbol] = price

        # Lưu cache qua repository

        try:

            market_repository.upsert_market_data(
                symbol,
                df
            )

        except Exception:

            # Lỗi cache không làm mất
            # kết quả giá vừa lấy được.
            logger.exception(
                "Không thể lưu cache giá "
                "cho mã %s.",
                symbol
            )

    return result


# _extract_latest_close

def _extract_latest_close(
    df: pd.DataFrame,
    symbol: str
):
    """
    Lấy giá Close gần nhất.

    Trả về:
        float nếu có giá hợp lệ
        None nếu không có dữ liệu
    """

    if df is None or df.empty:
        return None

    # Trường hợp DataFrame có MultiIndex

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        try:

            df = df.xs(
                "Close",
                axis=1,
                level=0
            )

            if isinstance(
                df,
                pd.DataFrame
            ):

                df = df.iloc[:, 0]

        except KeyError:

            logger.warning(
                "Không tìm thấy Close của %s.",
                symbol
            )

            return None

    else:

        # Trường hợp column bình thường
        if "Close" not in df.columns:
            return None

        df = df["Close"]

    # Bỏ NaN

    close_series = df.dropna()

    if close_series.empty:
        return None

    # Lấy giá cuối cùng

    latest_close = close_series.iloc[-1]
    # Chuyển sang float

    try:

        latest_close = float(
            latest_close
        )

    except (TypeError, ValueError):

        return None
    
    # Kiểm tra giá

    if pd.isna(latest_close):
        return None

    if latest_close <= 0:
        return None

    return latest_close


# get_price_history

def get_price_history(
    symbol: str,
    start: date,
    end: date,
    interval: str = "1d"
) -> pd.DataFrame:
    
    # Chuẩn hóa symbol

    sym = str(symbol).strip().upper()

    if not sym:
        raise ValueError(
            "symbol không được rỗng"
        )

   
    # Kiểm tra thời gian

    if start >= end:
        raise ValueError(
            "start phải nhỏ hơn end"
        )


    # Gọi yfinance

    try:

        logger.info(
            "Đang lấy dữ liệu lịch sử cho %s",
            sym
        )

        raw = yf.download(
            tickers=sym,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
            progress=False,
            timeout=_REQUEST_TIMEOUT,
            multi_level_index=False
        )

    except Exception as exc:

        logger.exception(
            "Lỗi yfinance khi lấy lịch sử %s",
            sym
        )

        raise MarketDataError(
            f"Lỗi khi lấy dữ liệu lịch sử "
            f"cho {sym}: {exc}"
        ) from exc

    # Chuẩn hóa dữ liệu

    df = _normalize_history(
        raw
    )


    # Không có nến hợp lệ

    if df.empty:

        logger.warning(
            "Không có nến hợp lệ cho %s.",
            sym
        )

        return df

    # Lưu cache qua repository

    try:

        market_repository.upsert_market_data(
            sym,
            df
        )

    except Exception:

        # Không làm mất dữ liệu vừa lấy
        logger.exception(
            "Không thể lưu cache lịch sử "
            "giá cho mã %s.",
            sym
        )

    return df


# _normalize_history

def _normalize_history(
    raw: pd.DataFrame
) -> pd.DataFrame:
    
    # DataFrame rỗng theo đúng schema

    empty_schema = pd.DataFrame(
        columns=_OHLCV_COLUMNS
    )

    empty_schema.index = pd.DatetimeIndex(
        []
    )

    empty_schema.index.name = "Date"

    if raw is None or raw.empty:
        return empty_schema

    df = raw.copy()


    # Flatten MultiIndex

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        df.columns = [
            col[0]
            if isinstance(col, tuple)
            else col
            for col in df.columns
        ]

    # Kiểm tra các cột bắt buộc

    missing = [
        column
        for column in _OHLCV_COLUMNS
        if column not in df.columns
    ]

    if missing:

        logger.warning(
            "Dữ liệu thiếu cột: %s",
            missing
        )

        return empty_schema

    # Chỉ giữ OHLCV


    df = df[
        _OHLCV_COLUMNS
    ].copy()

    # Đảm bảo DatetimeIndex

    try:

        if not isinstance(
            df.index,
            pd.DatetimeIndex
        ):

            df.index = pd.to_datetime(
                df.index
            )

    except Exception:

        logger.exception(
            "Không thể chuyển index "
            "thành DatetimeIndex."
        )

        return empty_schema


    # Bỏ dòng thiếu OHLC

    df = df.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close"
        ]
    )

    if df.empty:
        return empty_schema


    # Loại giá không hợp lệ


    df = df[
        (df["Open"] > 0)
        & (df["High"] > 0)
        & (df["Low"] > 0)
        & (df["Close"] > 0)
    ]

    if df.empty:
        return empty_schema

    # Sắp xếp tăng dần

    df = df.sort_index()

    df.index.name = "Date"

    return df[
        _OHLCV_COLUMNS
    ]

