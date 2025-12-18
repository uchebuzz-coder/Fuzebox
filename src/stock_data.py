"""
Stock data management module for VIP Play Inc.
Handles storing, retrieving, and managing stock price data.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import random


DATA_DIR = Path(__file__).parent.parent / "data"
STOCK_FILE = DATA_DIR / "vip_play_stock.json"


def ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_stock_data():
    """Load stock data from JSON file."""
    ensure_data_dir()
    if STOCK_FILE.exists():
        with open(STOCK_FILE, 'r') as f:
            return json.load(f)
    return {"company": "VIP Play Inc", "ticker": "VIPP", "prices": []}


def save_stock_data(data):
    """Save stock data to JSON file."""
    ensure_data_dir()
    with open(STOCK_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def add_daily_price(date, open_price, high, low, close, volume):
    """Add a daily stock price entry."""
    data = load_stock_data()

    # Check if entry for this date already exists
    date_str = date if isinstance(date, str) else date.strftime("%Y-%m-%d")
    existing_dates = [p["date"] for p in data["prices"]]

    if date_str in existing_dates:
        # Update existing entry
        for p in data["prices"]:
            if p["date"] == date_str:
                p.update({
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })
                break
    else:
        # Add new entry
        data["prices"].append({
            "date": date_str,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })

    # Sort by date
    data["prices"].sort(key=lambda x: x["date"])
    save_stock_data(data)
    return data


def get_prices_for_period(start_date, end_date):
    """Get stock prices for a specific period."""
    data = load_stock_data()
    start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date
    end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else end_date

    return [p for p in data["prices"] if start_str <= p["date"] <= end_str]


def get_latest_price():
    """Get the most recent stock price."""
    data = load_stock_data()
    if data["prices"]:
        return data["prices"][-1]
    return None


def get_weekly_prices(weeks_back=1):
    """Get prices for the specified number of weeks back from today."""
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)
    return get_prices_for_period(start_date, end_date)


def get_monthly_prices(months_back=1):
    """Get prices for the specified number of months back from today."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    return get_prices_for_period(start_date, end_date)


def generate_sample_data(days=90):
    """Generate sample stock data for testing/demo purposes."""
    data = load_stock_data()

    # Start with a base price
    base_price = 45.00
    current_price = base_price

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    current_date = start_date
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:
            # Generate realistic price movements
            daily_change = random.uniform(-0.03, 0.035)  # -3% to +3.5% daily change
            current_price = current_price * (1 + daily_change)
            current_price = max(current_price, 10)  # Floor at $10

            open_price = round(current_price * random.uniform(0.99, 1.01), 2)
            close_price = round(current_price, 2)
            high = round(max(open_price, close_price) * random.uniform(1.0, 1.02), 2)
            low = round(min(open_price, close_price) * random.uniform(0.98, 1.0), 2)
            volume = random.randint(500000, 5000000)

            add_daily_price(
                current_date.strftime("%Y-%m-%d"),
                open_price,
                high,
                low,
                close_price,
                volume
            )

        current_date += timedelta(days=1)

    print(f"Generated {days} days of sample stock data for VIP Play Inc (VIPP)")
    return load_stock_data()


if __name__ == "__main__":
    # Generate sample data when run directly
    generate_sample_data()
