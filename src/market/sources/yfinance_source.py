"""Yahoo Finance stock data source via the yfinance library.

This is a new, independent code path that writes to SQLite (via
``StockDataService``).  The legacy ``src/stock_fetcher.py`` continues to
write to the JSON store for the CLI reporting commands and is untouched.
"""

from __future__ import annotations

import datetime

import yfinance as yf

from src.market.protocol import OHLCV


class YFinanceSource:
    """Fetches OHLCV data from Yahoo Finance.

    Implements the ``StockSource`` protocol.
    """

    @property
    def source_name(self) -> str:
        return "yfinance"

    def fetch(
        self,
        ticker: str,
        start: datetime.date,
        end: datetime.date,
    ) -> list[OHLCV]:
        """Download OHLCV records for *ticker* over [*start*, *end*] inclusive.

        Args:
            ticker: Real market ticker symbol, e.g. ``"RBLX"``.
            start:  First date to include.
            end:    Last date to include (inclusive).

        Returns:
            List of ``OHLCV`` instances ordered by date ascending.
            Returns an empty list if yfinance returns no data.
        """
        # yfinance end date is exclusive — add one day to make it inclusive
        end_exclusive = end + datetime.timedelta(days=1)

        tk = yf.Ticker(ticker)
        df = tk.history(
            start=start.isoformat(),
            end=end_exclusive.isoformat(),
            auto_adjust=True,
        )

        if df.empty:
            return []

        # yfinance may return a MultiIndex on some versions
        import pandas as pd
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        records: list[OHLCV] = []
        for date_idx, row in df.iterrows():
            records.append(OHLCV(
                ticker=ticker,
                date=date_idx.date(),
                open=round(float(row["Open"]), 4),
                high=round(float(row["High"]), 4),
                low=round(float(row["Low"]), 4),
                close=round(float(row["Close"]), 4),
                volume=int(row["Volume"]),
                source=self.source_name,
            ))

        return records
