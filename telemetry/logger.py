"""Telemetry logger — records every agent call to SQLite and computes AUoP."""

import logging
import statistics
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.dashboard.db import init_db, insert_task, insert_workflow, upsert_agent, get_tasks
from src.dashboard.models import Agent, AgentStatus, TaskRecord, TaskResult, WorkflowRecord

logger = logging.getLogger(__name__)

# ── Agent definitions for the V1 pipeline ─────────────────────────────────────

V1_AGENTS: list[Agent] = [
    Agent(
        agent_id="v1-classifier-01",
        name="Intake Classifier V1",
        description="Classifies incoming service requests by category",
        skills=["classification", "nlp"],
        permissions=["read_input"],
        group="v1_pipeline",
        status=AgentStatus.ACTIVE,
        cost_per_1k_input=0.00015,   # gpt-4o-mini input pricing
        cost_per_1k_output=0.00060,  # gpt-4o-mini output pricing
        model_name="gpt-4o-mini",
    ),
    Agent(
        agent_id="v1-triage-01",
        name="Triage Scorer V1",
        description="Scores priority of classified service requests",
        skills=["triage", "prioritization"],
        permissions=["read_classification"],
        group="v1_pipeline",
        status=AgentStatus.ACTIVE,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.00060,
        model_name="gpt-4o-mini",
    ),
    Agent(
        agent_id="v1-responder-01",
        name="Response Drafter V1",
        description="Drafts customer-facing responses for triaged requests",
        skills=["response_drafting", "nlp"],
        permissions=["read_triage", "write_response"],
        group="v1_pipeline",
        status=AgentStatus.ACTIVE,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.00060,
        model_name="gpt-4o-mini",
    ),
]

_AGENT_MAP: dict[str, Agent] = {a.agent_id: a for a in V1_AGENTS}


def ensure_agents_registered() -> None:
    """Idempotently register V1 agents in the DB."""
    init_db()
    for agent in V1_AGENTS:
        upsert_agent(agent)


# ── Per-call telemetry ─────────────────────────────────────────────────────────

class TelemetryLogger:
    """
    Records a single agent invocation.

    Usage:
        tel = TelemetryLogger("v1-classifier-01", workflow_id="wf-123").start()
        ...call agent...
        record = tel.record(
            task_type="classification",
            input_tokens=350, output_tokens=80,
            success=True, escalation_flag=False,
            metadata={"raw_output": {...}},
        )
    """

    def __init__(self, agent_id: str, workflow_id: Optional[str] = None):
        self.agent_id = agent_id
        self.workflow_id = workflow_id
        self.task_id = str(uuid.uuid4())[:12]
        self._start: Optional[float] = None
        self._start_dt: Optional[datetime] = None

    def start(self) -> "TelemetryLogger":
        import time
        self._start = time.time()
        self._start_dt = datetime.now(timezone.utc).replace(tzinfo=None)
        return self

    def record(
        self,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        escalation_flag: bool = False,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Persist the record and return the telemetry dict."""
        import time

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        latency_ms = (time.time() - self._start) * 1000 if self._start else 0.0
        total_tokens = input_tokens + output_tokens

        # AUoP = successful_output / total_tokens_used
        auop_score = (1.0 / total_tokens) if (success and total_tokens > 0) else 0.0

        # Cost
        agent = _AGENT_MAP.get(self.agent_id)
        cost_usd = 0.0
        if agent:
            cost_usd = (
                input_tokens / 1000.0 * agent.cost_per_1k_input
                + output_tokens / 1000.0 * agent.cost_per_1k_output
            )

        task = TaskRecord(
            task_id=self.task_id,
            agent_id=self.agent_id,
            workflow_id=self.workflow_id,
            task_type=task_type,
            result=TaskResult.SUCCESS if success else TaskResult.FAILURE,
            started_at=self._start_dt or now,
            completed_at=now,
            latency_ms=round(latency_ms, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=round(cost_usd, 8),
            quality_score=1.0 if success else 0.0,
            metadata={
                "escalation_flag": escalation_flag,
                "auop_score": auop_score,
                "completion_status": "success" if success else "failure",
                **(metadata or {}),
            },
        )
        insert_task(task)

        telemetry = {
            "timestamp": now.isoformat(),
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "task_type": task_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "completion_status": "success" if success else "failure",
            "escalation_flag": escalation_flag,
            "auop_score": auop_score,
            "cost_usd": round(cost_usd, 8),
        }
        logger.info("[telemetry] %s", telemetry)
        return telemetry


# ── Workflow log ───────────────────────────────────────────────────────────────

def log_workflow(
    workflow_id: str,
    task_ids: list[str],
    agent_ids: list[str],
    total_cost: float,
    success: bool,
) -> None:
    """Persist a completed pipeline workflow record."""
    wf = WorkflowRecord(
        workflow_id=workflow_id,
        name="V1 Pipeline",
        description="Intake Classifier → Triage Scorer → Response Drafter",
        agent_ids=agent_ids,
        task_ids=task_ids,
        result=TaskResult.SUCCESS if success else TaskResult.FAILURE,
        total_cost_usd=round(total_cost, 8),
    )
    insert_workflow(wf)


# ── Derived metrics (computed from logs, never hardcoded) ─────────────────────

def compute_metrics(agent_id: Optional[str] = None) -> dict:
    """
    Compute pipeline metrics from real telemetry logs.

    Returns:
        completion_rate, avg_latency_ms, escalation_rate, avg_auop
        plus per-agent breakdowns when agent_id is None.
    """
    tasks = get_tasks(agent_id=agent_id)
    if not tasks:
        return {"total_tasks": 0, "note": "No telemetry records found."}

    total = len(tasks)
    successful = sum(1 for t in tasks if t.result == TaskResult.SUCCESS)
    latencies = [t.latency_ms for t in tasks if t.latency_ms is not None]
    escalations = sum(
        1 for t in tasks if t.metadata.get("escalation_flag", False)
    )
    auop_scores = [t.metadata.get("auop_score", 0.0) for t in tasks]

    summary = {
        "total_tasks": total,
        "completion_rate": round(successful / total, 4),
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
        "escalation_rate": round(escalations / total, 4),
        "avg_auop": round(statistics.mean(auop_scores), 8) if auop_scores else 0.0,
    }

    # Per-agent breakdown (only when querying all agents)
    if agent_id is None:
        per_agent = {}
        for aid in {t.agent_id for t in tasks}:
            agent_tasks = [t for t in tasks if t.agent_id == aid]
            at_total = len(agent_tasks)
            at_success = sum(1 for t in agent_tasks if t.result == TaskResult.SUCCESS)
            at_lat = [t.latency_ms for t in agent_tasks if t.latency_ms]
            at_auop = [t.metadata.get("auop_score", 0.0) for t in agent_tasks]
            per_agent[aid] = {
                "total_tasks": at_total,
                "completion_rate": round(at_success / at_total, 4),
                "avg_latency_ms": round(statistics.mean(at_lat), 2) if at_lat else 0.0,
                "avg_auop": round(statistics.mean(at_auop), 8) if at_auop else 0.0,
            }
        summary["per_agent"] = per_agent

    return summary
