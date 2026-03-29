"""Streamlit dashboard for Agent Performance monitoring."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

from . import db, evaluators, economics, metrics


def _sidebar_css(theme: str) -> str:
    """Return theme-aware sidebar CSS for st.html() injection."""
    d = theme == "dark"

    sb_bg          = "linear-gradient(180deg,#0B1120 0%,#0F172A 60%,#111827 100%)" if d else "linear-gradient(180deg,#F8FAFC 0%,#F1F5F9 60%,#EEF2FF 100%)"
    sb_header_bg   = "#0B1120"                      if d else "#F8FAFC"
    sb_border      = "rgba(255,255,255,0.06)"        if d else "rgba(15,23,42,0.07)"
    sb_label       = "#334155"                       if d else "#94A3B8"
    sb_logo_title  = "#F1F5F9"                       if d else "#1E293B"
    sb_logo_sub    = "#475569"                       if d else "#94A3B8"
    nav_text       = "#64748B"                       if d else "#475569"
    nav_hover_bg   = "rgba(99,102,241,0.08)"         if d else "rgba(99,102,241,0.06)"
    nav_hover_text = "#C7D2FE"                       if d else "#4338CA"
    nav_hover_bdr  = "rgba(99,102,241,0.12)"         if d else "rgba(99,102,241,0.15)"
    nav_act_bg     = "rgba(99,102,241,0.15)"         if d else "rgba(99,102,241,0.10)"
    nav_act_text   = "#A5B4FC"                       if d else "#4338CA"
    nav_act_bdr    = "rgba(99,102,241,0.25)"         if d else "rgba(99,102,241,0.22)"
    ctrl_bg        = "rgba(255,255,255,0.04)"        if d else "rgba(0,0,0,0.03)"
    ctrl_bdr       = "rgba(255,255,255,0.09)"        if d else "rgba(0,0,0,0.10)"
    ctrl_text      = "#CBD5E1"                       if d else "#475569"
    ctrl_ph        = "#475569"                       if d else "#94A3B8"
    alert_bg       = "rgba(34,197,94,0.08)"          if d else "rgba(34,197,94,0.06)"
    alert_bdr      = "rgba(34,197,94,0.20)"          if d else "rgba(34,197,94,0.25)"
    alert_text     = "#4ADE80"                       if d else "#16A34A"
    col_icon       = "rgba(250,250,250,0.6)"         if d else "rgba(15,23,42,0.40)"
    col_icon_hov   = "rgba(250,250,250,0.9)"         if d else "rgba(15,23,42,0.70)"
    ghost_bg       = "rgba(255,255,255,0.04)"        if d else "rgba(0,0,0,0.04)"
    ghost_bdr      = "rgba(255,255,255,0.10)"        if d else "rgba(0,0,0,0.12)"
    ghost_text     = "#64748B"                       if d else "#64748B"
    ghost_hov_bg   = "rgba(255,255,255,0.08)"        if d else "rgba(0,0,0,0.07)"
    ghost_hov_text = "#C7D2FE"                       if d else "#4338CA"
    status_text    = "#475569"                       if d else "#94A3B8"

    return f"""
    <style>
    /* ── Sidebar shell ───────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background: {sb_bg};
        border-right: 1px solid {sb_border};
        padding-top: 0 !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top: 0 !important; }}

    /* ── All sidebar text + font ─────────────────────────────── */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] * {{
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }}
    [data-testid="stSidebar"] [data-testid="stIconMaterial"] {{
        font-family: "Material Symbols Rounded","Material Icons" !important;
    }}

    /* ── Section labels ──────────────────────────────────────── */
    .sb-section-label {{
        color: {sb_label} !important;
        font-size: 0.62rem !important; font-weight: 700 !important;
        letter-spacing: 0.14em !important; text-transform: uppercase !important;
        margin: 0 0 6px 2px !important; display: block;
    }}

    /* ── Logo ────────────────────────────────────────────────── */
    .sb-logo-wrap {{
        display: flex; align-items: center; gap: 11px;
        padding: 22px 20px 18px;
        border-bottom: 1px solid {sb_border}; margin-bottom: 20px;
    }}
    .sb-logo-icon {{
        width: 38px; height: 38px;
        background: linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);
        border-radius: 11px; display: flex; align-items: center;
        justify-content: center; font-size: 19px; flex-shrink: 0;
        box-shadow: 0 4px 14px rgba(99,102,241,0.45);
    }}
    .sb-logo-title {{
        color: {sb_logo_title} !important;
        font-size: 0.95rem !important; font-weight: 700 !important;
        letter-spacing: -0.015em !important; line-height: 1.2 !important;
    }}
    .sb-logo-sub {{
        color: {sb_logo_sub} !important;
        font-size: 0.68rem !important; line-height: 1.3 !important;
    }}

    /* ── HR ──────────────────────────────────────────────────── */
    [data-testid="stSidebar"] hr {{
        border: none !important;
        border-top: 1px solid {sb_border} !important;
        margin: 14px 0 !important;
    }}

    /* ── Nav radio ───────────────────────────────────────────── */
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {{
        gap: 2px !important; flex-direction: column !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        background: transparent !important; border-radius: 9px !important;
        padding: 9px 12px 9px 10px !important; cursor: pointer !important;
        width: 100% !important; display: flex !important; align-items: center !important;
        transition: background 0.15s ease, color 0.15s ease !important;
        font-size: 0.855rem !important; font-weight: 400 !important;
        color: {nav_text} !important; text-transform: none !important;
        letter-spacing: normal !important; border: 1px solid transparent !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
        background: {nav_hover_bg} !important; color: {nav_hover_text} !important;
        border-color: {nav_hover_bdr} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{
        background: {nav_act_bg} !important; color: {nav_act_text} !important;
        border-color: {nav_act_bdr} !important; font-weight: 600 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child,
    [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {{ display: none !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {{ display: none !important; }}

    /* ── Primary button (Load Demo) ──────────────────────────── */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg,#6366F1 0%,#7C3AED 100%) !important;
        border: none !important; color: #F8FAFC !important;
        border-radius: 9px !important; font-weight: 600 !important;
        font-size: 0.82rem !important; padding: 9px 14px !important;
        width: 100% !important;
        transition: opacity 0.15s ease, transform 0.15s ease !important;
        box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
        opacity: 0.88 !important; transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:active {{
        transform: translateY(0) !important;
    }}

    /* ── Secondary button (Theme toggle) ─────────────────────── */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
        background: {ghost_bg} !important;
        border: 1px solid {ghost_bdr} !important;
        color: {ghost_text} !important; border-radius: 9px !important;
        font-weight: 500 !important; font-size: 0.8rem !important;
        padding: 7px 14px !important; width: 100% !important;
        transition: background 0.15s ease, border-color 0.15s ease,
                    color 0.15s ease !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
        background: {ghost_hov_bg} !important;
        border-color: rgba(99,102,241,0.30) !important;
        color: {ghost_hov_text} !important; transform: none !important;
    }}

    /* ── Selectbox ───────────────────────────────────────────── */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {{
        background-color: {ctrl_bg} !important;
        border: 1px solid {ctrl_bdr} !important;
        border-radius: 9px !important; color: {ctrl_text} !important;
        font-size: 0.84rem !important; transition: border-color 0.15s ease !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:hover {{
        border-color: rgba(99,102,241,0.35) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label {{
        color: {sb_label} !important; font-size: 0.68rem !important;
        font-weight: 600 !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }}

    /* ── Multiselect ─────────────────────────────────────────── */
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child {{
        background-color: {ctrl_bg} !important;
        border: 1px solid {ctrl_bdr} !important;
        border-radius: 9px !important; transition: border-color 0.15s ease !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child:hover {{
        border-color: rgba(99,102,241,0.35) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child * {{
        background-color: transparent !important; color: {ctrl_text} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] input::placeholder {{ color: {ctrl_ph} !important; }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] input {{ caret-color: #A5B4FC !important; }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background-color: rgba(99,102,241,0.18) !important;
        border: 1px solid rgba(99,102,241,0.30) !important;
        border-radius: 5px !important; color: #A5B4FC !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] span {{ color: #A5B4FC !important; }}
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] label {{
        color: {sb_label} !important; font-size: 0.68rem !important;
        font-weight: 600 !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }}

    /* ── Success alerts ──────────────────────────────────────── */
    [data-testid="stSidebar"] [data-testid="stAlert"] {{
        background: {alert_bg} !important;
        border: 1px solid {alert_bdr} !important;
        border-radius: 9px !important; color: {alert_text} !important;
        font-size: 0.78rem !important;
    }}

    /* ── Sidebar header / collapse button ────────────────────── */
    [data-testid="stSidebarHeader"] {{
        background: {sb_header_bg} !important; border-bottom: none !important;
    }}
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {{
        color: {col_icon} !important;
    }}
    [data-testid="stSidebarCollapseButton"] button:hover [data-testid="stIconMaterial"] {{
        color: {col_icon_hov} !important;
    }}

    /* ── Status badge ────────────────────────────────────────── */
    .sb-status-wrap {{
        display: flex; align-items: center; gap: 8px;
        padding: 14px 4px 6px;
        border-top: 1px solid {sb_border};
    }}
    .sb-status-dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: #22C55E; box-shadow: 0 0 7px rgba(34,197,94,0.7);
        flex-shrink: 0;
    }}
    .sb-status-text {{
        color: {status_text} !important;
        font-size: 0.7rem !important; font-weight: 500 !important;
    }}

    /* ── Padding ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] .block-container {{ padding: 0 !important; }}
    [data-testid="stSidebar"] section[data-testid="stSidebarContent"] > div {{
        padding-left: 14px !important; padding-right: 14px !important;
    }}
    </style>
    """


def _overview_css(theme: str) -> str:
    """Theme-aware CSS for the Overview page."""
    d = theme == "dark"

    page_bg       = "#0F172A"              if d else "#F8FAFC"
    card_bg       = "rgba(255,255,255,0.04)" if d else "#FFFFFF"
    card_border   = "rgba(255,255,255,0.07)" if d else "rgba(15,23,42,0.08)"
    card_shadow   = "0 1px 3px rgba(0,0,0,0.35), 0 4px 12px rgba(0,0,0,0.2)" if d else "0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04)"
    card_hover    = "rgba(255,255,255,0.07)" if d else "#F1F5F9"
    kpi_label     = "#475569"              if d else "#94A3B8"
    kpi_value     = "#F1F5F9"              if d else "#0F172A"
    kpi_sub       = "#334155"              if d else "#CBD5E1"
    section_title = "#94A3B8"              if d else "#64748B"
    page_title    = "#F8FAFC"              if d else "#0F172A"
    page_sub      = "#475569"              if d else "#94A3B8"
    divider       = "rgba(255,255,255,0.06)" if d else "rgba(15,23,42,0.07)"
    badge_bg      = "rgba(99,102,241,0.15)" if d else "rgba(99,102,241,0.08)"
    badge_text    = "#A5B4FC"              if d else "#4338CA"
    chart_bg      = "rgba(255,255,255,0.02)" if d else "#FFFFFF"
    chart_border  = "rgba(255,255,255,0.06)" if d else "rgba(15,23,42,0.07)"
    empty_bg      = "rgba(99,102,241,0.06)" if d else "rgba(99,102,241,0.04)"
    empty_border  = "rgba(99,102,241,0.15)" if d else "rgba(99,102,241,0.12)"
    empty_text    = "#6366F1"              if d else "#4338CA"

    return f"""
    <style>
    /* ── Page header ─────────────────────────────────────────── */
    .ov-header {{ margin-bottom: 28px; }}
    .ov-title {{
        color: {page_title} !important;
        font-size: 1.6rem !important; font-weight: 700 !important;
        letter-spacing: -0.02em !important; line-height: 1.2 !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        margin: 0 0 4px !important;
    }}
    .ov-subtitle {{
        color: {page_sub} !important;
        font-size: 0.875rem !important; font-weight: 400 !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        margin: 0 0 14px !important;
    }}
    .ov-badge {{
        display: inline-flex; align-items: center; gap: 5px;
        background: {badge_bg}; color: {badge_text} !important;
        border-radius: 20px; padding: 3px 10px;
        font-size: 0.72rem !important; font-weight: 600 !important;
        letter-spacing: 0.02em;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }}

    /* ── KPI grid ────────────────────────────────────────────── */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 12px;
    }}
    .kpi-grid-4 {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 28px;
    }}
    .kpi-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: {card_shadow};
        transition: background 0.15s ease, box-shadow 0.15s ease;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }}
    .kpi-card:hover {{ background: {card_hover}; }}
    .kpi-icon-wrap {{
        width: 34px; height: 34px; border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; margin-bottom: 12px; flex-shrink: 0;
    }}
    .kpi-label {{
        color: {kpi_label} !important;
        font-size: 0.68rem !important; font-weight: 600 !important;
        letter-spacing: 0.08em !important; text-transform: uppercase !important;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        color: {kpi_value} !important;
        font-size: 1.45rem !important; font-weight: 700 !important;
        letter-spacing: -0.02em !important; line-height: 1.1 !important;
    }}
    .kpi-value-sm {{
        color: {kpi_value} !important;
        font-size: 1.2rem !important; font-weight: 700 !important;
        letter-spacing: -0.02em !important; line-height: 1.1 !important;
    }}
    .kpi-sub {{
        color: {kpi_sub} !important;
        font-size: 0.7rem !important; margin-top: 4px;
    }}

    /* ── Section header ──────────────────────────────────────── */
    .ov-section {{
        color: {section_title} !important;
        font-size: 0.72rem !important; font-weight: 700 !important;
        letter-spacing: 0.1em !important; text-transform: uppercase !important;
        margin: 28px 0 12px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        display: flex; align-items: center; gap: 8px;
    }}
    .ov-section::after {{
        content: ""; flex: 1; height: 1px; background: {divider};
    }}

    /* ── Chart card wrapper ──────────────────────────────────── */
    .chart-card {{
        background: {chart_bg};
        border: 1px solid {chart_border};
        border-radius: 14px; padding: 20px;
        box-shadow: {card_shadow};
    }}
    .chart-title {{
        color: {kpi_value} !important;
        font-size: 0.875rem !important; font-weight: 600 !important;
        letter-spacing: -0.01em !important; margin-bottom: 2px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }}
    .chart-subtitle {{
        color: {kpi_label} !important;
        font-size: 0.72rem !important; margin-bottom: 14px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }}

    /* ── Empty state ─────────────────────────────────────────── */
    .ov-empty {{
        background: {empty_bg};
        border: 1px dashed {empty_border};
        border-radius: 14px; padding: 40px 24px;
        text-align: center;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }}
    .ov-empty-icon {{ font-size: 2.2rem; margin-bottom: 12px; }}
    .ov-empty-title {{
        color: {empty_text} !important;
        font-size: 0.95rem !important; font-weight: 600 !important;
        margin-bottom: 6px;
    }}
    .ov-empty-sub {{
        color: {page_sub} !important; font-size: 0.82rem !important;
    }}
    </style>
    """


def _kpi_card(icon: str, label: str, value: str, accent: str,
              sub: str = "", small: bool = False) -> str:
    val_class = "kpi-value-sm" if small else "kpi-value"
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon-wrap" style="background:{accent}22;color:{accent};">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="{val_class}">{value}</div>
        {sub_html}
    </div>"""


def _plotly_layout(theme: str, height: int = 300) -> dict:
    """Shared plotly layout tokens for the active theme."""
    d = theme == "dark"
    return dict(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif",
                  color="#64748B" if d else "#94A3B8", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)" if d else "rgba(0,0,0,0.05)",
                   linecolor="rgba(255,255,255,0.08)" if d else "rgba(0,0,0,0.08)",
                   tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)" if d else "rgba(0,0,0,0.05)",
                   linecolor="rgba(255,255,255,0.08)" if d else "rgba(0,0,0,0.08)",
                   tickfont=dict(size=10)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        hovermode="x unified",
    )


def main():
    st.set_page_config(
        page_title="Agent Performance Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize database
    db.init_db()

    # ---- Theme state ----
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    theme = st.session_state.theme

    # ---- Custom CSS (via st.html per Streamlit docs) ----
    st.html(_sidebar_css(theme))

    # ---- Sidebar ----

    # Logo / brand
    st.sidebar.html("""
    <div class="sb-logo-wrap">
        <div class="sb-logo-icon">⚡</div>
        <div>
            <div class="sb-logo-title">FuzeBox</div>
            <div class="sb-logo-sub">Agent Performance Platform</div>
        </div>
    </div>
    """)

    # Actions
    st.sidebar.html('<span class="sb-section-label">Workspace</span>')
    if st.sidebar.button("↑  Load Demo Data", type="primary", use_container_width=False):
        with st.spinner("Generating demo data..."):
            result = db.seed_demo_data()
        st.sidebar.success(
            f"Loaded {result['agents']} agents · {result['tasks']} tasks · "
            f"{result['spans']} spans · {result['workflows']} workflows"
        )
        st.rerun()

    # Navigation
    st.sidebar.html('<span class="sb-section-label">Navigation</span>')
    _NAV_LABELS = [
        "🏠  Overview",
        "🤖  Agent Registry",
        "📋  Task Scorecards",
        "💰  Economic Analysis",
        "⚡  Performance Metrics",
        "🔍  Workflow Traces",
    ]
    _NAV_MAP = {label: label.split("  ", 1)[1] for label in _NAV_LABELS}

    _selected_nav = st.sidebar.radio(
        "nav",
        _NAV_LABELS,
        label_visibility="collapsed",
    )
    page = _NAV_MAP[_selected_nav]

    st.sidebar.html("<hr>")

    # Filters
    st.sidebar.html('<span class="sb-section-label">Filters</span>')

    date_range = st.sidebar.selectbox(
        "TIME RANGE",
        ["Last 7 days", "Last 14 days", "Last 30 days", "All time"],
        index=0,
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
    selected_agents = st.sidebar.multiselect("AGENTS", list(agent_names.keys()))
    selected_agent_ids = [agent_names[n] for n in selected_agents] if selected_agents else None

    # Group filter
    groups = sorted(set(a.group for a in all_agents))
    selected_group = st.sidebar.selectbox("GROUP", ["All"] + groups)

    st.sidebar.html("<hr>")

    # # Theme toggle + status
    # _toggle_label = "☀️  Light mode" if theme == "dark" else "🌙  Dark mode"
    # if st.sidebar.button(_toggle_label, use_container_width=True):
    #     st.session_state.theme = "light" if theme == "dark" else "dark"
    #     st.rerun()


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


# ==================== OVERVIEW ====================

def render_overview(start_date, end_date, agent_ids):
    theme = st.session_state.get("theme", "dark")
    d = theme == "dark"

    # Inject overview CSS
    st.html(_overview_css(theme))

    # ── Page header ───────────────────────────────────────────
    range_label = "All time"
    if start_date:
        days = (datetime.utcnow() - start_date).days
        range_label = f"Last {days} days"

    st.html(f"""
    <div class="ov-header">
        <div class="ov-title">Dashboard Overview</div>
        <div class="ov-subtitle">Monitor agent performance, costs, and system health</div>
        <span class="ov-badge">📅 {range_label}</span>
    </div>
    """)

    summary = metrics.performance_summary(start_date, end_date)
    if summary.get("total_tasks", 0) == 0:
        st.html("""
        <div class="ov-empty">
            <div class="ov-empty-icon">⚡</div>
            <div class="ov-empty-title">No data yet</div>
            <div class="ov-empty-sub">Click <strong>Load Demo Data</strong> in the sidebar to populate the dashboard.</div>
        </div>
        """)
        return

    # ── Row 1: primary KPIs ───────────────────────────────────
    sr = summary["success_rate"]
    sr_accent = "#22C55E" if sr >= 0.8 else "#F59E0B" if sr >= 0.6 else "#EF4444"

    st.html(f"""
    <div class="kpi-grid">
        {_kpi_card("📊", "Total Tasks",   f"{summary['total_tasks']:,}",          "#6366F1")}
        {_kpi_card("✅", "Success Rate",  f"{sr:.1%}",                             sr_accent)}
        {_kpi_card("⭐", "Avg Quality",   f"{summary['avg_quality']:.2f}",         "#8B5CF6")}
        {_kpi_card("⚡", "Avg Latency",   f"{summary['avg_latency_ms']:,.0f}ms",   "#06B6D4")}
        {_kpi_card("💰", "Total Cost",    f"${summary['total_cost']:.2f}",         "#F59E0B")}
        {_kpi_card("🤖", "Active Agents", str(summary['active_agents']),           "#10B981")}
    </div>
    """)

    # ── Row 2: secondary KPIs ─────────────────────────────────
    wsr = summary["workflow_success_rate"]
    wsr_accent = "#22C55E" if wsr >= 0.8 else "#F59E0B" if wsr >= 0.6 else "#EF4444"

    st.html(f"""
    <div class="kpi-grid-4">
        {_kpi_card("🔁", "Workflows",        str(summary['total_workflows']),              "#6366F1", small=True)}
        {_kpi_card("🎯", "Workflow Success",  f"{wsr:.1%}",                                 wsr_accent, small=True)}
        {_kpi_card("📈", "P90 Latency",      f"{summary['p90_latency_ms']:,.0f}ms",        "#06B6D4", small=True)}
        {_kpi_card("🏷️", "Avg Cost / Task",  f"${summary['avg_cost_per_task']:.4f}",       "#F59E0B", small=True)}
    </div>
    """)

    # ── Charts ────────────────────────────────────────────────
    st.html('<div class="ov-section">Trends</div>')
    left, right = st.columns(2, gap="medium")

    with left:
        st.html('<div class="chart-card"><div class="chart-title">Cost Trend</div>'
                '<div class="chart-subtitle">Daily spend vs. cumulative total</div>')
        cost_ts = economics.cost_time_series(start_date, end_date)
        if not cost_ts.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=cost_ts["date"], y=cost_ts["total_cost"],
                name="Daily Cost",
                line=dict(color="#6366F1", width=2),
                fill="tozeroy", fillcolor="rgba(99,102,241,0.12)",
                hovertemplate="$%{y:.4f}<extra>Daily</extra>",
            ))
            fig.add_trace(go.Scatter(
                x=cost_ts["date"], y=cost_ts["cumulative_cost"],
                name="Cumulative",
                line=dict(color="#F59E0B", width=2, dash="dot"),
                hovertemplate="$%{y:.4f}<extra>Cumulative</extra>",
                yaxis="y2",
            ))
            layout = _plotly_layout(theme)
            layout["yaxis2"] = dict(
                overlaying="y", side="right",
                gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10),
                color="#F59E0B",
            )
            layout["yaxis"]["title"] = dict(text="Daily ($)", font=dict(size=10))
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    with right:
        st.html('<div class="chart-card"><div class="chart-title">Throughput & Success Rate</div>'
                '<div class="chart-subtitle">Task volume with success rate overlay</div>')
        tp = metrics.throughput_time_series(start_date=start_date, end_date=end_date)
        if not tp.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=tp["date"], y=tp["task_count"],
                name="Tasks",
                marker_color="rgba(16,185,129,0.55)",
                marker_line_color="rgba(16,185,129,0.8)",
                marker_line_width=1,
                hovertemplate="%{y} tasks<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=tp["date"], y=tp["success_rate"],
                name="Success Rate",
                line=dict(color="#F59E0B", width=2),
                mode="lines+markers",
                marker=dict(size=4),
                hovertemplate="%{y:.1%}<extra>Success</extra>",
                yaxis="y2",
            ))
            layout = _plotly_layout(theme)
            layout["yaxis2"] = dict(
                overlaying="y", side="right", range=[0, 1.05],
                gridcolor="rgba(0,0,0,0)", tickformat=".0%",
                tickfont=dict(size=10), color="#F59E0B",
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    # ── Agent Leaderboard ─────────────────────────────────────
    st.html('<div class="ov-section">Agent Leaderboard</div>')
    lb = metrics.agent_leaderboard(start_date, end_date)
    if not lb.empty:
        _search_col, _ = st.columns([0.4, 0.6])
        lb_search = _search_col.text_input(
            "Filter agents",
            placeholder="🔍  Search by agent name…",
            label_visibility="collapsed",
            key="ov_lb_search",
        )
        if lb_search.strip():
            mask = lb["Agent"].astype(str).str.contains(lb_search.strip(), case=False, na=False, regex=False)
            lb_filtered = lb[mask]
        else:
            lb_filtered = lb
        st.dataframe(
            lb_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Success Rate": st.column_config.ProgressColumn(
                    "Success Rate", format="%.1f%%", min_value=0, max_value=1),
                "Avg Quality": st.column_config.NumberColumn(
                    "Avg Quality", format="%.2f"),
                "Avg Latency (ms)": st.column_config.NumberColumn(
                    "Avg Latency", format="%,d ms"),
                "Total Cost ($)": st.column_config.NumberColumn(
                    "Total Cost", format="$%.4f"),
                "Score": st.column_config.ProgressColumn(
                    "Score", format="%.3f", min_value=0, max_value=1),
            },
        )


# ==================== AGENT REGISTRY ====================

_AVATAR_ACCENTS = ["#6366F1","#8B5CF6","#06B6D4","#10B981","#F59E0B","#EF4444","#EC4899","#14B8A6"]

def _agent_card_html(agent, idx: int) -> str:
    accent = _AVATAR_ACCENTS[idx % len(_AVATAR_ACCENTS)]
    initial = agent.name[0].upper()

    status_val = agent.status.value.upper()
    if status_val == "ACTIVE":
        status_color, status_bg = "#22C55E", "rgba(34,197,94,0.12)"
    elif status_val == "INACTIVE":
        status_color, status_bg = "#EF4444", "rgba(239,68,68,0.12)"
    else:
        status_color, status_bg = "#64748B", "rgba(100,116,139,0.12)"

    return f"""
    <div class="ar-agent-card">
        <div class="ar-card-top">
            <div class="ar-avatar" style="background:{accent}22; color:{accent};">{initial}</div>
            <div class="ar-card-identity">
                <div class="ar-agent-name">{agent.name}</div>
                <div class="ar-agent-group">{agent.group}</div>
            </div>
            <span class="ar-status-badge" style="color:{status_color}; background:{status_bg};">
                ● {status_val.capitalize()}
            </span>
        </div>
        <div class="ar-card-body">
            <div class="ar-model">🧠 {agent.model_name}</div>
            <div class="ar-card-stats">
                <div class="ar-stat"><span class="ar-stat-num">{len(agent.skills)}</span><span class="ar-stat-lbl">Skills</span></div>
                <div class="ar-stat-divider"></div>
                <div class="ar-stat"><span class="ar-stat-num">{len(agent.permissions)}</span><span class="ar-stat-lbl">Perms</span></div>
                <div class="ar-stat-divider"></div>
                <div class="ar-stat"><span class="ar-stat-num">${agent.cost_per_1k_input:.3f}</span><span class="ar-stat-lbl">In/1K</span></div>
                <div class="ar-stat-divider"></div>
                <div class="ar-stat"><span class="ar-stat-num">${agent.cost_per_1k_output:.3f}</span><span class="ar-stat-lbl">Out/1K</span></div>
            </div>
        </div>
    </div>"""


def render_agent_registry(agent_ids):
    st.html("""
    <style>
    /* ── Shared page header classes ──────────────────────────── */
    .ov-header { margin-bottom: 28px; }
    .ov-title {
        color: #F8FAFC !important; font-size: 1.6rem !important;
        font-weight: 700 !important; letter-spacing: -0.02em !important;
        line-height: 1.2 !important; margin: 0 0 4px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ov-subtitle {
        color: #475569 !important; font-size: 0.875rem !important;
        margin: 0 0 14px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ov-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(99,102,241,0.15); color: #A5B4FC !important;
        border-radius: 20px; padding: 3px 10px;
        font-size: 0.72rem !important; font-weight: 600 !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ov-empty {
        background: rgba(99,102,241,0.06);
        border: 1px dashed rgba(99,102,241,0.15);
        border-radius: 14px; padding: 40px 24px; text-align: center;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ov-empty-icon { font-size: 2.2rem; margin-bottom: 12px; }
    .ov-empty-title {
        color: #6366F1 !important; font-size: 0.95rem !important;
        font-weight: 600 !important; margin-bottom: 6px;
    }
    .ov-empty-sub { color: #475569 !important; font-size: 0.82rem !important; }
    /* ── KPI card (shared with overview) ────────────────────── */
    .kpi-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07); border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.35), 0 4px 12px rgba(0,0,0,0.2);
        transition: background 0.15s ease;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .kpi-card:hover { background: rgba(255,255,255,0.06); }
    .kpi-icon-wrap {
        width: 34px; height: 34px; border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; margin-bottom: 12px;
    }
    .kpi-label {
        color: #475569 !important; font-size: 0.68rem !important;
        font-weight: 600 !important; letter-spacing: 0.08em !important;
        text-transform: uppercase !important; margin-bottom: 4px;
    }
    .kpi-value-sm {
        color: #F1F5F9 !important; font-size: 1.2rem !important;
        font-weight: 700 !important; letter-spacing: -0.02em !important;
    }

    /* ── Agent cards grid ────────────────────────────────────── */
    .ar-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 6px;
    }
    .ar-agent-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.35), 0 4px 12px rgba(0,0,0,0.2);
        transition: background 0.15s ease;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ar-agent-card:hover { background: rgba(255,255,255,0.06); }
    .ar-card-top {
        display: flex; align-items: center; gap: 12px; margin-bottom: 14px;
    }
    .ar-avatar {
        width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; font-weight: 700;
    }
    .ar-card-identity { flex: 1; min-width: 0; }
    .ar-agent-name {
        color: #F1F5F9 !important; font-size: 0.875rem !important;
        font-weight: 600 !important; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;
    }
    .ar-agent-group {
        color: #475569 !important; font-size: 0.7rem !important;
        margin-top: 1px;
    }
    .ar-status-badge {
        font-size: 0.65rem !important; font-weight: 600 !important;
        padding: 3px 8px; border-radius: 20px; white-space: nowrap;
        letter-spacing: 0.02em; flex-shrink: 0;
    }
    .ar-card-body { border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; }
    .ar-model {
        color: #64748B !important; font-size: 0.75rem !important;
        margin-bottom: 10px;
    }
    .ar-card-stats {
        display: flex; align-items: center; gap: 0;
    }
    .ar-stat {
        flex: 1; display: flex; flex-direction: column;
        align-items: center; gap: 2px;
    }
    .ar-stat-num {
        color: #CBD5E1 !important; font-size: 0.8rem !important;
        font-weight: 600 !important;
    }
    .ar-stat-lbl {
        color: #334155 !important; font-size: 0.6rem !important;
        text-transform: uppercase; letter-spacing: 0.06em;
    }
    .ar-stat-divider {
        width: 1px; height: 24px; background: rgba(255,255,255,0.06);
        flex-shrink: 0;
    }

    /* ── Summary stat cards (reuses kpi-card from overview) ─── */
    .ar-summary-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin-bottom: 28px;
    }

    /* ── Matrix section ──────────────────────────────────────── */
    .ar-matrix-wrap {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.35);
    }
    .ar-matrix-title {
        color: #F1F5F9 !important; font-size: 0.875rem !important;
        font-weight: 600 !important; margin-bottom: 2px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ar-matrix-sub {
        color: #475569 !important; font-size: 0.72rem !important;
        margin-bottom: 12px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }

    /* ── Violations ──────────────────────────────────────────── */
    .ar-violation-card {
        background: rgba(239,68,68,0.06);
        border: 1px solid rgba(239,68,68,0.18);
        border-radius: 12px; padding: 14px 18px;
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 8px;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ar-violation-icon { font-size: 1rem; flex-shrink: 0; }
    .ar-violation-agent {
        color: #FCA5A5 !important; font-size: 0.8rem !important;
        font-weight: 600 !important;
    }
    .ar-violation-desc {
        color: #64748B !important; font-size: 0.75rem !important;
        margin-top: 2px;
    }
    .ar-all-clear {
        background: rgba(34,197,94,0.06);
        border: 1px solid rgba(34,197,94,0.18);
        border-radius: 12px; padding: 16px 20px;
        display: flex; align-items: center; gap: 12px;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ar-all-clear-text {
        color: #4ADE80 !important; font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    .ar-all-clear-sub {
        color: #334155 !important; font-size: 0.75rem !important;
        margin-top: 2px;
    }

    /* ── Shared section label for this page ──────────────────── */
    .ar-section {
        color: #475569 !important;
        font-size: 0.72rem !important; font-weight: 700 !important;
        letter-spacing: 0.1em !important; text-transform: uppercase !important;
        margin: 28px 0 12px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        display: flex; align-items: center; gap: 8px;
    }
    .ar-section::after {
        content: ""; flex: 1; height: 1px;
        background: rgba(255,255,255,0.06);
    }
    </style>
    """)

    agents = db.get_all_agents()

    # ── Page header ───────────────────────────────────────────
    st.html(f"""
    <div class="ov-header">
        <div class="ov-title">Agent Registry</div>
        <div class="ov-subtitle">Manage and inspect your registered AI agents</div>
        <span class="ov-badge">🤖 {len(agents)} agent{'s' if len(agents) != 1 else ''} registered</span>
    </div>
    """)

    if not agents:
        st.html("""
        <div class="ov-empty">
            <div class="ov-empty-icon">🤖</div>
            <div class="ov-empty-title">No agents registered</div>
            <div class="ov-empty-sub">Click <strong>Load Demo Data</strong> in the sidebar to populate the registry.</div>
        </div>
        """)
        return

    # ── Summary KPI row ───────────────────────────────────────
    total    = len(agents)
    active   = sum(1 for a in agents if a.status.value.upper() == "ACTIVE")
    all_skills = set(s for a in agents for s in a.skills)
    avg_in_cost = sum(a.cost_per_1k_input for a in agents) / total

    st.html(f"""
    <div class="ar-summary-grid">
        {_kpi_card("🤖", "Total Agents",   str(total),                    "#6366F1", small=True)}
        {_kpi_card("✅", "Active Agents",  str(active),                   "#22C55E", small=True)}
        {_kpi_card("⚡", "Unique Skills",  str(len(all_skills)),           "#8B5CF6", small=True)}
        {_kpi_card("💰", "Avg In Cost/1K", f"${avg_in_cost:.4f}",         "#F59E0B", small=True)}
    </div>
    """)

    # ── Agent cards ───────────────────────────────────────────
    st.html('<div class="ar-section">All Agents</div>')
    cards_html = "\n".join(_agent_card_html(a, i) for i, a in enumerate(agents))
    st.html(f'<div class="ar-grid">{cards_html}</div>')

    # ── Skills & Permissions matrices ─────────────────────────
    st.html('<div class="ar-section">Capability Matrices</div>')
    left, right = st.columns(2, gap="medium")

    with left:
        st.html('<div class="ar-matrix-wrap">'
                '<div class="ar-matrix-title">Skills Matrix</div>'
                '<div class="ar-matrix-sub">Which agents have each skill</div>')
        skills_df = evaluators.get_skills_matrix(agent_ids)
        if not skills_df.empty:
            display_df = skills_df.set_index("agent").drop(columns=["agent_id"], errors="ignore")
            _sc, _ = st.columns([0.4, 0.6])
            _skills_q = _sc.text_input("Filter agents", placeholder="🔍  Search agent…", label_visibility="collapsed", key="ar_skills_search")
            if _skills_q.strip():
                display_df = display_df[display_df.index.astype(str).str.contains(_skills_q.strip(), case=False, na=False, regex=False)]
            styled = display_df.style.map(
                lambda v: "background:#22C55E22; color:#4ADE80; font-weight:600" if v
                else "color:#334155"
            ).format(lambda v: "✓" if v else "–")
            st.dataframe(styled, use_container_width=True, hide_index=False)
        st.html('</div>')

    with right:
        st.html('<div class="ar-matrix-wrap">'
                '<div class="ar-matrix-title">Permissions Matrix</div>'
                '<div class="ar-matrix-sub">Which agents hold each permission</div>')
        perms_df = evaluators.get_permissions_matrix(agent_ids)
        if not perms_df.empty:
            display_df = perms_df.set_index("agent").drop(columns=["agent_id"], errors="ignore")
            _pc, _ = st.columns([0.4, 0.6])
            _perms_q = _pc.text_input("Filter agents", placeholder="🔍  Search agent…", label_visibility="collapsed", key="ar_perms_search")
            if _perms_q.strip():
                display_df = display_df[display_df.index.astype(str).str.contains(_perms_q.strip(), case=False, na=False, regex=False)]
            styled = display_df.style.map(
                lambda v: "background:#6366F122; color:#A5B4FC; font-weight:600" if v
                else "color:#334155"
            ).format(lambda v: "✓" if v else "–")
            st.dataframe(styled, use_container_width=True, hide_index=False)
        st.html('</div>')

    # ── Permission violations ─────────────────────────────────
    st.html('<div class="ar-section">Permission Violations</div>')
    all_violations = []
    for a in agents:
        for v in evaluators.check_permission_violations(a.agent_id):
            v["agent"] = a.name
            all_violations.append(v)

    if all_violations:
        df_v = pd.DataFrame(all_violations)
        cols = ["agent"] + [c for c in df_v.columns if c != "agent"]
        df_v = df_v[cols]

        _RESULT_STYLES = {
            "success": ("rgba(34,197,94,0.15)",  "#4ADE80"),
            "failure": ("rgba(239,68,68,0.15)",   "#F87171"),
            "partial": ("rgba(245,158,11,0.15)",  "#FCD34D"),
            "timeout": ("rgba(100,116,139,0.15)", "#94A3B8"),
        }

        def _style_result(val):
            bg, color = _RESULT_STYLES.get(str(val).lower(), ("transparent", "#94A3B8"))
            return (f"background:{bg}; color:{color}; font-weight:600; "
                    "border-radius:6px; text-align:center;")

        _vc, _ = st.columns([0.4, 0.6])
        _viol_q = _vc.text_input("Filter violations", placeholder="🔍  Search by agent…", label_visibility="collapsed", key="ar_viol_search")
        if _viol_q.strip():
            df_v = df_v[df_v["agent"].astype(str).str.contains(_viol_q.strip(), case=False, na=False, regex=False)]

        styled_v = df_v.style.applymap(_style_result, subset=["result"])

        st.html(f'<div class="ar-violation-card" style="margin-bottom:12px;">'
                f'<span class="ar-violation-icon">⚠️</span>'
                f'<div><div class="ar-violation-agent">'
                f'{len(all_violations)} violation{"s" if len(all_violations) != 1 else ""} detected</div>'
                f'<div class="ar-violation-desc">Review the table below and resolve outstanding issues.</div>'
                f'</div></div>')
        st.dataframe(styled_v, use_container_width=True, hide_index=True)
    else:
        st.html("""
        <div class="ar-all-clear">
            <span style="font-size:1.2rem">✅</span>
            <div>
                <div class="ar-all-clear-text">All clear</div>
                <div class="ar-all-clear-sub">No permission or skill violations detected across any agent.</div>
            </div>
        </div>
        """)


# ==================== TASK SCORECARDS ====================

def render_scorecards(start_date, end_date, agent_ids, selected_group):
    theme = st.session_state.get("theme", "dark")

    st.html(_SHARED_PAGE_CSS + """
    <style>
    /* ── Scorecard-specific ───────────────────────────────────── */
    .sc-section {
        color: #475569 !important; font-size: 0.72rem !important;
        font-weight: 700 !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important; margin: 28px 0 12px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        display: flex; align-items: center; gap: 8px;
    }
    .sc-section::after {
        content: ""; flex: 1; height: 1px;
        background: rgba(255,255,255,0.06);
    }
    .sc-summary-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin-bottom: 28px;
    }
    .sc-card-wrap {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.35);
        margin-bottom: 6px;
    }
    .sc-card-title {
        color: #F1F5F9 !important; font-size: 0.875rem !important;
        font-weight: 600 !important; margin-bottom: 2px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .sc-card-sub {
        color: #475569 !important; font-size: 0.72rem !important;
        margin-bottom: 14px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    /* Group eval pass/fail banner */
    .sc-group-banner {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 18px; border-radius: 12px; margin-bottom: 16px;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .sc-group-banner-icon { font-size: 1.4rem; flex-shrink: 0; }
    .sc-group-banner-label {
        font-size: 0.72rem !important; font-weight: 700 !important;
        letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px;
    }
    .sc-group-banner-name {
        font-size: 0.95rem !important; font-weight: 600 !important;
    }
    .sc-group-kpi-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin-bottom: 4px;
    }
    </style>
    """)

    # ── Page header ───────────────────────────────────────────
    group_badge = f"· {selected_group}" if selected_group != "All" else "· All groups"
    st.html(f"""
    <div class="ov-header">
        <div class="ov-title">Task Scorecards</div>
        <div class="ov-subtitle">Completion rates, quality scores, and pass/fail status per agent</div>
        <span class="ov-badge">📋 {group_badge}</span>
    </div>
    """)

    scorecard_df = evaluators.get_agent_scorecard_df(start_date, end_date)
    if scorecard_df.empty:
        st.html("""
        <div class="ov-empty">
            <div class="ov-empty-icon">📋</div>
            <div class="ov-empty-title">No scorecard data yet</div>
            <div class="ov-empty-sub">Click <strong>Load Demo Data</strong> in the sidebar to populate task results.</div>
        </div>
        """)
        return

    if selected_group != "All":
        scorecard_df = scorecard_df[scorecard_df["Group"] == selected_group]

    # ── Summary KPIs ──────────────────────────────────────────
    total_scored  = len(scorecard_df)
    passing       = (scorecard_df["Status"] == "PASS").sum()
    failing       = total_scored - passing
    avg_quality   = scorecard_df["Avg Quality"].mean() if "Avg Quality" in scorecard_df.columns else 0
    pass_accent   = "#22C55E" if passing == total_scored else "#F59E0B" if passing > 0 else "#EF4444"

    st.html(f"""
    <div class="sc-summary-grid">
        {_kpi_card("📋", "Agents Scored",  str(total_scored),          "#6366F1", small=True)}
        {_kpi_card("✅", "Passing",         str(passing),               "#22C55E", small=True)}
        {_kpi_card("❌", "Failing",          str(failing),               "#EF4444" if failing else "#334155", small=True)}
        {_kpi_card("⭐", "Avg Quality",     f"{avg_quality:.2f}",       "#8B5CF6", small=True)}
    </div>
    """)

    # ── Scorecard table ───────────────────────────────────────
    st.html('<div class="sc-section">Agent Scorecards</div>')
    st.html('<div class="sc-card-wrap">'
            '<div class="sc-card-title">Completion Scorecard</div>'
            '<div class="sc-card-sub">Pass threshold: ≥ 80% success rate</div>')
    _scc, _ = st.columns([0.4, 0.6])
    _sc_q = _scc.text_input("Filter agents", placeholder="🔍  Search agent…", label_visibility="collapsed", key="sc_search")
    if _sc_q.strip():
        scorecard_df = scorecard_df[scorecard_df["Agent"].astype(str).str.contains(_sc_q.strip(), case=False, na=False, regex=False)]
    st.dataframe(
        scorecard_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status"),
            "Success Rate": st.column_config.ProgressColumn(
                "Success Rate", format="%.1f%%", min_value=0, max_value=1),
            "Failure Rate": st.column_config.ProgressColumn(
                "Failure Rate", format="%.1f%%", min_value=0, max_value=1),
            "Avg Quality": st.column_config.NumberColumn(
                "Avg Quality", format="%.2f"),
        },
    )
    st.html('</div>')

    # ── Group evaluation ──────────────────────────────────────
    if selected_group != "All":
        st.html('<div class="sc-section">Group Evaluation</div>')
        group_eval   = evaluators.evaluate_group_completion(selected_group, start_date, end_date)
        is_pass      = group_eval["pass"]
        banner_bg    = "rgba(34,197,94,0.07)"  if is_pass else "rgba(239,68,68,0.07)"
        banner_bdr   = "rgba(34,197,94,0.18)"  if is_pass else "rgba(239,68,68,0.18)"
        banner_label_color = "#4ADE80"         if is_pass else "#FCA5A5"
        banner_icon  = "✅" if is_pass else "❌"
        verdict      = "PASS" if is_pass else "FAIL"

        st.html(f"""
        <div class="sc-group-banner"
             style="background:{banner_bg}; border:1px solid {banner_bdr};">
            <span class="sc-group-banner-icon">{banner_icon}</span>
            <div>
                <div class="sc-group-banner-label"
                     style="color:{banner_label_color}">Group verdict · {verdict}</div>
                <div class="sc-group-banner-name"
                     style="color:#F1F5F9">{selected_group}</div>
            </div>
        </div>
        <div class="sc-group-kpi-grid">
            {_kpi_card("🤖", "Agents",          str(group_eval['agents']),                   "#6366F1", small=True)}
            {_kpi_card("📈", "Group Success",    f"{group_eval['group_success_rate']:.1%}",   "#22C55E" if is_pass else "#EF4444", small=True)}
            {_kpi_card("✅", "Passing Agents",   str(group_eval['agents_passing']),           "#22C55E", small=True)}
            {_kpi_card("🎯", "Verdict",          verdict,                                      "#22C55E" if is_pass else "#EF4444", small=True)}
        </div>
        """)

    # ── Success by task type ───────────────────────────────────
    st.html('<div class="sc-section">Success by Task Type</div>')
    acc_df = metrics.accuracy_by_type(start_date=start_date, end_date=end_date)
    if not acc_df.empty:
        bar_colors = ["#22C55E" if r >= 0.8 else "#F59E0B" if r >= 0.6 else "#EF4444"
                      for r in acc_df["Success Rate"]]
        fig = go.Figure(go.Bar(
            x=acc_df["Success Rate"],
            y=acc_df["Task Type"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"{r:.0%}" for r in acc_df["Success Rate"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1%}<extra></extra>",
        ))
        layout = _plotly_layout(theme, height=max(260, len(acc_df) * 42))
        layout["xaxis"].update(range=[0, 1.12], tickformat=".0%")
        layout["margin"] = dict(l=0, r=40, t=10, b=0)
        fig.update_layout(**layout)

        st.html('<div class="sc-card-wrap">'
                '<div class="sc-card-title">Success Rate by Task Type</div>'
                '<div class="sc-card-sub">Green ≥ 80% · Amber 60–80% · Red &lt; 60%</div>')
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')


# ==================== ECONOMIC ANALYSIS ====================

_SHARED_PAGE_CSS = """
<style>
.ov-header { margin-bottom: 28px; }
.ov-title {
    color: #F8FAFC !important; font-size: 1.6rem !important;
    font-weight: 700 !important; letter-spacing: -0.02em !important;
    line-height: 1.2 !important; margin: 0 0 4px !important;
    font-family: "Inter","SF Pro Display",system-ui,sans-serif;
}
.ov-subtitle {
    color: #475569 !important; font-size: 0.875rem !important;
    margin: 0 0 14px !important;
    font-family: "Inter","SF Pro Display",system-ui,sans-serif;
}
.ov-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(99,102,241,0.15); color: #A5B4FC !important;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.72rem !important; font-weight: 600 !important;
    font-family: "Inter","SF Pro Display",system-ui,sans-serif;
}
.ov-empty {
    background: rgba(99,102,241,0.06);
    border: 1px dashed rgba(99,102,241,0.15);
    border-radius: 14px; padding: 40px 24px; text-align: center;
    font-family: "Inter","SF Pro Display",system-ui,sans-serif;
}
.ov-empty-icon { font-size: 2.2rem; margin-bottom: 12px; }
.ov-empty-title {
    color: #6366F1 !important; font-size: 0.95rem !important;
    font-weight: 600 !important; margin-bottom: 6px;
}
.ov-empty-sub { color: #475569 !important; font-size: 0.82rem !important; }
.kpi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07); border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.35), 0 4px 12px rgba(0,0,0,0.2);
    transition: background 0.15s ease;
    font-family: "Inter","SF Pro Display",system-ui,sans-serif;
}
.kpi-card:hover { background: rgba(255,255,255,0.06); }
.kpi-icon-wrap {
    width: 34px; height: 34px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; margin-bottom: 12px;
}
.kpi-label {
    color: #475569 !important; font-size: 0.68rem !important;
    font-weight: 600 !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important; margin-bottom: 4px;
}
.kpi-value-sm {
    color: #F1F5F9 !important; font-size: 1.2rem !important;
    font-weight: 700 !important; letter-spacing: -0.02em !important;
}
</style>
"""


def render_economics(start_date, end_date):
    theme = st.session_state.get("theme", "dark")

    st.html(_SHARED_PAGE_CSS + """
    <style>
    .ec-section {
        color: #475569 !important; font-size: 0.72rem !important;
        font-weight: 700 !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important; margin: 28px 0 12px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        display: flex; align-items: center; gap: 8px;
    }
    .ec-section::after {
        content: ""; flex: 1; height: 1px;
        background: rgba(255,255,255,0.06);
    }
    .ec-kpi-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin-bottom: 28px;
    }
    .ec-card-wrap {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.35);
    }
    .ec-card-title {
        color: #F1F5F9 !important; font-size: 0.875rem !important;
        font-weight: 600 !important; margin-bottom: 2px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ec-card-sub {
        color: #475569 !important; font-size: 0.72rem !important;
        margin-bottom: 14px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .ec-roi-banner {
        display: flex; align-items: center; gap: 20px;
        background: rgba(99,102,241,0.07);
        border: 1px solid rgba(99,102,241,0.18);
        border-radius: 14px; padding: 16px 20px; margin-bottom: 20px;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        flex-wrap: wrap;
    }
    .ec-roi-item { display: flex; flex-direction: column; gap: 2px; }
    .ec-roi-label {
        color: #475569 !important; font-size: 0.65rem !important;
        font-weight: 600 !important; letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .ec-roi-value {
        color: #F1F5F9 !important; font-size: 1.1rem !important;
        font-weight: 700 !important; letter-spacing: -0.02em;
    }
    .ec-roi-divider {
        width: 1px; height: 36px; background: rgba(255,255,255,0.08);
        flex-shrink: 0;
    }
    .ec-slider-label {
        color: #94A3B8 !important; font-size: 0.75rem !important;
        font-weight: 500 !important; margin-bottom: 6px;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    </style>
    """)

    # ── Page header ───────────────────────────────────────────
    st.html("""
    <div class="ov-header">
        <div class="ov-title">Economic Analysis</div>
        <div class="ov-subtitle">Cost breakdown, ROI, token usage, and workflow economics</div>
        <span class="ov-badge">💰 Cost intelligence</span>
    </div>
    """)

    # ── ROI Calculator ────────────────────────────────────────
    st.html('<div class="ec-section">ROI Calculator</div>')
    st.html('<div class="ec-slider-label">Manual cost per task — adjust to calculate savings vs. agent automation</div>')
    manual_cost = st.slider("Manual cost per task ($)", 10, 200, 50, 5,
                            label_visibility="collapsed")
    roi = economics.calculate_roi(manual_cost, start_date, end_date)

    if roi.get("total_tasks", 0) > 0:
        roi_pct       = roi["roi_pct"]
        roi_color     = "#22C55E" if roi_pct > 0 else "#EF4444"
        savings_color = "#22C55E" if roi["savings"] > 0 else "#EF4444"
        st.html(f"""
        <div class="ec-roi-banner">
            <div class="ec-roi-item">
                <span class="ec-roi-label">Agent Total Cost</span>
                <span class="ec-roi-value">${roi['agent_total_cost']:.2f}</span>
            </div>
            <div class="ec-roi-divider"></div>
            <div class="ec-roi-item">
                <span class="ec-roi-label">Manual Equivalent</span>
                <span class="ec-roi-value">${roi['manual_equivalent_cost']:.2f}</span>
            </div>
            <div class="ec-roi-divider"></div>
            <div class="ec-roi-item">
                <span class="ec-roi-label">Savings</span>
                <span class="ec-roi-value" style="color:{savings_color}">
                    ${roi['savings']:.2f}
                </span>
            </div>
            <div class="ec-roi-divider"></div>
            <div class="ec-roi-item">
                <span class="ec-roi-label">ROI</span>
                <span class="ec-roi-value" style="color:{roi_color}">
                    {roi_pct:.0f}%
                </span>
            </div>
        </div>
        """)

    # ── Cost breakdown charts ─────────────────────────────────
    st.html('<div class="ec-section">Cost Breakdown</div>')
    left, right = st.columns(2, gap="medium")

    with left:
        cpa = economics.cost_per_agent(start_date, end_date)
        st.html('<div class="ec-card-wrap">'
                '<div class="ec-card-title">Cost by Agent</div>'
                '<div class="ec-card-sub">Total spend per agent over the selected period</div>')
        if not cpa.empty:
            fig = go.Figure(go.Bar(
                x=cpa["Total Cost ($)"], y=cpa["Agent"],
                orientation="h",
                marker_color="#6366F1", marker_opacity=0.85,
                text=[f"${v:.3f}" for v in cpa["Total Cost ($)"]],
                textposition="outside",
                hovertemplate="%{y}: $%{x:.4f}<extra></extra>",
            ))
            layout = _plotly_layout(theme, height=max(260, len(cpa) * 44))
            layout["margin"] = dict(l=0, r=60, t=10, b=0)
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            _cpac, _ = st.columns([0.4, 0.6])
            _cpa_q = _cpac.text_input("Filter agents", placeholder="🔍  Search agent…", label_visibility="collapsed", key="ec_cpa_search")
            if _cpa_q.strip():
                cpa = cpa[cpa["Agent"].astype(str).str.contains(_cpa_q.strip(), case=False, na=False, regex=False)]
            st.dataframe(cpa, use_container_width=True, hide_index=True,
                         column_config={"Total Cost ($)": st.column_config.NumberColumn(
                             "Total Cost", format="$%.4f")})
        st.html('</div>')

    with right:
        cpt = economics.cost_per_task_type(start_date, end_date)
        st.html('<div class="ec-card-wrap">'
                '<div class="ec-card-title">Cost by Task Type</div>'
                '<div class="ec-card-sub">Where spend is concentrated across task categories</div>')
        if not cpt.empty:
            fig = go.Figure(go.Bar(
                x=cpt["Total Cost ($)"], y=cpt["Task Type"],
                orientation="h",
                marker_color="#8B5CF6", marker_opacity=0.85,
                text=[f"${v:.3f}" for v in cpt["Total Cost ($)"]],
                textposition="outside",
                hovertemplate="%{y}: $%{x:.4f}<extra></extra>",
            ))
            layout = _plotly_layout(theme, height=max(260, len(cpt) * 44))
            layout["margin"] = dict(l=0, r=60, t=10, b=0)
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            _cptc, _ = st.columns([0.4, 0.6])
            _cpt_q = _cptc.text_input("Filter task types", placeholder="🔍  Search task type…", label_visibility="collapsed", key="ec_cpt_search")
            if _cpt_q.strip():
                cpt = cpt[cpt["Task Type"].astype(str).str.contains(_cpt_q.strip(), case=False, na=False, regex=False)]
            st.dataframe(cpt, use_container_width=True, hide_index=True,
                         column_config={"Total Cost ($)": st.column_config.NumberColumn(
                             "Total Cost", format="$%.4f")})
        st.html('</div>')

    # ── Token usage ───────────────────────────────────────────
    st.html('<div class="ec-section">Token Usage</div>')
    tokens = economics.token_usage_summary(start_date, end_date)
    if tokens:
        st.html(f"""
        <div class="ec-kpi-grid">
            {_kpi_card("🔤", "Total Tokens",       f"{tokens['total_tokens']:,}",           "#6366F1", small=True)}
            {_kpi_card("📊", "Avg Tokens / Task",  f"{tokens['avg_tokens_per_task']:,}",    "#8B5CF6", small=True)}
            {_kpi_card("⚖️",  "Input:Output Ratio", f"{tokens['input_output_ratio']:.2f}",  "#06B6D4", small=True)}
            {_kpi_card("⚡", "Token Efficiency",   f"{tokens['token_efficiency']:.1%}",     "#10B981", small=True)}
        </div>
        """)

        left, right = st.columns(2, gap="medium")

        with left:
            st.html('<div class="ec-card-wrap">'
                    '<div class="ec-card-title">Token Distribution</div>'
                    '<div class="ec-card-sub">Input vs. output token split</div>')
            fig = go.Figure(go.Pie(
                labels=["Input", "Output"],
                values=[tokens["total_input_tokens"], tokens["total_output_tokens"]],
                marker_colors=["#6366F1", "#F59E0B"],
                hole=0.55,
                textinfo="label+percent",
                hovertemplate="%{label}: %{value:,}<extra></extra>",
            ))
            layout = _plotly_layout(theme, height=260)
            layout.pop("xaxis", None); layout.pop("yaxis", None)
            layout["showlegend"] = False
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.html('</div>')

        with right:
            st.html('<div class="ec-card-wrap">'
                    '<div class="ec-card-title">Tokens by Outcome</div>'
                    '<div class="ec-card-sub">Average token consumption per success vs. failure</div>')
            fig = go.Figure(go.Bar(
                x=["Per Success", "Per Failure"],
                y=[tokens["avg_tokens_per_success"], tokens["avg_tokens_per_failure"]],
                marker_color=["#22C55E", "#EF4444"],
                marker_opacity=0.85,
                text=[f"{tokens['avg_tokens_per_success']:,}", f"{tokens['avg_tokens_per_failure']:,}"],
                textposition="outside",
                hovertemplate="%{x}: %{y:,} tokens<extra></extra>",
            ))
            layout = _plotly_layout(theme, height=260)
            layout["margin"] = dict(l=0, r=0, t=10, b=0)
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.html('</div>')

    # ── Cumulative cost trend ─────────────────────────────────
    st.html('<div class="ec-section">Cumulative Cost Trend</div>')
    cost_ts = economics.cost_time_series(start_date, end_date)
    if not cost_ts.empty:
        fig = go.Figure(go.Scatter(
            x=cost_ts["date"], y=cost_ts["cumulative_cost"],
            line=dict(color="#6366F1", width=2.5),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.10)",
            hovertemplate="%{x|%b %d}: $%{y:.4f}<extra>Cumulative</extra>",
        ))
        layout = _plotly_layout(theme, height=280)
        layout["yaxis"]["tickprefix"] = "$"
        fig.update_layout(**layout)
        st.html('<div class="ec-card-wrap">'
                '<div class="ec-card-title">Cumulative Spend</div>'
                '<div class="ec-card-sub">Running total cost over the selected period</div>')
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    # ── Workflow economics ────────────────────────────────────
    st.html('<div class="ec-section">Workflow Economics</div>')
    wf_econ = economics.workflow_economics(start_date, end_date)
    if not wf_econ.empty:
        st.html('<div class="ec-card-wrap">'
                '<div class="ec-card-title">Per-Workflow Breakdown</div>'
                '<div class="ec-card-sub">Cost and performance metrics per workflow run</div>')
        _wfc, _ = st.columns([0.4, 0.6])
        _wf_q = _wfc.text_input("Filter workflows", placeholder="🔍  Search workflow…", label_visibility="collapsed", key="ec_wf_search")
        if _wf_q.strip():
            wf_econ = wf_econ[wf_econ["Workflow"].astype(str).str.contains(_wf_q.strip(), case=False, na=False, regex=False)]
        st.dataframe(wf_econ, use_container_width=True, hide_index=True)
        st.html('</div>')
    else:
        st.html("""
        <div class="ov-empty">
            <div class="ov-empty-icon">💰</div>
            <div class="ov-empty-title">No economic data yet</div>
            <div class="ov-empty-sub">Load demo data to populate cost and ROI analysis.</div>
        </div>
        """)


# ==================== PERFORMANCE METRICS ====================

def render_performance(start_date, end_date, agent_ids):
    theme = st.session_state.get("theme", "dark")

    st.html(_SHARED_PAGE_CSS + """
    <style>
    .pm-section {
        color: #475569 !important; font-size: 0.72rem !important;
        font-weight: 700 !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important; margin: 28px 0 12px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
        display: flex; align-items: center; gap: 8px;
    }
    .pm-section::after {
        content: ""; flex: 1; height: 1px;
        background: rgba(255,255,255,0.06);
    }
    .pm-kpi-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin-bottom: 28px;
    }
    .pm-card-wrap {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.35);
    }
    .pm-card-title {
        color: #F1F5F9 !important; font-size: 0.875rem !important;
        font-weight: 600 !important; margin-bottom: 2px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .pm-card-sub {
        color: #475569 !important; font-size: 0.72rem !important;
        margin-bottom: 14px !important;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    .pm-granularity-label {
        color: #94A3B8 !important; font-size: 0.75rem !important;
        font-weight: 500 !important; margin-bottom: 6px;
        font-family: "Inter","SF Pro Display",system-ui,sans-serif;
    }
    </style>
    """)

    # ── Page header ───────────────────────────────────────────
    st.html("""
    <div class="ov-header">
        <div class="ov-title">Performance Metrics</div>
        <div class="ov-subtitle">Latency, throughput, completion rates, and agent leaderboard</div>
        <span class="ov-badge">⚡ Performance intelligence</span>
    </div>
    """)

    # ── Latency KPIs ──────────────────────────────────────────
    lat_stats = metrics.latency_stats(start_date=start_date, end_date=end_date)
    if lat_stats:
        st.html(f"""
        <div class="pm-kpi-grid">
            {_kpi_card("⚡", "P50 Latency", f"{lat_stats['p50_ms']:,.0f} ms", "#6366F1", small=True)}
            {_kpi_card("📈", "P90 Latency", f"{lat_stats['p90_ms']:,.0f} ms", "#F59E0B", small=True)}
            {_kpi_card("🔴", "P99 Latency", f"{lat_stats['p99_ms']:,.0f} ms", "#EF4444", small=True)}
            {_kpi_card("📊", "Avg Latency",  f"{lat_stats['mean_ms']:,.0f} ms", "#8B5CF6", small=True)}
        </div>
        """)

    # ── Completion rates + Latency by agent ───────────────────
    st.html('<div class="pm-section">Agent Breakdown</div>')
    left, right = st.columns(2, gap="medium")

    with left:
        cr = metrics.completion_rates(start_date, end_date)
        st.html('<div class="pm-card-wrap">'
                '<div class="pm-card-title">Completion Rates</div>'
                '<div class="pm-card-sub">Success rate per agent — dashed line marks 80% threshold</div>')
        if not cr.empty:
            bar_colors = ["#22C55E" if r >= 0.8 else "#F59E0B" if r >= 0.6 else "#EF4444"
                          for r in cr["Completion Rate"]]
            fig = go.Figure(go.Bar(
                x=cr["Completion Rate"], y=cr["Agent"],
                orientation="h",
                marker_color=bar_colors, marker_opacity=0.85,
                text=[f"{r:.0%}" for r in cr["Completion Rate"]],
                textposition="outside",
                hovertemplate="%{y}: %{x:.1%}<extra></extra>",
            ))
            layout = _plotly_layout(theme, height=max(260, len(cr) * 44))
            layout["xaxis"].update(range=[0, 1.15], tickformat=".0%")
            layout["margin"] = dict(l=0, r=40, t=10, b=0)
            fig.add_vline(x=0.8, line_dash="dot", line_color="rgba(148,163,184,0.4)",
                          annotation_text="80%", annotation_font_size=10,
                          annotation_font_color="#64748B")
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    with right:
        lat = metrics.latency_by_agent(start_date, end_date)
        st.html('<div class="pm-card-wrap">'
                '<div class="pm-card-title">Latency by Agent</div>'
                '<div class="pm-card-sub">P50 (median) and P90 response time per agent</div>')
        if not lat.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="P50", x=lat["Agent"], y=lat["P50 (ms)"],
                marker_color="#6366F1", marker_opacity=0.85,
                hovertemplate="%{x} P50: %{y:,}ms<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                name="P90", x=lat["Agent"], y=lat["P90 (ms)"],
                marker_color="#F59E0B", marker_opacity=0.85,
                hovertemplate="%{x} P90: %{y:,}ms<extra></extra>",
            ))
            layout = _plotly_layout(theme, height=max(260, len(lat) * 44))
            layout["barmode"] = "group"
            layout["yaxis"]["ticksuffix"] = "ms"
            layout["margin"] = dict(l=0, r=0, t=10, b=0)
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    # ── Latency distribution ──────────────────────────────────
    st.html('<div class="pm-section">Latency Distribution</div>')
    all_tasks = db.get_tasks(start_date=start_date, end_date=end_date)
    latencies = [t.latency_ms for t in all_tasks if t.latency_ms is not None] if all_tasks else []

    if latencies:
        st.html('<div class="pm-card-wrap">'
                '<div class="pm-card-title">Latency Histogram</div>'
                '<div class="pm-card-sub">Distribution of task response times with P50 / P90 / P99 markers</div>')
        fig = go.Figure(go.Histogram(
            x=latencies, nbinsx=50,
            marker_color="#6366F1", marker_opacity=0.75,
            hovertemplate="~%{x}ms: %{y} tasks<extra></extra>",
        ))
        if lat_stats:
            for val, label, color in [
                (lat_stats["p50_ms"], "P50", "#22C55E"),
                (lat_stats["p90_ms"], "P90", "#F59E0B"),
                (lat_stats["p99_ms"], "P99", "#EF4444"),
            ]:
                fig.add_vline(x=val, line_dash="dot", line_color=color, line_width=1.5,
                              annotation_text=f"{label}: {val:.0f}ms",
                              annotation_font_size=10, annotation_font_color=color,
                              annotation_position="top right")
        layout = _plotly_layout(theme, height=300)
        layout["xaxis"]["ticksuffix"] = "ms"
        layout["yaxis"]["title"] = dict(text="Tasks", font=dict(size=10))
        layout["bargap"] = 0.05
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    # ── Throughput trend ──────────────────────────────────────
    st.html('<div class="pm-section">Throughput Trend</div>')
    st.html('<div class="pm-granularity-label">Granularity</div>')
    granularity = st.selectbox("Granularity", ["day", "hour", "week"],
                               index=0, label_visibility="collapsed")
    tp = metrics.throughput_time_series(start_date=start_date, end_date=end_date,
                                        granularity=granularity)
    if not tp.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=tp["date"], y=tp["task_count"], name="Tasks",
            marker_color="rgba(16,185,129,0.55)",
            marker_line_color="rgba(16,185,129,0.8)", marker_line_width=1,
            hovertemplate="%{x|%b %d}: %{y} tasks<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=tp["date"], y=tp["success_rate"], name="Success Rate",
            line=dict(color="#F59E0B", width=2),
            mode="lines+markers", marker=dict(size=4),
            hovertemplate="%{x|%b %d}: %{y:.1%}<extra>Success</extra>",
            yaxis="y2",
        ))
        layout = _plotly_layout(theme, height=300)
        layout["yaxis2"] = dict(
            overlaying="y", side="right", range=[0, 1.05],
            gridcolor="rgba(0,0,0,0)", tickformat=".0%",
            tickfont=dict(size=10), color="#F59E0B",
        )
        layout["barmode"] = "relative"
        fig.update_layout(**layout)
        st.html('<div class="pm-card-wrap">'
                '<div class="pm-card-title">Task Throughput & Success Rate</div>'
                f'<div class="pm-card-sub">Volume and success rate grouped by {granularity}</div>')
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.html('</div>')

    # ── Leaderboard ───────────────────────────────────────────
    st.html('<div class="pm-section">Agent Leaderboard</div>')
    lb = metrics.agent_leaderboard(start_date, end_date)
    if not lb.empty:
        st.html('<div class="pm-card-wrap">'
                '<div class="pm-card-title">Overall Agent Rankings</div>'
                '<div class="pm-card-sub">Composite score weighted by success rate, quality, latency, and cost</div>')
        _pmc, _ = st.columns([0.4, 0.6])
        _pm_q = _pmc.text_input("Filter agents", placeholder="🔍  Search agent…", label_visibility="collapsed", key="pm_lb_search")
        lb_pm = lb[lb["Agent"].astype(str).str.contains(_pm_q.strip(), case=False, na=False, regex=False)] if _pm_q.strip() else lb
        st.dataframe(
            lb_pm,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Success Rate": st.column_config.ProgressColumn(
                    "Success Rate", format="%.1f%%", min_value=0, max_value=1),
                "Avg Quality": st.column_config.NumberColumn(
                    "Avg Quality", format="%.2f"),
                "Avg Latency (ms)": st.column_config.NumberColumn(
                    "Avg Latency", format="%,d ms"),
                "Total Cost ($)": st.column_config.NumberColumn(
                    "Total Cost", format="$%.4f"),
                "Score": st.column_config.ProgressColumn(
                    "Score", format="%.3f", min_value=0, max_value=1),
            },
        )
        st.html('</div>')
    else:
        st.html("""
        <div class="ov-empty">
            <div class="ov-empty-icon">⚡</div>
            <div class="ov-empty-title">No performance data yet</div>
            <div class="ov-empty-sub">Load demo data to populate metrics and rankings.</div>
        </div>
        """)


# ==================== WORKFLOW TRACES ====================

def render_traces(start_date, end_date):
    _TRACE_CSS = _SHARED_PAGE_CSS + """
    <style>
    .tr-selector-wrap {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }
    .tr-selector-label {
        color: #64748B;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .tr-chart-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 20px 24px 8px;
        margin-bottom: 24px;
    }
    .tr-chart-title {
        color: #E2E8F0;
        font-size: 0.92rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .tr-chart-sub {
        color: #475569;
        font-size: 0.78rem;
        margin-bottom: 16px;
    }
    .tr-table-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }
    .tr-status-ok   { color: #4ADE80; font-weight: 600; }
    .tr-status-err  { color: #F87171; font-weight: 600; }
    .tr-kpi-row     { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
    .tr-kpi-row .kpi-card { flex: 1; min-width: 140px; }
    </style>
    """

    st.html(_TRACE_CSS)

    # Page header
    st.html("""
    <div class="ov-header">
        <div>
            <div class="ov-header-title">Workflow Traces</div>
            <div class="ov-header-sub">End-to-end span timelines and distributed trace inspection</div>
        </div>
        <div class="ov-badge">Traces</div>
    </div>
    """)

    trace_ids = db.get_unique_trace_ids(limit=50)
    if not trace_ids:
        st.html("""<div class="ov-empty">
            <div style="font-size:2rem;margin-bottom:8px;">🔍</div>
            <div style="color:#E2E8F0;font-weight:600;margin-bottom:4px;">No trace data available</div>
            <div style="color:#475569;font-size:0.85rem;">Traces will appear here once agents start executing workflows.</div>
        </div>""")
        return

    # Trace selector card
    st.html('<div class="tr-selector-wrap"><div class="tr-selector-label">Select a trace to inspect</div></div>')
    selected_trace = st.selectbox("Trace ID", trace_ids, label_visibility="collapsed")

    if not selected_trace:
        return

    spans = db.get_spans(trace_id=selected_trace)
    if not spans:
        st.html("""<div class="ov-empty">
            <div style="font-size:2rem;margin-bottom:8px;">📭</div>
            <div style="color:#E2E8F0;font-weight:600;margin-bottom:4px;">No spans found</div>
            <div style="color:#475569;font-size:0.85rem;">This trace has no recorded spans.</div>
        </div>""")
        return

    # ── Data prep ──────────────────────────────────────────────────────
    spans_sorted  = sorted(spans, key=lambda s: s.started_at)
    agents_in_trace = set(s.agent_id for s in spans)
    agent_map     = {a.agent_id: a.name for a in db.get_all_agents()}
    min_time      = min(s.started_at for s in spans_sorted)
    root_duration = sum(s.duration_ms or 0 for s in spans if s.parent_span_id is None)
    errors        = sum(1 for s in spans if s.status == "ERROR")
    ok_count      = sum(1 for s in spans if s.status == "OK")
    success_pct   = round(ok_count / len(spans) * 100) if spans else 0

    # ── KPI row ────────────────────────────────────────────────────────
    kpi_row = "".join([
        _kpi_card("🔗", "Total Spans",  str(len(spans)),            "#6366F1"),
        _kpi_card("🤖", "Agents",        str(len(agents_in_trace)), "#8B5CF6"),
        _kpi_card("⏱️", "Root Duration", f"{root_duration:,.0f} ms","#06B6D4"),
        _kpi_card("✅", "Success Rate",  f"{success_pct}%",         "#10B981",
                  sub=f"{ok_count}/{len(spans)} spans OK"),
        _kpi_card("❌", "Errors",        str(errors),
                  "#F87171" if errors else "#475569"),
    ])
    st.html(f'<div class="tr-kpi-row">{kpi_row}</div>')

    # ── Gantt (Plotly) ─────────────────────────────────────────────────
    color_palette = [
        "#6366F1","#10B981","#F59E0B","#8B5CF6","#F87171",
        "#06B6D4","#EC4899","#84CC16","#F97316","#64748B",
    ]
    colors_map = {aid: color_palette[i % len(color_palette)]
                  for i, aid in enumerate(sorted(agents_in_trace))}

    gantt_rows = []
    for span in spans_sorted:
        start_ms = (span.started_at - min_time).total_seconds() * 1000
        dur_ms   = max(span.duration_ms or 1, 1)
        depth    = 0
        if span.parent_span_id:
            parent_ids = {s.span_id for s in spans_sorted}
            if span.parent_span_id in parent_ids:
                depth = 1
                parent = next((s for s in spans_sorted if s.span_id == span.parent_span_id), None)
                if parent and parent.parent_span_id:
                    depth = 2
        prefix = "\u00a0\u00a0\u00a0\u00a0" * depth
        agent_name = agent_map.get(span.agent_id, span.agent_id)
        label = f"{prefix}{span.operation}" if depth else f"[{agent_name}] {span.operation}"
        gantt_rows.append({
            "label":      label,
            "start":      start_ms,
            "duration":   dur_ms,
            "color":      colors_map.get(span.agent_id, "#64748B"),
            "opacity":    1.0 if span.status == "OK" else 0.45,
            "status":     span.status,
            "agent":      agent_name,
        })

    gantt_height = max(320, len(spans_sorted) * 28 + 60)
    fig_gantt = go.Figure()

    for row in gantt_rows:
        fig_gantt.add_trace(go.Bar(
            x=[row["duration"]],
            y=[row["label"]],
            base=[row["start"]],
            orientation="h",
            marker=dict(
                color=row["color"],
                opacity=row["opacity"],
                line=dict(color="#F87171" if row["status"] == "ERROR" else "rgba(0,0,0,0)", width=2),
            ),
            hovertemplate=(
                f"<b>{row['label']}</b><br>"
                f"Agent: {row['agent']}<br>"
                f"Start: {row['start']:.1f} ms<br>"
                f"Duration: {row['duration']:.1f} ms<br>"
                f"Status: {row['status']}<extra></extra>"
            ),
            showlegend=False,
        ))

    # Legend traces (one per agent)
    for aid, color in colors_map.items():
        fig_gantt.add_trace(go.Bar(
            x=[None], y=[None], orientation="h",
            name=agent_map.get(aid, aid),
            marker_color=color,
            showlegend=True,
        ))

    layout = _plotly_layout("dark", height=gantt_height)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Time (ms)"
    layout["yaxis"]["autorange"] = "reversed"
    layout["legend"].update(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
    layout["margin"] = dict(l=0, r=0, t=8, b=0)
    fig_gantt.update_layout(**layout)

    st.html('<div class="tr-chart-card">'
            '<div class="tr-chart-title">Trace Timeline</div>'
            '<div class="tr-chart-sub">Gantt chart of all spans — red outlines indicate errors</div>')
    st.plotly_chart(fig_gantt, use_container_width=True, config={"displayModeBar": False})
    st.html('</div>')

    # ── Span details table ─────────────────────────────────────────────
    span_data = []
    for s in spans_sorted:
        depth = 0
        if s.parent_span_id:
            parent_ids = {sp.span_id for sp in spans_sorted}
            if s.parent_span_id in parent_ids:
                depth = 1
                parent = next((sp for sp in spans_sorted if sp.span_id == s.parent_span_id), None)
                if parent and parent.parent_span_id:
                    depth = 2
        indent = "\u00a0\u00a0" * depth
        span_data.append({
            "Operation":    f"{indent}{s.operation}",
            "Agent":        agent_map.get(s.agent_id, s.agent_id),
            "Duration (ms)": round(s.duration_ms, 1) if s.duration_ms else 0,
            "Status":       s.status,
            "Start (ms)":   round((s.started_at - min_time).total_seconds() * 1000, 1),
            "Attributes":   str(s.attributes) if s.attributes else "—",
        })

    df_spans = pd.DataFrame(span_data)

    st.html('<style>[data-testid="stDataFrame"] [role="gridcell"]{text-align:left!important;justify-content:flex-start!important;}</style>'
            '<div class="tr-table-card">'
            '<div class="tr-chart-title">Span Details</div>'
            '<div class="tr-chart-sub">All spans sorted by start time</div>')
    _trc, _ = st.columns([0.4, 0.6])
    _tr_q = _trc.text_input("Filter spans", placeholder="🔍  Search operation or agent…", label_visibility="collapsed", key="tr_span_search")
    if _tr_q.strip():
        _q = _tr_q.strip()
        df_spans = df_spans[
            df_spans["Operation"].astype(str).str.contains(_q, case=False, na=False, regex=False) |
            df_spans["Agent"].astype(str).str.contains(_q, case=False, na=False, regex=False)
        ]
    st.dataframe(
        df_spans,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Operation":     st.column_config.TextColumn("Operation", width="large"),
            "Agent":         st.column_config.TextColumn("Agent"),
            "Duration (ms)": st.column_config.NumberColumn("Duration (ms)", format="%.1f ms"),
            "Start (ms)":    st.column_config.NumberColumn("Start (ms)", format="%.1f ms"),
            "Status":        st.column_config.TextColumn("Status"),
            "Attributes":    st.column_config.TextColumn("Attributes", width="medium"),
        },
    )
    st.html('</div>')


if __name__ == "__main__":
    main()
