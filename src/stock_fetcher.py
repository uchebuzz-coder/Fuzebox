"""
Real stock data fetcher for VIP Play Inc.
Pulls OHLCV data from Yahoo Finance via yfinance and seeds the local JSON store.

RBLX (Roblox Corporation) is used as the underlying real-world data source;
the company is presented as "VIP Play Inc" in all reports.
"""

import yfinance as yf
from datetime import datetime, timedelta

from src.stock_data import add_daily_price, load_stock_data, save_stock_data

REAL_TICKER = "RBLX"


def fetch_and_store(days: int = 90, start: str = None, end: str = None) -> int:
    """
    Download RBLX OHLCV data from Yahoo Finance and store it as VIP Play Inc data.

    Args:
        days:  Number of calendar days back from today (used when start/end are not given).
        start: Start date string YYYY-MM-DD (overrides days).
        end:   End date string YYYY-MM-DD (defaults to today).

    Returns:
        Number of trading days stored.
    """
    if end is None:
        end_dt = datetime.now()
    else:
        end_dt = datetime.strptime(end, "%Y-%m-%d")

    if start is None:
        start_dt = end_dt - timedelta(days=days)
    else:
        start_dt = datetime.strptime(start, "%Y-%m-%d")

    start_str = start_dt.strftime("%Y-%m-%d")
    # yfinance end date is exclusive, so add one day
    end_str = (end_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Fetching {REAL_TICKER} data from {start_str} to {end_dt.strftime('%Y-%m-%d')} ...")
    ticker = yf.Ticker(REAL_TICKER)
    df = ticker.history(start=start_str, end=end_str, auto_adjust=True)

    if df.empty:
        print("No data returned. Check your date range or network connection.")
        return 0

    # Flatten MultiIndex columns that yfinance may return
    if isinstance(df.columns, __import__("pandas").MultiIndex):
        df.columns = df.columns.get_level_values(0)

    stored = 0
    for date_idx, row in df.iterrows():
        date_str = date_idx.strftime("%Y-%m-%d")
        add_daily_price(
            date=date_str,
            open_price=round(float(row["Open"]), 2),
            high=round(float(row["High"]), 2),
            low=round(float(row["Low"]), 2),
            close=round(float(row["Close"]), 2),
            volume=int(row["Volume"]),
        )
        stored += 1

    # Preserve company metadata (do not overwrite the fictional branding)
    data = load_stock_data()
    data["company"] = "VIP Play Inc"
    data["ticker"] = "VIPP"
    save_stock_data(data)

    return stored
