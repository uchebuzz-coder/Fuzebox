"""SQLite storage layer for the Agent Performance Dashboard."""

import json
import sqlite3
import uuid
import random
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

from .config import get_dashboard_db_path
from .models import Agent, AgentStatus, TaskRecord, TaskResult, SpanRecord, WorkflowRecord

DB_PATH = get_dashboard_db_path()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    skills TEXT DEFAULT '[]',
    permissions TEXT DEFAULT '[]',
    "group" TEXT DEFAULT 'default',
    status TEXT DEFAULT 'active',
    cost_per_1k_input REAL DEFAULT 0.003,
    cost_per_1k_output REAL DEFAULT 0.015,
    model_name TEXT DEFAULT 'gpt-4',
    registered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    workflow_id TEXT,
    task_type TEXT NOT NULL,
    description TEXT DEFAULT '',
    required_skills TEXT DEFAULT '[]',
    required_permissions TEXT DEFAULT '[]',
    result TEXT NOT NULL DEFAULT 'success',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    latency_ms REAL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    quality_score REAL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    parent_span_id TEXT,
    agent_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_ms REAL,
    status TEXT DEFAULT 'OK',
    attributes TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    agent_ids TEXT DEFAULT '[]',
    task_ids TEXT DEFAULT '[]',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    result TEXT DEFAULT 'success',
    total_cost_usd REAL DEFAULT 0.0,
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_started ON tasks(started_at);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_agent ON spans(agent_id);
CREATE INDEX IF NOT EXISTS idx_workflows_started ON workflows(started_at);
"""


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)


# ---- Agent CRUD ----

def upsert_agent(agent: Agent):
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO agents
               (agent_id, name, description, skills, permissions, "group", status,
                cost_per_1k_input, cost_per_1k_output, model_name, registered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (agent.agent_id, agent.name, agent.description,
             json.dumps(agent.skills), json.dumps(agent.permissions),
             agent.group, agent.status.value,
             agent.cost_per_1k_input, agent.cost_per_1k_output,
             agent.model_name, agent.registered_at.isoformat())
        )


def get_agent(agent_id: str) -> Optional[Agent]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()
    if not row:
        return None
    return _row_to_agent(row)


def get_all_agents() -> list[Agent]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM agents ORDER BY name").fetchall()
    return [_row_to_agent(r) for r in rows]


def get_agents_by_group(group: str) -> list[Agent]:
    with get_connection() as conn:
        rows = conn.execute('SELECT * FROM agents WHERE "group" = ? ORDER BY name', (group,)).fetchall()
    return [_row_to_agent(r) for r in rows]


def _row_to_agent(row) -> Agent:
    return Agent(
        agent_id=row["agent_id"], name=row["name"], description=row["description"],
        skills=json.loads(row["skills"]), permissions=json.loads(row["permissions"]),
        group=row["group"], status=AgentStatus(row["status"]),
        cost_per_1k_input=row["cost_per_1k_input"],
        cost_per_1k_output=row["cost_per_1k_output"],
        model_name=row["model_name"],
        registered_at=datetime.fromisoformat(row["registered_at"])
    )


# ---- Task CRUD ----

def insert_task(task: TaskRecord):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO tasks
               (task_id, agent_id, workflow_id, task_type, description,
                required_skills, required_permissions, result, started_at, completed_at,
                latency_ms, input_tokens, output_tokens, total_tokens,
                cost_usd, quality_score, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.task_id, task.agent_id, task.workflow_id, task.task_type,
             task.description, json.dumps(task.required_skills),
             json.dumps(task.required_permissions),
             task.result.value, task.started_at.isoformat(),
             task.completed_at.isoformat() if task.completed_at else None,
             task.latency_ms, task.input_tokens, task.output_tokens, task.total_tokens,
             task.cost_usd, task.quality_score, json.dumps(task.metadata))
        )


def get_tasks(agent_id: Optional[str] = None, task_type: Optional[str] = None,
              start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
              workflow_id: Optional[str] = None) -> list[TaskRecord]:
    clauses, params = [], []
    if agent_id:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    if task_type:
        clauses.append("task_type = ?")
        params.append(task_type)
    if workflow_id:
        clauses.append("workflow_id = ?")
        params.append(workflow_id)
    if start_date:
        clauses.append("started_at >= ?")
        params.append(start_date.isoformat())
    if end_date:
        clauses.append("started_at <= ?")
        params.append(end_date.isoformat())

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM tasks{where} ORDER BY started_at DESC", params).fetchall()
    return [_row_to_task(r) for r in rows]


def _row_to_task(row) -> TaskRecord:
    return TaskRecord(
        task_id=row["task_id"], agent_id=row["agent_id"],
        workflow_id=row["workflow_id"], task_type=row["task_type"],
        description=row["description"],
        required_skills=json.loads(row["required_skills"]),
        required_permissions=json.loads(row["required_permissions"]),
        result=TaskResult(row["result"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        latency_ms=row["latency_ms"], input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"], total_tokens=row["total_tokens"],
        cost_usd=row["cost_usd"], quality_score=row["quality_score"],
        metadata=json.loads(row["metadata"])
    )


# ---- Span CRUD ----

def insert_span(span: SpanRecord):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO spans
               (span_id, trace_id, parent_span_id, agent_id, operation,
                started_at, ended_at, duration_ms, status, attributes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (span.span_id, span.trace_id, span.parent_span_id,
             span.agent_id, span.operation, span.started_at.isoformat(),
             span.ended_at.isoformat() if span.ended_at else None,
             span.duration_ms, span.status, json.dumps(span.attributes))
        )


def get_spans(trace_id: Optional[str] = None, agent_id: Optional[str] = None) -> list[SpanRecord]:
    clauses, params = [], []
    if trace_id:
        clauses.append("trace_id = ?")
        params.append(trace_id)
    if agent_id:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM spans{where} ORDER BY started_at", params).fetchall()
    return [_row_to_span(r) for r in rows]


def get_unique_trace_ids(limit: int = 50) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT trace_id FROM spans ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [r["trace_id"] for r in rows]


def _row_to_span(row) -> SpanRecord:
    return SpanRecord(
        span_id=row["span_id"], trace_id=row["trace_id"],
        parent_span_id=row["parent_span_id"], agent_id=row["agent_id"],
        operation=row["operation"],
        started_at=datetime.fromisoformat(row["started_at"]),
        ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
        duration_ms=row["duration_ms"], status=row["status"],
        attributes=json.loads(row["attributes"])
    )


# ---- Workflow CRUD ----

def insert_workflow(wf: WorkflowRecord):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO workflows
               (workflow_id, name, description, agent_ids, task_ids,
                started_at, completed_at, result, total_cost_usd, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (wf.workflow_id, wf.name, wf.description,
             json.dumps(wf.agent_ids), json.dumps(wf.task_ids),
             wf.started_at.isoformat(),
             wf.completed_at.isoformat() if wf.completed_at else None,
             wf.result.value, wf.total_cost_usd, json.dumps(wf.metadata))
        )


def get_workflows(start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> list[WorkflowRecord]:
    clauses, params = [], []
    if start_date:
        clauses.append("started_at >= ?")
        params.append(start_date.isoformat())
    if end_date:
        clauses.append("started_at <= ?")
        params.append(end_date.isoformat())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM workflows{where} ORDER BY started_at DESC", params).fetchall()
    return [_row_to_workflow(r) for r in rows]


def _row_to_workflow(row) -> WorkflowRecord:
    return WorkflowRecord(
        workflow_id=row["workflow_id"], name=row["name"],
        description=row["description"],
        agent_ids=json.loads(row["agent_ids"]),
        task_ids=json.loads(row["task_ids"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        result=TaskResult(row["result"]),
        total_cost_usd=row["total_cost_usd"],
        metadata=json.loads(row["metadata"])
    )


# ---- Demo Data Seeder ----

def seed_demo_data():
    """Populate the database with realistic demo agent workflow data."""
    init_db()

    agents_def = [
        Agent(agent_id="agent-coder-01", name="CodeGen Alpha",
              description="Primary code generation agent",
              skills=["code_generation", "code_review", "refactoring", "testing"],
              permissions=["read_repo", "write_files", "run_tests", "create_pr"],
              group="engineering", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.003, cost_per_1k_output=0.015, model_name="claude-sonnet-4-20250514"),
        Agent(agent_id="agent-coder-02", name="CodeGen Beta",
              description="Secondary code generation agent for parallel tasks",
              skills=["code_generation", "debugging", "testing"],
              permissions=["read_repo", "write_files", "run_tests"],
              group="engineering", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.003, cost_per_1k_output=0.015, model_name="claude-sonnet-4-20250514"),
        Agent(agent_id="agent-reviewer-01", name="Review Sentinel",
              description="Code review and quality assurance agent",
              skills=["code_review", "security_audit", "performance_analysis"],
              permissions=["read_repo", "comment_pr", "approve_pr"],
              group="quality", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.01, cost_per_1k_output=0.03, model_name="claude-opus-4-20250514"),
        Agent(agent_id="agent-data-01", name="Data Wrangler",
              description="Data extraction, transformation, and analysis agent",
              skills=["data_extraction", "data_transformation", "summarization", "sql_queries"],
              permissions=["read_db", "read_api", "write_files"],
              group="data", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.0005, cost_per_1k_output=0.0015, model_name="claude-haiku-4-5-20251001"),
        Agent(agent_id="agent-planner-01", name="Orchestrator Prime",
              description="Workflow planning and task delegation agent",
              skills=["planning", "task_decomposition", "resource_allocation", "monitoring"],
              permissions=["read_repo", "assign_tasks", "monitor_agents", "escalate"],
              group="orchestration", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.01, cost_per_1k_output=0.03, model_name="claude-opus-4-20250514"),
        Agent(agent_id="agent-search-01", name="Research Scout",
              description="Information retrieval and research agent",
              skills=["web_search", "document_analysis", "summarization"],
              permissions=["read_api", "web_access", "read_docs"],
              group="research", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.0005, cost_per_1k_output=0.0015, model_name="claude-haiku-4-5-20251001"),
        Agent(agent_id="agent-deploy-01", name="Deploy Guardian",
              description="CI/CD and deployment automation agent",
              skills=["ci_cd", "infrastructure", "monitoring", "rollback"],
              permissions=["read_repo", "run_pipeline", "deploy_staging", "deploy_prod"],
              group="devops", status=AgentStatus.ACTIVE,
              cost_per_1k_input=0.003, cost_per_1k_output=0.015, model_name="claude-sonnet-4-20250514"),
        Agent(agent_id="agent-legacy-01", name="Legacy Processor",
              description="Deprecated agent kept for reference",
              skills=["data_extraction"],
              permissions=["read_db"],
              group="data", status=AgentStatus.INACTIVE,
              cost_per_1k_input=0.0005, cost_per_1k_output=0.0015, model_name="claude-haiku-4-5-20251001"),
    ]

    for agent in agents_def:
        upsert_agent(agent)

    task_types = {
        "code_generation": {"skills": ["code_generation"], "perms": ["read_repo", "write_files"],
                            "agents": ["agent-coder-01", "agent-coder-02"]},
        "code_review": {"skills": ["code_review"], "perms": ["read_repo", "comment_pr"],
                        "agents": ["agent-reviewer-01", "agent-coder-01"]},
        "bug_fix": {"skills": ["debugging", "code_generation"], "perms": ["read_repo", "write_files", "run_tests"],
                    "agents": ["agent-coder-01", "agent-coder-02"]},
        "data_extraction": {"skills": ["data_extraction", "sql_queries"], "perms": ["read_db"],
                            "agents": ["agent-data-01"]},
        "data_analysis": {"skills": ["data_transformation", "summarization"], "perms": ["read_db", "write_files"],
                          "agents": ["agent-data-01"]},
        "research": {"skills": ["web_search", "summarization"], "perms": ["web_access", "read_docs"],
                     "agents": ["agent-search-01"]},
        "planning": {"skills": ["planning", "task_decomposition"], "perms": ["assign_tasks"],
                     "agents": ["agent-planner-01"]},
        "deployment": {"skills": ["ci_cd", "infrastructure"], "perms": ["run_pipeline", "deploy_staging"],
                       "agents": ["agent-deploy-01"]},
        "security_audit": {"skills": ["security_audit"], "perms": ["read_repo"],
                           "agents": ["agent-reviewer-01"]},
        "test_generation": {"skills": ["testing", "code_generation"], "perms": ["read_repo", "write_files", "run_tests"],
                            "agents": ["agent-coder-01", "agent-coder-02"]},
    }

    agent_map = {a.agent_id: a for a in agents_def}
    now = datetime.utcnow()
    all_tasks = []
    all_spans = []
    all_workflows = []

    # Generate 30 days of data
    for day_offset in range(30, 0, -1):
        day_start = now - timedelta(days=day_offset)
        num_workflows = random.randint(2, 5)

        for _ in range(num_workflows):
            wf_id = str(uuid.uuid4())[:12]
            wf_start = day_start + timedelta(hours=random.uniform(0, 20))
            wf_task_ids = []
            wf_agent_ids = set()
            wf_cost = 0.0
            trace_id = str(uuid.uuid4())[:16]

            num_tasks = random.randint(2, 6)
            task_offset_ms = 0

            # Root planning span
            plan_span = SpanRecord(
                trace_id=trace_id, span_id=str(uuid.uuid4())[:12],
                agent_id="agent-planner-01", operation="workflow_planning",
                started_at=wf_start, ended_at=wf_start + timedelta(milliseconds=random.randint(200, 800)),
                duration_ms=random.uniform(200, 800), status="OK",
                attributes={"workflow_id": wf_id, "num_tasks": num_tasks}
            )
            all_spans.append(plan_span)
            parent_span = plan_span.span_id

            for t_idx in range(num_tasks):
                tt = random.choice(list(task_types.keys()))
                tt_def = task_types[tt]
                agent_id = random.choice(tt_def["agents"])
                agent = agent_map[agent_id]
                wf_agent_ids.add(agent_id)

                task_start = wf_start + timedelta(milliseconds=task_offset_ms)
                latency = random.uniform(500, 15000)
                task_end = task_start + timedelta(milliseconds=latency)
                task_offset_ms += latency + random.uniform(100, 500)

                # Determine result with realistic distribution
                r = random.random()
                if r < 0.72:
                    result = TaskResult.SUCCESS
                    quality = round(random.uniform(0.7, 1.0), 3)
                elif r < 0.85:
                    result = TaskResult.PARTIAL
                    quality = round(random.uniform(0.3, 0.7), 3)
                elif r < 0.95:
                    result = TaskResult.FAILURE
                    quality = round(random.uniform(0.0, 0.3), 3)
                else:
                    result = TaskResult.TIMEOUT
                    quality = 0.0
                    latency = 30000

                input_tokens = random.randint(500, 8000)
                output_tokens = random.randint(200, 4000)
                total_tokens = input_tokens + output_tokens
                cost = (input_tokens / 1000 * agent.cost_per_1k_input +
                        output_tokens / 1000 * agent.cost_per_1k_output)
                cost = round(cost, 6)
                wf_cost += cost

                task_id = str(uuid.uuid4())[:12]
                wf_task_ids.append(task_id)

                task = TaskRecord(
                    task_id=task_id, agent_id=agent_id, workflow_id=wf_id,
                    task_type=tt, description=f"Auto-generated {tt} task",
                    required_skills=tt_def["skills"], required_permissions=tt_def["perms"],
                    result=result, started_at=task_start, completed_at=task_end,
                    latency_ms=round(latency, 2),
                    input_tokens=input_tokens, output_tokens=output_tokens,
                    total_tokens=total_tokens, cost_usd=cost,
                    quality_score=quality,
                    metadata={"workflow_id": wf_id, "task_index": t_idx}
                )
                all_tasks.append(task)

                # Create spans for this task
                task_span = SpanRecord(
                    trace_id=trace_id, span_id=str(uuid.uuid4())[:12],
                    parent_span_id=parent_span, agent_id=agent_id,
                    operation=f"execute_{tt}",
                    started_at=task_start, ended_at=task_end,
                    duration_ms=round(latency, 2),
                    status="OK" if result in (TaskResult.SUCCESS, TaskResult.PARTIAL) else "ERROR",
                    attributes={"task_id": task_id, "task_type": tt, "result": result.value}
                )
                all_spans.append(task_span)

                # Add sub-spans for detail
                sub_ops = ["initialize", "process", "validate", "finalize"]
                sub_start = task_start
                for sop in sub_ops:
                    sub_dur = latency / len(sub_ops) * random.uniform(0.5, 1.5)
                    sub_end = sub_start + timedelta(milliseconds=sub_dur)
                    sub_span = SpanRecord(
                        trace_id=trace_id, span_id=str(uuid.uuid4())[:12],
                        parent_span_id=task_span.span_id, agent_id=agent_id,
                        operation=f"{tt}.{sop}",
                        started_at=sub_start, ended_at=sub_end,
                        duration_ms=round(sub_dur, 2), status="OK",
                        attributes={"sub_operation": sop}
                    )
                    all_spans.append(sub_span)
                    sub_start = sub_end

            # Determine workflow result
            task_results = [t.result for t in all_tasks[-num_tasks:]]
            if all(r == TaskResult.SUCCESS for r in task_results):
                wf_result = TaskResult.SUCCESS
            elif any(r == TaskResult.FAILURE for r in task_results):
                wf_result = TaskResult.FAILURE
            else:
                wf_result = TaskResult.PARTIAL

            wf_end = wf_start + timedelta(milliseconds=task_offset_ms)
            workflow = WorkflowRecord(
                workflow_id=wf_id, name=f"Workflow-{day_offset:02d}-{_}",
                description=f"Auto-generated workflow",
                agent_ids=list(wf_agent_ids), task_ids=wf_task_ids,
                started_at=wf_start, completed_at=wf_end,
                result=wf_result, total_cost_usd=round(wf_cost, 6),
                metadata={"day_offset": day_offset}
            )
            all_workflows.append(workflow)

    # Bulk insert
    for task in all_tasks:
        insert_task(task)
    for span in all_spans:
        insert_span(span)
    for wf in all_workflows:
        insert_workflow(wf)

    return {"agents": len(agents_def), "tasks": len(all_tasks),
            "spans": len(all_spans), "workflows": len(all_workflows)}
