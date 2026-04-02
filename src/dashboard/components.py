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


def plotly_layout(height: int = 300) -> dict:
    """Theme-aware Plotly layout.  Reads dark_mode from session state so axis
    labels stay legible on both dark and light backgrounds."""
    dark = st.session_state.get("dark_mode", True)
    tc = "#94A3B8" if dark else "#334155"   # tick / label colour
    gc = "rgba(148,163,184,0.10)" if dark else "rgba(51,65,85,0.10)"   # gridlines
    lc = "rgba(148,163,184,0.14)" if dark else "rgba(51,65,85,0.14)"   # axis lines
    return dict(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=tc, size=11),
        xaxis=dict(gridcolor=gc, linecolor=lc, tickfont=dict(size=10, color=tc)),
        yaxis=dict(gridcolor=gc, linecolor=lc, tickfont=dict(size=10, color=tc)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=tc)),
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


def df_html_table(df, formats: dict | None = None, cell_styles: dict | None = None, hide_index: bool = True) -> None:
    """Render a DataFrame as a themed HTML table.

    Avoids Streamlit's canvas-based GlideDataEditor which ignores CSS custom-property
    overrides and always follows the config.toml theme.

    formats:     {col_name: callable(val) -> html_string}
    cell_styles: {col_name: callable(val) -> inline_style_string}
    """
    import math
    data = df.data if hasattr(df, "data") else df
    cols = list(data.columns)

    idx_th = "" if hide_index else f'<th>{data.index.name or ""}</th>'
    header = idx_th + "".join(f"<th>{c}</th>" for c in cols)

    rows = ""
    for _, row in data.iterrows():
        cells = ("" if hide_index
                 else f'<td style="font-weight:600;color:var(--fb-text-muted)">{row.name}</td>')
        for c in cols:
            val = row[c]
            style = cell_styles[c](val) if cell_styles and c in cell_styles else ""
            if formats and c in formats:
                display = formats[c](val)
            elif isinstance(val, float) and math.isnan(val):
                display = "—"
            else:
                display = "" if val is None else str(val)
            cells += f'<td style="{style}">{display}</td>'
        rows += f"<tr>{cells}</tr>"

    st.html(
        f'<div class="fb-table-wrap">'
        f'<table class="fb-table"><thead><tr>{header}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
    )


_AVATAR_ACCENTS = ["#6366F1", "#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#14B8A6"]


def agent_card_html(agent, idx: int) -> str:
    accent = _AVATAR_ACCENTS[idx % len(_AVATAR_ACCENTS)]
    sv = agent.status.value.upper()
    sc, sb = ("#22C55E", "rgba(34,197,94,0.12)") if sv == "ACTIVE" else ("#EF4444", "rgba(239,68,68,0.12)") if sv == "INACTIVE" else ("#64748B", "rgba(100,116,139,0.12)")
    return f'''<div class="ar-agent-card"><div class="ar-card-top"><div class="ar-avatar" style="background:{accent}22;color:{accent};">{agent.name[0].upper()}</div><div class="ar-card-identity"><div class="ar-agent-name">{agent.name}</div><div class="ar-agent-group">{agent.group}</div></div><span class="ar-status-badge" style="color:{sc};background:{sb};">● {sv.capitalize()}</span></div><div class="ar-card-body"><div class="ar-model">🧠 {agent.model_name}</div><div class="ar-card-stats"><div class="ar-stat"><span class="ar-stat-num">{len(agent.skills)}</span><span class="ar-stat-lbl">Skills</span></div><div class="ar-stat-divider"></div><div class="ar-stat"><span class="ar-stat-num">{len(agent.permissions)}</span><span class="ar-stat-lbl">Perms</span></div><div class="ar-stat-divider"></div><div class="ar-stat"><span class="ar-stat-num">${agent.cost_per_1k_input:.3f}</span><span class="ar-stat-lbl">In/1K</span></div><div class="ar-stat-divider"></div><div class="ar-stat"><span class="ar-stat-num">${agent.cost_per_1k_output:.3f}</span><span class="ar-stat-lbl">Out/1K</span></div></div></div></div>'''
