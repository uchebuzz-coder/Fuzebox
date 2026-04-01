"""
V1 Sequential Pipeline
    input → Intake Classifier → Triage Scorer → Response Drafter → output

Every step generates telemetry. No data is mocked or simulated.
"""

import uuid
from typing import Optional

from pydantic import BaseModel

from agents.classifier import run_classifier, ClassificationOutput
from agents.triage import run_triage, TriageOutput
from agents.responder import run_responder, ResponderOutput
from telemetry.logger import (
    TelemetryLogger,
    ensure_agents_registered,
    log_workflow,
)


class PipelineResult(BaseModel):
    workflow_id: str
    input_text: str

    # Agent outputs
    classification: ClassificationOutput
    triage: TriageOutput
    response: ResponderOutput

    # Derived flags
    escalation_flag: bool

    # Per-step telemetry
    telemetry: list[dict]

    # Aggregate
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    pipeline_success: bool


def run_pipeline(input_text: str, workflow_id: Optional[str] = None) -> PipelineResult:
    """
    Run all three agents sequentially and log telemetry for each step.

    Args:
        input_text:   Raw customer service request text.
        workflow_id:  Optional workflow ID; generated if not provided.

    Returns:
        PipelineResult with outputs from all three agents + telemetry.
    """
    ensure_agents_registered()

    if not workflow_id:
        workflow_id = str(uuid.uuid4())[:12]

    telemetry_records: list[dict] = []
    task_ids: list[str] = []
    total_in_tok = 0
    total_out_tok = 0
    total_cost = 0.0
    all_succeeded = True

    # ── Step 1: Intake Classifier ──────────────────────────────────────────────
    tel1 = TelemetryLogger("v1-classifier-01", workflow_id=workflow_id).start()
    try:
        classification, in1, out1 = run_classifier(input_text)
        escalation_flag = classification.classification == "urgent"
        rec1 = tel1.record(
            task_type="classification",
            input_tokens=in1,
            output_tokens=out1,
            success=True,
            escalation_flag=escalation_flag,
            metadata={"classification": classification.classification,
                      "confidence": classification.confidence},
        )
    except Exception as exc:
        rec1 = tel1.record(
            task_type="classification",
            input_tokens=0, output_tokens=0,
            success=False,
            metadata={"error": str(exc)},
        )
        all_succeeded = False
        raise RuntimeError(f"Classifier failed: {exc}") from exc

    telemetry_records.append(rec1)
    task_ids.append(tel1.task_id)
    total_in_tok += in1
    total_out_tok += out1
    total_cost += rec1["cost_usd"]

    # ── Step 2: Triage Scorer ──────────────────────────────────────────────────
    tel2 = TelemetryLogger("v1-triage-01", workflow_id=workflow_id).start()
    try:
        triage, in2, out2 = run_triage(
            input_text,
            classification=classification.classification,
            confidence=classification.confidence,
        )
        # Escalate if urgent classification OR high priority
        escalation_flag = escalation_flag or triage.priority >= 4
        rec2 = tel2.record(
            task_type="triage",
            input_tokens=in2,
            output_tokens=out2,
            success=True,
            escalation_flag=escalation_flag,
            metadata={"priority": triage.priority, "rationale": triage.rationale},
        )
    except Exception as exc:
        rec2 = tel2.record(
            task_type="triage",
            input_tokens=0, output_tokens=0,
            success=False,
            metadata={"error": str(exc)},
        )
        all_succeeded = False
        raise RuntimeError(f"Triage failed: {exc}") from exc

    telemetry_records.append(rec2)
    task_ids.append(tel2.task_id)
    total_in_tok += in2
    total_out_tok += out2
    total_cost += rec2["cost_usd"]

    # ── Step 3: Response Drafter ───────────────────────────────────────────────
    tel3 = TelemetryLogger("v1-responder-01", workflow_id=workflow_id).start()
    try:
        response, in3, out3 = run_responder(
            input_text,
            classification=classification.classification,
            priority=triage.priority,
            rationale=triage.rationale,
        )
        rec3 = tel3.record(
            task_type="response_drafting",
            input_tokens=in3,
            output_tokens=out3,
            success=True,
            escalation_flag=escalation_flag,
            metadata={"sentiment": response.sentiment},
        )
    except Exception as exc:
        rec3 = tel3.record(
            task_type="response_drafting",
            input_tokens=0, output_tokens=0,
            success=False,
            metadata={"error": str(exc)},
        )
        all_succeeded = False
        raise RuntimeError(f"Responder failed: {exc}") from exc

    telemetry_records.append(rec3)
    task_ids.append(tel3.task_id)
    total_in_tok += in3
    total_out_tok += out3
    total_cost += rec3["cost_usd"]

    # ── Log workflow ───────────────────────────────────────────────────────────
    log_workflow(
        workflow_id=workflow_id,
        task_ids=task_ids,
        agent_ids=["v1-classifier-01", "v1-triage-01", "v1-responder-01"],
        total_cost=total_cost,
        success=all_succeeded,
    )

    return PipelineResult(
        workflow_id=workflow_id,
        input_text=input_text,
        classification=classification,
        triage=triage,
        response=response,
        escalation_flag=escalation_flag,
        telemetry=telemetry_records,
        total_input_tokens=total_in_tok,
        total_output_tokens=total_out_tok,
        total_cost_usd=round(total_cost, 8),
        pipeline_success=all_succeeded,
    )
