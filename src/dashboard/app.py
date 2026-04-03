"""Streamlit dashboard for Agent Performance monitoring."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta

from . import db, evaluators, economics, metrics
from .playground import render_playground


# ---------------------------------------------------------------------------
# Cached resource initialisers — called once per Streamlit session
# ---------------------------------------------------------------------------

@st.cache_resource
def _init_agent_registry():
    """Load all agent YAML configs and populate the AgentRegistry."""
    try:
        from src.dashboard.agent_protocol import init_registry
        return init_registry()
    except Exception:
        return None


@st.cache_resource
def _init_market_service():
    """Return a StockDataService backed by the default yfinance source."""
    try:
        from src.market.service import get_stock_service
        return get_stock_service()
    except Exception:
        return None


def main():
    st.set_page_config(
        page_title="Agent Performance Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize database and optional services
    db.init_db()
    _init_agent_registry()
    _init_market_service()

    # ---- Sidebar ----
    st.sidebar.title("Agent Performance Dashboard")

    # Demo data button
    if st.sidebar.button("Load Demo Data", type="primary"):
        with st.spinner("Generating demo data..."):
            result = db.seed_demo_data()
        st.sidebar.success(f"Loaded {result['agents']} agents, {result['tasks']} tasks, "
                           f"{result['spans']} spans, {result['workflows']} workflows")
        st.rerun()

    # Date range filter
    st.sidebar.subheader("Filters")
    date_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 7 days", "Last 14 days", "Last 30 days", "All time"],
        index=0
    )

    now = datetime.utcnow()
    if date_range == "Last 7 days":
        start_date = now - timedelta(days=7)
    elif date_range == "Last 14 days":
        start_date = now - timedelta(days=14)
    elif date_range == "Last 30 days":
        start_date = now - timedelta(days=30)
    else:
        start_date = None
    end_date = now

    # Agent filter
    all_agents = db.get_all_agents()
    agent_names = {a.name: a.agent_id for a in all_agents}
    selected_agents = st.sidebar.multiselect("Agents", list(agent_names.keys()))
    selected_agent_ids = [agent_names[n] for n in selected_agents] if selected_agents else None

    # Group filter
    groups = sorted(set(a.group for a in all_agents))
    selected_group = st.sidebar.selectbox("Group", ["All"] + groups)

    # Navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Agent Registry", "Task Scorecards",
         "Economic Analysis", "Performance Metrics", "Workflow Traces",
         "Market Intelligence", "Agent Playground"]
    )

    # ---- Pages ----
    if page == "Overview":
        render_overview(start_date, end_date, selected_agent_ids)
    elif page == "Agent Registry":
        render_agent_registry(selected_agent_ids)
    elif page == "Task Scorecards":
        render_scorecards(start_date, end_date, selected_agent_ids, selected_group)
    elif page == "Economic Analysis":
        render_economics(start_date, end_date)
    elif page == "Performance Metrics":
        render_performance(start_date, end_date, selected_agent_ids)
    elif page == "Workflow Traces":
        render_traces(start_date, end_date)
    elif page == "Market Intelligence":
        render_market_intelligence()
    elif page == "Agent Playground":
        render_playground()


# ==================== OVERVIEW ====================

def render_overview(start_date, end_date, agent_ids):
    st.title("Dashboard Overview")

    summary = metrics.performance_summary(start_date, end_date)
    if summary.get("total_tasks", 0) == 0:
        st.info("No data available. Click 'Load Demo Data' in the sidebar to get started.")
        return

    # KPI cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Tasks", f"{summary['total_tasks']:,}")
    col2.metric("Success Rate", f"{summary['success_rate']:.1%}")
    col3.metric("Avg Quality", f"{summary['avg_quality']:.2f}")
    col4.metric("Avg Latency", f"{summary['avg_latency_ms']:,.0f}ms")
    col5.metric("Total Cost", f"${summary['total_cost']:.2f}")
    col6.metric("Active Agents", summary['active_agents'])

    st.divider()

    # Second row of KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Workflows", summary['total_workflows'])
    col2.metric("Workflow Success", f"{summary['workflow_success_rate']:.1%}")
    col3.metric("P90 Latency", f"{summary['p90_latency_ms']:,.0f}ms")
    col4.metric("Avg Cost/Task", f"${summary['avg_cost_per_task']:.4f}")

    st.divider()

    # Charts row
    left, right = st.columns(2)

    with left:
        st.subheader("Cost Trend")
        cost_ts = economics.cost_time_series(start_date, end_date)
        if not cost_ts.empty:
            fig, ax1 = plt.subplots(figsize=(8, 4))
            ax1.fill_between(cost_ts["date"], cost_ts["total_cost"], alpha=0.3, color="#2196F3")
            ax1.plot(cost_ts["date"], cost_ts["total_cost"], color="#2196F3", linewidth=1.5)
            ax1.set_ylabel("Daily Cost ($)", color="#2196F3")
            ax2 = ax1.twinx()
            ax2.plot(cost_ts["date"], cost_ts["cumulative_cost"], color="#FF5722",
                     linewidth=2, linestyle="--")
            ax2.set_ylabel("Cumulative Cost ($)", color="#FF5722")
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    with right:
        st.subheader("Throughput & Success Rate")
        tp = metrics.throughput_time_series(start_date=start_date, end_date=end_date)
        if not tp.empty:
            fig, ax1 = plt.subplots(figsize=(8, 4))
            ax1.bar(tp["date"], tp["task_count"], alpha=0.6, color="#4CAF50", label="Tasks")
            ax1.set_ylabel("Task Count", color="#4CAF50")
            ax2 = ax1.twinx()
            ax2.plot(tp["date"], tp["success_rate"], color="#FF9800", linewidth=2, marker="o", markersize=3)
            ax2.set_ylabel("Success Rate", color="#FF9800")
            ax2.set_ylim(0, 1.05)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # Leaderboard
    st.subheader("Agent Leaderboard")
    lb = metrics.agent_leaderboard(start_date, end_date)
    if not lb.empty:
        st.dataframe(lb, use_container_width=True)


# ==================== AGENT REGISTRY ====================

def render_agent_registry(agent_ids):
    st.title("Agent Registry")

    agents = db.get_all_agents()
    if not agents:
        st.info("No agents registered. Load demo data to get started.")
        return

    # Agent table
    agent_data = []
    for a in agents:
        agent_data.append({
            "Name": a.name,
            "Group": a.group,
            "Status": a.status.value.upper(),
            "Model": a.model_name,
            "Skills": len(a.skills),
            "Permissions": len(a.permissions),
            "Input $/1K": a.cost_per_1k_input,
            "Output $/1K": a.cost_per_1k_output,
        })
    st.dataframe(pd.DataFrame(agent_data), use_container_width=True)

    st.divider()

    # Skills and Permissions matrices
    left, right = st.columns(2)

    with left:
        st.subheader("Skills Matrix")
        skills_df = evaluators.get_skills_matrix(agent_ids)
        if not skills_df.empty:
            display_df = skills_df.set_index("agent").drop(columns=["agent_id"], errors="ignore")
            # Style: green for True, gray for False
            styled = display_df.style.map(
                lambda v: "background-color: #4CAF50; color: white" if v else "background-color: #EEEEEE"
            )
            st.dataframe(styled, use_container_width=True)

    with right:
        st.subheader("Permissions Matrix")
        perms_df = evaluators.get_permissions_matrix(agent_ids)
        if not perms_df.empty:
            display_df = perms_df.set_index("agent").drop(columns=["agent_id"], errors="ignore")
            styled = display_df.style.map(
                lambda v: "background-color: #2196F3; color: white" if v else "background-color: #EEEEEE"
            )
            st.dataframe(styled, use_container_width=True)

    # Registry routing table
    st.divider()
    st.subheader("Registry Routing")
    registry = _init_agent_registry()
    if registry and not registry.is_empty():
        routing = registry.routing_table()
        agent_name_map = {a.agent_id: a.name for a in agents}
        routing_rows = []
        for task_type, agent_ids in sorted(routing.items()):
            routing_rows.append({
                "Task Type": task_type,
                "Agents (in priority order)": " → ".join(
                    agent_name_map.get(aid, aid) for aid in agent_ids
                ),
                "Agent Count": len(agent_ids),
            })
        if routing_rows:
            st.dataframe(pd.DataFrame(routing_rows), use_container_width=True)
        else:
            st.info("No routing entries — load demo data or run agents.")
    else:
        st.info("AgentRegistry is empty. Agents are registered when run_agent.py is executed "
                "or when YAML configs exist in the agents/ directory.")

    # Permission violations
    st.subheader("Permission Violations")
    all_violations = []
    for a in agents:
        violations = evaluators.check_permission_violations(a.agent_id)
        for v in violations:
            v["agent"] = a.name
            all_violations.append(v)

    if all_violations:
        st.warning(f"Found {len(all_violations)} permission/skill violations")
        st.dataframe(pd.DataFrame(all_violations), use_container_width=True)
    else:
        st.success("No permission or skill violations detected")


# ==================== TASK SCORECARDS ====================

def render_scorecards(start_date, end_date, agent_ids, selected_group):
    st.title("Task Completion Scorecards")

    # Overall scorecard table
    scorecard_df = evaluators.get_agent_scorecard_df(start_date, end_date)
    if scorecard_df.empty:
        st.info("No task data available.")
        return

    if selected_group != "All":
        scorecard_df = scorecard_df[scorecard_df["Group"] == selected_group]

    # Color the Status column
    def color_status(val):
        if val == "PASS":
            return "background-color: #4CAF50; color: white"
        return "background-color: #F44336; color: white"

    def color_rate(val):
        if isinstance(val, (int, float)):
            if val >= 0.8:
                return "background-color: #C8E6C9"
            elif val >= 0.6:
                return "background-color: #FFF9C4"
            return "background-color: #FFCDD2"
        return ""

    styled = scorecard_df.style.map(color_status, subset=["Status"])
    styled = styled.map(color_rate, subset=["Success Rate"])
    styled = styled.format({
        "Success Rate": "{:.1%}",
        "Failure Rate": "{:.1%}",
        "Avg Quality": "{:.2f}",
    })
    st.dataframe(styled, use_container_width=True)

    st.divider()

    # Group evaluation
    if selected_group != "All":
        st.subheader(f"Group Evaluation: {selected_group}")
        group_eval = evaluators.evaluate_group_completion(selected_group, start_date, end_date)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Agents", group_eval["agents"])
        col2.metric("Group Success Rate", f"{group_eval['group_success_rate']:.1%}")
        col3.metric("Passing Agents", group_eval["agents_passing"])
        col4.metric("Status", "PASS" if group_eval["pass"] else "FAIL")

    # Task type breakdown
    st.subheader("Success Rate by Task Type")
    acc_df = metrics.accuracy_by_type(start_date=start_date, end_date=end_date)
    if not acc_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = ["#4CAF50" if r >= 0.8 else "#FF9800" if r >= 0.6 else "#F44336"
                  for r in acc_df["Success Rate"]]
        bars = ax.barh(acc_df["Task Type"], acc_df["Success Rate"], color=colors)
        ax.set_xlim(0, 1.0)
        ax.set_xlabel("Success Rate")
        for bar, val in zip(bars, acc_df["Success Rate"]):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val:.0%}", va='center', fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()


# ==================== ECONOMIC ANALYSIS ====================

def render_economics(start_date, end_date):
    st.title("Economic Analysis")

    # ROI calculator
    st.subheader("ROI Calculator")
    manual_cost = st.slider("Manual cost per task ($)", 10, 200, 50, 5)
    roi = economics.calculate_roi(manual_cost, start_date, end_date)

    if roi.get("total_tasks", 0) > 0:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Agent Total Cost", f"${roi['agent_total_cost']:.2f}")
        col2.metric("Manual Equivalent", f"${roi['manual_equivalent_cost']:.2f}")
        col3.metric("Savings", f"${roi['savings']:.2f}")
        col4.metric("ROI", f"{roi['roi_pct']:.0f}%")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Cost by Agent")
        cpa = economics.cost_per_agent(start_date, end_date)
        if not cpa.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.barh(cpa["Agent"], cpa["Total Cost ($)"], color="#2196F3")
            ax.set_xlabel("Total Cost ($)")
            for bar, val in zip(bars, cpa["Total Cost ($)"]):
                ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                        f"${val:.3f}", va='center', fontsize=9)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.dataframe(cpa, use_container_width=True)

    with right:
        st.subheader("Cost by Task Type")
        cpt = economics.cost_per_task_type(start_date, end_date)
        if not cpt.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.barh(cpt["Task Type"], cpt["Total Cost ($)"], color="#FF9800")
            ax.set_xlabel("Total Cost ($)")
            for bar, val in zip(bars, cpt["Total Cost ($)"]):
                ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                        f"${val:.3f}", va='center', fontsize=9)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.dataframe(cpt, use_container_width=True)

    # Token usage
    st.divider()
    st.subheader("Token Usage Summary")
    tokens = economics.token_usage_summary(start_date, end_date)
    if tokens:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tokens", f"{tokens['total_tokens']:,}")
        col2.metric("Avg Tokens/Task", f"{tokens['avg_tokens_per_task']:,}")
        col3.metric("Input:Output Ratio", f"{tokens['input_output_ratio']:.2f}")
        col4.metric("Token Efficiency", f"{tokens['token_efficiency']:.1%}")

        # Token breakdown chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        ax1.pie([tokens["total_input_tokens"], tokens["total_output_tokens"]],
                labels=["Input", "Output"], autopct="%1.1f%%",
                colors=["#2196F3", "#FF5722"])
        ax1.set_title("Token Distribution")

        categories = ["Per Success", "Per Failure"]
        values = [tokens["avg_tokens_per_success"], tokens["avg_tokens_per_failure"]]
        ax2.bar(categories, values, color=["#4CAF50", "#F44336"])
        ax2.set_ylabel("Avg Tokens")
        ax2.set_title("Tokens by Outcome")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Cumulative cost trend
    st.subheader("Cumulative Cost Trend")
    cost_ts = economics.cost_time_series(start_date, end_date)
    if not cost_ts.empty:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(cost_ts["date"], cost_ts["cumulative_cost"], color="#2196F3", linewidth=2)
        ax.fill_between(cost_ts["date"], cost_ts["cumulative_cost"], alpha=0.2, color="#2196F3")
        ax.set_ylabel("Cumulative Cost ($)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Workflow economics
    st.subheader("Workflow Economics")
    wf_econ = economics.workflow_economics(start_date, end_date)
    if not wf_econ.empty:
        st.dataframe(wf_econ, use_container_width=True)


# ==================== PERFORMANCE METRICS ====================

def render_performance(start_date, end_date, agent_ids):
    st.title("Performance Metrics")

    # Completion rates
    left, right = st.columns(2)

    with left:
        st.subheader("Completion Rates")
        cr = metrics.completion_rates(start_date, end_date)
        if not cr.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            colors = ["#4CAF50" if r >= 0.8 else "#FF9800" if r >= 0.6 else "#F44336"
                      for r in cr["Completion Rate"]]
            ax.barh(cr["Agent"], cr["Completion Rate"], color=colors)
            ax.set_xlim(0, 1.0)
            ax.axvline(x=0.8, color="#666", linestyle="--", alpha=0.5, label="Threshold (80%)")
            ax.set_xlabel("Success Rate")
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    with right:
        st.subheader("Latency by Agent")
        lat = metrics.latency_by_agent(start_date, end_date)
        if not lat.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            x = range(len(lat))
            width = 0.35
            ax.bar([i - width / 2 for i in x], lat["P50 (ms)"], width, label="P50", color="#2196F3")
            ax.bar([i + width / 2 for i in x], lat["P90 (ms)"], width, label="P90", color="#FF5722")
            ax.set_xticks(list(x))
            ax.set_xticklabels(lat["Agent"], rotation=45, ha="right")
            ax.set_ylabel("Latency (ms)")
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    st.divider()

    # Latency distribution
    st.subheader("Latency Distribution")
    all_tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    if all_tasks:
        latencies = [t.latency_ms for t in all_tasks if t.latency_ms is not None]
        if latencies:
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.hist(latencies, bins=50, color="#2196F3", alpha=0.7, edgecolor="white")
            stats = metrics.latency_stats(start_date=start_date, end_date=end_date)
            if stats:
                ax.axvline(stats["p50_ms"], color="#4CAF50", linestyle="--", label=f"P50: {stats['p50_ms']:.0f}ms")
                ax.axvline(stats["p90_ms"], color="#FF9800", linestyle="--", label=f"P90: {stats['p90_ms']:.0f}ms")
                ax.axvline(stats["p99_ms"], color="#F44336", linestyle="--", label=f"P99: {stats['p99_ms']:.0f}ms")
            ax.set_xlabel("Latency (ms)")
            ax.set_ylabel("Count")
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    st.divider()

    # Throughput trend
    st.subheader("Throughput Trend")
    granularity = st.selectbox("Granularity", ["day", "hour", "week"], index=0)
    tp = metrics.throughput_time_series(start_date=start_date, end_date=end_date,
                                        granularity=granularity)
    if not tp.empty:
        fig, ax1 = plt.subplots(figsize=(12, 5))
        ax1.bar(tp["date"], tp["task_count"], alpha=0.6, color="#4CAF50", label="Tasks")
        ax1.set_ylabel("Task Count", color="#4CAF50")
        ax2 = ax1.twinx()
        ax2.plot(tp["date"], tp["success_rate"], color="#FF9800", linewidth=2, marker="o", markersize=3)
        ax2.set_ylabel("Success Rate", color="#FF9800")
        ax2.set_ylim(0, 1.05)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Leaderboard
    st.divider()
    st.subheader("Agent Leaderboard")
    lb = metrics.agent_leaderboard(start_date, end_date)
    if not lb.empty:
        def color_score(val):
            if isinstance(val, (int, float)):
                if val >= 0.7:
                    return "background-color: #C8E6C9"
                elif val >= 0.5:
                    return "background-color: #FFF9C4"
                return "background-color: #FFCDD2"
            return ""

        styled = lb.style.map(color_score, subset=["Score"])
        styled = styled.format({
            "Success Rate": "{:.1%}",
            "Avg Quality": "{:.2f}",
            "Avg Latency (ms)": "{:,.0f}",
            "Total Cost ($)": "${:.4f}",
            "Score": "{:.3f}",
        })
        st.dataframe(styled, use_container_width=True)


# ==================== WORKFLOW TRACES ====================

def render_traces(start_date, end_date):
    st.title("Workflow Traces")

    trace_ids = db.get_unique_trace_ids(limit=50)
    if not trace_ids:
        st.info("No trace data available.")
        return

    # Trace selector
    selected_trace = st.selectbox("Select Trace", trace_ids)

    if selected_trace:
        spans = db.get_spans(trace_id=selected_trace)
        if not spans:
            st.warning("No spans found for this trace.")
            return

        # Trace summary
        agents_in_trace = set(s.agent_id for s in spans)
        agent_map = {a.agent_id: a.name for a in db.get_all_agents()}
        total_duration = sum(s.duration_ms or 0 for s in spans if s.parent_span_id is None)
        errors = sum(1 for s in spans if s.status == "ERROR")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Spans", len(spans))
        col2.metric("Agents", len(agents_in_trace))
        col3.metric("Root Duration", f"{total_duration:,.0f}ms")
        col4.metric("Errors", errors)

        st.divider()

        # Gantt chart
        st.subheader("Trace Timeline")
        fig, ax = plt.subplots(figsize=(14, max(4, len(spans) * 0.3)))

        # Sort spans by start time
        spans_sorted = sorted(spans, key=lambda s: s.started_at)
        min_time = min(s.started_at for s in spans_sorted)

        colors_map = {}
        color_palette = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336",
                         "#00BCD4", "#795548", "#607D8B"]
        for i, aid in enumerate(sorted(agents_in_trace)):
            colors_map[aid] = color_palette[i % len(color_palette)]

        y_labels = []
        for i, span in enumerate(spans_sorted):
            start_offset = (span.started_at - min_time).total_seconds() * 1000
            duration = span.duration_ms or 0
            depth = 0
            if span.parent_span_id:
                parent_ids = [s.span_id for s in spans_sorted]
                if span.parent_span_id in parent_ids:
                    depth = 1
                    # Check for grandparent
                    parent = next((s for s in spans_sorted if s.span_id == span.parent_span_id), None)
                    if parent and parent.parent_span_id:
                        depth = 2

            color = colors_map.get(span.agent_id, "#999")
            alpha = 1.0 if span.status == "OK" else 0.5
            edgecolor = "red" if span.status == "ERROR" else "none"

            ax.barh(i, duration, left=start_offset, height=0.6,
                    color=color, alpha=alpha, edgecolor=edgecolor, linewidth=2 if edgecolor == "red" else 0)

            label = span.operation
            if depth == 0:
                label = f"[{agent_map.get(span.agent_id, span.agent_id)}] {label}"
            y_labels.append(f"{'  ' * depth}{label}")

        ax.set_yticks(range(len(spans_sorted)))
        ax.set_yticklabels(y_labels, fontsize=8)
        ax.set_xlabel("Time (ms)")
        ax.invert_yaxis()

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=c, label=agent_map.get(aid, aid))
                          for aid, c in colors_map.items()]
        ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Span details table
        st.subheader("Span Details")
        span_data = []
        for s in spans_sorted:
            span_data.append({
                "Operation": s.operation,
                "Agent": agent_map.get(s.agent_id, s.agent_id),
                "Duration (ms)": round(s.duration_ms, 1) if s.duration_ms else 0,
                "Status": s.status,
                "Attributes": str(s.attributes) if s.attributes else "",
            })
        st.dataframe(pd.DataFrame(span_data), use_container_width=True)


# ==================== MARKET INTELLIGENCE ====================

def render_market_intelligence():
    st.title("Market Intelligence")

    svc = _init_market_service()
    if svc is None:
        st.error("Market service unavailable. Ensure src/market/ is installed correctly.")
        return

    # Load ticker mapping for display names
    tickers_in_db = svc.get_available_tickers()

    # Build display-name -> real-ticker map
    ticker_display: dict[str, str] = {}
    for t in tickers_in_db:
        display = f"{svc.get_display_name(t)} ({svc.get_display_ticker(t)})"
        ticker_display[display] = t

    col_controls, col_fetch = st.columns([3, 1])

    with col_fetch:
        st.markdown("**Fetch New Data**")
        fetch_ticker_raw = st.text_input("Ticker symbol", value="RBLX",
                                         help="Real market ticker, e.g. RBLX, AAPL")
        fetch_days = st.number_input("Days back", min_value=1, max_value=1825, value=90)
        if st.button("Fetch from Yahoo Finance", type="primary"):
            import datetime as _dt
            end_dt = _dt.date.today()
            start_dt = end_dt - _dt.timedelta(days=int(fetch_days))
            with st.spinner(f"Fetching {fetch_ticker_raw} data..."):
                stored = svc.fetch_and_store(
                    fetch_ticker_raw.upper(), start=start_dt, end=end_dt
                )
            if stored:
                st.success(f"Stored {stored} trading days for {fetch_ticker_raw.upper()}.")
                st.rerun()
            else:
                st.warning("No data returned. Check the ticker symbol or date range.")

    if not tickers_in_db:
        st.info("No market data in the database yet. Use the 'Fetch New Data' panel to load prices.")
        return

    with col_controls:
        selected_display = st.selectbox("Ticker", list(ticker_display.keys()))
        selected_ticker = ticker_display[selected_display]

        import datetime as _dt
        col_d1, col_d2 = st.columns(2)
        default_start = _dt.date.today() - _dt.timedelta(days=90)
        view_start = col_d1.date_input("From", value=default_start)
        view_end = col_d2.date_input("To", value=_dt.date.today())

    st.divider()

    df = svc.get_prices(selected_ticker, start=view_start, end=view_end)
    if df.empty:
        st.info(f"No price data for {selected_ticker} in the selected range. "
                f"Try fetching data first.")
        return

    # KPI strip
    latest = df.iloc[-1]
    earliest = df.iloc[0]
    period_return = (latest["close"] - earliest["close"]) / earliest["close"]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Latest Close", f"${latest['close']:.2f}")
    col2.metric("Period High", f"${df['high'].max():.2f}")
    col3.metric("Period Low", f"${df['low'].min():.2f}")
    col4.metric("Period Return", f"{period_return:+.1%}")
    col5.metric("Trading Days", len(df))

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Price History")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(df["date"], df["close"], color="#2196F3", linewidth=1.5, label="Close")
        ax.fill_between(df["date"], df["low"], df["high"], alpha=0.15, color="#2196F3", label="Low–High")
        ax.set_ylabel("Price ($)")
        ax.set_xlabel("")
        display_name = svc.get_display_name(selected_ticker)
        display_tick = svc.get_display_ticker(selected_ticker)
        ax.set_title(f"{display_name} ({display_tick})")
        ax.legend(fontsize=8)
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with right:
        st.subheader("Daily Returns")
        df_ret = df.copy()
        df_ret["daily_return"] = df_ret["close"].pct_change()
        df_ret["cumulative_return"] = (1 + df_ret["daily_return"].fillna(0)).cumprod() - 1

        fig, ax1 = plt.subplots(figsize=(8, 4))
        colors = ["#4CAF50" if r >= 0 else "#F44336" for r in df_ret["daily_return"].fillna(0)]
        ax1.bar(df_ret["date"], df_ret["daily_return"].fillna(0), color=colors, alpha=0.7)
        ax1.set_ylabel("Daily Return", color="#555")
        ax1.axhline(0, color="#999", linewidth=0.8)
        ax2 = ax1.twinx()
        ax2.plot(df_ret["date"], df_ret["cumulative_return"], color="#FF9800",
                 linewidth=2, label="Cumulative")
        ax2.set_ylabel("Cumulative Return", color="#FF9800")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Volume chart
    st.subheader("Volume")
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.bar(df["date"], df["volume"], color="#9C27B0", alpha=0.7)
    ax.set_ylabel("Volume")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Raw data table
    st.subheader("Price Data")
    display_df = df.copy()
    display_df["date"] = display_df["date"].astype(str)
    st.dataframe(display_df, use_container_width=True)


if __name__ == "__main__":
    main()
