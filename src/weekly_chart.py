"""
Weekly visual chart generator for VIP Play Inc stock prices.
Creates visual charts showing weekly stock price trends.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

from .stock_data import get_weekly_prices, load_stock_data, get_prices_for_period


REPORTS_DIR = Path(__file__).parent.parent / "reports"


def ensure_reports_dir():
    """Ensure the reports directory exists."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_weekly_chart(weeks_back=1, save=True, show=False):
    """
    Generate a visual chart for weekly stock prices.

    Args:
        weeks_back: Number of weeks to include in the chart
        save: Whether to save the chart to a file
        show: Whether to display the chart

    Returns:
        str: Path to the saved chart file (if saved)
    """
    ensure_reports_dir()

    # Get price data
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)
    prices = get_prices_for_period(start_date, end_date)

    if not prices:
        print("No price data available for the specified period")
        return None

    # Extract data for plotting
    dates = [datetime.strptime(p["date"], "%Y-%m-%d") for p in prices]
    closes = [p["close"] for p in prices]
    highs = [p["high"] for p in prices]
    lows = [p["low"] for p in prices]
    opens = [p["open"] for p in prices]
    volumes = [p["volume"] for p in prices]

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    fig.suptitle('VIP Play Inc (VIPP) - Weekly Stock Report', fontsize=14, fontweight='bold')

    # Price chart (top)
    ax1.fill_between(dates, lows, highs, alpha=0.3, color='blue', label='Day Range')
    ax1.plot(dates, closes, 'b-', linewidth=2, label='Close Price', marker='o', markersize=4)
    ax1.plot(dates, opens, 'g--', linewidth=1, alpha=0.7, label='Open Price')

    # Add trend line
    if len(dates) > 1:
        z = np.polyfit(range(len(closes)), closes, 1)
        p = np.poly1d(z)
        ax1.plot(dates, p(range(len(closes))), 'r--', linewidth=1.5, alpha=0.7, label='Trend')

    ax1.set_ylabel('Price ($)', fontsize=11)
    ax1.set_title(f'Stock Price: {start_date.strftime("%b %d")} - {end_date.strftime("%b %d, %Y")}')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))

    # Calculate and display statistics
    avg_close = np.mean(closes)
    min_close = min(closes)
    max_close = max(closes)
    change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] != 0 else 0

    stats_text = f'Avg: ${avg_close:.2f} | Min: ${min_close:.2f} | Max: ${max_close:.2f} | Change: {change_pct:+.2f}%'
    ax1.annotate(stats_text, xy=(0.5, 0.02), xycoords='axes fraction',
                 ha='center', fontsize=9, style='italic',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Volume chart (bottom)
    colors = ['green' if closes[i] >= opens[i] else 'red' for i in range(len(dates))]
    ax2.bar(dates, volumes, color=colors, alpha=0.7, width=0.8)
    ax2.set_ylabel('Volume', fontsize=11)
    ax2.set_xlabel('Date', fontsize=11)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))
    ax2.grid(True, alpha=0.3, axis='y')

    # Format volume axis
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

    plt.tight_layout()

    # Save chart
    filename = None
    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = REPORTS_DIR / f"weekly_chart_{date_str}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Weekly chart saved to: {filename}")

    if show:
        plt.show()
    else:
        plt.close()

    return str(filename) if filename else None


def generate_weekly_candlestick_chart(weeks_back=1, save=True, show=False):
    """
    Generate a candlestick-style chart for weekly data.

    Args:
        weeks_back: Number of weeks to include
        save: Whether to save the chart
        show: Whether to display the chart

    Returns:
        str: Path to the saved chart file
    """
    ensure_reports_dir()

    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)
    prices = get_prices_for_period(start_date, end_date)

    if not prices:
        print("No price data available")
        return None

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.suptitle('VIP Play Inc (VIPP) - Weekly Candlestick Chart', fontsize=14, fontweight='bold')

    for i, p in enumerate(prices):
        date = datetime.strptime(p["date"], "%Y-%m-%d")
        open_p = p["open"]
        close_p = p["close"]
        high_p = p["high"]
        low_p = p["low"]

        # Determine color
        color = 'green' if close_p >= open_p else 'red'

        # Draw the wick (high-low line)
        ax.plot([i, i], [low_p, high_p], color=color, linewidth=1)

        # Draw the body (open-close rectangle)
        body_bottom = min(open_p, close_p)
        body_height = abs(close_p - open_p)
        rect = plt.Rectangle((i - 0.3, body_bottom), 0.6, body_height,
                              facecolor=color, edgecolor=color, alpha=0.8)
        ax.add_patch(rect)

    # Set x-axis labels
    dates = [datetime.strptime(p["date"], "%Y-%m-%d") for p in prices]
    ax.set_xticks(range(len(prices)))
    ax.set_xticklabels([d.strftime('%b %d') for d in dates], rotation=45, ha='right')

    ax.set_ylabel('Price ($)', fontsize=11)
    ax.set_xlabel('Date', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    filename = None
    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = REPORTS_DIR / f"weekly_candlestick_{date_str}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Weekly candlestick chart saved to: {filename}")

    if show:
        plt.show()
    else:
        plt.close()

    return str(filename) if filename else None


if __name__ == "__main__":
    generate_weekly_chart(weeks_back=1, show=True)
