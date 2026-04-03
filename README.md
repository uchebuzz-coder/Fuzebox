# Fuzebox

A dual-purpose system:
1. **Legacy stock reporting CLI** — generates text reports and charts for VIP Play Inc (VIPP) stock data
2. **Agent Performance Dashboard** — real-time monitoring and analytics platform for AI agents, built with Streamlit, SQLite, and OpenTelemetry

---

## Quick Start

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Launch the dashboard
streamlit run dashboard_app.py

# Or run the real Claude agent CLI
export ANTHROPIC_API_KEY=sk-ant-...
python run_agent.py demo
```

---

## Agent Performance Dashboard

### Run
```bash
streamlit run dashboard_app.py
```

Opens on [http://localhost:8501](http://localhost:8501) with 7 pages:

| Page | What it shows |
|---|---|
| Overview | KPI cards, cost trend, throughput, agent leaderboard |
| Agent Registry | Registered agents, skills/permissions matrices, **registry routing table** |
| Task Scorecards | Per-agent success rates, group evaluation, task-type breakdown |
| Economic Analysis | ROI calculator, cost by agent/task-type, token usage |
| Performance Metrics | Latency percentiles, completion rates, throughput trend |
| Workflow Traces | Gantt timeline of OTel spans per trace |
| **Market Intelligence** | Stock price history, returns, volume; fetch from Yahoo Finance |

### Load demo data
Click **Load Demo Data** in the sidebar — seeds 30 days of realistic agent workflow history.

### Run real Claude agent tasks
```bash
export ANTHROPIC_API_KEY=sk-ant-...

python run_agent.py demo                        # 5-task demo (all task types)
python run_agent.py generate "Write a BST in Python"
python run_agent.py review src/dashboard/db.py
python run_agent.py debug src/dashboard/db.py "AttributeError: ..."
python run_agent.py research "Python asyncio patterns"
python run_agent.py tests src/dashboard/models.py
```

All tasks are automatically recorded in the dashboard (tokens, latency, cost, quality).

---

## Adding a New Agent

No Python changes required for most agent additions:

1. Copy `agents/claude_opus.yaml` to `agents/<your_agent>.yaml`
2. Edit `agent_id`, `model`, `cost_per_1k_*`, `skills`, `task_types`, and `system_prompts`
3. If you need a **new agent class** (different SDK, different provider):
   - Implement `run_task(task_type, payload) -> str` and `agent_id: str`
   - Add `class_name: YourClass` to the YAML
   - Register the class in `_get_agent_classes()` in `src/dashboard/agent_protocol.py`

The `AgentRegistry` routes task types to agents automatically on startup.

---

## Adding a New Stock Data Source

1. Create `src/market/sources/<your_source>.py`
2. Implement two things:
   - `source_name: str` property
   - `fetch(ticker, start, end) -> list[OHLCV]`
3. Pass an instance to `StockDataService`:
   ```python
   from src.market.service import StockDataService
   from src.market.sources.your_source import YourSource
   svc = StockDataService(source=YourSource())
   svc.fetch_and_store("AAPL", start=..., end=...)
   ```
4. To add new tickers to the dashboard UI, add them to `config/market/tickers.yaml`

---

## Stock Reporting CLI (Legacy)

Stock data is sourced from **RBLX (Roblox Corporation)** via Yahoo Finance and stored under the fictional "VIP Play Inc / VIPP" branding.

### Fetch real data (SQLite — dashboard)
```bash
# Fetches via the new market layer into agent_dashboard.db
# Use the Market Intelligence page in the dashboard, or:
python -c "
from src.market.service import get_stock_service
import datetime
svc = get_stock_service()
svc.fetch_and_store('RBLX', datetime.date(2024,1,1), datetime.date.today())
"
```

### Fetch real data (JSON — legacy CLI reports)
```bash
python fetch_stock.py                              # Last 90 days
python fetch_stock.py --days 365
python fetch_stock.py --start 2024-01-01
python fetch_stock.py --start 2024-01-01 --end 2024-12-31
```

### Generate reports
```bash
python main.py init             # Seed 90 days of mock data
python main.py all              # Generate all reports and charts
python main.py daily
python main.py weekly [--weeks 2] [--candlestick]
python main.py monthly [--months 3] [--combined]
python main.py add --date YYYY-MM-DD --open X --high X --low X --close X --volume X
python main.py status
```

Reports are saved to `reports/`:
- `daily_report_YYYY-MM-DD.txt`
- `weekly_chart_YYYY-MM-DD.png`
- `monthly_line_chart_YYYY-MM-DD.png`
- `monthly_bar_chart_YYYY-MM-DD.png`

---

## Docker

```bash
docker compose up --build                        # Dashboard on port 8501
docker compose --profile util up cli             # CLI utility container
docker build -t fuzebox-dashboard .
docker run --rm -p 8501:8501 \
  -e DASHBOARD_DB_PATH=/data/agent_dashboard.db \
  -v fuzebox-db:/data fuzebox-dashboard
```

---

## Project Structure

```
Fuzebox/
├── main.py                  # Legacy stock reporting CLI
├── fetch_stock.py           # Fetch RBLX → VIP Play Inc JSON store
├── run_agent.py             # Real Claude agent CLI (registry-driven)
├── dashboard_app.py         # Streamlit dashboard entry point
│
├── agents/                  # Per-agent YAML configs (model, pricing, prompts)
│   ├── claude_opus.yaml
│   └── claude_sonnet.yaml
│
├── config/
│   └── market/
│       └── tickers.yaml     # Real ticker → display name mapping
│
├── src/
│   ├── real_agent.py        # ClaudeAgent implementation (AgentProtocol)
│   ├── stock_fetcher.py     # Legacy yfinance → JSON bridge (do not modify)
│   ├── stock_data.py        # Legacy JSON store (do not modify)
│   ├── daily_report.py      # Legacy report generator (do not modify)
│   ├── weekly_chart.py      # Legacy chart generator (do not modify)
│   ├── monthly_charts.py    # Legacy chart generator (do not modify)
│   │
│   ├── dashboard/           # Agent Performance Dashboard modules
│   │   ├── agent_protocol.py  # AgentProtocol, AgentRegistry, YAML loader
│   │   ├── models.py          # Pydantic models + TaskType enum
│   │   ├── db.py              # SQLite CRUD (agents, tasks, spans, workflows, stock_prices)
│   │   ├── config.py          # Pydantic Settings (env vars + defaults)
│   │   ├── tracing.py         # trace_agent_task() + OTel span exporter
│   │   ├── evaluators.py      # Scoring, skills/permissions matrices
│   │   ├── economics.py       # Cost, ROI, token usage
│   │   ├── metrics.py         # Latency percentiles, throughput, leaderboard
│   │   └── app.py             # Streamlit UI (7 pages)
│   │
│   └── market/              # Pluggable stock data layer
│       ├── protocol.py        # OHLCV model + StockSource protocol
│       ├── service.py         # StockDataService facade + get_stock_service()
│       ├── queries.py         # Pure DataFrame query functions
│       └── sources/
│           └── yfinance_source.py  # YFinanceSource (StockSource impl)
│
├── data/                    # Gitignored runtime data
│   ├── vip_play_stock.json  # Legacy JSON store
│   └── agent_dashboard.db   # SQLite (agents, tasks, spans, workflows, stock_prices)
└── reports/                 # Gitignored generated reports and charts
```

---

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required to run real agent tasks |
| `DASHBOARD_DB_PATH` | `data/agent_dashboard.db` | Override SQLite database path |
| `AGENTS_CONFIG_DIR` | `agents/` | Directory containing agent YAML files |
| `MARKET_CONFIG_DIR` | `config/market/` | Directory containing market config files |

---

## Architecture: Pluggable Layers

### Agent layer
```
agents/*.yaml
    → AgentRegistry (agent_protocol.py)
    → AgentProtocol.run_task()
    → trace_agent_task() context manager
    → SQLite via db.py
    → Dashboard (app.py)
```

### Stock data layer
```
StockSource.fetch()      ← YFinanceSource (or any custom source)
    → StockDataService
    → db.upsert_ohlcv_batch()
    → stock_prices table (SQLite)
    → queries.py / service.get_prices()
    → Market Intelligence page (app.py)
```

### What is locked (legacy, do not modify)
`main.py` · `src/stock_data.py` · `src/daily_report.py` · `src/weekly_chart.py` · `src/monthly_charts.py` · `src/stock_fetcher.py`
