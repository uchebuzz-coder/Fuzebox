"""Economic analysis: cost calculation, ROI, and token usage metrics."""

from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from . import db


def cost_per_agent(start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Total and average cost per agent."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return pd.DataFrame()

    agents = {a.agent_id: a.name for a in db.get_all_agents()}
    data = {}
    for t in tasks:
        aid = t.agent_id
        if aid not in data:
            data[aid] = {"agent": agents.get(aid, aid), "total_cost": 0, "task_count": 0,
                         "total_input_tokens": 0, "total_output_tokens": 0}
        data[aid]["total_cost"] += t.cost_usd
        data[aid]["task_count"] += 1
        data[aid]["total_input_tokens"] += t.input_tokens
        data[aid]["total_output_tokens"] += t.output_tokens

    rows = []
    for aid, d in data.items():
        rows.append({
            "Agent": d["agent"],
            "Tasks": d["task_count"],
            "Total Cost ($)": round(d["total_cost"], 4),
            "Avg Cost/Task ($)": round(d["total_cost"] / d["task_count"], 4) if d["task_count"] > 0 else 0,
            "Input Tokens": d["total_input_tokens"],
            "Output Tokens": d["total_output_tokens"],
        })

    return pd.DataFrame(rows).sort_values("Total Cost ($)", ascending=False).reset_index(drop=True)


def cost_per_task_type(start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Average cost grouped by task type."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return pd.DataFrame()

    data = {}
    for t in tasks:
        tt = t.task_type
        if tt not in data:
            data[tt] = {"costs": [], "tokens": [], "latencies": []}
        data[tt]["costs"].append(t.cost_usd)
        data[tt]["tokens"].append(t.total_tokens)
        data[tt]["latencies"].append(t.latency_ms or 0)

    rows = []
    for tt, d in data.items():
        rows.append({
            "Task Type": tt,
            "Count": len(d["costs"]),
            "Total Cost ($)": round(sum(d["costs"]), 4),
            "Avg Cost ($)": round(np.mean(d["costs"]), 4),
            "Avg Tokens": int(np.mean(d["tokens"])),
            "Avg Latency (ms)": round(np.mean(d["latencies"]), 1),
        })

    return pd.DataFrame(rows).sort_values("Total Cost ($)", ascending=False).reset_index(drop=True)


def calculate_roi(manual_cost_per_task: float = 50.0,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> dict:
    """Calculate ROI comparing agent costs to manual baseline."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return {"total_tasks": 0, "roi_pct": 0}

    successful = [t for t in tasks if t.result.value == "success"]
    agent_cost = sum(t.cost_usd for t in tasks)
    manual_cost = len(successful) * manual_cost_per_task
    savings = manual_cost - agent_cost

    return {
        "total_tasks": len(tasks),
        "successful_tasks": len(successful),
        "agent_total_cost": round(agent_cost, 2),
        "manual_equivalent_cost": round(manual_cost, 2),
        "savings": round(savings, 2),
        "roi_pct": round((savings / agent_cost * 100), 1) if agent_cost > 0 else 0,
        "cost_per_successful_task": round(agent_cost / len(successful), 4) if successful else 0,
    }


def token_usage_summary(start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> dict:
    """Token usage breakdown across all agents."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return {}

    total_input = sum(t.input_tokens for t in tasks)
    total_output = sum(t.output_tokens for t in tasks)
    total = total_input + total_output

    success_tokens = sum(t.total_tokens for t in tasks if t.result.value == "success")
    failed_tokens = sum(t.total_tokens for t in tasks if t.result.value == "failure")
    success_count = sum(1 for t in tasks if t.result.value == "success")
    failed_count = sum(1 for t in tasks if t.result.value == "failure")

    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total,
        "avg_tokens_per_task": int(total / len(tasks)) if tasks else 0,
        "avg_tokens_per_success": int(success_tokens / success_count) if success_count > 0 else 0,
        "avg_tokens_per_failure": int(failed_tokens / failed_count) if failed_count > 0 else 0,
        "input_output_ratio": round(total_input / total_output, 2) if total_output > 0 else 0,
        "token_efficiency": round(success_tokens / total, 4) if total > 0 else 0,
    }


def cost_time_series(start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     granularity: str = "day") -> pd.DataFrame:
    """Time series of costs for trend visualization."""
    tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if not tasks:
        return pd.DataFrame()

    data = []
    for t in tasks:
        data.append({
            "date": t.started_at,
            "cost": t.cost_usd,
            "tokens": t.total_tokens,
            "agent_id": t.agent_id,
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
        total_cost=("cost", "sum"),
        total_tokens=("tokens", "sum"),
        task_count=("cost", "count")
    ).reset_index()

    grouped["cumulative_cost"] = grouped["total_cost"].cumsum()
    grouped = grouped.rename(columns={"period": "date"})

    return grouped


def workflow_economics(start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Economic analysis per workflow."""
    workflows = db.get_workflows(start_date=start_date, end_date=end_date)
    if not workflows:
        return pd.DataFrame()

    rows = []
    for wf in workflows:
        duration_ms = 0
        if wf.completed_at and wf.started_at:
            duration_ms = (wf.completed_at - wf.started_at).total_seconds() * 1000

        rows.append({
            "Workflow": wf.name,
            "Agents": len(wf.agent_ids),
            "Tasks": len(wf.task_ids),
            "Result": wf.result.value,
            "Cost ($)": round(wf.total_cost_usd, 4),
            "Duration (s)": round(duration_ms / 1000, 1),
            "Date": wf.started_at.strftime("%Y-%m-%d %H:%M"),
        })

    return pd.DataFrame(rows)
