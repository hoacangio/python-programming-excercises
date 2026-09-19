# get_current_prices: tích hợp yfinance.
# Thiết kế: docs/functions/get_current_prices.md
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
        else:
            logger.info(
                "Giá hiện tại cho mã %s: %s",
                symbol,
                price
            )

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

