"""
FastAPI application — V1 pipeline endpoint.

Run:
    uvicorn api.main:app --reload --port 8000

Endpoint:
    POST /v1/process
    GET  /v1/metrics
    GET  /v1/health
"""

import logging
import sys
import os

# Ensure project root is on path when running via uvicorn
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pipeline.pipeline import run_pipeline, PipelineResult
from telemetry.logger import compute_metrics

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Fuzebox V1 Multi-Agent Pipeline",
    description="Sequential 3-agent pipeline: Intake Classifier → Triage Scorer → Response Drafter",
    version="1.0.0",
)


# ── Request / Response schemas ─────────────────────────────────────────────────

class ProcessRequest(BaseModel):
    input: str
    workflow_id: str | None = None


class ProcessResponse(BaseModel):
    workflow_id: str
    classification: dict
    triage: dict
    response: dict
    escalation_flag: bool
    telemetry: list[dict]
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    pipeline_success: bool


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/v1/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/v1/process", response_model=ProcessResponse)
def process(req: ProcessRequest):
    """
    Run the full V1 pipeline on the provided input text.

    All three agents are called in sequence with real LLM calls.
    Telemetry is logged to SQLite after every agent step.
    """
    if not req.input or not req.input.strip():
        raise HTTPException(status_code=422, detail="input must not be empty")

    try:
        result: PipelineResult = run_pipeline(
            input_text=req.input.strip(),
            workflow_id=req.workflow_id,
        )
    except Exception as exc:
        logging.exception("Pipeline error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ProcessResponse(
        workflow_id=result.workflow_id,
        classification=result.classification.model_dump(),
        triage=result.triage.model_dump(),
        response=result.response.model_dump(),
        escalation_flag=result.escalation_flag,
        telemetry=result.telemetry,
        total_input_tokens=result.total_input_tokens,
        total_output_tokens=result.total_output_tokens,
        total_cost_usd=result.total_cost_usd,
        pipeline_success=result.pipeline_success,
    )


@app.get("/v1/metrics")
def metrics(agent_id: str | None = None):
    """
    Return pipeline metrics derived from real telemetry logs.

    Computes: completion_rate, avg_latency_ms, escalation_rate, avg_auop.
    Optionally filter by agent_id.
    """
    return compute_metrics(agent_id=agent_id)
