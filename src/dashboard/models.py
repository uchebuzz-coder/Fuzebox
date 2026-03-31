"""Pydantic data models for the Agent Performance Dashboard."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class TaskResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


class Agent(BaseModel):
    agent_id: str
    name: str
    description: str = ""
    skills: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    group: str = "default"
    status: AgentStatus = AgentStatus.ACTIVE
    cost_per_1k_input: float = 0.003
    cost_per_1k_output: float = 0.015
    model_name: str = "gpt-4"
    registered_at: datetime = Field(default_factory=_utcnow)


class TaskRecord(BaseModel):
    task_id: str
    agent_id: str
    workflow_id: Optional[str] = None
    task_type: str
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    result: TaskResult = TaskResult.SUCCESS
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: Optional[datetime] = None
    latency_ms: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    quality_score: Optional[float] = None  # 0.0 - 1.0
    metadata: dict = Field(default_factory=dict)


class SpanRecord(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    agent_id: str
    operation: str
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "OK"
    attributes: dict = Field(default_factory=dict)


class WorkflowRecord(BaseModel):
    workflow_id: str
    name: str
    description: str = ""
    agent_ids: list[str] = Field(default_factory=list)
    task_ids: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: Optional[datetime] = None
    result: TaskResult = TaskResult.SUCCESS
    total_cost_usd: float = 0.0
    metadata: dict = Field(default_factory=dict)


# ==================== V2 Models ====================


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    ADJUSTING = "adjusting"
    RUNNING = "running"
    CAPTURING = "capturing"
    COMPLETE = "complete"
    FAILED = "failed"


class AgentConfig(BaseModel):
    config_id: str
    agent_id: str
    version: int = 1
    prompt_precision: int = 5
    confidence_threshold: float = 0.6
    fallback_depth: int = 2
    data_prefetch: bool = True
    sentiment_weighting: float = 0.3
    tone_variant: str = "balanced"
    is_baseline: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    notes: str = ""


class FailurePattern(BaseModel):
    pattern_id: str
    agent_id: str
    pattern_description: str
    occurrence_count: int = 0
    severity: str = "warning"
    affected_task_types: list[str] = Field(default_factory=list)
    common_attributes: dict = Field(default_factory=dict)
    suggested_fix: str = ""


class ExperimentRecord(BaseModel):
    experiment_id: str
    agent_id: str
    baseline_config_version: int
    candidate_config_version: int
    status: ExperimentStatus = ExperimentStatus.PENDING
    task_sample_size: int = 100
    started_at: datetime = Field(default_factory=_utcnow)
    completed_at: Optional[datetime] = None
    baseline_metrics: dict = Field(default_factory=dict)
    candidate_metrics: dict = Field(default_factory=dict)
    failure_patterns: list[dict] = Field(default_factory=list)
    parameter_changes: dict = Field(default_factory=dict)
    promoted: Optional[bool] = None
