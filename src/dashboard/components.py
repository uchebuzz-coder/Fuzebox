"""Shared UI components and helpers for the dashboard."""

import streamlit as st
import plotly.graph_objects as go


def kpi_card(icon: str, label: str, value: str, accent: str, sub: str = "", small: bool = False) -> str:
    vc = "kpi-value-sm" if small else "kpi-value"
    sh = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f'<div class="kpi-card"><div class="kpi-icon-wrap" style="background:{accent}22;color:{accent};">{icon}</div><div class="kpi-label">{label}</div><div class="{vc}">{value}</div>{sh}</div>'


def page_header(title: str, subtitle: str, badges: list[str] | None = None):
    bhtml = " ".join(f'<span class="badge">{b}</span>' for b in (badges or []))
    st.html(f'<div class="page-header"><div class="page-title">{title}</div><div class="page-sub">{subtitle}</div>{bhtml}</div>')


def section(label: str):
    st.html(f'<div class="section-label">{label}</div>')


def empty_state(icon: str, title: str, subtitle: str):
    st.html(f'<div class="empty-state"><div class="empty-icon">{icon}</div><div class="empty-title">{title}</div><div class="empty-sub">{subtitle}</div></div>')


def card_wrap(title: str = "", subtitle: str = ""):
    t = f'<div class="card-title">{title}</div>' if title else ""
    s = f'<div class="card-sub">{subtitle}</div>' if subtitle else ""
    return f'<div class="card">{t}{s}'


def search_filter(df, column: str, key: str, placeholder: str = "Search..."):
    col, _ = st.columns([0.4, 0.6])
    q = col.text_input("Filter", placeholder=f"🔍  {placeholder}", label_visibility="collapsed", key=key)
    if q.strip():
        return df[df[column].astype(str).str.contains(q.strip(), case=False, na=False, regex=False)]
    return df


def diff_html(changes: dict) -> str:
    rows = ""
    for param, vals in changes.items():
        rows += f'<div class="diff-row"><span class="diff-param">{param}</span><span><span class="diff-old">{vals["old"]}</span><span class="diff-arrow">→</span><span class="diff-new">{vals["new"]}</span></span></div>'
    return f'<div class="card">{rows}</div>'


def plotly_layout(theme: str, height: int = 300) -> dict:
    d = theme == "dark"
    gc = "rgba(255,255,255,0.04)" if d else "rgba(0,0,0,0.05)"
    lc = "rgba(255,255,255,0.08)" if d else "rgba(0,0,0,0.08)"
    return dict(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#64748B" if d else "#94A3B8", size=11),
        xaxis=dict(gridcolor=gc, linecolor=lc, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=gc, linecolor=lc, tickfont=dict(size=10)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        hovermode="x unified",
    )


def delta_html(old_val, new_val, fmt=".1%", invert=False) -> str:
    if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
        diff = new_val - old_val
        if abs(diff) < 0.001:
            return '<span class="v2-delta v2-delta-flat">~0</span>'
        improved = diff < 0 if invert else diff > 0
        cls = "v2-delta-up" if improved else "v2-delta-down"
        fmts = {".1%": f"{diff:+.1%}", ".0f": f"{diff:+.0f}", ".4f": f"{diff:+.4f}", ".1f": f"{diff:+.1f}"}
        label = fmts.get(fmt, f"{diff:+.3f}")
        return f'<span class="v2-delta {cls}">{label}</span>'
    return '<span class="v2-delta v2-delta-flat">—</span>'


_AVATAR_ACCENTS = ["#6366F1", "#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#14B8A6"]


def agent_card_html(agent, idx: int) -> str:
    accent = _AVATAR_ACCENTS[idx % len(_AVATAR_ACCENTS)]
    sv = agent.status.value.upper()
    sc, sb = ("#22C55E", "rgba(34,197,94,0.12)") if sv == "ACTIVE" else ("#EF4444", "rgba(239,68,68,0.12)") if sv == "INACTIVE" else ("#64748B", "rgba(100,116,139,0.12)")
    return f'''<div class="ar-agent-card"><div class="ar-card-top"><div class="ar-avatar" style="background:{accent}22;color:{accent};">{agent.name[0].upper()}</div><div class="ar-card-identity"><div class="ar-agent-name">{agent.name}</div><div class="ar-agent-group">{agent.group}</div></div><span class="ar-status-badge" style="color:{sc};background:{sb};">● {sv.capitalize()}</span></div><div class="ar-card-body"><div class="ar-model">🧠 {agent.model_name}</div><div class="ar-card-stats"><div class="ar-stat"><span class="ar-stat-num">{len(agent.skills)}</span><span class="ar-stat-lbl">Skills</span></div><div class="ar-stat-divider"></div><div class="ar-stat"><span class="ar-stat-num">{len(agent.permissions)}</span><span class="ar-stat-lbl">Perms</span></div><div class="ar-stat-divider"></div><div class="ar-stat"><span class="ar-stat-num">${agent.cost_per_1k_input:.3f}</span><span class="ar-stat-lbl">In/1K</span></div><div class="ar-stat-divider"></div><div class="ar-stat"><span class="ar-stat-num">${agent.cost_per_1k_output:.3f}</span><span class="ar-stat-lbl">Out/1K</span></div></div></div></div>'''
