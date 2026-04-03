"""Market data package — pluggable stock data sources and storage."""

from .service import StockDataService, get_stock_service

__all__ = ["StockDataService", "get_stock_service"]
