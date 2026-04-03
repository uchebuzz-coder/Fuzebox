"""Pydantic data models for the Agent Performance Dashboard."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class TaskType(str, Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    DATA_EXTRACTION = "data_extraction"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    PLANNING = "planning"
    DEPLOYMENT = "deployment"
    SECURITY_AUDIT = "security_audit"
    TEST_GENERATION = "test_generation"


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
    registered_at: datetime = Field(default_factory=datetime.utcnow)


class TaskRecord(BaseModel):
    task_id: str
    agent_id: str
    workflow_id: Optional[str] = None
    task_type: str
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    result: TaskResult = TaskResult.SUCCESS
    started_at: datetime = Field(default_factory=datetime.utcnow)
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
    started_at: datetime = Field(default_factory=datetime.utcnow)
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
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: TaskResult = TaskResult.SUCCESS
    total_cost_usd: float = 0.0
    metadata: dict = Field(default_factory=dict)
