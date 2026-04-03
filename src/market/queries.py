"""Pure DataFrame query functions for market data analysis.

All functions read from the SQLite store via ``db.get_ohlcv()`` /
``db.get_distinct_tickers()``.  They have no side-effects and can be
tested independently of the service layer.
"""

from __future__ import annotations

import datetime

import pandas as pd

from src.dashboard import db


def price_history_df(
    ticker: str,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> pd.DataFrame:
    """Return OHLCV price history for one ticker.

    Columns: ``date, open, high, low, close, volume``
    """
    records = db.get_ohlcv(ticker, start=start, end=end)
    if not records:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    return pd.DataFrame([
        {"date": r.date, "open": r.open, "high": r.high,
         "low": r.low, "close": r.close, "volume": r.volume}
        for r in records
    ])


def returns_df(
    ticker: str,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> pd.DataFrame:
    """Return daily and cumulative percentage returns for one ticker.

    Columns: ``date, close, daily_return, cumulative_return``
    """
    df = price_history_df(ticker, start, end)
    if df.empty or len(df) < 2:
        return pd.DataFrame(columns=["date", "close", "daily_return", "cumulative_return"])
    df = df.copy()
    df["daily_return"] = df["close"].pct_change()
    df["cumulative_return"] = (1 + df["daily_return"].fillna(0)).cumprod() - 1
    return df[["date", "close", "daily_return", "cumulative_return"]]


def multi_ticker_comparison_df(
    tickers: list[str],
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> pd.DataFrame:
    """Return close prices for multiple tickers in a wide DataFrame.

    Columns: ``date`` + one column per ticker (e.g. ``close_RBLX``).
    Rows are aligned by date; missing values are NaN.
    """
    frames: list[pd.DataFrame] = []
    for ticker in tickers:
        df = price_history_df(ticker, start, end)
        if df.empty:
            continue
        sub = df[["date", "close"]].copy()
        sub = sub.rename(columns={"close": f"close_{ticker}"})
        frames.append(sub)

    if not frames:
        return pd.DataFrame(columns=["date"])

    merged = frames[0]
    for frame in frames[1:]:
        merged = pd.merge(merged, frame, on="date", how="outer")
    return merged.sort_values("date").reset_index(drop=True)
