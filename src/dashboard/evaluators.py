"""Task completion and skills/permissions evaluation for agents."""

from datetime import datetime
from typing import Optional

import pandas as pd

from .models import TaskResult
from . import db

# Scorecard thresholds
MIN_SUCCESS_RATE = 0.80
MAX_FAILURE_RATE = 0.10
MAX_TIMEOUT_RATE = 0.05
MIN_QUALITY_SCORE = 0.70


def evaluate_task_completion(agent_id: str, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> dict:
    """Evaluate an agent's task completion performance."""
    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    if not tasks:
        return {"agent_id": agent_id, "total_tasks": 0, "pass": False, "reason": "No tasks found"}

    total = len(tasks)
    counts = {r.value: 0 for r in TaskResult}
    for t in tasks:
        counts[t.result.value] += 1

    success_rate = counts["success"] / total
    failure_rate = counts["failure"] / total
    timeout_rate = counts["timeout"] / total
    partial_rate = counts["partial"] / total

    quality_scores = [t.quality_score for t in tasks if t.quality_score is not None]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    # Scorecard evaluation
    issues = []
    if success_rate < MIN_SUCCESS_RATE:
        issues.append(f"Success rate {success_rate:.1%} < {MIN_SUCCESS_RATE:.0%}")
    if failure_rate > MAX_FAILURE_RATE:
        issues.append(f"Failure rate {failure_rate:.1%} > {MAX_FAILURE_RATE:.0%}")
    if timeout_rate > MAX_TIMEOUT_RATE:
        issues.append(f"Timeout rate {timeout_rate:.1%} > {MAX_TIMEOUT_RATE:.0%}")
    if avg_quality < MIN_QUALITY_SCORE:
        issues.append(f"Avg quality {avg_quality:.2f} < {MIN_QUALITY_SCORE:.2f}")

    return {
        "agent_id": agent_id,
        "total_tasks": total,
        "success_count": counts["success"],
        "failure_count": counts["failure"],
        "partial_count": counts["partial"],
        "timeout_count": counts["timeout"],
        "success_rate": round(success_rate, 4),
        "failure_rate": round(failure_rate, 4),
        "timeout_rate": round(timeout_rate, 4),
        "partial_rate": round(partial_rate, 4),
        "avg_quality": round(avg_quality, 4),
        "pass": len(issues) == 0,
        "issues": issues,
    }


def evaluate_group_completion(group: str, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> dict:
    """Evaluate task completion for a group of agents."""
    agents = db.get_agents_by_group(group)
    if not agents:
        return {"group": group, "agents": 0, "pass": False, "reason": "No agents in group"}

    agent_evals = []
    for agent in agents:
        ev = evaluate_task_completion(agent.agent_id, start_date, end_date)
        agent_evals.append(ev)

    total_tasks = sum(e["total_tasks"] for e in agent_evals)
    total_success = sum(e.get("success_count", 0) for e in agent_evals)
    passing = sum(1 for e in agent_evals if e.get("pass", False))

    return {
        "group": group,
        "agents": len(agents),
        "total_tasks": total_tasks,
        "group_success_rate": round(total_success / total_tasks, 4) if total_tasks > 0 else 0,
        "agents_passing": passing,
        "agents_failing": len(agents) - passing,
        "pass": passing == len(agents),
        "agent_evaluations": agent_evals,
    }


def get_skills_matrix(agent_ids: Optional[list[str]] = None) -> pd.DataFrame:
    """Build a skills matrix: agents (rows) x skills (columns) with boolean values."""
    agents = db.get_all_agents()
    if agent_ids:
        agents = [a for a in agents if a.agent_id in agent_ids]

    all_skills = sorted(set(s for a in agents for s in a.skills))
    data = []
    for agent in agents:
        row = {"agent": agent.name, "agent_id": agent.agent_id}
        for skill in all_skills:
            row[skill] = skill in agent.skills
        data.append(row)

    return pd.DataFrame(data)


def get_permissions_matrix(agent_ids: Optional[list[str]] = None) -> pd.DataFrame:
    """Build a permissions matrix: agents (rows) x permissions (columns)."""
    agents = db.get_all_agents()
    if agent_ids:
        agents = [a for a in agents if a.agent_id in agent_ids]

    all_perms = sorted(set(p for a in agents for p in a.permissions))
    data = []
    for agent in agents:
        row = {"agent": agent.name, "agent_id": agent.agent_id}
        for perm in all_perms:
            row[perm] = perm in agent.permissions
        data.append(row)

    return pd.DataFrame(data)


def check_permission_violations(agent_id: str, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> list[dict]:
    """Check if an agent attempted tasks requiring permissions it doesn't have."""
    agent = db.get_agent(agent_id)
    if not agent:
        return []

    tasks = db.get_tasks(agent_id=agent_id, start_date=start_date, end_date=end_date)
    violations = []
    for task in tasks:
        missing_perms = [p for p in task.required_permissions if p not in agent.permissions]
        missing_skills = [s for s in task.required_skills if s not in agent.skills]
        if missing_perms or missing_skills:
            violations.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "result": task.result.value,
                "missing_permissions": missing_perms,
                "missing_skills": missing_skills,
            })

    return violations


def get_agent_scorecard_df(start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Get a DataFrame of all agent evaluations for the scorecard view."""
    agents = db.get_all_agents()
    rows = []
    for agent in agents:
        ev = evaluate_task_completion(agent.agent_id, start_date, end_date)
        rows.append({
            "Agent": agent.name,
            "Group": agent.group,
            "Tasks": ev["total_tasks"],
            "Success Rate": ev.get("success_rate", 0),
            "Failure Rate": ev.get("failure_rate", 0),
            "Avg Quality": ev.get("avg_quality", 0),
            "Status": "PASS" if ev.get("pass", False) else "FAIL",
            "Issues": "; ".join(ev.get("issues", [])),
        })
    return pd.DataFrame(rows)
