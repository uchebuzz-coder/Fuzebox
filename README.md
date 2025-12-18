# VIP Play Inc Stock Price Reporting System

A comprehensive stock price reporting tool for VIP Play Inc (VIPP) that generates daily reports and visual charts.

## Features

- **Daily Reports**: Text-based reports with key metrics including open, close, high, low prices and trading volume
- **Weekly Visual Charts**: Price charts with trend lines and volume data
- **Monthly Line Charts**: Line charts with moving averages and statistics
- **Monthly Bar Charts**: Bar charts with up/down day coloring and volume analysis

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Initialize with sample data (90 days)
python main.py init

# Generate all reports
python main.py all
```

## Usage

### Generate Daily Report
```bash
python main.py daily
```

### Generate Weekly Chart
```bash
python main.py weekly
python main.py weekly --weeks 2  # Last 2 weeks
python main.py weekly --candlestick  # Include candlestick chart
```

### Generate Monthly Charts
```bash
python main.py monthly
python main.py monthly --months 3  # Last 3 months
python main.py monthly --combined  # Include combined analysis chart
```

### Generate All Reports
```bash
python main.py all
```

### Add Custom Price Entry
```bash
python main.py add --date 2024-01-15 --open 45.00 --high 46.50 --low 44.25 --close 45.75 --volume 1500000
```

### Check Data Status
```bash
python main.py status
```

## Output

Reports and charts are saved to the `reports/` directory:
- `daily_report_YYYY-MM-DD.txt` - Daily text reports
- `weekly_chart_YYYY-MM-DD.png` - Weekly price charts
- `monthly_line_chart_YYYY-MM-DD.png` - Monthly line charts
- `monthly_bar_chart_YYYY-MM-DD.png` - Monthly bar charts

## Project Structure

```
Fuzebox/
├── main.py              # Main runner script
├── requirements.txt     # Python dependencies
├── README.md           # Documentation
├── src/
│   ├── __init__.py
│   ├── stock_data.py    # Stock data management
│   ├── daily_report.py  # Daily report generator
│   ├── weekly_chart.py  # Weekly chart generator
│   └── monthly_charts.py # Monthly charts generator
├── data/
│   └── vip_play_stock.json  # Stock price data
└── reports/
    └── (generated reports)
```
