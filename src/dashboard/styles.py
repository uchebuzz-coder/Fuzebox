"""Consolidated CSS for all dashboard pages."""

_FONT = '"Inter","SF Pro Display",system-ui,sans-serif'


def _t(d, dark, light):
    return dark if d else light


def get_all_css(theme: str) -> str:
    d = theme == "dark"
    # Core tokens
    card_bg = _t(d, "rgba(255,255,255,0.04)", "#FFFFFF")
    card_bdr = _t(d, "rgba(255,255,255,0.07)", "rgba(15,23,42,0.08)")
    card_shd = _t(d, "0 1px 3px rgba(0,0,0,0.35),0 4px 12px rgba(0,0,0,0.2)", "0 1px 3px rgba(0,0,0,0.06),0 4px 12px rgba(0,0,0,0.04)")
    card_hov = _t(d, "rgba(255,255,255,0.07)", "#F1F5F9")
    txt1 = _t(d, "#F1F5F9", "#0F172A")
    txt2 = _t(d, "#475569", "#94A3B8")
    txt3 = _t(d, "#334155", "#CBD5E1")
    div = _t(d, "rgba(255,255,255,0.06)", "rgba(15,23,42,0.07)")
    badge_bg = _t(d, "rgba(99,102,241,0.15)", "rgba(99,102,241,0.08)")
    badge_txt = _t(d, "#A5B4FC", "#4338CA")
    empty_bg = _t(d, "rgba(99,102,241,0.06)", "rgba(99,102,241,0.04)")
    empty_bdr = _t(d, "rgba(99,102,241,0.15)", "rgba(99,102,241,0.12)")
    chart_bg = _t(d, "rgba(255,255,255,0.02)", "#FFFFFF")

    return f"""<style>
/* ── Shared ── */
.page-header{{margin-bottom:28px}}.page-title{{color:{txt1}!important;font:700 1.6rem/1.2 {_FONT};letter-spacing:-.02em;margin:0 0 4px}}
.page-sub{{color:{txt2}!important;font:400 .875rem/1.4 {_FONT};margin:0 0 14px}}.badge{{display:inline-flex;align-items:center;gap:5px;background:{badge_bg};color:{badge_txt}!important;border-radius:20px;padding:3px 10px;font:600 .72rem {_FONT};letter-spacing:.02em}}
.section-label{{color:{txt2}!important;font:700 .72rem {_FONT};letter-spacing:.1em;text-transform:uppercase;margin:28px 0 12px;display:flex;align-items:center;gap:8px}}.section-label::after{{content:"";flex:1;height:1px;background:{div}}}
.card{{background:{card_bg};border:1px solid {card_bdr};border-radius:14px;padding:18px 20px;box-shadow:{card_shd};margin-bottom:12px;font-family:{_FONT}}}.card:hover{{background:{card_hov}}}
.card-title{{color:{txt1}!important;font:600 .875rem {_FONT};letter-spacing:-.01em;margin-bottom:2px}}.card-sub{{color:{txt2}!important;font:400 .72rem {_FONT};margin-bottom:14px}}
.chart-card{{background:{chart_bg};border:1px solid {card_bdr};border-radius:14px;padding:20px;box-shadow:{card_shd}}}
.empty-state{{background:{empty_bg};border:1px dashed {empty_bdr};border-radius:14px;padding:40px 24px;text-align:center;font-family:{_FONT}}}.empty-icon{{font-size:2.2rem;margin-bottom:12px}}.empty-title{{color:#6366F1!important;font:600 .95rem {_FONT};margin-bottom:6px}}.empty-sub{{color:{txt2}!important;font-size:.82rem}}
/* ── KPI ── */
.kpi-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:12px}}.kpi-grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}}
.kpi-card{{background:{card_bg};border:1px solid {card_bdr};border-radius:14px;padding:16px 18px;box-shadow:{card_shd};transition:background .15s;font-family:{_FONT}}}.kpi-card:hover{{background:{card_hov}}}
.kpi-icon-wrap{{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:16px;margin-bottom:12px}}
.kpi-label{{color:{txt2}!important;font:600 .68rem {_FONT};letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}
.kpi-value{{color:{txt1}!important;font:700 1.45rem {_FONT};letter-spacing:-.02em;line-height:1.1}}.kpi-value-sm{{color:{txt1}!important;font:700 1.2rem {_FONT};letter-spacing:-.02em;line-height:1.1}}
.kpi-sub{{color:{txt3}!important;font-size:.7rem;margin-top:4px}}
/* ── Agent Registry ── */
.ar-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:6px}}
.ar-agent-card{{background:{card_bg};border:1px solid {card_bdr};border-radius:14px;padding:16px 18px;box-shadow:{card_shd};transition:background .15s;font-family:{_FONT}}}.ar-agent-card:hover{{background:{card_hov}}}
.ar-card-top{{display:flex;align-items:center;gap:12px;margin-bottom:14px}}.ar-avatar{{width:38px;height:38px;border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1rem;font-weight:700}}.ar-card-identity{{flex:1;min-width:0}}
.ar-agent-name{{color:{txt1}!important;font:600 .875rem {_FONT};white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.ar-agent-group{{color:{txt2}!important;font-size:.7rem;margin-top:1px}}
.ar-status-badge{{font:600 .65rem {_FONT};padding:3px 8px;border-radius:20px;white-space:nowrap;letter-spacing:.02em;flex-shrink:0}}
.ar-card-body{{border-top:1px solid {div};padding-top:12px}}.ar-model{{color:#64748B!important;font-size:.75rem;margin-bottom:10px}}
.ar-card-stats{{display:flex;align-items:center}}.ar-stat{{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px}}.ar-stat-num{{color:#CBD5E1!important;font:600 .8rem {_FONT}}}.ar-stat-lbl{{color:{txt3}!important;font-size:.6rem;text-transform:uppercase;letter-spacing:.06em}}.ar-stat-divider{{width:1px;height:24px;background:{div};flex-shrink:0}}
.ar-matrix-wrap{{background:{card_bg};border:1px solid {card_bdr};border-radius:14px;padding:18px 20px;box-shadow:{card_shd}}}
.ar-violation-card{{background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.18);border-radius:12px;padding:14px 18px;display:flex;align-items:center;gap:12px;margin-bottom:8px;font-family:{_FONT}}}
.ar-all-clear{{background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.18);border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:12px;font-family:{_FONT}}}
/* ── Scorecards ── */
.sc-group-banner{{display:flex;align-items:center;gap:14px;padding:14px 18px;border-radius:12px;margin-bottom:16px;font-family:{_FONT}}}
/* ── Economics ── */
.ec-roi-banner{{display:flex;align-items:center;gap:20px;background:rgba(99,102,241,.07);border:1px solid rgba(99,102,241,.18);border-radius:14px;padding:16px 20px;margin-bottom:20px;font-family:{_FONT};flex-wrap:wrap}}
.ec-roi-item{{display:flex;flex-direction:column;gap:2px}}.ec-roi-label{{color:{txt2}!important;font:600 .65rem {_FONT};letter-spacing:.1em;text-transform:uppercase}}.ec-roi-value{{color:{txt1}!important;font:700 1.1rem {_FONT};letter-spacing:-.02em}}.ec-roi-divider{{width:1px;height:36px;background:rgba(255,255,255,.08);flex-shrink:0}}
/* ── Traces ── */
.tr-selector-wrap{{background:rgba(255,255,255,.03);border:1px solid {card_bdr};border-radius:14px;padding:20px 24px;margin-bottom:24px}}
.tr-chart-card{{background:rgba(255,255,255,.03);border:1px solid {card_bdr};border-radius:14px;padding:20px 24px 8px;margin-bottom:24px}}
.tr-table-card{{background:rgba(255,255,255,.03);border:1px solid {card_bdr};border-radius:14px;padding:20px 24px;margin-bottom:24px}}
.tr-kpi-row{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}.tr-kpi-row .kpi-card{{flex:1;min-width:140px}}
/* ── V2 ── */
.v2-metric-row{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px}}.v2-metric{{flex:1;min-width:120px;padding:12px 14px;background:{card_bg};border:1px solid {card_bdr};border-radius:10px}}
.v2-metric-label{{color:{txt2}!important;font:600 .62rem {_FONT};letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}.v2-metric-val{{color:{txt1}!important;font:700 1.3rem {_FONT};letter-spacing:-.02em}}
.v2-gauge-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}}.v2-gauge{{background:{card_bg};border:1px solid {card_bdr};border-radius:12px;padding:16px;text-align:center}}
.v2-gauge-val{{color:{txt1}!important;font:700 1.6rem {_FONT};letter-spacing:-.02em}}.v2-gauge-label{{color:{txt2}!important;font:600 .65rem {_FONT};letter-spacing:.06em;text-transform:uppercase;margin-top:6px}}
.v2-waterfall-band{{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;margin-bottom:4px;font:500 .82rem {_FONT}}}
.v2-wf-success{{background:rgba(34,197,94,.1);color:#22C55E}}.v2-wf-warning{{background:rgba(245,158,11,.1);color:#F59E0B}}.v2-wf-error{{background:rgba(239,68,68,.1);color:#EF4444}}
.v2-wf-bar{{height:6px;border-radius:3px;flex-shrink:0}}.v2-wf-count{{font-weight:700;min-width:32px;text-align:right}}.v2-wf-pct{{font-size:.72rem;opacity:.7;min-width:40px}}
.v2-pattern-card{{background:{card_bg};border:1px solid {card_bdr};border-radius:10px;padding:14px 16px;margin-bottom:8px}}
.v2-pattern-sev{{display:inline-block;border-radius:12px;padding:2px 8px;font:600 .65rem {_FONT};text-transform:uppercase}}
.v2-sev-critical{{background:rgba(239,68,68,.15);color:#EF4444}}.v2-sev-warning{{background:rgba(245,158,11,.15);color:#F59E0B}}.v2-sev-info{{background:rgba(99,102,241,.15);color:#6366F1}}
.v2-pattern-desc{{color:{txt1}!important;font:500 .82rem {_FONT};margin:6px 0 4px}}.v2-pattern-fix{{color:{txt2}!important;font:400 .75rem {_FONT};font-style:italic}}
.v2-pipeline{{display:flex;align-items:center;gap:0;margin:20px 0}}.v2-pipe-step{{flex:1;text-align:center;padding:16px 8px;background:{card_bg};border:1px solid {card_bdr};border-radius:12px;margin:0 4px}}
.v2-pipe-step.active{{border-color:#6366F1;box-shadow:0 0 12px rgba(99,102,241,.3)}}.v2-pipe-step.done{{border-color:#22C55E;background:rgba(34,197,94,.06)}}
.v2-pipe-icon{{font-size:1.4rem;margin-bottom:6px}}.v2-pipe-label{{color:{txt1}!important;font:600 .75rem {_FONT}}}.v2-pipe-status{{color:{txt2}!important;font:400 .65rem {_FONT};margin-top:4px}}.v2-pipe-arrow{{color:{txt2};font-size:1.2rem;flex-shrink:0}}
.v2-compare-grid{{display:grid;grid-template-columns:1fr 60px 1fr;gap:0;margin-bottom:16px}}.v2-compare-col{{background:{card_bg};border:1px solid {card_bdr};border-radius:12px;padding:20px}}
.v2-compare-center{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:8px 0}}
.v2-compare-header{{color:{txt2}!important;font:700 .72rem {_FONT};letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px;text-align:center}}
.v2-compare-row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {div}}}.v2-compare-label{{color:{txt2}!important;font:500 .78rem {_FONT}}}.v2-compare-val{{color:{txt1}!important;font:700 .85rem {_FONT}}}
.v2-delta{{font:700 .72rem {_FONT};border-radius:10px;padding:2px 6px}}.v2-delta-up{{background:rgba(34,197,94,.15);color:#22C55E}}.v2-delta-down{{background:rgba(239,68,68,.15);color:#EF4444}}.v2-delta-flat{{background:rgba(100,116,139,.15);color:{txt2}}}
.v2-trend{{display:inline-flex;align-items:center;gap:4px;border-radius:12px;padding:3px 10px;font:600 .72rem {_FONT}}}
.v2-trend-improving{{background:rgba(34,197,94,.12);color:#22C55E}}.v2-trend-stable{{background:rgba(100,116,139,.12);color:{txt2}}}.v2-trend-degrading{{background:rgba(239,68,68,.12);color:#EF4444}}
.v2-control-card{{background:{card_bg};border:1px solid {card_bdr};border-radius:12px;padding:16px 18px;margin-bottom:10px}}
.v2-ctrl-label{{color:{txt1}!important;font:600 .82rem {_FONT};margin-bottom:2px}}.v2-ctrl-desc{{color:{txt2}!important;font:400 .72rem {_FONT};margin-bottom:10px}}
.v2-rec-card{{background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.15);border-radius:10px;padding:12px 14px;margin-bottom:8px}}
.v2-rec-param{{color:#6366F1!important;font:700 .78rem {_FONT}}}.v2-rec-reason{{color:{txt2}!important;font:400 .75rem {_FONT};margin-top:4px}}.v2-rec-impact{{color:#22C55E!important;font:600 .72rem {_FONT};margin-top:2px}}
.diff-row{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {div}}}.diff-param{{font:500 .82rem {_FONT};color:#A5B4FC}}.diff-old{{color:#EF4444;text-decoration:line-through}}.diff-arrow{{margin:0 6px;opacity:.4}}.diff-new{{color:#22C55E;font-weight:600}}
</style>"""


def sidebar_css(theme: str) -> str:
    d = theme == "dark"
    sb_bg = _t(d, "linear-gradient(180deg,#0B1120 0%,#0F172A 60%,#111827 100%)", "linear-gradient(180deg,#F8FAFC 0%,#F1F5F9 60%,#EEF2FF 100%)")
    sb_bdr = _t(d, "rgba(255,255,255,0.06)", "rgba(15,23,42,0.07)")
    sb_lbl = _t(d, "#334155", "#94A3B8")
    logo_t = _t(d, "#F1F5F9", "#1E293B")
    logo_s = _t(d, "#475569", "#94A3B8")
    nav_t = _t(d, "#64748B", "#475569")
    nav_hbg = _t(d, "rgba(99,102,241,0.08)", "rgba(99,102,241,0.06)")
    nav_ht = _t(d, "#C7D2FE", "#4338CA")
    nav_hb = _t(d, "rgba(99,102,241,0.12)", "rgba(99,102,241,0.15)")
    nav_abg = _t(d, "rgba(99,102,241,0.15)", "rgba(99,102,241,0.10)")
    nav_at = _t(d, "#A5B4FC", "#4338CA")
    nav_ab = _t(d, "rgba(99,102,241,0.25)", "rgba(99,102,241,0.22)")
    ctrl_bg = _t(d, "rgba(255,255,255,0.04)", "rgba(0,0,0,0.03)")
    ctrl_bdr = _t(d, "rgba(255,255,255,0.09)", "rgba(0,0,0,0.10)")
    ctrl_t = _t(d, "#CBD5E1", "#475569")
    ctrl_ph = _t(d, "#475569", "#94A3B8")
    alert_bg = _t(d, "rgba(34,197,94,0.08)", "rgba(34,197,94,0.06)")
    alert_bdr = _t(d, "rgba(34,197,94,0.20)", "rgba(34,197,94,0.25)")
    alert_t = _t(d, "#4ADE80", "#16A34A")
    hdr_bg = _t(d, "#0B1120", "#F8FAFC")
    col_ic = _t(d, "rgba(250,250,250,0.6)", "rgba(15,23,42,0.40)")
    col_ih = _t(d, "rgba(250,250,250,0.9)", "rgba(15,23,42,0.70)")

    return f"""<style>
[data-testid="stSidebar"]{{background:{sb_bg};border-right:1px solid {sb_bdr};padding-top:0!important}}
[data-testid="stSidebar"]>div:first-child{{padding-top:0!important}}
[data-testid="stSidebar"],[data-testid="stSidebar"] *{{font-family:{_FONT}}}
[data-testid="stSidebar"] [data-testid="stIconMaterial"]{{font-family:"Material Symbols Rounded","Material Icons"!important}}
.sb-section-label{{color:{sb_lbl}!important;font:700 .62rem {_FONT};letter-spacing:.14em;text-transform:uppercase;margin:0 0 6px 2px;display:block}}
.sb-logo-wrap{{display:flex;align-items:center;gap:11px;padding:22px 20px 18px;border-bottom:1px solid {sb_bdr};margin-bottom:20px}}
.sb-logo-icon{{width:38px;height:38px;background:linear-gradient(135deg,#6366F1,#8B5CF6);border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0;box-shadow:0 4px 14px rgba(99,102,241,.45)}}
.sb-logo-title{{color:{logo_t}!important;font:700 .95rem {_FONT};letter-spacing:-.015em;line-height:1.2}}.sb-logo-sub{{color:{logo_s}!important;font-size:.68rem;line-height:1.3}}
[data-testid="stSidebar"] hr{{border:none!important;border-top:1px solid {sb_bdr}!important;margin:14px 0!important}}
[data-testid="stSidebar"] [data-testid="stRadio"]>div{{gap:2px!important;flex-direction:column!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label{{background:transparent!important;border-radius:9px!important;padding:9px 12px 9px 10px!important;cursor:pointer!important;width:100%!important;display:flex!important;align-items:center!important;transition:background .15s,color .15s!important;font:400 .855rem {_FONT}!important;color:{nav_t}!important;text-transform:none!important;letter-spacing:normal!important;border:1px solid transparent!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{{background:{nav_hbg}!important;color:{nav_ht}!important;border-color:{nav_hb}!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){{background:{nav_abg}!important;color:{nav_at}!important;border-color:{nav_ab}!important;font-weight:600!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label>div:first-child,[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"]{{display:none!important}}
[data-testid="stSidebar"] [data-testid="stRadio"]>label{{display:none!important}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:linear-gradient(135deg,#6366F1,#7C3AED)!important;border:none!important;color:#F8FAFC!important;border-radius:9px!important;font:600 .82rem {_FONT}!important;padding:9px 14px!important;width:100%!important;transition:opacity .15s,transform .15s!important;box-shadow:0 4px 14px rgba(99,102,241,.35)!important}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{{opacity:.88!important;transform:translateY(-1px)!important}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:active{{transform:translateY(0)!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"]>div>div{{background-color:{ctrl_bg}!important;border:1px solid {ctrl_bdr}!important;border-radius:9px!important;color:{ctrl_t}!important;font-size:.84rem!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"]>div>div:hover{{border-color:rgba(99,102,241,.35)!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,[data-testid="stSidebar"] [data-testid="stMultiSelect"] label{{color:{sb_lbl}!important;font:600 .68rem {_FONT};letter-spacing:.1em;text-transform:uppercase}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child{{background-color:{ctrl_bg}!important;border:1px solid {ctrl_bdr}!important;border-radius:9px!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child:hover{{border-color:rgba(99,102,241,.35)!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child *{{background-color:transparent!important;color:{ctrl_t}!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] input::placeholder{{color:{ctrl_ph}!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"]{{background-color:rgba(99,102,241,.18)!important;border:1px solid rgba(99,102,241,.30)!important;border-radius:5px!important;color:#A5B4FC!important}}
[data-testid="stSidebar"] [data-testid="stAlert"]{{background:{alert_bg}!important;border:1px solid {alert_bdr}!important;border-radius:9px!important;color:{alert_t}!important;font-size:.78rem!important}}
[data-testid="stSidebarHeader"]{{background:{hdr_bg}!important;border-bottom:none!important}}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]{{color:{col_ic}!important}}
[data-testid="stSidebarCollapseButton"] button:hover [data-testid="stIconMaterial"]{{color:{col_ih}!important}}
[data-testid="stSidebar"] .block-container{{padding:0!important}}
[data-testid="stSidebar"] section[data-testid="stSidebarContent"]>div{{padding-left:14px!important;padding-right:14px!important}}
</style>"""
