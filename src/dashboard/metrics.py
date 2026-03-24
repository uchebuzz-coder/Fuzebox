"""Performance metrics aggregation for the dashboard."""

from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from . import db


def completion_rates(start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Success rate per agent."""
    agents = db.get_all_agents()
    rows = []
    for agent in agents:
        tasks = db.get_tasks(agent_id=agent.agent_id, start_date=start_date, end_date=end_date)
        if not tasks:
            continue
        total = len(tasks)
        success = sum(1 for t in tasks if t.result.value == "success")
        rows.append({
            "Agent": agent.name,
            "Group": agent.group,
            "Total Tasks": total,
            "Successful": success,
            "Completion Rate": round(success / total, 4),
        })
    return pd.DataFrame(rows)


def accuracy_by_type(agent_id: Optional[str] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Success rate per task type."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return pd.DataFrame()

    data = {}
    for t in tasks:
        tt = t.task_type
        if tt not in data:
            data[tt] = {"total": 0, "success": 0, "qualities": []}
        data[tt]["total"] += 1
        if t.result.value == "success":
            data[tt]["success"] += 1
        if t.quality_score is not None:
            data[tt]["qualities"].append(t.quality_score)

    rows = []
    for tt, d in data.items():
        rows.append({
            "Task Type": tt,
            "Total": d["total"],
            "Success": d["success"],
            "Success Rate": round(d["success"] / d["total"], 4) if d["total"] > 0 else 0,
            "Avg Quality": round(np.mean(d["qualities"]), 4) if d["qualities"] else 0,
        })

    return pd.DataFrame(rows).sort_values("Success Rate", ascending=False).reset_index(drop=True)


def latency_stats(agent_id: Optional[str] = None,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> dict:
    """Latency percentiles and statistics."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    latencies = [t.latency_ms for t in tasks if t.latency_ms is not None]
    if not latencies:
        return {}

    arr = np.array(latencies)
    return {
        "count": len(arr),
        "mean_ms": round(float(np.mean(arr)), 1),
        "median_ms": round(float(np.median(arr)), 1),
        "std_ms": round(float(np.std(arr)), 1),
        "p50_ms": round(float(np.percentile(arr, 50)), 1),
        "p90_ms": round(float(np.percentile(arr, 90)), 1),
        "p95_ms": round(float(np.percentile(arr, 95)), 1),
        "p99_ms": round(float(np.percentile(arr, 99)), 1),
        "min_ms": round(float(np.min(arr)), 1),
        "max_ms": round(float(np.max(arr)), 1),
    }


def latency_by_agent(start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Latency statistics per agent."""
    agents = db.get_all_agents()
    rows = []
    for agent in agents:
        stats = latency_stats(agent.agent_id, start_date, end_date)
        if stats:
            rows.append({
                "Agent": agent.name,
                "Mean (ms)": stats["mean_ms"],
                "P50 (ms)": stats["p50_ms"],
                "P90 (ms)": stats["p90_ms"],
                "P99 (ms)": stats["p99_ms"],
                "Tasks": stats["count"],
            })
    return pd.DataFrame(rows)


def throughput_time_series(agent_id: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           granularity: str = "day") -> pd.DataFrame:
    """Tasks per time period for throughput visualization."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return pd.DataFrame()

    data = []
    for t in tasks:
        data.append({
            "date": t.started_at,
            "success": 1 if t.result.value == "success" else 0,
            "latency": t.latency_ms or 0,
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
        task_count=("success", "count"),
        success_count=("success", "sum"),
        avg_latency=("latency", "mean"),
    ).reset_index()

    grouped["success_rate"] = (grouped["success_count"] / grouped["task_count"]).round(4)
    grouped = grouped.rename(columns={"period": "date"})

    return grouped


def agent_leaderboard(start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Rank agents by a composite performance score."""
    agents = db.get_all_agents()
    rows = []

    for agent in agents:
        tasks = db.get_tasks(agent_id=agent.agent_id, start_date=start_date, end_date=end_date)
        if not tasks:
            continue

        total = len(tasks)
        success = sum(1 for t in tasks if t.result.value == "success")
        success_rate = success / total

        latencies = [t.latency_ms for t in tasks if t.latency_ms is not None]
        avg_latency = np.mean(latencies) if latencies else 30000

        qualities = [t.quality_score for t in tasks if t.quality_score is not None]
        avg_quality = np.mean(qualities) if qualities else 0

        total_cost = sum(t.cost_usd for t in tasks)
        cost_per_success = total_cost / success if success > 0 else total_cost

        # Composite score: higher is better
        # 40% success rate + 30% quality + 20% speed (inverse latency) + 10% efficiency (inverse cost)
        speed_score = max(0, 1 - (avg_latency / 30000))  # normalize to 0-1
        efficiency_score = max(0, 1 - (cost_per_success / 1.0))  # normalize

        composite = (0.4 * success_rate + 0.3 * avg_quality +
                     0.2 * speed_score + 0.1 * efficiency_score)

        rows.append({
            "Agent": agent.name,
            "Group": agent.group,
            "Model": agent.model_name,
            "Tasks": total,
            "Success Rate": round(success_rate, 3),
            "Avg Quality": round(float(avg_quality), 3),
            "Avg Latency (ms)": round(float(avg_latency), 0),
            "Total Cost ($)": round(total_cost, 4),
            "Score": round(composite, 3),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Score", ascending=False).reset_index(drop=True)
        df.index = df.index + 1  # 1-based ranking
        df.index.name = "Rank"
    return df


def performance_summary(start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> dict:
    """High-level performance summary for KPI cards."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return {"total_tasks": 0}

    total = len(tasks)
    success = sum(1 for t in tasks if t.result.value == "success")
    total_cost = sum(t.cost_usd for t in tasks)
    latencies = [t.latency_ms for t in tasks if t.latency_ms is not None]
    qualities = [t.quality_score for t in tasks if t.quality_score is not None]

    workflows = db.get_workflows(start_date=start_date, end_date=end_date)
    wf_success = sum(1 for w in workflows if w.result.value == "success")

    return {
        "total_tasks": total,
        "successful_tasks": success,
        "success_rate": round(success / total, 4) if total > 0 else 0,
        "total_cost": round(total_cost, 2),
        "avg_cost_per_task": round(total_cost / total, 4) if total > 0 else 0,
        "avg_latency_ms": round(float(np.mean(latencies)), 1) if latencies else 0,
        "p90_latency_ms": round(float(np.percentile(latencies, 90)), 1) if latencies else 0,
        "avg_quality": round(float(np.mean(qualities)), 3) if qualities else 0,
        "total_workflows": len(workflows),
        "workflow_success_rate": round(wf_success / len(workflows), 4) if workflows else 0,
        "active_agents": len(set(t.agent_id for t in tasks)),
    }
