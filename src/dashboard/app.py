"""Streamlit dashboard for Agent Performance monitoring."""

import uuid
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

from . import db, evaluators, economics, metrics, failure_analyzer, experiment_runner
from .models import AgentConfig, ExperimentStatus
from .styles import get_all_css, sidebar_css
from .components import (
    kpi_card, page_header, section, empty_state, card_wrap,
    search_filter, diff_html, plotly_layout, delta_html, agent_card_html, df_html_table,
)

# ── Helpers ──

def _sr_color(rate, good=0.8, warn=0.6):
    return "#22C55E" if rate >= good else "#F59E0B" if rate >= warn else "#EF4444"

def _get_active_agents():
    return [a for a in db.get_all_agents() if a.status.value == "active"]

def _agent_selector(agent_ids, key):
    active = _get_active_agents()
    if not active:
        return None
    amap = {a.name: a for a in active}
    default = None
    if agent_ids:
        for a in active:
            if a.agent_id in agent_ids:
                default = a.name; break
    idx = list(amap.keys()).index(default) if default and default in amap else 0
    name = st.selectbox("Select Agent", list(amap.keys()), index=idx, key=key)
    return amap[name]

def _ensure_baseline(agent_id):
    bl = db.get_baseline_config(agent_id)
    if bl: return bl
    c = AgentConfig(config_id=str(uuid.uuid4())[:12], agent_id=agent_id, version=1, is_baseline=True, notes="Default baseline")
    db.upsert_config(c)
    return c


# ==================== MAIN ====================

def main():
    st.set_page_config(page_title="Agent Performance Dashboard", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
    db.init_db()

    # ── Theme toggle (persisted in session state) ──
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    dark = st.session_state.dark_mode

    st.markdown(get_all_css(dark) + sidebar_css(), unsafe_allow_html=True)

    st.sidebar.html('<div class="sb-logo-wrap"><div class="sb-logo-icon">⚡</div><div><div class="sb-logo-title">FuzeBox</div><div class="sb-logo-sub">Agent Performance Platform</div></div></div>')
    if st.sidebar.button("☀️  Light Mode" if dark else "🌙  Dark Mode", use_container_width=True):
        st.session_state.dark_mode = not dark
        st.rerun()
    st.sidebar.html('<span class="sb-section-label">Workspace</span>')
    if st.sidebar.button("↑  Load Demo Data", type="primary", use_container_width=False):
        import time
        with st.spinner("Generating demo data..."):
            result = db.seed_demo_data()
            time.sleep(2.5)
        st.sidebar.success(f"Loaded {result['agents']} agents · {result['tasks']} tasks · {result['spans']} spans · {result['workflows']} workflows")
        st.rerun()

    st.sidebar.html('<span class="sb-section-label">Navigation</span>')
    NAV = ["🏠  Overview", "🤖  Agent Registry", "📋  Task Scorecards", "💰  Economic Analysis",
           "⚡  Performance Metrics", "🔍  Workflow Traces", "🔬  Diagnose", "🎛️  Tune", "🧪  Train", "📊  Compare"]
    sel = st.sidebar.radio("nav", NAV, label_visibility="collapsed")
    page = sel.split("  ", 1)[1]
    st.sidebar.html("<hr><span class='sb-section-label'>Filters</span>")

    dr = st.sidebar.selectbox("TIME RANGE", ["Last 7 days", "Last 14 days", "Last 30 days", "All time"], index=0)
    now = datetime.now()
    start_date = now - timedelta(days={"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30}.get(dr, 0)) if dr != "All time" else None
    end_date = now

    all_agents = db.get_all_agents()
    anames = {a.name: a.agent_id for a in all_agents}
    sa = st.sidebar.multiselect("AGENTS", list(anames.keys()))
    agent_ids = [anames[n] for n in sa] if sa else None
    groups = sorted(set(a.group for a in all_agents))
    selected_group = st.sidebar.selectbox("GROUP", ["All"] + groups)
    st.sidebar.html("<hr>")

    routes = {
        "Overview": lambda: render_overview(start_date, end_date, agent_ids),
        "Agent Registry": lambda: render_agent_registry(agent_ids),
        "Task Scorecards": lambda: render_scorecards(start_date, end_date, agent_ids, selected_group),
        "Economic Analysis": lambda: render_economics(start_date, end_date),
        "Performance Metrics": lambda: render_performance(start_date, end_date, agent_ids),
        "Workflow Traces": lambda: render_traces(start_date, end_date),
        "Diagnose": lambda: render_diagnose(start_date, end_date, agent_ids),
        "Tune": lambda: render_tune(start_date, end_date, agent_ids),
        "Train": lambda: render_train(start_date, end_date, agent_ids),
        "Compare": lambda: render_compare(start_date, end_date, agent_ids),
    }
    routes.get(page, routes["Overview"])()


# ==================== OVERVIEW ====================

def render_overview(start_date, end_date, agent_ids):
    range_label = f"Last {(datetime.now() - start_date).days} days" if start_date else "All time"
    page_header("Dashboard Overview", "Monitor agent performance, costs, and system health", [f"📅 {range_label}"])

    summary = metrics.performance_summary(start_date, end_date)
    if summary.get("total_tasks", 0) == 0:
        empty_state("⚡", "No data yet", "Click <strong>Load Demo Data</strong> in the sidebar to populate the dashboard.")
        return

    sr = summary["success_rate"]
    s = summary
    kpis = kpi_card("📊","Total Tasks",f"{s['total_tasks']:,}","#6366F1") + kpi_card("✅","Success Rate",f"{sr:.1%}",_sr_color(sr)) + kpi_card("⭐","Avg Quality",f"{s['avg_quality']:.2f}","#8B5CF6") + kpi_card("⚡","Avg Latency",f"{s['avg_latency_ms']:,.0f}ms","#06B6D4") + kpi_card("💰","Total Cost",f"${s['total_cost']:.2f}","#F59E0B") + kpi_card("🤖","Active Agents",str(s['active_agents']),"#10B981")
    st.html(f'<div class="kpi-grid">{kpis}</div>')

    wsr = s["workflow_success_rate"]
    kpis2 = kpi_card("🔁","Workflows",str(s["total_workflows"]),"#6366F1",small=True) + kpi_card("🎯","Workflow Success",f"{wsr:.1%}",_sr_color(wsr),small=True) + kpi_card("📈","P90 Latency",f"{s['p90_latency_ms']:,.0f}ms","#06B6D4",small=True) + kpi_card("🏷️","Avg Cost/Task",f"${s['avg_cost_per_task']:.4f}","#F59E0B",small=True)
    st.html(f'<div class="kpi-grid-4">{kpis2}</div>')

    section("Trends")
    left, right = st.columns(2, gap="medium")
    with left:
        st.html('<div class="chart-card"><div class="card-title">Cost Trend</div><div class="card-sub">Daily spend vs. cumulative total</div>')
        cost_ts = economics.cost_time_series(start_date, end_date)
        if not cost_ts.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cost_ts["date"], y=cost_ts["total_cost"], name="Daily Cost", line=dict(color="#6366F1", width=2), fill="tozeroy", fillcolor="rgba(99,102,241,0.12)", hovertemplate="$%{y:.4f}<extra>Daily</extra>"))
            fig.add_trace(go.Scatter(x=cost_ts["date"], y=cost_ts["cumulative_cost"], name="Cumulative", line=dict(color="#F59E0B", width=2, dash="dot"), hovertemplate="$%{y:.4f}<extra>Cumulative</extra>", yaxis="y2"))
            layout = plotly_layout()
            layout["yaxis2"] = dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10), color="#F59E0B")
            fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')
    with right:
        st.html('<div class="chart-card"><div class="card-title">Throughput & Success Rate</div><div class="card-sub">Task volume with success rate overlay</div>')
        tp = metrics.throughput_time_series(start_date=start_date, end_date=end_date)
        if not tp.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=tp["date"], y=tp["task_count"], name="Tasks", marker_color="rgba(16,185,129,0.55)", marker_line_color="rgba(16,185,129,0.8)", marker_line_width=1))
            fig.add_trace(go.Scatter(x=tp["date"], y=tp["success_rate"], name="Success Rate", line=dict(color="#F59E0B", width=2), mode="lines+markers", marker=dict(size=4), yaxis="y2"))
            layout = plotly_layout()
            layout["yaxis2"] = dict(overlaying="y", side="right", range=[0, 1.05], gridcolor="rgba(0,0,0,0)", tickformat=".0%", tickfont=dict(size=10), color="#F59E0B")
            fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    section("Agent Leaderboard")
    lb = metrics.agent_leaderboard(start_date, end_date)
    if not lb.empty:
        lb = search_filter(lb, "Agent", "ov_lb_search", "Search by agent name…")
        df_html_table(lb, formats={
            "Success Rate": lambda v: f'<span style="color:{_sr_color(v)}">{v:.1%}</span>',
            "Avg Quality": lambda v: f"{v:.2f}",
            "Avg Latency (ms)": lambda v: f"{v:,.0f} ms",
            "Total Cost ($)": lambda v: f"${v:.4f}",
            "Score": lambda v: f'<span style="color:{_sr_color(v)}">{v:.3f}</span>',
        })


# ==================== AGENT REGISTRY ====================

def render_agent_registry(agent_ids):
    agents = db.get_all_agents()
    page_header("Agent Registry", "Manage and inspect your registered AI agents", [f"🤖 {len(agents)} agents registered"])
    if not agents:
        empty_state("🤖", "No agents registered", "Click <strong>Load Demo Data</strong> in the sidebar to populate the registry.")
        return

    total, active = len(agents), sum(1 for a in agents if a.status.value.lower() == "active")
    all_skills = set(s for a in agents for s in a.skills)
    avg_in = sum(a.cost_per_1k_input for a in agents) / total
    st.html(f'<div class="kpi-grid-4">{kpi_card("🤖","Total Agents",str(total),"#6366F1",small=True)}{kpi_card("✅","Active Agents",str(active),"#22C55E",small=True)}{kpi_card("⚡","Unique Skills",str(len(all_skills)),"#8B5CF6",small=True)}{kpi_card("💰","Avg In Cost/1K",f"${avg_in:.4f}","#F59E0B",small=True)}</div>')

    section("All Agents")
    st.html(f'<div class="ar-grid">{"".join(agent_card_html(a, i) for i, a in enumerate(agents))}</div>')

    section("Capability Matrices")
    left, right = st.columns(2, gap="medium")
    for col, title, sub, getter, key in [(left, "Skills Matrix", "Which agents have each skill", evaluators.get_skills_matrix, "ar_skills"), (right, "Permissions Matrix", "Which agents hold each permission", evaluators.get_permissions_matrix, "ar_perms")]:
        with col:
            st.html(f'<div class="ar-matrix-wrap"><div class="card-title">{title}</div><div class="card-sub">{sub}</div>')
            df = getter(agent_ids)
            if not df.empty:
                ddf = df.set_index("agent").drop(columns=["agent_id"], errors="ignore")
                tmp = ddf.reset_index()
                tmp = search_filter(tmp, "agent", f"{key}_search", "Search agent…")
                ddf = tmp.set_index("agent")
                _dcols = list(ddf.columns)
                df_html_table(
                    ddf,
                    formats={c: (lambda v: "✓" if v else "–") for c in _dcols},
                    cell_styles={c: (lambda v: "color:#22C55E;font-weight:600" if v else "color:var(--fb-text-faint);opacity:.5") for c in _dcols},
                    hide_index=False,
                )
            st.html('</div>')

    section("Permission Violations")
    violations = []
    for a in agents:
        for v in evaluators.check_permission_violations(a.agent_id):
            v["agent"] = a.name; violations.append(v)
    if violations:
        st.html(f'<div class="ar-violation-card" style="margin-bottom:12px;"><span style="font-size:1rem">⚠️</span><div><div style="color:#EF4444;font:600 .8rem Inter,system-ui">{len(violations)} violation(s) detected</div><div style="color:var(--fb-text-muted);font-size:.75rem;margin-top:2px">Review the table below.</div></div></div>')
        df_html_table(pd.DataFrame(violations))
    else:
        st.html('<div class="ar-all-clear"><span style="font-size:1.2rem">✅</span><div><div style="color:#22C55E;font:600 .85rem Inter,system-ui">All clear</div><div style="color:var(--fb-text-muted);font-size:.75rem;margin-top:2px">No permission or skill violations detected.</div></div></div>')


# ==================== TASK SCORECARDS ====================

def render_scorecards(start_date, end_date, agent_ids, selected_group):
    gb = f"· {selected_group}" if selected_group != "All" else "· All groups"
    page_header("Task Scorecards", "Completion rates, quality scores, and pass/fail status per agent", [f"📋 {gb}"])

    sdf = evaluators.get_agent_scorecard_df(start_date, end_date)
    if sdf.empty:
        empty_state("📋", "No scorecard data yet", "Click <strong>Load Demo Data</strong> in the sidebar.")
        return
    if selected_group != "All":
        sdf = sdf[sdf["Group"] == selected_group]

    ts, ps = len(sdf), (sdf["Status"] == "PASS").sum()
    aq = sdf["Avg Quality"].mean() if "Avg Quality" in sdf.columns else 0
    st.html(f'<div class="kpi-grid-4">{kpi_card("📋","Agents Scored",str(ts),"#6366F1",small=True)}{kpi_card("✅","Passing",str(ps),"#22C55E",small=True)}{kpi_card("❌","Failing",str(ts-ps),"#EF4444" if ts-ps else "#334155",small=True)}{kpi_card("⭐","Avg Quality",f"{aq:.2f}","#8B5CF6",small=True)}</div>')

    section("Agent Scorecards")
    sdf = search_filter(sdf, "Agent", "sc_search", "Search agent…")
    df_html_table(sdf, formats={
        "Success Rate": lambda v: f'<span style="color:{_sr_color(v)}">{v:.1%}</span>',
        "Failure Rate": lambda v: f'<span style="color:{_sr_color(1 - v)}">{v:.1%}</span>',
        "Avg Quality": lambda v: f"{v:.2f}",
    })

    if selected_group != "All":
        section("Group Evaluation")
        ge = evaluators.evaluate_group_completion(selected_group, start_date, end_date)
        ip = ge["pass"]
        bg, bdr, lc = ("rgba(34,197,94,.07)", "rgba(34,197,94,.18)", "#4ADE80") if ip else ("rgba(239,68,68,.07)", "rgba(239,68,68,.18)", "#FCA5A5")
        st.html(f'<div class="sc-group-banner" style="background:{bg};border:1px solid {bdr};"><span style="font-size:1.4rem">{"✅" if ip else "❌"}</span><div><div style="color:{lc};font:700 .72rem Inter,system-ui;letter-spacing:.08em;text-transform:uppercase">Group verdict · {"PASS" if ip else "FAIL"}</div><div style="color:var(--fb-text);font:600 .95rem Inter,system-ui">{selected_group}</div></div></div>')
        gsr = f"{ge['group_success_rate']:.1%}"
        gac = "#22C55E" if ip else "#EF4444"
        gk = kpi_card("🤖","Agents",str(ge["agents"]),"#6366F1",small=True) + kpi_card("📈","Group Success",gsr,gac,small=True) + kpi_card("✅","Passing Agents",str(ge["agents_passing"]),"#22C55E",small=True) + kpi_card("🎯","Verdict","PASS" if ip else "FAIL",gac,small=True)
        st.html(f'<div class="kpi-grid-4">{gk}</div>')

    section("Success by Task Type")
    adf = metrics.accuracy_by_type(start_date=start_date, end_date=end_date)
    if not adf.empty:
        colors = [_sr_color(r) for r in adf["Success Rate"]]
        fig = go.Figure(go.Bar(x=adf["Success Rate"], y=adf["Task Type"], orientation="h", marker_color=colors, text=[f"{r:.0%}" for r in adf["Success Rate"]], textposition="outside"))
        layout = plotly_layout(height=max(260, len(adf) * 42))
        layout["xaxis"].update(range=[0, 1.12], tickformat=".0%"); layout["margin"] = dict(l=0, r=40, t=10, b=0)
        fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ==================== ECONOMIC ANALYSIS ====================

def render_economics(start_date, end_date):
    page_header("Economic Analysis", "Cost breakdown, ROI, token usage, and workflow economics", ["💰 Cost intelligence"])

    section("ROI Calculator")
    st.html('<div style="color:var(--fb-text-muted);font-size:.75rem;margin-bottom:6px">Manual cost per task — adjust to calculate savings vs. agent automation</div>')
    manual_cost = st.slider("Manual cost per task ($)", 10, 200, 50, 5, label_visibility="collapsed")
    roi = economics.calculate_roi(manual_cost, start_date, end_date)
    if roi.get("total_tasks", 0) > 0:
        rc = "#22C55E" if roi["roi_pct"] > 0 else "#EF4444"
        sc = "#22C55E" if roi["savings"] > 0 else "#EF4444"
        st.html(f'<div class="ec-roi-banner"><div class="ec-roi-item"><span class="ec-roi-label">Agent Total Cost</span><span class="ec-roi-value">${roi["agent_total_cost"]:.2f}</span></div><div class="ec-roi-divider"></div><div class="ec-roi-item"><span class="ec-roi-label">Manual Equivalent</span><span class="ec-roi-value">${roi["manual_equivalent_cost"]:.2f}</span></div><div class="ec-roi-divider"></div><div class="ec-roi-item"><span class="ec-roi-label">Savings</span><span class="ec-roi-value" style="color:{sc}">${roi["savings"]:.2f}</span></div><div class="ec-roi-divider"></div><div class="ec-roi-item"><span class="ec-roi-label">ROI</span><span class="ec-roi-value" style="color:{rc}">{roi["roi_pct"]:.0f}%</span></div></div>')

    section("Cost Breakdown")
    left, right = st.columns(2, gap="medium")
    for col, getter, title, sub, color, key in [(left, economics.cost_per_agent, "Cost by Agent", "Total spend per agent", "#6366F1", "ec_cpa"), (right, economics.cost_per_task_type, "Cost by Task Type", "Where spend is concentrated", "#8B5CF6", "ec_cpt")]:
        with col:
            df = getter(start_date, end_date)
            st.html(f'{card_wrap(title, sub)}')
            if not df.empty:
                ycol = "Agent" if "Agent" in df.columns else "Task Type"
                fig = go.Figure(go.Bar(x=df["Total Cost ($)"], y=df[ycol], orientation="h", marker_color=color, marker_opacity=0.85, text=[f"${v:.3f}" for v in df["Total Cost ($)"]], textposition="outside"))
                layout = plotly_layout(height=max(260, len(df) * 44)); layout["margin"] = dict(l=0, r=60, t=10, b=0)
                fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                df = search_filter(df, ycol, f"{key}_search", f"Search {ycol.lower()}…")
                df_html_table(df)
            st.html('</div>')

    section("Token Usage")
    tokens = economics.token_usage_summary(start_date, end_date)
    if tokens:
        tk = kpi_card("🔤","Total Tokens",f"{tokens['total_tokens']:,}","#6366F1",small=True) + kpi_card("📊","Avg Tokens/Task",f"{tokens['avg_tokens_per_task']:,}","#8B5CF6",small=True) + kpi_card("⚖️","Input:Output Ratio",f"{tokens['input_output_ratio']:.2f}","#06B6D4",small=True) + kpi_card("⚡","Token Efficiency",f"{tokens['token_efficiency']:.1%}","#10B981",small=True)
        st.html(f'<div class="kpi-grid-4">{tk}</div>')
        left, right = st.columns(2, gap="medium")
        with left:
            st.html(f'{card_wrap("Token Distribution", "Input vs. output token split")}')
            fig = go.Figure(go.Pie(labels=["Input", "Output"], values=[tokens["total_input_tokens"], tokens["total_output_tokens"]], marker_colors=["#6366F1", "#F59E0B"], hole=0.55, textinfo="label+percent"))
            layout = plotly_layout(height=260); layout.pop("xaxis", None); layout.pop("yaxis", None); layout["showlegend"] = False
            fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}); st.html('</div>')
        with right:
            st.html(f'{card_wrap("Tokens by Outcome", "Average token consumption per success vs. failure")}')
            fig = go.Figure(go.Bar(x=["Per Success", "Per Failure"], y=[tokens["avg_tokens_per_success"], tokens["avg_tokens_per_failure"]], marker_color=["#22C55E", "#EF4444"], marker_opacity=0.85, text=[f"{tokens['avg_tokens_per_success']:,}", f"{tokens['avg_tokens_per_failure']:,}"], textposition="outside"))
            layout = plotly_layout(height=260); fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}); st.html('</div>')

    section("Cumulative Cost Trend")
    cost_ts = economics.cost_time_series(start_date, end_date)
    if not cost_ts.empty:
        st.html(f'{card_wrap("Cumulative Spend", "Running total over the selected period")}')
        fig = go.Figure(go.Scatter(x=cost_ts["date"], y=cost_ts["cumulative_cost"], line=dict(color="#6366F1", width=2.5), fill="tozeroy", fillcolor="rgba(99,102,241,0.10)"))
        layout = plotly_layout(height=280); layout["yaxis"]["tickprefix"] = "$"; fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}); st.html('</div>')

    section("Workflow Economics")
    wf_econ = economics.workflow_economics(start_date, end_date)
    if not wf_econ.empty:
        wf_econ = search_filter(wf_econ, "Workflow", "ec_wf_search", "Search workflow…")
        df_html_table(wf_econ)
    else:
        empty_state("💰", "No economic data yet", "Load demo data to populate cost and ROI analysis.")


# ==================== PERFORMANCE METRICS ====================

def render_performance(start_date, end_date, agent_ids):
    page_header("Performance Metrics", "Latency, throughput, completion rates, and agent leaderboard", ["⚡ Performance intelligence"])

    lat_stats = metrics.latency_stats(start_date=start_date, end_date=end_date)
    if lat_stats:
        ls = lat_stats
        lk = kpi_card("⚡","P50 Latency",f"{ls['p50_ms']:,.0f} ms","#6366F1",small=True) + kpi_card("📈","P90 Latency",f"{ls['p90_ms']:,.0f} ms","#F59E0B",small=True) + kpi_card("🔴","P99 Latency",f"{ls['p99_ms']:,.0f} ms","#EF4444",small=True) + kpi_card("📊","Avg Latency",f"{ls['mean_ms']:,.0f} ms","#8B5CF6",small=True)
        st.html(f'<div class="kpi-grid-4">{lk}</div>')

    section("Agent Breakdown")
    left, right = st.columns(2, gap="medium")
    with left:
        cr = metrics.completion_rates(start_date, end_date)
        st.html(f'{card_wrap("Completion Rates", "Success rate per agent — dashed line marks 80%")}')
        if not cr.empty:
            fig = go.Figure(go.Bar(x=cr["Completion Rate"], y=cr["Agent"], orientation="h", marker_color=[_sr_color(r) for r in cr["Completion Rate"]], text=[f"{r:.0%}" for r in cr["Completion Rate"]], textposition="outside"))
            layout = plotly_layout(height=max(260, len(cr) * 44)); layout["xaxis"].update(range=[0, 1.15], tickformat=".0%"); layout["margin"] = dict(l=0, r=40, t=10, b=0)
            fig.add_vline(x=0.8, line_dash="dot", line_color="rgba(148,163,184,0.4)"); fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')
    with right:
        lat = metrics.latency_by_agent(start_date, end_date)
        st.html(f'{card_wrap("Latency by Agent", "P50 and P90 response time per agent")}')
        if not lat.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="P50", x=lat["Agent"], y=lat["P50 (ms)"], marker_color="#6366F1", marker_opacity=0.85))
            fig.add_trace(go.Bar(name="P90", x=lat["Agent"], y=lat["P90 (ms)"], marker_color="#F59E0B", marker_opacity=0.85))
            layout = plotly_layout(height=max(260, len(lat) * 44)); layout["barmode"] = "group"; layout["yaxis"]["ticksuffix"] = "ms"
            fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    section("Latency Distribution")
    all_tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    latencies = [t.latency_ms for t in all_tasks if t.latency_ms is not None] if all_tasks else []
    if latencies:
        st.html(f'{card_wrap("Latency Histogram", "Distribution with P50/P90/P99 markers")}')
        fig = go.Figure(go.Histogram(x=latencies, nbinsx=50, marker_color="#6366F1", marker_opacity=0.75))
        if lat_stats:
            for val, lbl, clr in [(lat_stats["p50_ms"], "P50", "#22C55E"), (lat_stats["p90_ms"], "P90", "#F59E0B"), (lat_stats["p99_ms"], "P99", "#EF4444")]:
                fig.add_vline(x=val, line_dash="dot", line_color=clr, line_width=1.5, annotation_text=f"{lbl}: {val:.0f}ms", annotation_font_size=10, annotation_font_color=clr)
        layout = plotly_layout(height=300); layout["xaxis"]["ticksuffix"] = "ms"; layout["bargap"] = 0.05
        fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}); st.html('</div>')

    section("Throughput Trend")
    granularity = st.selectbox("Granularity", ["day", "hour", "week"], index=0, label_visibility="collapsed")
    tp = metrics.throughput_time_series(start_date=start_date, end_date=end_date, granularity=granularity)
    if not tp.empty:
        st.html(f'{card_wrap("Task Throughput & Success Rate", f"Volume and success rate by {granularity}")}')
        fig = go.Figure()
        fig.add_trace(go.Bar(x=tp["date"], y=tp["task_count"], name="Tasks", marker_color="rgba(16,185,129,0.55)"))
        fig.add_trace(go.Scatter(x=tp["date"], y=tp["success_rate"], name="Success Rate", line=dict(color="#F59E0B", width=2), mode="lines+markers", marker=dict(size=4), yaxis="y2"))
        layout = plotly_layout(height=300)
        layout["yaxis2"] = dict(overlaying="y", side="right", range=[0, 1.05], gridcolor="rgba(0,0,0,0)", tickformat=".0%", tickfont=dict(size=10), color="#F59E0B")
        fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}); st.html('</div>')

    section("Agent Leaderboard")
    lb = metrics.agent_leaderboard(start_date, end_date)
    if not lb.empty:
        lb = search_filter(lb, "Agent", "pm_lb_search", "Search agent…")
        df_html_table(lb, formats={
            "Success Rate": lambda v: f'<span style="color:{_sr_color(v)}">{v:.1%}</span>',
            "Avg Quality": lambda v: f"{v:.2f}",
            "Avg Latency (ms)": lambda v: f"{v:,.0f} ms",
            "Total Cost ($)": lambda v: f"${v:.4f}",
            "Score": lambda v: f'<span style="color:{_sr_color(v)}">{v:.3f}</span>',
        })
    else:
        empty_state("⚡", "No performance data yet", "Load demo data to populate metrics and rankings.")


# ==================== WORKFLOW TRACES ====================

def render_traces(start_date, end_date):
    page_header("Workflow Traces", "End-to-end span timelines and distributed trace inspection", ["Traces"])
    trace_ids = db.get_unique_trace_ids(limit=50)
    if not trace_ids:
        empty_state("🔍", "No trace data available", "Traces will appear here once agents start executing workflows.")
        return

    selected_trace = st.selectbox("Trace ID", trace_ids, label_visibility="collapsed")
    if not selected_trace: return
    spans = db.get_spans(trace_id=selected_trace)
    if not spans:
        empty_state("📭", "No spans found", "This trace has no recorded spans.")
        return

    spans_sorted = sorted(spans, key=lambda s: s.started_at)
    agents_in = set(s.agent_id for s in spans)
    amap = {a.agent_id: a.name for a in db.get_all_agents()}
    min_time = min(s.started_at for s in spans_sorted)
    root_dur = sum(s.duration_ms or 0 for s in spans if s.parent_span_id is None)
    errors = sum(1 for s in spans if s.status == "ERROR")
    ok = sum(1 for s in spans if s.status == "OK")
    sp = round(ok / len(spans) * 100) if spans else 0

    st.html(f'<div class="tr-kpi-row">{kpi_card("🔗","Total Spans",str(len(spans)),"#6366F1")}{kpi_card("🤖","Agents",str(len(agents_in)),"#8B5CF6")}{kpi_card("⏱️","Root Duration",f"{root_dur:,.0f} ms","#06B6D4")}{kpi_card("✅","Success Rate",f"{sp}%","#10B981",sub=f"{ok}/{len(spans)} OK")}{kpi_card("❌","Errors",str(errors),"#F87171" if errors else "#475569")}</div>')

    palette = ["#6366F1","#10B981","#F59E0B","#8B5CF6","#F87171","#06B6D4","#EC4899","#84CC16","#F97316","#64748B"]
    cmap = {aid: palette[i % len(palette)] for i, aid in enumerate(sorted(agents_in))}

    def _depth(s):
        if not s.parent_span_id: return 0
        pids = {sp.span_id for sp in spans_sorted}
        if s.parent_span_id not in pids: return 0
        p = next((sp for sp in spans_sorted if sp.span_id == s.parent_span_id), None)
        return 2 if p and p.parent_span_id else 1

    fig = go.Figure()
    for s in spans_sorted:
        dep = _depth(s)
        start_ms = (s.started_at - min_time).total_seconds() * 1000
        dur = max(s.duration_ms or 1, 1)
        prefix = "\u00a0\u00a0\u00a0\u00a0" * dep
        label = f"{prefix}{s.operation}" if dep else f"[{amap.get(s.agent_id, s.agent_id)}] {s.operation}"
        fig.add_trace(go.Bar(x=[dur], y=[label], base=[start_ms], orientation="h", marker=dict(color=cmap.get(s.agent_id, "#64748B"), opacity=1.0 if s.status == "OK" else 0.45, line=dict(color="#F87171" if s.status == "ERROR" else "rgba(0,0,0,0)", width=2)), showlegend=False, hovertemplate=f"<b>{label}</b><br>Start: {start_ms:.1f}ms<br>Duration: {dur:.1f}ms<br>Status: {s.status}<extra></extra>"))
    for aid, color in cmap.items():
        fig.add_trace(go.Bar(x=[None], y=[None], orientation="h", name=amap.get(aid, aid), marker_color=color, showlegend=True))
    layout = plotly_layout(height=max(320, len(spans_sorted) * 28 + 60))
    layout["barmode"] = "overlay"; layout["xaxis"]["title"] = "Time (ms)"; layout["yaxis"]["autorange"] = "reversed"
    layout["legend"].update(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1); layout["margin"] = dict(l=0, r=0, t=8, b=0)
    fig.update_layout(**layout)
    st.html('<div class="tr-chart-card"><div class="card-title">Trace Timeline</div><div class="card-sub">Gantt chart — red outlines indicate errors</div>')
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}); st.html('</div>')

    span_data = [{"Operation": f"{'  '*_depth(s)}{s.operation}", "Agent": amap.get(s.agent_id, s.agent_id), "Duration (ms)": round(s.duration_ms, 1) if s.duration_ms else 0, "Status": s.status, "Start (ms)": round((s.started_at - min_time).total_seconds() * 1000, 1)} for s in spans_sorted]
    df = pd.DataFrame(span_data)
    st.html('<div class="tr-table-card"><div class="card-title">Span Details</div><div class="card-sub">All spans sorted by start time</div>')
    df = search_filter(df, "Operation", "tr_span_search", "Search operation or agent…")
    df_html_table(df); st.html('</div>')


# ==================== V2: DIAGNOSE ====================

def render_diagnose(start_date, end_date, agent_ids):
    agent = _agent_selector(agent_ids, "v2_diagnose_agent")
    if not agent:
        page_header("Diagnose", "No active agents found. Load demo data first."); return

    page_header(f"Diagnose: {agent.name}", "Observe telemetry, identify failure patterns, and understand what to fix", [agent.group, agent.model_name])
    m = experiment_runner.compute_agent_metrics(agent.agent_id, start_date, end_date)
    if m["total_tasks"] == 0:
        st.info("No task data for this agent in the selected time range."); return

    def _gc(val, good, warn, invert=False):
        if invert: return "#22C55E" if val <= good else "#F59E0B" if val <= warn else "#EF4444"
        return "#22C55E" if val >= good else "#F59E0B" if val >= warn else "#EF4444"

    section("Health Gauges")
    st.html(f'<div class="v2-gauge-grid"><div class="v2-gauge"><div class="v2-gauge-val" style="color:{_gc(m["completion_rate"],.8,.6)}">{m["completion_rate"]:.1%}</div><div class="v2-gauge-label">Completion Rate</div></div><div class="v2-gauge"><div class="v2-gauge-val" style="color:{_gc(m["escalation_rate"],.05,.1,True)}">{m["escalation_rate"]:.1%}</div><div class="v2-gauge-label">Escalation Rate</div></div><div class="v2-gauge"><div class="v2-gauge-val" style="color:{_gc(m["accuracy"],.7,.5)}">{m["accuracy"]:.2f}</div><div class="v2-gauge-label">Accuracy</div></div><div class="v2-gauge"><div class="v2-gauge-val" style="color:{_gc(m["avg_task_time"],5000,10000,True)}">{m["avg_task_time"]:,.0f}ms</div><div class="v2-gauge-label">Avg Task Time</div></div><div class="v2-gauge"><div class="v2-gauge-val" style="color:{_gc(m["auop"],.6,.4)}">{m["auop"]:.3f}</div><div class="v2-gauge-label">AUoP</div></div></div>')

    section("Failure Waterfall")
    wf = failure_analyzer.get_failure_waterfall(agent.agent_id, start_date, end_date)
    if wf["total_tasks"] > 0:
        bh = f'<div class="card"><div class="card-title">{wf["total_tasks"]} tasks received</div>'
        for b in wf["bands"]:
            cls = "v2-wf-success" if b["type"] == "success" else "v2-wf-warning" if b["type"] == "warning" else "v2-wf-error"
            clr = "#22C55E" if b["type"] == "success" else "#F59E0B" if b["type"] == "warning" else "#EF4444"
            bar_w = min(100, max(4, round(b["pct"] * 100, 1)))
            bh += f'<div class="v2-waterfall-band {cls}"><span class="v2-wf-count">{b["count"]}</span><div style="flex:1;min-width:60px"><div class="v2-wf-bar" style="width:{bar_w}%;max-width:100%;background:{clr};"></div></div><span>{b["label"]}</span><span class="v2-wf-pct">{b["pct"]:.1%}</span></div>'
        st.html(bh + '</div>')

    section("Failure Pattern Clusters")
    summary = failure_analyzer.get_failure_summary(agent.agent_id, start_date, end_date)
    if summary["total_failures"] > 0:
        ti = {"improving": "↗", "stable": "→", "degrading": "↘"}.get(summary["trend"], "→")
        st.html(f'<div class="v2-metric-row"><div class="v2-metric"><div class="v2-metric-label">Failure Rate</div><div class="v2-metric-val">{summary["failure_rate"]:.1%}</div></div><div class="v2-metric"><div class="v2-metric-label">Total Failures</div><div class="v2-metric-val">{summary["total_failures"]}</div></div><div class="v2-metric"><div class="v2-metric-label">Most Affected</div><div class="v2-metric-val" style="font-size:.9rem">{summary["most_affected_task_type"]}</div></div><div class="v2-metric"><div class="v2-metric-label">Trend</div><div><span class="v2-trend v2-trend-{summary["trend"]}">{ti} {summary["trend"].title()}</span></div></div></div>')
        for p in failure_analyzer.analyze_failure_patterns(agent.agent_id, start_date, end_date)[:5]:
            st.html(f'<div class="v2-pattern-card"><span class="v2-pattern-sev v2-sev-{p["severity"]}">{p["severity"]}</span><span style="font:500 .72rem Inter,system-ui;margin-left:8px;opacity:.6">{p["occurrence_count"]} occ.</span><div class="v2-pattern-desc">{p["pattern_description"]}</div><div class="v2-pattern-fix">Fix: {p["suggested_fix"]}</div></div>')

    section("Completion Rate by Task Type")
    adf = metrics.accuracy_by_type(agent_id=agent.agent_id, start_date=start_date, end_date=end_date)
    if not adf.empty:
        fig = go.Figure(go.Bar(x=adf["Success Rate"], y=adf["Task Type"], orientation="h", marker_color=[_sr_color(r) for r in adf["Success Rate"]], text=[f"{r:.0%}" for r in adf["Success Rate"]], textposition="auto"))
        layout = plotly_layout(height=max(200, len(adf) * 35)); layout["xaxis"].update(range=[0, 1.05], tickformat=".0%")
        fig.add_vline(x=0.8, line_dash="dash", line_color="rgba(239,68,68,0.4)", line_width=1); fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if agent.group == "v1_pipeline":
        _render_v1_pipeline_trace(start_date, end_date)


# ==================== V1: PIPELINE TRACE ====================

def _render_v1_pipeline_trace(start_date, end_date):
    """Scenario 1 — Unexpected Charge: full pipeline trace with live telemetry."""
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)

    V1_AGENTS = ["v1-classifier-01", "v1-triage-01", "v1-responder-01"]
    TC01_INPUT = (
        "Hi, I noticed a charge of $49.99 on my credit card statement from "
        "your company but I never signed up for any premium plan. I need this "
        "refunded immediately. My account email is user@example.com."
    )

    section("V1 Pipeline Trace — Scenario 1: Unexpected Charge")

    # ── Fetch all V1 tasks from DB ──────────────────────────────────────────
    all_v1_tasks = []
    for aid in V1_AGENTS:
        all_v1_tasks.extend(db.get_tasks(agent_id=aid, start_date=start_date, end_date=end_date))

    # Group into complete workflows (all 3 agents present)
    wf_map: dict = {}
    for t in all_v1_tasks:
        if t.workflow_id:
            wf_map.setdefault(t.workflow_id, {})[t.agent_id] = t
    complete_wfs = {wid: tasks for wid, tasks in wf_map.items() if all(aid in tasks for aid in V1_AGENTS)}

    # ── Run Scenario 1 button ───────────────────────────────────────────────
    # btn_col, info_col = st.columns([1, 4])
    # with btn_col:
    #     run_clicked = st.button("▶  Run Scenario 1", type="primary", key="v1_run_sc1")
    # with info_col:
    #     if not complete_wfs:
    #         st.info("No V1 pipeline runs found. Click **Run Scenario 1** to execute (requires LLM API key in .env).")

    # if run_clicked:
    #     try:
    #         with st.spinner("Running pipeline — 3 real LLM calls in sequence..."):
    #             from pipeline.pipeline import run_pipeline
    #             result = run_pipeline(TC01_INPUT)
    #         st.success(f"Done — workflow `{result.workflow_id}` · {result.total_input_tokens + result.total_output_tokens} tokens · ${result.total_cost_usd:.6f}")
    #         st.rerun()
    #     except Exception as exc:
    #         st.error(f"Pipeline failed: {exc}  —  Check that `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set in `.env`")

    # if not complete_wfs:
    #     return

    # ── Workflow selector ───────────────────────────────────────────────────
    wf_ids = sorted(complete_wfs.keys(), reverse=True)

    # Prefer billing + escalated (closest to scenario 1)
    best = next(
        (wid for wid in wf_ids
         if complete_wfs[wid].get("v1-classifier-01", None) is not None
         and complete_wfs[wid]["v1-classifier-01"].metadata.get("classification") == "billing"
         and complete_wfs[wid].get("v1-triage-01", None) is not None
         and complete_wfs[wid]["v1-triage-01"].metadata.get("escalation_flag", False)),
        wf_ids[0],
    )

    def _wf_label(wid):
        clf = complete_wfs[wid].get("v1-classifier-01")
        cat = clf.metadata.get("classification", "?") if clf else "?"
        ts  = clf.started_at.strftime("%b %d  %H:%M") if clf else wid
        return f"{ts}  ·  {cat}  ·  {wid}"

    selected_wf = st.selectbox("Pipeline Run", wf_ids, index=wf_ids.index(best),
                                format_func=_wf_label, key="v1_trace_wf")
    wf_tasks = complete_wfs[selected_wf]
    clf_t = wf_tasks["v1-classifier-01"]
    tri_t = wf_tasks["v1-triage-01"]
    res_t = wf_tasks["v1-responder-01"]

    # ── Pipeline input card ─────────────────────────────────────────────────
    st.html(f'''
    <div class="card" style="margin-bottom:14px">
        <div style="font:.62rem Inter;color:var(--fb-text-faint);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Pipeline Input</div>
        <div style="font:.82rem Inter;line-height:1.55;color:var(--fb-text)">{TC01_INPUT}</div>
    </div>
    ''')

    # ── 3-step agent cards ──────────────────────────────────────────────────
    def _step_card(task, step_title, output_html):
        ok  = task.result.value == "success"
        sc  = "#22C55E" if ok else "#EF4444"
        esc = task.metadata.get("escalation_flag", False)
        auop = task.metadata.get("auop_score", 0.0)
        esc_badge = '<span style="background:#EF444422;color:#EF4444;padding:2px 8px;border-radius:12px;font:.67rem Inter;font-weight:600">ESCALATE</span>' if esc else ''
        return f'''
        <div class="card" style="height:100%">
            <div style="font:600 .72rem Inter;color:var(--fb-text-muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px">{step_title}</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px">
                <span style="background:{sc}22;color:{sc};padding:2px 8px;border-radius:12px;font:.67rem Inter;font-weight:600">{task.result.value.upper()}</span>
                {esc_badge}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">
                <div><div style="font:.6rem Inter;color:var(--fb-text-faint);margin-bottom:2px;text-transform:uppercase">In Tokens</div><div style="font:600 .9rem Inter;color:var(--fb-text)">{task.input_tokens:,}</div></div>
                <div><div style="font:.6rem Inter;color:var(--fb-text-faint);margin-bottom:2px;text-transform:uppercase">Out Tokens</div><div style="font:600 .9rem Inter;color:var(--fb-text)">{task.output_tokens:,}</div></div>
                <div><div style="font:.6rem Inter;color:var(--fb-text-faint);margin-bottom:2px;text-transform:uppercase">Latency</div><div style="font:600 .9rem Inter;color:var(--fb-text)">{(task.latency_ms or 0):,.0f}ms</div></div>
                <div><div style="font:.6rem Inter;color:var(--fb-text-faint);margin-bottom:2px;text-transform:uppercase">AUoP</div><div style="font:600 .9rem Inter;color:var(--fb-text)">{auop:.2e}</div></div>
            </div>
            <div style="font:.6rem Inter;color:var(--fb-text-faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px">Output</div>
            {output_html}
        </div>'''

    # Classifier output HTML
    clf_cat  = clf_t.metadata.get("classification", "—")
    clf_conf = clf_t.metadata.get("confidence", 0.0)
    clf_out  = f'<div style="background:var(--fb-bg2);border-radius:6px;padding:10px"><span style="color:#60A5FA;font:600 .85rem Inter">{clf_cat}</span><span style="color:var(--fb-text-muted);font:.75rem Inter;margin-left:8px">{clf_conf:.0%} confidence</span></div>'

    # Triage output HTML
    tri_prio  = tri_t.metadata.get("priority", 0)
    tri_rat   = tri_t.metadata.get("rationale", "")
    prio_clr  = "#EF4444" if tri_prio >= 4 else "#F59E0B" if tri_prio >= 3 else "#22C55E"
    tri_out   = f'<div style="background:var(--fb-bg2);border-radius:6px;padding:10px"><span style="color:{prio_clr};font:700 1rem Inter">P{tri_prio}/5</span><div style="font:.72rem Inter;color:var(--fb-text-muted);margin-top:6px;line-height:1.4">{tri_rat[:110]}{"…" if len(tri_rat)>110 else ""}</div></div>'

    # Responder output HTML
    res_sent = res_t.metadata.get("sentiment", "—")
    sent_clr = {"positive": "#22C55E", "empathetic": "#60A5FA", "neutral": "#9CA3AF"}.get(res_sent, "#9CA3AF")
    res_out  = f'<div style="background:var(--fb-bg2);border-radius:6px;padding:10px"><span style="color:{sent_clr};font:600 .85rem Inter">{res_sent}</span><div style="font:.72rem Inter;color:var(--fb-text-muted);margin-top:4px">Response drafted and ready to send</div></div>'

    c1, arr1, c2, arr2, c3 = st.columns([10, 1, 10, 1, 10])
    with c1:   st.html(_step_card(clf_t, "Step 1 · Intake Classifier", clf_out))
    with arr1: st.html('<div style="height:100%;display:flex;align-items:center;justify-content:center;color:var(--fb-text-faint);font-size:1.4rem;padding-top:80px">→</div>')
    with c2:   st.html(_step_card(tri_t, "Step 2 · Triage Scorer",    tri_out))
    with arr2: st.html('<div style="height:100%;display:flex;align-items:center;justify-content:center;color:var(--fb-text-faint);font-size:1.4rem;padding-top:80px">→</div>')
    with c3:   st.html(_step_card(res_t, "Step 3 · Response Drafter", res_out))

    # ── Escalation alert ────────────────────────────────────────────────────
    if res_t.metadata.get("escalation_flag", False):
        st.html(f'''
        <div style="background:#EF444414;border:1px solid #EF444438;border-radius:8px;padding:14px 20px;margin-top:14px;display:flex;align-items:center;gap:14px">
            <span style="font-size:1.3rem">🚨</span>
            <div>
                <div style="font:600 .82rem Inter;color:#EF4444">Escalation Triggered</div>
                <div style="font:.73rem Inter;color:var(--fb-text-muted);margin-top:3px">Priority {tri_t.metadata.get("priority")}/5 — routed to on-call support team for immediate action</div>
            </div>
        </div>
        ''')

    # ── Pipeline cost / token summary ───────────────────────────────────────
    total_tok  = clf_t.total_tokens + tri_t.total_tokens + res_t.total_tokens
    total_cost = clf_t.cost_usd + tri_t.cost_usd + res_t.cost_usd
    total_lat  = (clf_t.latency_ms or 0) + (tri_t.latency_ms or 0) + (res_t.latency_ms or 0)

    st.html(f'''
    <div style="display:flex;gap:12px;margin-top:14px">
        <div style="background:var(--fb-card-bg);border-radius:8px;padding:12px 18px;flex:1;text-align:center">
            <div style="font:.6rem Inter;color:var(--fb-text-faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Total Tokens</div>
            <div style="font:700 1.05rem Inter;color:var(--fb-text)">{total_tok:,}</div>
        </div>
        <div style="background:var(--fb-card-bg);border-radius:8px;padding:12px 18px;flex:1;text-align:center">
            <div style="font:.6rem Inter;color:var(--fb-text-faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Total Cost</div>
            <div style="font:700 1.05rem Inter;color:var(--fb-text)">${total_cost:.6f}</div>
        </div>
        <div style="background:var(--fb-card-bg);border-radius:8px;padding:12px 18px;flex:1;text-align:center">
            <div style="font:.6rem Inter;color:var(--fb-text-faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Pipeline Latency</div>
            <div style="font:700 1.05rem Inter;color:var(--fb-text)">{total_lat:,.0f}ms</div>
        </div>
        <div style="background:var(--fb-card-bg);border-radius:8px;padding:12px 18px;flex:1;text-align:center">
            <div style="font:.6rem Inter;color:var(--fb-text-faint);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Workflow ID</div>
            <div style="font:600 .78rem Inter;color:var(--fb-text-muted);margin-top:4px">{selected_wf}</div>
        </div>
    </div>
    ''')


# ==================== V2: TUNE ====================

def render_tune(start_date, end_date, agent_ids):
    agent = _agent_selector(agent_ids, "v2_tune_agent")
    if not agent:
        page_header("Tune", "No active agents found."); return
    baseline = _ensure_baseline(agent.agent_id)

    page_header(f"Tune: {agent.name}", "Adjust agent parameters — changes are staged, not applied until you run a training cycle", [f"Baseline v{baseline.version}"])

    section("Recommendations")
    recs = experiment_runner.get_parameter_recommendations(agent.agent_id, start_date, end_date)
    if recs:
        for r in recs:
            st.html(f'<div class="v2-rec-card"><div class="v2-rec-param">{r["parameter"]}: {r["current"]} → {r["suggested"]}</div><div class="v2-rec-reason">{r["reason"]}</div><div class="v2-rec-impact">Estimated: {r["estimated_impact"]}</div></div>')
    else:
        st.html('<div class="card"><div class="card-sub">No recommendations — agent within acceptable thresholds.</div></div>')

    section("Parameter Controls")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.html('<div class="v2-control-card"><div class="v2-ctrl-label">Prompt Precision</div><div class="v2-ctrl-desc">System prompt specificity. Low = general, high = constrained.</div></div>')
        pp = st.slider("Prompt Precision", 1, 10, baseline.prompt_precision, key="v2_pp")
        st.html('<div class="v2-control-card"><div class="v2-ctrl-label">Confidence Threshold</div><div class="v2-ctrl-desc">Minimum confidence before committing.</div></div>')
        ct = st.slider("Confidence Threshold", 0.0, 1.0, baseline.confidence_threshold, 0.05, key="v2_ct")
        st.html('<div class="v2-control-card"><div class="v2-ctrl-label">Fallback Depth</div><div class="v2-ctrl-desc">Retry strategies before escalating.</div></div>')
        fd = st.slider("Fallback Depth", 1, 5, baseline.fallback_depth, key="v2_fd")
    with c2:
        st.html('<div class="v2-control-card"><div class="v2-ctrl-label">Data Pre-fetch</div><div class="v2-ctrl-desc">Pre-load context before execution.</div></div>')
        dp = st.toggle("Data Pre-fetch", baseline.data_prefetch, key="v2_dp")
        st.html('<div class="v2-control-card"><div class="v2-ctrl-label">Sentiment Weighting</div><div class="v2-ctrl-desc">How much user sentiment affects response.</div></div>')
        sw = st.slider("Sentiment Weighting", 0.0, 1.0, baseline.sentiment_weighting, 0.05, key="v2_sw")
        st.html('<div class="v2-control-card"><div class="v2-ctrl-label">Tone Variant</div><div class="v2-ctrl-desc">Output verbosity and style.</div></div>')
        tv = st.selectbox("Tone Variant", ["concise", "balanced", "detailed"], index=["concise", "balanced", "detailed"].index(baseline.tone_variant), key="v2_tv")

    changes = {}
    for k, ov, nv in [("prompt_precision", baseline.prompt_precision, pp), ("confidence_threshold", baseline.confidence_threshold, ct), ("fallback_depth", baseline.fallback_depth, fd), ("data_prefetch", baseline.data_prefetch, dp), ("sentiment_weighting", baseline.sentiment_weighting, sw), ("tone_variant", baseline.tone_variant, tv)]:
        if isinstance(ov, float) and isinstance(nv, float):
            if abs(ov - nv) > 0.001: changes[k] = {"old": ov, "new": nv}
        elif ov != nv:
            changes[k] = {"old": ov, "new": nv}

    section("Staged Changes")
    if changes:
        st.html(diff_html(changes))
        st.html(f'<div class="card-sub">{len(changes)} parameter(s) modified — not yet applied</div>')
        if st.button("Stage for Training Cycle", type="primary", key="v2_stage"):
            nv = db.get_next_config_version(agent.agent_id)
            cand = AgentConfig(config_id=str(uuid.uuid4())[:12], agent_id=agent.agent_id, version=nv, prompt_precision=pp, confidence_threshold=ct, fallback_depth=fd, data_prefetch=dp, sentiment_weighting=sw, tone_variant=tv, is_baseline=False, notes=f"Candidate v{nv} with {len(changes)} changes")
            db.upsert_config(cand)
            st.session_state["v2_staged_config"] = cand.config_id
            st.session_state["v2_staged_agent"] = agent.agent_id
            st.success(f"Staged candidate config v{nv} — go to Train to execute.")
    else:
        st.html('<div class="card"><div class="card-sub">No changes — adjust parameters above.</div></div>')

    section("Config History")
    configs = db.get_agent_configs(agent.agent_id)
    if configs:
        df_html_table(pd.DataFrame([{"Version": f"v{c.version}", "Baseline": "Yes" if c.is_baseline else "", "Prompt": c.prompt_precision, "Conf.": c.confidence_threshold, "Fallback": c.fallback_depth, "Pre-fetch": "On" if c.data_prefetch else "Off", "Tone": c.tone_variant, "Created": c.created_at.strftime("%b %d, %H:%M"), "Notes": c.notes} for c in configs[:10]]))


# ==================== V2: TRAIN ====================

def render_train(start_date, end_date, agent_ids):
    agent = _agent_selector(agent_ids, "v2_train_agent")
    if not agent:
        page_header("Train", "No active agents found."); return
    baseline = _ensure_baseline(agent.agent_id)
    page_header(f"Train: {agent.name}", "Execute a training cycle — replay historical tasks with new parameters and measure improvement")

    configs = db.get_agent_configs(agent.agent_id)
    candidates = [c for c in configs if not c.is_baseline]
    candidate = None
    sid = st.session_state.get("v2_staged_config")
    if sid and st.session_state.get("v2_staged_agent") == agent.agent_id:
        candidate = next((c for c in configs if c.config_id == sid), None)
    if not candidate and candidates:
        candidate = candidates[0]

    section("Training Configuration")
    c1, c2, c3 = st.columns(3)
    with c1: sample_size = st.number_input("Sample Size", 20, 500, 100, 10, key="v2_sample")
    with c2: st.html(f'<div class="card"><div class="card-sub">Baseline: v{baseline.version}</div></div>')
    with c3: st.html(f'<div class="card"><div class="card-sub">{"Candidate: v" + str(candidate.version) if candidate else "No candidate — go to Tune"}</div></div>')

    if candidate:
        diff = experiment_runner.compute_config_diff(baseline, candidate)
        if diff:
            section("Parameter Changes"); st.html(diff_html(diff))

    section("Execute Training Cycle")
    if not candidate:
        st.info("Stage a candidate config on the Tune page before running a training cycle.")
    elif st.button("Start Training Cycle", type="primary", key="v2_run_train"):
        steps = ["Ingest Telemetry", "Analyze Failures", "Adjust Parameters", "Re-run Agent", "Capture Results"]
        progress = st.progress(0, text="Starting..."); step_ctr = st.empty()
        for i, sn in enumerate(steps):
            progress.progress((i + 1) / len(steps), text=f"Step {i+1}/5: {sn}")
            pipe = '<div class="v2-pipeline">'
            for j, s in enumerate(steps):
                cls = "done" if j < i else "active" if j == i else ""
                icon = "&#10003;" if j < i else "&#9881;" if j == i else "&#9675;"
                pipe += f'<div class="v2-pipe-step {cls}"><div class="v2-pipe-icon">{icon}</div><div class="v2-pipe-label">{s}</div></div>'
                if j < len(steps) - 1: pipe += '<div class="v2-pipe-arrow">→</div>'
            step_ctr.html(pipe + '</div>')

        result = experiment_runner.simulate_experiment(agent.agent_id, baseline, candidate, sample_size=sample_size, start_date=start_date, end_date=end_date)
        db.insert_experiment(result); st.session_state["v2_last_experiment"] = result.experiment_id
        progress.progress(1.0, text="Training cycle complete!")
        step_ctr.html('<div class="v2-pipeline">' + ''.join(f'<div class="v2-pipe-step done"><div class="v2-pipe-icon">&#10003;</div><div class="v2-pipe-label">{s}</div></div>{"<div class=\"v2-pipe-arrow\">→</div>" if i < 4 else ""}' for i, s in enumerate(steps)) + '</div>')

        bm, cm = result.baseline_metrics, result.candidate_metrics
        st.html(f'<div class="card"><div class="card-title">Training Cycle Complete</div><div class="card-sub">Experiment #{result.experiment_id} — {result.task_sample_size} tasks replayed</div><div class="v2-metric-row"><div class="v2-metric"><div class="v2-metric-label">Completion</div><div class="v2-metric-val">{bm.get("completion_rate",0):.1%} → {cm.get("completion_rate",0):.1%}</div></div><div class="v2-metric"><div class="v2-metric-label">Accuracy</div><div class="v2-metric-val">{bm.get("accuracy",0):.2f} → {cm.get("accuracy",0):.2f}</div></div><div class="v2-metric"><div class="v2-metric-label">AUoP</div><div class="v2-metric-val">{bm.get("auop",0):.3f} → {cm.get("auop",0):.3f}</div></div></div></div>')
        st.info("Go to Compare to see the full side-by-side analysis.")

    section("Experiment History")
    exps = db.get_experiments(agent.agent_id)
    if exps:
        df_html_table(pd.DataFrame([{"ID": e.experiment_id, "Status": e.status.value, "Base v": e.baseline_config_version, "Cand v": e.candidate_config_version, "Sample": e.task_sample_size, "Base CR": f"{e.baseline_metrics.get('completion_rate',0):.1%}", "New CR": f"{e.candidate_metrics.get('completion_rate',0):.1%}", "Date": e.started_at.strftime("%b %d, %H:%M")} for e in exps[:10]]))


# ==================== V2: COMPARE ====================

def render_compare(start_date, end_date, agent_ids):
    agent = _agent_selector(agent_ids, "v2_compare_agent")
    if not agent:
        page_header("Compare", "No active agents found."); return
    page_header(f"Compare: {agent.name}", "Evaluate before vs. after — measure the impact of parameter tuning")

    completed = [e for e in db.get_experiments(agent.agent_id) if e.status == ExperimentStatus.COMPLETE]
    if not completed:
        st.html('<div class="card"><div class="card-sub">No completed experiments. Run a training cycle first.</div></div>'); return

    labels = [f"Exp {e.experiment_id} (v{e.baseline_config_version}→v{e.candidate_config_version}) — {e.started_at.strftime('%b %d, %H:%M')}" for e in completed]
    idx = st.selectbox("Select Experiment", range(len(labels)), format_func=lambda i: labels[i], key="v2_compare_exp")
    exp = completed[idx]; bm, cm = exp.baseline_metrics, exp.candidate_metrics

    section("Side-by-Side Comparison")
    mdefs = [("Completion Rate", "completion_rate", ".1%", False), ("Escalation Rate", "escalation_rate", ".1%", True), ("Accuracy", "accuracy", ".3f", False), ("Avg Task Time", "avg_task_time", ".0f", True), ("AUoP", "auop", ".3f", False), ("Cost/Task", "cost_per_task", ".4f", True), ("AI-ROI", "ai_roi", ".1f", False)]
    lh = f'<div class="v2-compare-col"><div class="v2-compare-header">Baseline (v{exp.baseline_config_version})</div>'
    rh = f'<div class="v2-compare-col"><div class="v2-compare-header">Candidate (v{exp.candidate_config_version})</div>'
    ch = '<div class="v2-compare-center" style="padding-top:36px;">'
    for label, key, fmt, inv in mdefs:
        bv, cv = bm.get(key, 0), cm.get(key, 0)
        fmts = {".1%": (f"{bv:.1%}", f"{cv:.1%}"), ".3f": (f"{bv:.3f}", f"{cv:.3f}"), ".0f": (f"{bv:,.0f}ms", f"{cv:,.0f}ms"), ".4f": (f"${bv:.4f}", f"${cv:.4f}"), ".1f": (f"{bv:.1f}%", f"{cv:.1f}%")}
        bs, cs = fmts.get(fmt, (str(bv), str(cv)))
        lh += f'<div class="v2-compare-row"><span class="v2-compare-label">{label}</span><span class="v2-compare-val">{bs}</span></div>'
        rh += f'<div class="v2-compare-row"><span class="v2-compare-label">{label}</span><span class="v2-compare-val">{cs}</span></div>'
        ch += delta_html(bv, cv, fmt, inv)
    st.html(f'<div class="v2-compare-grid">{lh}</div>{ch}</div>{rh}</div></div>')

    section("Performance Shape")
    bsp = max(0, 1 - bm.get("avg_task_time", 0) / 30000); csp = max(0, 1 - cm.get("avg_task_time", 0) / 30000)
    bef = max(0, 1 - bm.get("cost_per_task", 0) / 1.0); cef = max(0, 1 - cm.get("cost_per_task", 0) / 1.0)
    labels = ["Completion", "Accuracy", "AUoP", "Speed", "Efficiency", "Completion"]
    bvals = [bm.get("completion_rate", 0), bm.get("accuracy", 0), bm.get("auop", 0), bsp, bef, bm.get("completion_rate", 0)]
    cvals = [cm.get("completion_rate", 0), cm.get("accuracy", 0), cm.get("auop", 0), csp, cef, cm.get("completion_rate", 0)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=bvals, theta=labels, name=f"Baseline v{exp.baseline_config_version}", line=dict(color="#6366F1", width=2, dash="dash"), fill="toself", fillcolor="rgba(99,102,241,0.08)"))
    fig.add_trace(go.Scatterpolar(r=cvals, theta=labels, name=f"Candidate v{exp.candidate_config_version}", line=dict(color="#22C55E", width=2), fill="toself", fillcolor="rgba(34,197,94,0.1)"))
    layout = plotly_layout(height=350)
    gc = "rgba(128,128,128,0.1)"
    layout["polar"] = dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor=gc, tickfont=dict(size=9)), angularaxis=dict(gridcolor=gc), bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if exp.failure_patterns:
        section("Failure Patterns Identified")
        for p in exp.failure_patterns:
            st.html(f'<div class="v2-pattern-card"><span class="v2-pattern-sev v2-sev-{p.get("severity","info")}">{p.get("severity","info")}</span><span style="font:500 .72rem Inter,system-ui;margin-left:8px;opacity:.6">{p.get("count",0)} occ.</span><div class="v2-pattern-desc">{p.get("description","")}</div><div class="v2-pattern-fix">Fix: {p.get("suggested_fix","")}</div></div>')

    if exp.parameter_changes:
        section("Parameter Changes Applied"); st.html(diff_html(exp.parameter_changes))

    section("Actions")
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        if st.button(f"Promote v{exp.candidate_config_version}", type="primary", key="v2_promote"):
            for c in db.get_agent_configs(agent.agent_id):
                if c.version == exp.candidate_config_version: c.is_baseline = True; db.upsert_config(c)
                elif c.is_baseline: c.is_baseline = False; db.upsert_config(c)
            st.success(f"Promoted v{exp.candidate_config_version} as new baseline!")
    with c2:
        if st.button("Revert to Baseline", key="v2_revert"):
            st.info(f"Keeping v{exp.baseline_config_version} as baseline.")

    section("Human → Agent Ratio Shift")
    rdf = experiment_runner.compute_ratio_shift(start_date, end_date)
    if not rdf.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rdf["date"], y=rdf["agent_pct"], name="Agent-Handled", line=dict(color="#6366F1", width=0), fill="tozeroy", fillcolor="rgba(99,102,241,0.3)", stackgroup="one"))
        fig.add_trace(go.Scatter(x=rdf["date"], y=rdf["human_pct"], name="Human-Required", line=dict(color="#F59E0B", width=0), fill="tonexty", fillcolor="rgba(245,158,11,0.2)", stackgroup="one"))
        layout = plotly_layout(height=250); layout["yaxis"].update(range=[0, 1.05], tickformat=".0%"); layout["showlegend"] = True
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(size=10))
        fig.update_layout(**layout); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if len(rdf) > 1:
            fp, lp = rdf.iloc[0]["agent_pct"], rdf.iloc[-1]["agent_pct"]
            hs = rdf["human_count"].sum() * 0.5
            st.html(f'<div class="v2-metric-row"><div class="v2-metric"><div class="v2-metric-label">Agent Autonomy (Start)</div><div class="v2-metric-val">{fp:.1%}</div></div><div class="v2-metric"><div class="v2-metric-label">Agent Autonomy (Current)</div><div class="v2-metric-val">{lp:.1%}</div></div><div class="v2-metric"><div class="v2-metric-label">Est. Human Hours Saved</div><div class="v2-metric-val">{hs:,.0f}h</div></div></div>')


if __name__ == "__main__":
    main()
