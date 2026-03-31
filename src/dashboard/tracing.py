"""OpenTelemetry-based tracing for agent workflows."""

import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

from .models import TaskRecord, TaskResult, SpanRecord
from . import db


class DashboardSpanExporter(SpanExporter):
    """Custom exporter that writes spans to the SQLite dashboard database."""

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes) if span.attributes else {}
            started = datetime.fromtimestamp(span.start_time / 1e9) if span.start_time else datetime.now()
            ended = datetime.fromtimestamp(span.end_time / 1e9) if span.end_time else None
            duration = None
            if span.start_time and span.end_time:
                duration = (span.end_time - span.start_time) / 1e6  # ns to ms

            span_record = SpanRecord(
                trace_id=format(span.context.trace_id, '032x'),
                span_id=format(span.context.span_id, '016x'),
                parent_span_id=format(span.parent.span_id, '016x') if span.parent else None,
                agent_id=attrs.get("agent_id", "unknown"),
                operation=span.name,
                started_at=started,
                ended_at=ended,
                duration_ms=duration,
                status="ERROR" if span.status.is_ok is False else "OK",
                attributes={k: str(v) for k, v in attrs.items()}
            )
            db.insert_span(span_record)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


_tracer_provider = None
_tracer = None


def init_tracing():
    """Initialize the OpenTelemetry tracing pipeline with SQLite export."""
    global _tracer_provider, _tracer
    db.init_db()
    _tracer_provider = TracerProvider()
    _tracer_provider.add_span_processor(SimpleSpanProcessor(DashboardSpanExporter()))
    trace.set_tracer_provider(_tracer_provider)
    _tracer = trace.get_tracer("agent-dashboard")
    return _tracer


def get_tracer():
    global _tracer
    if _tracer is None:
        return init_tracing()
    return _tracer


class TaskContext:
    """Context object for tracking task metrics during execution."""

    def __init__(self, agent_id: str, task_type: str, workflow_id: str = None):
        self.task_id = str(uuid.uuid4())[:12]
        self.agent_id = agent_id
        self.task_type = task_type
        self.workflow_id = workflow_id
        self.input_tokens = 0
        self.output_tokens = 0
        self.result = TaskResult.SUCCESS
        self.quality_score = None
        self.description = ""
        self.required_skills = []
        self.required_permissions = []
        self.metadata = {}
        self._started_at = None

    def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def set_result(self, result: str):
        self.result = TaskResult(result)

    def set_quality(self, score: float):
        self.quality_score = max(0.0, min(1.0, score))

    def add_metadata(self, key: str, value):
        self.metadata[key] = value


@contextmanager
def trace_agent_task(agent_id: str, task_type: str, workflow_id: str = None):
    """Context manager that traces an agent task and records it to the database.

    Usage:
        with trace_agent_task("agent-001", "code_review") as ctx:
            # ... agent does work ...
            ctx.set_tokens(input_tokens=1500, output_tokens=800)
            ctx.set_result("success")
            ctx.set_quality(0.92)
    """
    tracer = get_tracer()
    ctx = TaskContext(agent_id, task_type, workflow_id)
    ctx._started_at = datetime.now()

    with tracer.start_as_current_span(
        f"{task_type}",
        attributes={"agent_id": agent_id, "task_type": task_type,
                     "task_id": ctx.task_id, "workflow_id": workflow_id or ""}
    ):
        try:
            yield ctx
        except Exception as e:
            ctx.result = TaskResult.FAILURE
            ctx.metadata["error"] = str(e)
            raise
        finally:
            completed_at = datetime.now()
            latency_ms = (completed_at - ctx._started_at).total_seconds() * 1000

            # Calculate cost
            agent = db.get_agent(agent_id)
            cost = 0.0
            if agent:
                cost = (ctx.input_tokens / 1000 * agent.cost_per_1k_input +
                        ctx.output_tokens / 1000 * agent.cost_per_1k_output)

            task = TaskRecord(
                task_id=ctx.task_id, agent_id=agent_id,
                workflow_id=workflow_id, task_type=task_type,
                description=ctx.description,
                required_skills=ctx.required_skills,
                required_permissions=ctx.required_permissions,
                result=ctx.result,
                started_at=ctx._started_at, completed_at=completed_at,
                latency_ms=round(latency_ms, 2),
                input_tokens=ctx.input_tokens, output_tokens=ctx.output_tokens,
                total_tokens=ctx.input_tokens + ctx.output_tokens,
                cost_usd=round(cost, 6),
                quality_score=ctx.quality_score,
                metadata=ctx.metadata
            )
            db.insert_task(task)


@contextmanager
def trace_subtask(operation: str, agent_id: str = ""):
    """Context manager for tracing sub-operations within a task."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        operation,
        attributes={"agent_id": agent_id, "operation": operation}
    ):
        yield
