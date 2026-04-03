"""StockDataService — facade that wires a StockSource to the SQLite store.

Usage (fetch and store)::

    from src.market.service import get_stock_service
    import datetime

    svc = get_stock_service()
    stored = svc.fetch_and_store("RBLX",
                                  start=datetime.date(2024, 1, 1),
                                  end=datetime.date.today())
    print(f"Stored {stored} trading days.")

Usage (query)::

    df = svc.get_prices("RBLX",
                         start=datetime.date(2024, 1, 1),
                         end=datetime.date.today())
    print(df.head())
"""

from __future__ import annotations

import datetime
import yaml
from pathlib import Path

import pandas as pd

from src.dashboard import db
from src.dashboard.config import settings
from src.market.protocol import OHLCV, StockSource


class StockDataService:
    """Coordinates a ``StockSource`` with the SQLite persistence layer.

    Args:
        source: Any object satisfying ``StockSource`` — e.g. ``YFinanceSource()``.
    """

    def __init__(self, source: StockSource) -> None:
        self.source = source

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def fetch_and_store(
        self,
        ticker: str,
        start: datetime.date,
        end: datetime.date,
    ) -> int:
        """Fetch OHLCV data from the source and persist it to SQLite.

        Args:
            ticker: Real market ticker symbol (e.g. ``"RBLX"``).
            start:  First date to include.
            end:    Last date to include (inclusive).

        Returns:
            Number of rows stored (0 if the source returned nothing).
        """
        records: list[OHLCV] = self.source.fetch(ticker, start, end)
        if not records:
            return 0
        return db.upsert_ohlcv_batch(records)

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def get_prices(
        self,
        ticker: str,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> pd.DataFrame:
        """Return price history for *ticker* as a DataFrame.

        Columns: ``date, open, high, low, close, volume, source``

        Args:
            ticker: Ticker symbol to query.
            start:  Inclusive start date (``None`` = no lower bound).
            end:    Inclusive end date (``None`` = no upper bound).

        Returns:
            DataFrame with one row per trading day, sorted by date ascending.
            Returns an empty DataFrame if no data is found.
        """
        records = db.get_ohlcv(ticker, start=start, end=end)
        if not records:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "source"])
        rows = [
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "source": r.source,
            }
            for r in records
        ]
        return pd.DataFrame(rows)

    def get_available_tickers(self) -> list[str]:
        """Return all ticker symbols that have data in the database."""
        return db.get_distinct_tickers()

    # ------------------------------------------------------------------
    # Display name helpers (reads config/market/tickers.yaml)
    # ------------------------------------------------------------------

    def get_display_name(self, ticker: str) -> str:
        """Return the configured display name for *ticker*, or *ticker* itself."""
        mapping = self._load_ticker_mapping()
        return mapping.get(ticker, {}).get("display_name", ticker)

    def get_display_ticker(self, ticker: str) -> str:
        """Return the configured display ticker for *ticker*, or *ticker* itself."""
        mapping = self._load_ticker_mapping()
        return mapping.get(ticker, {}).get("display_ticker", ticker)

    def _load_ticker_mapping(self) -> dict:
        config_file = settings.market_config_dir / "tickers.yaml"
        if not config_file.exists():
            return {}
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("symbols", {})


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_stock_service() -> StockDataService:
    """Return a ``StockDataService`` wired with the default data source (yfinance).

    Use ``@st.cache_resource`` in Streamlit to avoid re-initialising on every
    script rerun::

        @st.cache_resource
        def _market_service():
            from src.market.service import get_stock_service
            return get_stock_service()
    """
    from src.market.sources.yfinance_source import YFinanceSource
    return StockDataService(source=YFinanceSource())
