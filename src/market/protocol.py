"""Core types for the market data layer.

Defines the canonical ``OHLCV`` record and the ``StockSource`` protocol.
All data sources (yfinance, Alpha Vantage, CSV, etc.) must implement
``StockSource``; the rest of the system only depends on this module.

Adding a new data source
------------------------
1. Create ``src/market/sources/<your_source>.py``.
2. Implement ``fetch(ticker, start, end) -> list[OHLCV]`` and
   a ``source_name`` property.
3. Pass an instance to ``StockDataService`` (or register it in
   ``config/market/tickers.yaml`` and update ``get_stock_service()``).
"""

from __future__ import annotations

import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class OHLCV(BaseModel):
    """A single day's Open-High-Low-Close-Volume record for one ticker."""

    ticker: str
    date: datetime.date
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "unknown"


@runtime_checkable
class StockSource(Protocol):
    """Structural protocol for stock data providers.

    Any class with a ``fetch`` method and a ``source_name`` property
    satisfies this protocol — no inheritance required.
    """

    @property
    def source_name(self) -> str:
        """Short identifier for this data provider, e.g. ``'yfinance'``."""
        ...

    def fetch(
        self,
        ticker: str,
        start: datetime.date,
        end: datetime.date,
    ) -> list[OHLCV]:
        """Download OHLCV records for *ticker* over [*start*, *end*] inclusive.

        Args:
            ticker: The real market ticker symbol (e.g. ``"RBLX"``).
            start:  First date to include.
            end:    Last date to include (inclusive).

        Returns:
            List of ``OHLCV`` instances, one per trading day, ordered by date.
        """
        ...
