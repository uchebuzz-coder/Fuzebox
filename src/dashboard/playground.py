"""Agent Playground — interactive UI for running real Claude agent tasks.

Lets you select an agent, choose a task type, fill in inputs, and run tasks
directly from the dashboard. Every run is automatically recorded in the DB
(tokens, latency, cost, quality) and appears immediately in all other pages.
"""

from __future__ import annotations

import os
import time
import traceback

import streamlit as st

from src.dashboard import db
from src.dashboard.agent_protocol import get_registry
from src.dashboard.models import TaskType


# ---------------------------------------------------------------------------
# Task type definitions: labels, input fields, payload builder
# ---------------------------------------------------------------------------

_TASK_CONFIGS: dict[str, dict] = {
    TaskType.CODE_GENERATION: {
        "label": "Code Generation",
        "description": "Generate code from a natural language description.",
        "inputs": ["prompt"],
    },
    TaskType.CODE_REVIEW: {
        "label": "Code Review",
        "description": "Review code for quality, security, and performance.",
        "inputs": ["code", "language"],
    },
    TaskType.BUG_FIX: {
        "label": "Bug Fix",
        "description": "Diagnose an error and suggest a corrected version.",
        "inputs": ["code", "error", "language"],
    },
    TaskType.RESEARCH: {
        "label": "Research",
        "description": "Research a topic and return a structured summary.",
        "inputs": ["topic"],
    },
    TaskType.TEST_GENERATION: {
        "label": "Test Generation",
        "description": "Generate unit tests for a code snippet.",
        "inputs": ["code", "language"],
    },
}


def _api_key_present() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _agent_options() -> dict[str, str]:
    """Return {display_label: agent_id} for active agents that have a YAML config."""
    registry = get_registry()
    if not registry.is_empty():
        return {
            f"{a.agent_id}  [{getattr(a, '_model', a.agent_id)}]": a.agent_id
            for a in registry.all_agents()
        }
    # Fallback: active agents from DB
    agents = [a for a in db.get_all_agents() if a.status.value == "active"]
    return {f"{a.name}  ({a.model_name})": a.agent_id for a in agents}


def _task_options_for(agent_id: str) -> dict[str, TaskType]:
    """Return {label: TaskType} for task types the agent handles."""
    registry = get_registry()
    routing = registry.routing_table()
    supported = {
        tt for tt, agents in routing.items() if agent_id in agents
    }
    result = {}
    for task_type, cfg in _TASK_CONFIGS.items():
        if not supported or task_type.value in supported:
            result[cfg["label"]] = task_type
    return result


def _render_inputs(task_type: TaskType) -> dict | None:
    """Render input widgets for the given task type. Returns payload dict or None."""
    cfg = _TASK_CONFIGS[task_type]
    inputs = cfg["inputs"]
    payload: dict = {}

    if "prompt" in inputs:
        payload["prompt"] = st.text_area(
            "Prompt",
            height=150,
            placeholder="e.g. Write a Python function that finds the longest common subsequence of two strings.",
        )

    if "topic" in inputs:
        payload["topic"] = st.text_area(
            "Topic",
            height=100,
            placeholder="e.g. Python asyncio: event loop, coroutines, tasks, and common patterns",
        )

    if "code" in inputs:
        payload["code"] = st.text_area(
            "Code",
            height=250,
            placeholder="Paste your code here...",
        )

    if "error" in inputs:
        payload["error"] = st.text_area(
            "Error / Traceback",
            height=100,
            placeholder="e.g. ZeroDivisionError: division by zero\n  File 'main.py', line 4",
        )

    if "language" in inputs:
        payload["language"] = st.selectbox(
            "Language",
            ["python", "javascript", "typescript", "go", "rust", "java", "c++", "other"],
        )

    # Validate all required text fields are non-empty
    required_text = [k for k in inputs if k != "language"]
    if any(not payload.get(k, "").strip() for k in required_text):
        return None
    return payload


def render_playground():
    st.title("Agent Playground")
    st.caption("Run real Claude agent tasks directly from the dashboard. Every run is recorded automatically.")

    # ── API key check ──────────────────────────────────────────────────────
    if not _api_key_present():
        st.error(
            "**ANTHROPIC_API_KEY is not set.**  \n"
            "The playground requires a live API key to make real Claude calls.  \n"
            "Set it before launching the dashboard:  \n"
            "```\nexport ANTHROPIC_API_KEY=sk-ant-...\nstreamlit run dashboard_app.py\n```"
        )
        return

    # ── Agent + task type selectors ────────────────────────────────────────
    agent_options = _agent_options()
    if not agent_options:
        st.warning(
            "No agents are registered. Run `python run_agent.py demo` once to register agents, "
            "or click **Load Demo Data** in the sidebar."
        )
        return

    col_agent, col_task = st.columns(2)

    with col_agent:
        agent_label = st.selectbox("Agent", list(agent_options.keys()))
        agent_id = agent_options[agent_label]

    task_options = _task_options_for(agent_id)

    with col_task:
        task_label = st.selectbox("Task Type", list(task_options.keys()))
        task_type = task_options[task_label]

    st.caption(f"_{_TASK_CONFIGS[task_type]['description']}_")
    st.divider()

    # ── Input form ─────────────────────────────────────────────────────────
    with st.form("playground_form", clear_on_submit=False):
        payload = _render_inputs(task_type)
        submitted = st.form_submit_button("Run Task", type="primary", use_container_width=True)

    # ── Execution ──────────────────────────────────────────────────────────
    if submitted:
        if payload is None:
            st.warning("Please fill in all required fields before running.")
            return

        registry = get_registry()
        agent = registry.get(agent_id)

        if agent is None:
            st.error(
                f"Agent **{agent_id}** is not in the registry. "
                "Check that the agent YAML is present and lists this task type."
            )
            return

        result_text: str = ""
        error_msg: str = ""
        elapsed_ms: float = 0.0

        with st.spinner(f"Running **{task_label}** with `{agent.agent_id}` …"):
            t0 = time.perf_counter()
            try:
                result_text = agent.run_task(task_type, payload)
            except Exception as e:
                error_msg = str(e)
                st.error(f"**Task failed:** {error_msg}")
                with st.expander("Traceback"):
                    st.code(traceback.format_exc(), language="text")
            elapsed_ms = (time.perf_counter() - t0) * 1000

        if result_text:
            st.success(f"Completed in **{elapsed_ms:,.0f} ms**")

            # ── Result ─────────────────────────────────────────────────────
            st.subheader("Result")
            st.markdown(result_text)

            # ── Metrics from the most recent task ──────────────────────────
            st.divider()
            st.subheader("Task Metrics")

            recent = db.get_tasks(agent_id=agent.agent_id, task_type=task_type.value)
            if recent:
                t = recent[0]  # most recent first
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Result", t.result.value.upper())
                col2.metric("Latency", f"{t.latency_ms:,.0f} ms" if t.latency_ms else "—")
                col3.metric("Tokens", f"{t.total_tokens:,}")
                col4.metric("Cost", f"${t.cost_usd:.5f}")
                col5.metric("Quality", f"{t.quality_score:.2f}" if t.quality_score is not None else "—")

                with st.expander("Full task record"):
                    st.json({
                        "task_id": t.task_id,
                        "agent_id": t.agent_id,
                        "task_type": t.task_type,
                        "result": t.result.value,
                        "input_tokens": t.input_tokens,
                        "output_tokens": t.output_tokens,
                        "total_tokens": t.total_tokens,
                        "cost_usd": t.cost_usd,
                        "latency_ms": t.latency_ms,
                        "quality_score": t.quality_score,
                        "started_at": t.started_at.isoformat(),
                        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    })

            st.info("This task is now recorded — check **Task Scorecards**, **Economic Analysis**, and **Workflow Traces** for updated metrics.")
