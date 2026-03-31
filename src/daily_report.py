"""
Daily stock price report generator for VIP Play Inc.
Generates text-based daily reports with key metrics.
"""

from datetime import datetime
from pathlib import Path
from .stock_data import get_latest_price, load_stock_data, get_prices_for_period
from datetime import timedelta


REPORTS_DIR = Path(__file__).parent.parent / "reports"


def ensure_reports_dir():
    """Ensure the reports directory exists."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_change(current, previous):
    """Calculate percentage change between two values."""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100


def generate_daily_report(date=None):
    """
    Generate a daily stock price report for VIP Play Inc.

    Args:
        date: The date for the report (defaults to today)

    Returns:
        str: The generated report content
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    data = load_stock_data()

    # Find the price for the specified date
    today_price = None
    prev_price = None

    for i, p in enumerate(data["prices"]):
        if p["date"] == date_str:
            today_price = p
            if i > 0:
                prev_price = data["prices"][i - 1]
            break

    if not today_price:
        # Try to get the latest available price
        today_price = get_latest_price()
        if today_price and len(data["prices"]) > 1:
            prev_price = data["prices"][-2]

    if not today_price:
        return f"No stock data available for VIP Play Inc on {date_str}"

    # Calculate metrics
    daily_change = calculate_change(today_price["close"], today_price["open"])
    day_range = today_price["high"] - today_price["low"]

    prev_close_change = 0
    prev_close_change_pct = 0
    if prev_price:
        prev_close_change = today_price["close"] - prev_price["close"]
        prev_close_change_pct = calculate_change(today_price["close"], prev_price["close"])

    # Format volume
    volume_formatted = f"{today_price['volume']:,}"

    # Determine trend indicators
    trend_emoji = "📈" if daily_change >= 0 else "📉"
    trend_text = "UP" if daily_change >= 0 else "DOWN"

    # Generate report
    report = f"""
{'='*60}
       VIP PLAY INC (VIPP) - DAILY STOCK REPORT
{'='*60}

Report Date: {date_str}
Generated:   {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'─'*60}
                    PRICE SUMMARY
{'─'*60}

  Opening Price:     ${today_price['open']:>10.2f}
  Closing Price:     ${today_price['close']:>10.2f}
  Day's High:        ${today_price['high']:>10.2f}
  Day's Low:         ${today_price['low']:>10.2f}

{'─'*60}
                    PERFORMANCE
{'─'*60}

  Daily Change:      {trend_emoji} {trend_text} {abs(daily_change):>6.2f}%
  Day Range:         ${day_range:>10.2f}

  vs Previous Close: {"+" if prev_close_change >= 0 else ""}{prev_close_change:>6.2f} ({prev_close_change_pct:+.2f}%)

{'─'*60}
                    VOLUME
{'─'*60}

  Trading Volume:    {volume_formatted:>15} shares

{'='*60}
                    END OF REPORT
{'='*60}
"""
    return report


def save_daily_report(date=None):
    """Generate and save the daily report to a file."""
    ensure_reports_dir()

    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    report = generate_daily_report(date)

    filename = REPORTS_DIR / f"daily_report_{date_str}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Daily report saved to: {filename}")
    return filename, report


def print_daily_report(date=None):
    """Generate and print the daily report to console."""
    report = generate_daily_report(date)
    print(report)
    return report


if __name__ == "__main__":
    print_daily_report()
