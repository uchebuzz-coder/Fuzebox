"""
Monthly chart generators for VIP Play Inc stock prices.
Creates both line charts and bar charts for monthly data.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

from .stock_data import get_monthly_prices, load_stock_data, get_prices_for_period


REPORTS_DIR = Path(__file__).parent.parent / "reports"


def ensure_reports_dir():
    """Ensure the reports directory exists."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_monthly_line_chart(months_back=1, save=True, show=False):
    """
    Generate a line chart for monthly stock prices.

    Args:
        months_back: Number of months to include
        save: Whether to save the chart
        show: Whether to display the chart

    Returns:
        str: Path to the saved chart file
    """
    ensure_reports_dir()

    # Get price data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    prices = get_prices_for_period(start_date, end_date)

    if not prices:
        print("No price data available for the specified period")
        return None

    # Extract data
    dates = [datetime.strptime(p["date"], "%Y-%m-%d") for p in prices]
    closes = [p["close"] for p in prices]
    highs = [p["high"] for p in prices]
    lows = [p["low"] for p in prices]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.suptitle('VIP Play Inc (VIPP) - Monthly Stock Price (Line Chart)',
                 fontsize=14, fontweight='bold')

    # Plot the data
    ax.fill_between(dates, lows, highs, alpha=0.2, color='blue', label='Daily Range')
    ax.plot(dates, closes, 'b-', linewidth=2, label='Closing Price', marker='o', markersize=3)

    # Add moving averages
    if len(closes) >= 5:
        ma5 = np.convolve(closes, np.ones(5)/5, mode='valid')
        ma5_dates = dates[4:]
        ax.plot(ma5_dates, ma5, 'orange', linewidth=1.5, linestyle='--', label='5-Day MA')

    if len(closes) >= 10:
        ma10 = np.convolve(closes, np.ones(10)/10, mode='valid')
        ma10_dates = dates[9:]
        ax.plot(ma10_dates, ma10, 'green', linewidth=1.5, linestyle='-.', label='10-Day MA')

    # Add trend line
    if len(dates) > 1:
        z = np.polyfit(range(len(closes)), closes, 1)
        p = np.poly1d(z)
        ax.plot(dates, p(range(len(closes))), 'r--', linewidth=2, alpha=0.7, label='Trend Line')

    # Calculate statistics
    avg_price = np.mean(closes)
    min_price = min(closes)
    max_price = max(closes)
    volatility = np.std(closes)
    total_change = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] != 0 else 0

    # Add statistics annotation
    stats_text = (f'Period: {start_date.strftime("%b %d")} - {end_date.strftime("%b %d, %Y")}\n'
                  f'Average: ${avg_price:.2f} | Min: ${min_price:.2f} | Max: ${max_price:.2f}\n'
                  f'Volatility (StdDev): ${volatility:.2f} | Total Change: {total_change:+.2f}%')

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)

    # Formatting
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Price ($)', fontsize=11)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save chart
    filename = None
    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = REPORTS_DIR / f"monthly_line_chart_{date_str}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Monthly line chart saved to: {filename}")

    if show:
        plt.show()
    else:
        plt.close()

    return str(filename) if filename else None


def generate_monthly_bar_chart(months_back=1, save=True, show=False):
    """
    Generate a bar chart for monthly stock prices.
    Shows daily closing prices as bars with color coding for up/down days.

    Args:
        months_back: Number of months to include
        save: Whether to save the chart
        show: Whether to display the chart

    Returns:
        str: Path to the saved chart file
    """
    ensure_reports_dir()

    # Get price data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    prices = get_prices_for_period(start_date, end_date)

    if not prices:
        print("No price data available for the specified period")
        return None

    # Extract data
    dates = [datetime.strptime(p["date"], "%Y-%m-%d") for p in prices]
    closes = [p["close"] for p in prices]
    opens = [p["open"] for p in prices]
    volumes = [p["volume"] for p in prices]

    # Determine colors (green for up days, red for down days)
    colors = ['#2ecc71' if closes[i] >= opens[i] else '#e74c3c' for i in range(len(prices))]

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), height_ratios=[2, 1])
    fig.suptitle('VIP Play Inc (VIPP) - Monthly Stock Price (Bar Chart)',
                 fontsize=14, fontweight='bold')

    # Price bar chart (top)
    bars = ax1.bar(range(len(dates)), closes, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

    # Add average line
    avg_price = np.mean(closes)
    ax1.axhline(y=avg_price, color='blue', linestyle='--', linewidth=2,
                label=f'Average: ${avg_price:.2f}')

    # Add min/max markers
    min_idx = closes.index(min(closes))
    max_idx = closes.index(max(closes))
    ax1.annotate(f'Min: ${min(closes):.2f}', xy=(min_idx, min(closes)),
                 xytext=(min_idx, min(closes) * 0.95),
                 ha='center', fontsize=9, color='red',
                 arrowprops=dict(arrowstyle='->', color='red', lw=1))
    ax1.annotate(f'Max: ${max(closes):.2f}', xy=(max_idx, max(closes)),
                 xytext=(max_idx, max(closes) * 1.05),
                 ha='center', fontsize=9, color='green',
                 arrowprops=dict(arrowstyle='->', color='green', lw=1))

    # Set x-axis labels (show every few days to avoid crowding)
    step = max(1, len(dates) // 15)
    ax1.set_xticks(range(0, len(dates), step))
    ax1.set_xticklabels([dates[i].strftime('%b %d') for i in range(0, len(dates), step)],
                        rotation=45, ha='right')

    ax1.set_ylabel('Closing Price ($)', fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y')

    # Calculate statistics
    up_days = sum(1 for i in range(len(prices)) if closes[i] >= opens[i])
    down_days = len(prices) - up_days
    total_change = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] != 0 else 0

    stats_text = (f'Up Days: {up_days} ({up_days/len(prices)*100:.1f}%) | '
                  f'Down Days: {down_days} ({down_days/len(prices)*100:.1f}%) | '
                  f'Period Change: {total_change:+.2f}%')
    ax1.set_title(stats_text, fontsize=10, style='italic', pad=10)

    # Volume bar chart (bottom)
    ax2.bar(range(len(dates)), volumes, color=colors, alpha=0.6, edgecolor='none')
    ax2.set_xticks(range(0, len(dates), step))
    ax2.set_xticklabels([dates[i].strftime('%b %d') for i in range(0, len(dates), step)],
                        rotation=45, ha='right')
    ax2.set_ylabel('Volume', fontsize=11)
    ax2.set_xlabel('Date', fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

    # Add average volume line
    avg_volume = np.mean(volumes)
    ax2.axhline(y=avg_volume, color='blue', linestyle='--', linewidth=1.5,
                label=f'Avg Volume: {avg_volume/1e6:.2f}M')
    ax2.legend(loc='upper right')

    plt.tight_layout()

    # Save chart
    filename = None
    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = REPORTS_DIR / f"monthly_bar_chart_{date_str}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Monthly bar chart saved to: {filename}")

    if show:
        plt.show()
    else:
        plt.close()

    return str(filename) if filename else None


def generate_monthly_combined_chart(months_back=1, save=True, show=False):
    """
    Generate a combined chart showing both line and bar elements for monthly data.

    Args:
        months_back: Number of months to include
        save: Whether to save the chart
        show: Whether to display the chart

    Returns:
        str: Path to the saved chart file
    """
    ensure_reports_dir()

    # Get price data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    prices = get_prices_for_period(start_date, end_date)

    if not prices:
        print("No price data available for the specified period")
        return None

    # Extract data
    dates = [datetime.strptime(p["date"], "%Y-%m-%d") for p in prices]
    closes = [p["close"] for p in prices]
    opens = [p["open"] for p in prices]
    highs = [p["high"] for p in prices]
    lows = [p["low"] for p in prices]
    volumes = [p["volume"] for p in prices]

    # Create figure with gridspec for flexible layout
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 0.5], hspace=0.3, wspace=0.2)

    fig.suptitle('VIP Play Inc (VIPP) - Monthly Combined Analysis',
                 fontsize=16, fontweight='bold', y=0.98)

    # Line chart (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.fill_between(range(len(dates)), lows, highs, alpha=0.2, color='blue')
    ax1.plot(range(len(dates)), closes, 'b-', linewidth=2, marker='o', markersize=2, label='Close')
    ax1.set_title('Price Line Chart', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Price ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    step = max(1, len(dates) // 10)
    ax1.set_xticks(range(0, len(dates), step))
    ax1.set_xticklabels([dates[i].strftime('%b %d') for i in range(0, len(dates), step)],
                        rotation=45, ha='right', fontsize=8)

    # Bar chart (top right)
    ax2 = fig.add_subplot(gs[0, 1])
    colors = ['#2ecc71' if closes[i] >= opens[i] else '#e74c3c' for i in range(len(prices))]
    ax2.bar(range(len(dates)), closes, color=colors, alpha=0.8)
    ax2.axhline(y=np.mean(closes), color='blue', linestyle='--', linewidth=1.5, label='Average')
    ax2.set_title('Price Bar Chart', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Price ($)')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(range(0, len(dates), step))
    ax2.set_xticklabels([dates[i].strftime('%b %d') for i in range(0, len(dates), step)],
                        rotation=45, ha='right', fontsize=8)

    # Volume chart (middle, spanning both columns)
    ax3 = fig.add_subplot(gs[1, :])
    ax3.bar(range(len(dates)), volumes, color=colors, alpha=0.6)
    ax3.axhline(y=np.mean(volumes), color='blue', linestyle='--', linewidth=1)
    ax3.set_title('Trading Volume', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Volume')
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_xticks(range(0, len(dates), step))
    ax3.set_xticklabels([dates[i].strftime('%b %d') for i in range(0, len(dates), step)],
                        rotation=45, ha='right', fontsize=8)

    # Statistics panel (bottom, spanning both columns)
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')

    # Calculate comprehensive statistics
    avg_price = np.mean(closes)
    min_price = min(closes)
    max_price = max(closes)
    volatility = np.std(closes)
    total_change = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] != 0 else 0
    avg_volume = np.mean(volumes)
    up_days = sum(1 for i in range(len(prices)) if closes[i] >= opens[i])
    down_days = len(prices) - up_days

    stats = (
        f"{'='*80}\n"
        f"SUMMARY STATISTICS\n"
        f"{'='*80}\n"
        f"Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')} ({len(prices)} trading days)\n\n"
        f"Price Statistics:                          Volume Statistics:\n"
        f"  Start Price:  ${closes[0]:.2f}                    Avg Daily Volume: {avg_volume/1e6:.2f}M\n"
        f"  End Price:    ${closes[-1]:.2f}                    Total Volume: {sum(volumes)/1e6:.2f}M\n"
        f"  Average:      ${avg_price:.2f}\n"
        f"  Min:          ${min_price:.2f}                   Trading Days:\n"
        f"  Max:          ${max_price:.2f}                     Up Days: {up_days} ({up_days/len(prices)*100:.1f}%)\n"
        f"  Volatility:   ${volatility:.2f}                    Down Days: {down_days} ({down_days/len(prices)*100:.1f}%)\n"
        f"  Total Change: {total_change:+.2f}%\n"
        f"{'='*80}"
    )
    ax4.text(0.5, 0.5, stats, transform=ax4.transAxes, fontsize=9,
             verticalalignment='center', horizontalalignment='center',
             family='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()

    # Save chart
    filename = None
    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = REPORTS_DIR / f"monthly_combined_chart_{date_str}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Monthly combined chart saved to: {filename}")

    if show:
        plt.show()
    else:
        plt.close()

    return str(filename) if filename else None


if __name__ == "__main__":
    generate_monthly_line_chart(months_back=1, show=True)
    generate_monthly_bar_chart(months_back=1, show=True)
