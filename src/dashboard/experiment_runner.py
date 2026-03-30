"""Experiment execution engine: simulate training cycles with parameter changes."""

import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import numpy as np

from . import db
from .models import TaskResult, AgentConfig, ExperimentRecord, ExperimentStatus
from . import metrics, economics
from .failure_analyzer import analyze_failure_patterns, get_failure_summary


def compute_agent_metrics(agent_id: str, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> dict:
    """Calculate the full metrics snapshot for an agent."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return {"total_tasks": 0, "completion_rate": 0, "escalation_rate": 0,
                "accuracy": 0, "avg_task_time": 0, "auop": 0,
                "cost_per_task": 0, "ai_roi": 0,
                "success_count": 0, "failure_count": 0, "timeout_count": 0}

    total = len(tasks)
    success = sum(1 for t in tasks if t.result == TaskResult.SUCCESS)
    failures = sum(1 for t in tasks if t.result == TaskResult.FAILURE)
    timeouts = sum(1 for t in tasks if t.result == TaskResult.TIMEOUT)
    partials = sum(1 for t in tasks if t.result == TaskResult.PARTIAL)

    completion_rate = success / total
    escalation_rate = partials / total
    qualities = [t.quality_score for t in tasks if t.quality_score is not None]
    accuracy = float(np.mean(qualities)) if qualities else 0.0
    latencies = [t.latency_ms for t in tasks if t.latency_ms is not None]
    avg_task_time = float(np.mean(latencies)) if latencies else 0.0
    auop = completion_rate * accuracy

    total_cost = sum(t.cost_usd for t in tasks)
    cost_per_task = total_cost / total if total > 0 else 0

    roi_data = economics.calculate_roi(start_date=start_date, end_date=end_date)
    ai_roi = roi_data.get("roi_pct", 0)

    return {
        "completion_rate": round(completion_rate, 4),
        "escalation_rate": round(escalation_rate, 4),
        "accuracy": round(accuracy, 4),
        "avg_task_time": round(avg_task_time, 1),
        "auop": round(auop, 4),
        "cost_per_task": round(cost_per_task, 6),
        "ai_roi": round(ai_roi, 1),
        "total_tasks": total,
        "success_count": success,
        "failure_count": failures,
        "timeout_count": timeouts,
    }


def compute_config_diff(baseline: AgentConfig, candidate: AgentConfig) -> dict:
    """Return only the parameters that changed between two configs."""
    diff = {}
    params = ["prompt_precision", "confidence_threshold", "fallback_depth",
              "data_prefetch", "sentiment_weighting", "tone_variant"]
    for p in params:
        old_val = getattr(baseline, p)
        new_val = getattr(candidate, p)
        if old_val != new_val:
            diff[p] = {"old": old_val, "new": new_val}
    return diff


def simulate_experiment(agent_id: str, baseline_config: AgentConfig,
                        candidate_config: AgentConfig, sample_size: int = 100,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> ExperimentRecord:
    """Run a simulated training cycle by replaying historical tasks with new parameters."""
    experiment_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow()

    # Step 1: Ingest — get baseline metrics
    baseline_metrics = compute_agent_metrics(agent_id, start_date, end_date)

    # Step 2: Analyze — get failure patterns
    patterns = analyze_failure_patterns(agent_id, start_date, end_date)
    failure_patterns_data = [
        {"pattern_id": p["pattern_id"], "description": p["pattern_description"],
         "count": p["occurrence_count"], "severity": p["severity"],
         "suggested_fix": p["suggested_fix"]}
        for p in patterns[:5]
    ]

    # Step 3: Adjust — compute diff
    param_changes = compute_config_diff(baseline_config, candidate_config)

    # Step 4: Re-run — simulate with new parameters
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return ExperimentRecord(
            experiment_id=experiment_id, agent_id=agent_id,
            baseline_config_version=baseline_config.version,
            candidate_config_version=candidate_config.version,
            status=ExperimentStatus.FAILED,
            started_at=now, completed_at=datetime.utcnow(),
            baseline_metrics=baseline_metrics, candidate_metrics={},
            failure_patterns=failure_patterns_data,
            parameter_changes=param_changes,
        )

    # Sample tasks deterministically
    sampled = tasks[:sample_size] if len(tasks) <= sample_size else random.Random(42).sample(tasks, sample_size)

    # Compute parameter effects
    pp_delta = candidate_config.prompt_precision - baseline_config.prompt_precision
    ct_delta = candidate_config.confidence_threshold - baseline_config.confidence_threshold
    fd_delta = candidate_config.fallback_depth - baseline_config.fallback_depth
    dp_changed = candidate_config.data_prefetch != baseline_config.data_prefetch
    sw_delta = candidate_config.sentiment_weighting - baseline_config.sentiment_weighting

    # Simulate new outcomes
    sim_success = 0
    sim_partial = 0
    sim_failure = 0
    sim_timeout = 0
    sim_qualities = []
    sim_latencies = []
    sim_costs = []

    for t in sampled:
        rng = random.Random(hash(t.task_id))

        # Base probabilities from original outcome
        if t.result == TaskResult.SUCCESS:
            p_success = 0.92
        elif t.result == TaskResult.PARTIAL:
            p_success = 0.35
        elif t.result == TaskResult.FAILURE:
            p_success = 0.15
        else:  # TIMEOUT
            p_success = 0.08

        # Apply parameter effects
        # Higher prompt_precision → +3% success per point increase
        p_success += pp_delta * 0.03
        # Lower confidence_threshold → more attempts, +5% success per 0.1 decrease
        p_success += (-ct_delta) * 0.5
        # Higher fallback_depth → fewer hard failures, +4% per level
        p_success += fd_delta * 0.04
        # Data prefetch → +5% on context tasks
        if dp_changed and candidate_config.data_prefetch:
            p_success += 0.05
        elif dp_changed and not candidate_config.data_prefetch:
            p_success -= 0.03

        p_success = max(0.05, min(0.98, p_success))

        # Determine outcome
        roll = rng.random()
        if roll < p_success:
            result = TaskResult.SUCCESS
            sim_success += 1
        elif roll < p_success + 0.08:
            result = TaskResult.PARTIAL
            sim_partial += 1
        elif roll < p_success + 0.14:
            result = TaskResult.FAILURE
            sim_failure += 1
        else:
            result = TaskResult.TIMEOUT
            sim_timeout += 1

        # Simulate quality
        base_q = t.quality_score or 0.5
        q_adjust = pp_delta * 0.03 + sw_delta * 0.02
        if result == TaskResult.SUCCESS:
            q = min(1.0, base_q + q_adjust + rng.uniform(0, 0.1))
        elif result == TaskResult.PARTIAL:
            q = max(0.1, base_q * 0.7 + q_adjust)
        else:
            q = max(0.0, base_q * 0.3)
        sim_qualities.append(round(q, 3))

        # Simulate latency
        base_lat = t.latency_ms or 5000
        lat_adjust = 1.0
        lat_adjust += fd_delta * 0.08  # more fallbacks = slower
        if dp_changed and candidate_config.data_prefetch:
            lat_adjust += 0.06
        elif dp_changed and not candidate_config.data_prefetch:
            lat_adjust -= 0.04
        sim_lat = max(200, base_lat * lat_adjust + rng.uniform(-500, 500))
        sim_latencies.append(round(sim_lat, 1))

        sim_costs.append(t.cost_usd * lat_adjust)

    sim_total = len(sampled)
    sim_completion = sim_success / sim_total if sim_total > 0 else 0
    sim_escalation = sim_partial / sim_total if sim_total > 0 else 0
    sim_accuracy = float(np.mean(sim_qualities)) if sim_qualities else 0
    sim_avg_time = float(np.mean(sim_latencies)) if sim_latencies else 0
    sim_auop = sim_completion * sim_accuracy
    sim_cost_per = sum(sim_costs) / sim_total if sim_total > 0 else 0

    # Estimate ROI shift
    baseline_roi = baseline_metrics.get("ai_roi", 0)
    roi_boost = (sim_completion - baseline_metrics.get("completion_rate", 0)) * 100
    sim_roi = baseline_roi + roi_boost * 5

    candidate_metrics = {
        "completion_rate": round(sim_completion, 4),
        "escalation_rate": round(sim_escalation, 4),
        "accuracy": round(sim_accuracy, 4),
        "avg_task_time": round(sim_avg_time, 1),
        "auop": round(sim_auop, 4),
        "cost_per_task": round(sim_cost_per, 6),
        "ai_roi": round(sim_roi, 1),
        "total_tasks": sim_total,
        "success_count": sim_success,
        "failure_count": sim_failure,
        "timeout_count": sim_timeout,
    }

    return ExperimentRecord(
        experiment_id=experiment_id, agent_id=agent_id,
        baseline_config_version=baseline_config.version,
        candidate_config_version=candidate_config.version,
        status=ExperimentStatus.COMPLETE,
        task_sample_size=sim_total,
        started_at=now, completed_at=datetime.utcnow(),
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        failure_patterns=failure_patterns_data,
        parameter_changes=param_changes,
    )


def get_parameter_recommendations(agent_id: str, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> list[dict]:
    """Analyze performance and suggest parameter changes."""
    m = compute_agent_metrics(agent_id, start_date, end_date)
    if m["total_tasks"] == 0:
        return []

    recs = []
    failure_rate = m["failure_count"] / m["total_tasks"]
    timeout_rate = m["timeout_count"] / m["total_tasks"]

    if failure_rate > 0.15:
        recs.append({
            "parameter": "prompt_precision",
            "current": 5, "suggested": 7,
            "reason": f"High failure rate ({failure_rate:.0%}) suggests prompts need more specificity",
            "estimated_impact": "+8-12% completion rate",
        })

    if m["escalation_rate"] > 0.10:
        recs.append({
            "parameter": "confidence_threshold",
            "current": 0.6, "suggested": 0.45,
            "reason": f"High escalation rate ({m['escalation_rate']:.0%}) — threshold may be too conservative",
            "estimated_impact": "+5-8% completion rate",
        })

    if timeout_rate > 0.05:
        recs.append({
            "parameter": "fallback_depth",
            "current": 2, "suggested": 1,
            "reason": f"Timeout rate ({timeout_rate:.0%}) suggests too many retries",
            "estimated_impact": "-30% avg task time",
        })

    if m["accuracy"] < 0.7:
        recs.append({
            "parameter": "data_prefetch",
            "current": False, "suggested": True,
            "reason": f"Low accuracy ({m['accuracy']:.2f}) — pre-fetching context may help",
            "estimated_impact": "+10-15% accuracy",
        })
        recs.append({
            "parameter": "prompt_precision",
            "current": 5, "suggested": 8,
            "reason": f"Low accuracy ({m['accuracy']:.2f}) — more specific prompts needed",
            "estimated_impact": "+5-10% accuracy",
        })

    if m["avg_task_time"] > 10000:
        recs.append({
            "parameter": "fallback_depth",
            "current": 2, "suggested": 1,
            "reason": f"Avg task time ({m['avg_task_time']:.0f}ms) is high — reduce retry depth",
            "estimated_impact": "-25% avg task time",
        })

    return recs


def compute_ratio_shift(start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        granularity: str = "day") -> pd.DataFrame:
    """Compute agent vs human handling ratio over time."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return pd.DataFrame()

    data = []
    for t in tasks:
        agent_handled = 1 if t.result == TaskResult.SUCCESS else 0
        data.append({
            "date": t.started_at,
            "agent_handled": agent_handled,
            "human_handled": 1 - agent_handled,
        })

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    if granularity == "hour":
        df["period"] = df["date"].dt.floor("h")
    elif granularity == "week":
        df["period"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)
    else:
        df["period"] = df["date"].dt.floor("D")

    grouped = df.groupby("period").agg(
        agent_count=("agent_handled", "sum"),
        human_count=("human_handled", "sum"),
        total_count=("agent_handled", "count"),
    ).reset_index()

    grouped["agent_pct"] = (grouped["agent_count"] / grouped["total_count"]).round(4)
    grouped["human_pct"] = (grouped["human_count"] / grouped["total_count"]).round(4)
    grouped = grouped.rename(columns={"period": "date"})

    return grouped
