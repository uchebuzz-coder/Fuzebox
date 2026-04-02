#!/usr/bin/env python3
"""
Fetch real RBLX stock data from Yahoo Finance and store it as VIP Play Inc (VIPP) data.

Usage:
    python fetch_stock.py                        # Last 90 days
    python fetch_stock.py --days 180             # Last 180 days
    python fetch_stock.py --start 2024-01-01     # From a specific date to today
    python fetch_stock.py --start 2024-01-01 --end 2024-12-31
"""

import argparse
import sys

from src.stock_fetcher import fetch_and_store
from src.stock_data import load_stock_data


def main():
    parser = argparse.ArgumentParser(
        description="Fetch real RBLX data from Yahoo Finance into VIP Play Inc store.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_stock.py                          # Last 90 trading days
  python fetch_stock.py --days 365              # Last year
  python fetch_stock.py --start 2024-01-01      # From date to today
  python fetch_stock.py --start 2024-01-01 --end 2024-06-30
        """,
    )
    parser.add_argument("--days", type=int, default=90,
                        help="Calendar days back from today (default: 90). Ignored if --start is set.")
    parser.add_argument("--start", type=str, metavar="YYYY-MM-DD",
                        help="Start date (overrides --days).")
    parser.add_argument("--end", type=str, metavar="YYYY-MM-DD",
                        help="End date (default: today).")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("   FETCHING REAL STOCK DATA → VIP PLAY INC (VIPP)")
    print("=" * 60)

    stored = fetch_and_store(days=args.days, start=args.start, end=args.end)

    if stored == 0:
        print("\nNo data stored. Exiting.")
        sys.exit(1)

    data = load_stock_data()
    latest = data["prices"][-1]
    oldest = data["prices"][0]

    print(f"\nStored {stored} new trading day(s).")
    print(f"\nData Summary:")
    print(f"  Company: {data['company']}")
    print(f"  Ticker:  {data['ticker']}")
    print(f"  Records: {len(data['prices'])} total trading days")
    print(f"  Period:  {oldest['date']} to {latest['date']}")
    print(f"  Latest Close: ${latest['close']:.2f}")
    print("\nRun 'python main.py all' to generate reports from this data.")


if __name__ == "__main__":
    main()
