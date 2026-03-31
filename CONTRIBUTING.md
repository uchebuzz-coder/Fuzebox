# Contributing to Fuzebox Agent Performance Dashboard

## Quick Start (Get Running in 5 Minutes)

### Prerequisites
- Python 3.11+
- Git
- A terminal

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/lesotto/Fuzebox.git
cd Fuzebox

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run dashboard_app.py
```

The dashboard opens at `http://localhost:8501`. Click **"Load Demo Data"** in the sidebar to populate 30 days of sample agent workflow data.

### Verify It Works

Run the verification script to confirm all modules load and data flows correctly:

```bash
python verify_setup.py
```

You should see output confirming agents, tasks, spans, and workflows were created, plus summary metrics.

---

## Project Structure

```
Fuzebox/
├── main.py                    # Stock reporting CLI (existing, don't modify)
├── dashboard_app.py           # Dashboard entry point: streamlit run dashboard_app.py
├── requirements.txt           # Python dependencies
├── verify_setup.py            # Setup verification script
├── src/
│   ├── __init__.py
│   ├── stock_data.py          # Existing stock reporting (don't modify)
│   ├── daily_report.py        # Existing (don't modify)
│   ├── weekly_chart.py        # Existing (don't modify)
│   ├── monthly_charts.py      # Existing (don't modify)
│   └── dashboard/             # ← ALL DASHBOARD CODE LIVES HERE
│       ├── __init__.py
│       ├── models.py          # Pydantic data models (Agent, Task, Span, Workflow)
│       ├── db.py              # SQLite storage, CRUD operations, demo data seeder
│       ├── tracing.py         # OpenTelemetry integration + custom SQLite exporter
│       ├── evaluators.py      # Task completion scoring, skills/permissions matrices
│       ├── economics.py       # Cost analysis, ROI, token usage, workflow economics
│       ├── metrics.py         # Latency percentiles, throughput, agent leaderboard
│       └── app.py             # Streamlit dashboard UI (6 pages)
└── data/                      # Generated at runtime (gitignored)
    ├── vip_play_stock.json    # Stock data (existing)
    └── agent_dashboard.db     # SQLite database (auto-created)
```

---

## Architecture Overview

### Data Flow

```
Agent Workflow Execution
        │
        ▼
┌─────────────────┐     OpenTelemetry spans auto-recorded
│   tracing.py    │───► to SQLite via DashboardSpanExporter
│ trace_agent_task│───► TaskRecord also written to SQLite
└─────────────────┘
        │
        ▼
┌─────────────────┐
│     db.py       │     SQLite: agents, tasks, spans, workflows
│  (storage)      │     All queries go through this module
└─────────────────┘
        │
        ├──► evaluators.py  (scorecards, skills matrix, violations)
        ├──► economics.py   (costs, ROI, token usage)
        └──► metrics.py     (latency, throughput, leaderboard)
                │
                ▼
        ┌─────────────┐
        │   app.py    │     Streamlit renders 6 pages
        │ (dashboard) │     Uses all modules above for data
        └─────────────┘
```

### Key Data Models (models.py)

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `Agent` | Registered AI agent | skills, permissions, group, cost rates, model name |
| `TaskRecord` | Single task execution | result, latency, tokens, cost, quality score |
| `SpanRecord` | OpenTelemetry trace span | trace_id, parent_span_id, duration, attributes |
| `WorkflowRecord` | Multi-agent workflow | agent_ids, task_ids, total cost, result |

### Dashboard Pages (app.py)

| # | Page | What It Shows |
|---|------|---------------|
| 1 | **Overview** | KPI cards, cost trend chart, throughput chart, leaderboard |
| 2 | **Agent Registry** | Agent table, skills heatmap, permissions matrix, violations |
| 3 | **Task Scorecards** | Pass/fail per agent, group evaluation, success by task type |
| 4 | **Economic Analysis** | ROI calculator, cost by agent/type, token usage, workflow costs |
| 5 | **Performance Metrics** | Completion rates, latency histogram, throughput trend, leaderboard |
| 6 | **Workflow Traces** | Gantt timeline of spans, span detail table, trace selector |

---

## How to Add Features

### Adding a new metric

1. Add the query function in `metrics.py` or `economics.py`
2. It should accept `start_date`/`end_date` filters and return a `dict` or `pd.DataFrame`
3. Render it in the appropriate page in `app.py` using `st.metric()`, `st.dataframe()`, or `st.pyplot()`

### Adding a new agent to demo data

Edit the `agents_def` list in `db.py:seed_demo_data()`. Follow the existing pattern:

```python
Agent(
    agent_id="agent-new-01",
    name="My New Agent",
    skills=["skill_a", "skill_b"],
    permissions=["perm_x", "perm_y"],
    group="my_group",
    cost_per_1k_input=0.003,
    cost_per_1k_output=0.015,
    model_name="claude-sonnet-4-20250514",
)
```

### Integrating a real agent framework

Use the tracing context manager in your agent code:

```python
from src.dashboard.tracing import trace_agent_task

# Register the agent first
from src.dashboard.db import upsert_agent
from src.dashboard.models import Agent
upsert_agent(Agent(agent_id="my-agent", name="My Agent", skills=["code_gen"], permissions=["write"]))

# Then trace tasks
with trace_agent_task("my-agent", "code_generation") as ctx:
    result = my_agent.run(prompt)  # Your agent framework call
    ctx.set_tokens(input_tokens=result.usage.input, output_tokens=result.usage.output)
    ctx.set_result("success" if result.ok else "failure")
    ctx.set_quality(result.score)
```

---

## Coding Standards

- **No changes to existing stock reporting code** (`main.py`, `src/stock_data.py`, etc.)
- All dashboard code goes in `src/dashboard/`
- Use Pydantic models for any new data structures
- Return `pd.DataFrame` from query functions (Streamlit renders them natively)
- Use `matplotlib` for charts (consistent with existing project), rendered via `st.pyplot()`
- Store all persistent data in the SQLite database via `db.py` — no new JSON files
- Keep functions focused: query modules return data, `app.py` handles rendering

## Dependency Management

- Runtime dependencies in `requirements.txt` are pinned (`==`) for reproducible installs.
- Install dependencies with:

```bash
pip install -r requirements.txt
```

- To intentionally update dependencies:
  1. Edit one or more pinned versions in `requirements.txt`
  2. Reinstall in a clean virtual environment
  3. Run `python verify_setup.py`
  4. Run a dashboard smoke test: `streamlit run dashboard_app.py`
  5. Commit only after verification passes

## Configuration reference

Environment variables override defaults at process startup (no config file is required).

| Variable | Default | Purpose |
|----------|---------|---------|
| `DASHBOARD_DB_PATH` | `<repo root>/data/agent_dashboard.db` | SQLite database file. If set, the path is expanded (`~`) and resolved relative to the **current working directory** when not absolute. The parent directory is created automatically when the app connects. |

The same codebase supports local venv installs, containers, and hosted platforms: set variables in the shell, in your host’s UI (for example Streamlit Cloud secrets), or with `docker run -e`.

## Deployment Notes

### Local or on-premises (virtualenv)

Use the [Quick Start](#quick-start-get-running-in-5-minutes) steps. Optionally export `DASHBOARD_DB_PATH` before `streamlit run` if the database should live outside the repo tree.

### Streamlit Cloud (hosted)

- Set **Main file path** to `dashboard_app.py`.
- Dependencies come from `requirements.txt` (pinned versions).
- If the default database path is not writable or you need a fixed location, add `DASHBOARD_DB_PATH` in **Secrets** / environment settings using the same value you would use locally (absolute path recommended on the host).

### Docker

The canonical image definition is [`Dockerfile`](Dockerfile) at the repository root (layer-cached `pip install`, then application copy). Build and run:

```bash
docker build -t fuzebox-dashboard .
docker run --rm -p 8501:8501 \
  -e DASHBOARD_DB_PATH=/data/agent_dashboard.db \
  -v fuzebox-db:/data \
  fuzebox-dashboard
```

The dashboard is available at `http://localhost:8501`. The named volume `fuzebox-db` keeps the SQLite file across container restarts. For a bind mount instead: `-v /path/on/host:/data`.

`.dockerignore` excludes local `venv/`, `data/`, and similar paths so the image stays small and does not embed your development database.

---

## Questions?

Reach out to the project owner for architecture decisions or priority calls. When in doubt, keep it simple — we're building a POV, not a production system.
