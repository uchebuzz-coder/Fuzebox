#!/usr/bin/env python3
"""
VIP Play Inc Stock Price Reporting System
==========================================

A comprehensive stock price reporting tool that generates:
- Daily text-based reports
- Weekly visual charts
- Monthly line charts and bar charts

Usage:
    python main.py [command] [options]

Commands:
    daily       Generate daily stock price report
    weekly      Generate weekly visual chart
    monthly     Generate monthly charts (line and bar)
    all         Generate all reports and charts
    init        Initialize with sample data
    add         Add a new daily price entry
"""

import argparse
import sys
from datetime import datetime

from src.stock_data import generate_sample_data, add_daily_price, get_latest_price, load_stock_data
from src.daily_report import generate_daily_report, save_daily_report, print_daily_report
from src.weekly_chart import generate_weekly_chart, generate_weekly_candlestick_chart
from src.monthly_charts import (
    generate_monthly_line_chart,
    generate_monthly_bar_chart,
    generate_monthly_combined_chart
)


def cmd_daily(args):
    """Generate daily stock price report."""
    print("\n" + "="*60)
    print("       GENERATING DAILY REPORT - VIP PLAY INC")
    print("="*60)

    if args.save:
        filename, report = save_daily_report()
        print(report)
    else:
        print_daily_report()


def cmd_weekly(args):
    """Generate weekly visual chart."""
    print("\n" + "="*60)
    print("       GENERATING WEEKLY CHART - VIP PLAY INC")
    print("="*60)

    weeks = args.weeks if hasattr(args, 'weeks') else 1

    # Generate standard weekly chart
    filename = generate_weekly_chart(weeks_back=weeks, save=True, show=args.show)

    if args.candlestick:
        # Also generate candlestick chart
        generate_weekly_candlestick_chart(weeks_back=weeks, save=True, show=args.show)

    if filename:
        print(f"\nWeekly chart generated successfully!")


def cmd_monthly(args):
    """Generate monthly charts (line and bar)."""
    print("\n" + "="*60)
    print("       GENERATING MONTHLY CHARTS - VIP PLAY INC")
    print("="*60)

    months = args.months if hasattr(args, 'months') else 1

    # Generate line chart
    print("\nGenerating monthly line chart...")
    line_file = generate_monthly_line_chart(months_back=months, save=True, show=args.show)

    # Generate bar chart
    print("\nGenerating monthly bar chart...")
    bar_file = generate_monthly_bar_chart(months_back=months, save=True, show=args.show)

    if args.combined:
        # Also generate combined chart
        print("\nGenerating monthly combined chart...")
        generate_monthly_combined_chart(months_back=months, save=True, show=args.show)

    print("\nMonthly charts generated successfully!")


def cmd_all(args):
    """Generate all reports and charts."""
    print("\n" + "="*60)
    print("   GENERATING ALL REPORTS & CHARTS - VIP PLAY INC")
    print("="*60)

    # Daily report
    print("\n[1/4] Generating daily report...")
    save_daily_report()

    # Weekly chart
    print("\n[2/4] Generating weekly chart...")
    generate_weekly_chart(weeks_back=1, save=True, show=False)

    # Monthly line chart
    print("\n[3/4] Generating monthly line chart...")
    generate_monthly_line_chart(months_back=1, save=True, show=False)

    # Monthly bar chart
    print("\n[4/4] Generating monthly bar chart...")
    generate_monthly_bar_chart(months_back=1, save=True, show=False)

    print("\n" + "="*60)
    print("         ALL REPORTS GENERATED SUCCESSFULLY!")
    print("="*60)
    print("\nFiles saved to the 'reports' directory.")


def cmd_init(args):
    """Initialize with sample data."""
    print("\n" + "="*60)
    print("   INITIALIZING SAMPLE DATA - VIP PLAY INC")
    print("="*60)

    days = args.days if hasattr(args, 'days') else 90
    generate_sample_data(days=days)

    # Show current data summary
    data = load_stock_data()
    print(f"\nData Summary:")
    print(f"  Company: {data['company']}")
    print(f"  Ticker:  {data['ticker']}")
    print(f"  Records: {len(data['prices'])} trading days")

    if data['prices']:
        latest = data['prices'][-1]
        oldest = data['prices'][0]
        print(f"  Period:  {oldest['date']} to {latest['date']}")
        print(f"  Latest Close: ${latest['close']:.2f}")


def cmd_add(args):
    """Add a new daily price entry."""
    print("\n" + "="*60)
    print("   ADDING NEW PRICE ENTRY - VIP PLAY INC")
    print("="*60)

    date = args.date if args.date else datetime.now().strftime("%Y-%m-%d")

    add_daily_price(
        date=date,
        open_price=args.open,
        high=args.high,
        low=args.low,
        close=args.close,
        volume=args.volume
    )

    print(f"\nAdded price entry for {date}:")
    print(f"  Open:   ${args.open:.2f}")
    print(f"  High:   ${args.high:.2f}")
    print(f"  Low:    ${args.low:.2f}")
    print(f"  Close:  ${args.close:.2f}")
    print(f"  Volume: {args.volume:,}")


def cmd_status(args):
    """Show current data status."""
    data = load_stock_data()

    print("\n" + "="*60)
    print("       VIP PLAY INC - DATA STATUS")
    print("="*60)

    print(f"\nCompany: {data['company']}")
    print(f"Ticker:  {data['ticker']}")
    print(f"Records: {len(data['prices'])} trading days")

    if data['prices']:
        latest = data['prices'][-1]
        oldest = data['prices'][0]
        print(f"\nData Period: {oldest['date']} to {latest['date']}")
        print(f"\nLatest Price ({latest['date']}):")
        print(f"  Open:   ${latest['open']:.2f}")
        print(f"  High:   ${latest['high']:.2f}")
        print(f"  Low:    ${latest['low']:.2f}")
        print(f"  Close:  ${latest['close']:.2f}")
        print(f"  Volume: {latest['volume']:,}")
    else:
        print("\nNo price data available. Run 'python main.py init' to generate sample data.")


def main():
    parser = argparse.ArgumentParser(
        description='VIP Play Inc Stock Price Reporting System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py init              # Initialize with 90 days of sample data
  python main.py init --days 180   # Initialize with 180 days of sample data
  python main.py daily             # Generate daily report
  python main.py weekly            # Generate weekly chart
  python main.py monthly           # Generate monthly line and bar charts
  python main.py all               # Generate all reports and charts
  python main.py status            # Show current data status

  # Add a custom price entry:
  python main.py add --date 2024-01-15 --open 45.00 --high 46.50 --low 44.25 --close 45.75 --volume 1500000
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Daily report command
    daily_parser = subparsers.add_parser('daily', help='Generate daily stock price report')
    daily_parser.add_argument('--save', action='store_true', default=True,
                              help='Save report to file (default: True)')
    daily_parser.set_defaults(func=cmd_daily)

    # Weekly chart command
    weekly_parser = subparsers.add_parser('weekly', help='Generate weekly visual chart')
    weekly_parser.add_argument('--weeks', type=int, default=1,
                               help='Number of weeks to include (default: 1)')
    weekly_parser.add_argument('--show', action='store_true',
                               help='Display chart in window')
    weekly_parser.add_argument('--candlestick', action='store_true',
                               help='Also generate candlestick chart')
    weekly_parser.set_defaults(func=cmd_weekly)

    # Monthly charts command
    monthly_parser = subparsers.add_parser('monthly', help='Generate monthly charts')
    monthly_parser.add_argument('--months', type=int, default=1,
                                help='Number of months to include (default: 1)')
    monthly_parser.add_argument('--show', action='store_true',
                                help='Display charts in window')
    monthly_parser.add_argument('--combined', action='store_true',
                                help='Also generate combined analysis chart')
    monthly_parser.set_defaults(func=cmd_monthly)

    # All reports command
    all_parser = subparsers.add_parser('all', help='Generate all reports and charts')
    all_parser.set_defaults(func=cmd_all)

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize with sample data')
    init_parser.add_argument('--days', type=int, default=90,
                             help='Number of days of sample data (default: 90)')
    init_parser.set_defaults(func=cmd_init)

    # Add price command
    add_parser = subparsers.add_parser('add', help='Add a new daily price entry')
    add_parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD), defaults to today')
    add_parser.add_argument('--open', type=float, required=True, help='Opening price')
    add_parser.add_argument('--high', type=float, required=True, help='High price')
    add_parser.add_argument('--low', type=float, required=True, help='Low price')
    add_parser.add_argument('--close', type=float, required=True, help='Closing price')
    add_parser.add_argument('--volume', type=int, required=True, help='Trading volume')
    add_parser.set_defaults(func=cmd_add)

    # Status command
    status_parser = subparsers.add_parser('status', help='Show current data status')
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if args.command is None:
        # Default behavior: show help
        parser.print_help()
        print("\n" + "-"*60)
        print("Quick Start:")
        print("  1. Run 'python main.py init' to generate sample data")
        print("  2. Run 'python main.py all' to generate all reports")
        print("-"*60)
        return

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
