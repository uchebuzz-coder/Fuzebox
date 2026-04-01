# Fuzebox V1 — Production Multi-Agent Pipeline

Sequential 3-agent pipeline using real LLM calls, full telemetry, and a live FastAPI endpoint.

```
input → Intake Classifier → Triage Scorer → Response Drafter → output
```

---

## Architecture

| Layer | Files | Purpose |
|---|---|---|
| **Agents** | `agents/` | 3 modular LangChain agents |
| **Pipeline** | `pipeline/pipeline.py` | Sequential orchestration |
| **Telemetry** | `telemetry/logger.py` | Per-call logging → SQLite |
| **API** | `api/main.py` | FastAPI endpoint |
| **Tests** | `tests/run_v1_tests.py` | 13-case test harness |

### Agent Specifications

**Agent 1 — Intake Classifier** (`agents/classifier.py`)
```json
{ "classification": "billing|technical|account|general|urgent", "confidence": 0.0–1.0 }
```

**Agent 2 — Triage Scorer** (`agents/triage.py`)
```json
{ "priority": 1–5, "rationale": "string" }
```

**Agent 3 — Response Drafter** (`agents/responder.py`)
```json
{ "response": "string", "sentiment": "positive|neutral|empathetic" }
```

### Telemetry Fields (logged per agent call)

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO string | When the call completed |
| `agent_id` | string | Which agent ran |
| `task_type` | string | classification / triage / response_drafting |
| `input_tokens` | int | Tokens in the prompt |
| `output_tokens` | int | Tokens in the response |
| `latency_ms` | float | Wall-clock time for the LLM call |
| `completion_status` | string | success / failure |
| `escalation_flag` | bool | True if urgent or priority ≥ 4 |
| `auop_score` | float | Agent Unit of Productivity = 1/total_tokens (if success) |

**AUoP definition:** `successful_output / total_tokens_used`
- `successful_output` = 1 if the agent completed successfully, 0 otherwise.
- Higher AUoP = more productivity per token consumed.

### Derived Metrics (computed from logs, never hardcoded)

- `completion_rate` — fraction of successful agent calls
- `avg_latency_ms` — mean latency across all calls
- `escalation_rate` — fraction of calls that triggered escalation
- `avg_auop` — mean AUoP per agent / across pipeline

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure LLM credentials

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

To use Anthropic instead:
```bash
# In .env:
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

### 3. Run the test harness (13 real test cases)

```bash
python tests/run_v1_tests.py
```

This will:
- Call real LLM APIs for all 3 agents × 13 cases = 39 LLM calls
- Store all outputs + telemetry in `data/agent_dashboard.db`
- Print a summary table + save `tests/v1_test_report.json`

### 4. Start the API server

```bash
uvicorn api.main:app --reload --port 8000
```

### 5. Test the endpoint

```bash
curl -X POST http://localhost:8000/v1/process \
  -H "Content-Type: application/json" \
  -d '{"input": "I was charged twice for my subscription this month."}'
```

### 6. View metrics

```bash
curl http://localhost:8000/v1/metrics
# or filter by agent:
curl "http://localhost:8000/v1/metrics?agent_id=v1-classifier-01"
```

---

## Expose via Public URL (ngrok)

```bash
# Install ngrok: https://ngrok.com/download
# Start the API first (step 4 above), then:
ngrok http 8000
```

ngrok will output a public URL like `https://abc123.ngrok-free.app`.

```bash
curl -X POST https://abc123.ngrok-free.app/v1/process \
  -H "Content-Type: application/json" \
  -d '{"input": "Our entire database just went offline."}'
```

---

## File Structure

```
agents/
├── __init__.py
├── _base.py          # LLM factory (OpenAI / Anthropic)
├── classifier.py     # Agent 1: Intake Classifier
├── triage.py         # Agent 2: Triage Scorer
└── responder.py      # Agent 3: Response Drafter

pipeline/
├── __init__.py
└── pipeline.py       # Sequential orchestration + telemetry wiring

api/
├── __init__.py
└── main.py           # FastAPI: POST /v1/process, GET /v1/metrics

telemetry/
├── __init__.py
└── logger.py         # TelemetryLogger, AUoP, metrics computation

tests/
└── run_v1_tests.py   # 13 realistic test cases

data/
└── agent_dashboard.db  # SQLite — all telemetry lives here
```

---

## API Reference

### `POST /v1/process`

**Request:**
```json
{
  "input": "Customer request text",
  "workflow_id": "optional-custom-id"
}
```

**Response:**
```json
{
  "workflow_id": "abc123",
  "classification": { "classification": "billing", "confidence": 0.95 },
  "triage":         { "priority": 3, "rationale": "..." },
  "response":       { "response": "...", "sentiment": "empathetic" },
  "escalation_flag": false,
  "telemetry": [ {...}, {...}, {...} ],
  "total_input_tokens": 1240,
  "total_output_tokens": 380,
  "total_cost_usd": 0.000413,
  "pipeline_success": true
}
```

### `GET /v1/metrics`

Returns computed metrics from real telemetry logs:

```json
{
  "total_tasks": 39,
  "completion_rate": 1.0,
  "avg_latency_ms": 1823.4,
  "escalation_rate": 0.154,
  "avg_auop": 0.00000612,
  "per_agent": {
    "v1-classifier-01": { ... },
    "v1-triage-01":     { ... },
    "v1-responder-01":  { ... }
  }
}
```

---

## Viewing Telemetry in the Dashboard

The telemetry is stored in the same SQLite DB as the existing Streamlit dashboard.

```bash
streamlit run dashboard_app.py
```

V1 pipeline agents appear in the dashboard under the `v1_pipeline` group.

---

## Success Criteria

- [x] Real LLM outputs (no mocked data)
- [x] Telemetry logged per agent call (timestamp, tokens, latency, AUoP, escalation)
- [x] 13 test runs with varied inputs
- [x] Metrics computed from real logs (`/v1/metrics`)
- [x] API accessible via `POST /v1/process`
- [x] SQLite storage (reuses existing `data/agent_dashboard.db`)
- [x] Deployable locally + exposable via ngrok
