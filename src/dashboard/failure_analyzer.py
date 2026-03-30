"""Deterministic failure pattern clustering and analysis for agent tasks."""

from datetime import datetime
from typing import Optional
import hashlib

import pandas as pd
import numpy as np

from . import db
from .models import TaskResult


def _latency_bucket(ms: float) -> str:
    if ms < 1000:
        return "<1s"
    elif ms < 5000:
        return "1-5s"
    elif ms < 15000:
        return "5-15s"
    else:
        return ">15s"


def _quality_bucket(score: float) -> str:
    if score < 0.2:
        return "very_low"
    elif score < 0.5:
        return "low"
    elif score < 0.7:
        return "medium"
    else:
        return "acceptable"


def _make_pattern_id(agent_id: str, key: tuple) -> str:
    raw = f"{agent_id}:{':'.join(str(k) for k in key)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _describe_pattern(task_type: str, result: str, latency_bkt: str, quality_bkt: str) -> str:
    result_label = {
        "failure": "Hard failures",
        "timeout": "Timeouts",
        "partial": "Partial completions",
    }.get(result, result.title())

    quality_label = {
        "very_low": "with very low quality output",
        "low": "with low quality output",
        "medium": "with medium quality output",
        "acceptable": "",
    }.get(quality_bkt, "")

    latency_label = {
        "<1s": "(fast execution)",
        "1-5s": "",
        "5-15s": "(slow execution)",
        ">15s": "(very slow execution)",
    }.get(latency_bkt, "")

    parts = [f"{result_label} on {task_type} tasks"]
    if quality_label:
        parts.append(quality_label)
    if latency_label:
        parts.append(latency_label)
    return " ".join(parts)


def suggest_parameter_fix(pattern: dict) -> str:
    """Rule-based parameter adjustment suggestion for a failure pattern."""
    attrs = pattern.get("common_attributes", {})
    result = attrs.get("result", "")
    quality_bkt = attrs.get("quality_bucket", "")
    latency_bkt = attrs.get("latency_bucket", "")
    task_types = pattern.get("affected_task_types", [])

    if result == "timeout" or latency_bkt == ">15s":
        return "Consider reducing fallback_depth or enabling data_prefetch to avoid timeouts"
    if quality_bkt in ("very_low", "low"):
        return "Try increasing prompt_precision to 7-8 for more specific instructions"
    if result == "failure":
        if "planning" in task_types or "research" in task_types:
            return "Lower confidence_threshold to let the agent attempt more tasks"
        return "Increase fallback_depth to give the agent more retry strategies"
    if result == "partial":
        return "Lower confidence_threshold to reduce unnecessary escalations"
    return "Review agent logs for this failure pattern"


def analyze_failure_patterns(agent_id: str, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> list[dict]:
    """Cluster failed tasks into patterns using deterministic co-occurrence analysis."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return []

    total_tasks = len(tasks)
    failed = [t for t in tasks if t.result in (TaskResult.FAILURE, TaskResult.TIMEOUT, TaskResult.PARTIAL)]
    if not failed:
        return []

    # Group by (task_type, result, latency_bucket, quality_bucket)
    groups: dict[tuple, list] = {}
    for t in failed:
        latency = t.latency_ms or 0
        quality = t.quality_score or 0.0
        key = (t.task_type, t.result.value, _latency_bucket(latency), _quality_bucket(quality))
        groups.setdefault(key, []).append(t)

    patterns = []
    for key, group_tasks in groups.items():
        task_type, result, latency_bkt, quality_bkt = key
        count = len(group_tasks)
        pct = count / total_tasks

        if pct > 0.15:
            severity = "critical"
        elif pct > 0.05:
            severity = "warning"
        else:
            severity = "info"

        affected_types = sorted(set(t.task_type for t in group_tasks))
        common_attrs = {
            "result": result,
            "latency_bucket": latency_bkt,
            "quality_bucket": quality_bkt,
            "avg_latency_ms": round(np.mean([t.latency_ms or 0 for t in group_tasks]), 1),
            "avg_quality": round(np.mean([t.quality_score or 0 for t in group_tasks]), 3),
        }

        pattern = {
            "pattern_id": _make_pattern_id(agent_id, key),
            "agent_id": agent_id,
            "pattern_description": _describe_pattern(task_type, result, latency_bkt, quality_bkt),
            "occurrence_count": count,
            "severity": severity,
            "affected_task_types": affected_types,
            "common_attributes": common_attrs,
            "suggested_fix": "",
        }
        pattern["suggested_fix"] = suggest_parameter_fix(pattern)
        patterns.append(pattern)

    patterns.sort(key=lambda p: p["occurrence_count"], reverse=True)
    return patterns


def get_failure_waterfall(agent_id: str, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> dict:
    """Break down task outcomes into a waterfall of success/failure bands."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return {"total_tasks": 0, "bands": []}

    total = len(tasks)
    success = [t for t in tasks if t.result == TaskResult.SUCCESS]
    partial = [t for t in tasks if t.result == TaskResult.PARTIAL]
    failed = [t for t in tasks if t.result == TaskResult.FAILURE]
    timed_out = [t for t in tasks if t.result == TaskResult.TIMEOUT]

    bands = [
        {"label": "Completed Successfully", "count": len(success),
         "pct": round(len(success) / total, 4), "type": "success", "task_types": {}},
    ]

    if partial:
        type_counts = {}
        for t in partial:
            type_counts[t.task_type] = type_counts.get(t.task_type, 0) + 1
        bands.append({
            "label": "Partial Completion", "count": len(partial),
            "pct": round(len(partial) / total, 4), "type": "warning",
            "task_types": type_counts,
        })

    # Group failures by task type
    fail_by_type: dict[str, int] = {}
    for t in failed:
        fail_by_type[t.task_type] = fail_by_type.get(t.task_type, 0) + 1

    for tt, count in sorted(fail_by_type.items(), key=lambda x: -x[1]):
        bands.append({
            "label": f"Failed — {tt}", "count": count,
            "pct": round(count / total, 4), "type": "error",
            "task_types": {tt: count},
        })

    if timed_out:
        type_counts = {}
        for t in timed_out:
            type_counts[t.task_type] = type_counts.get(t.task_type, 0) + 1
        bands.append({
            "label": "Timed Out", "count": len(timed_out),
            "pct": round(len(timed_out) / total, 4), "type": "error",
            "task_types": type_counts,
        })

    return {"total_tasks": total, "bands": bands}


def get_failure_summary(agent_id: str, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> dict:
    """Compact failure summary with trend analysis."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return {"total_tasks": 0, "total_failures": 0, "failure_rate": 0,
                "top_patterns": [], "most_affected_task_type": "", "trend": "stable"}

    total = len(tasks)
    failures = [t for t in tasks if t.result in (TaskResult.FAILURE, TaskResult.TIMEOUT, TaskResult.PARTIAL)]
    failure_rate = len(failures) / total if total > 0 else 0

    # Top patterns
    patterns = analyze_failure_patterns(agent_id, start_date, end_date)
    top_patterns = patterns[:3]

    # Most affected task type
    type_counts: dict[str, int] = {}
    for t in failures:
        type_counts[t.task_type] = type_counts.get(t.task_type, 0) + 1
    most_affected = max(type_counts, key=type_counts.get) if type_counts else ""

    # Trend: compare first half vs second half
    sorted_tasks = sorted(tasks, key=lambda t: t.started_at)
    mid = len(sorted_tasks) // 2
    if mid > 0:
        first_half = sorted_tasks[:mid]
        second_half = sorted_tasks[mid:]
        first_fail_rate = sum(1 for t in first_half
                              if t.result in (TaskResult.FAILURE, TaskResult.TIMEOUT, TaskResult.PARTIAL)) / len(first_half)
        second_fail_rate = sum(1 for t in second_half
                               if t.result in (TaskResult.FAILURE, TaskResult.TIMEOUT, TaskResult.PARTIAL)) / len(second_half)
        if second_fail_rate < first_fail_rate - 0.03:
            trend = "improving"
        elif second_fail_rate > first_fail_rate + 0.03:
            trend = "degrading"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return {
        "total_tasks": total,
        "total_failures": len(failures),
        "failure_rate": round(failure_rate, 4),
        "top_patterns": top_patterns,
        "most_affected_task_type": most_affected,
        "trend": trend,
    }
