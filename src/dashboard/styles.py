"""Consolidated CSS for all dashboard pages.

Colours are controlled by four base CSS custom properties (--fb-text,
--fb-bg, --fb-bg2, --fb-primary) whose values are set once by the
Python-side dark/light toggle.  Every other token is *derived* via
``color-mix()`` so the entire palette auto-adapts.
"""

_FONT = '"Inter","SF Pro Display",system-ui,sans-serif'

# ── Base palette per mode ──────────────────────────────────────────
_DARK  = dict(text="#F1F5F9", bg="#0F172A", bg2="#1E293B", primary="#6366F1", border="rgba(241,245,249,0.10)")
_LIGHT = dict(text="#0F172A", bg="#FFFFFF",  bg2="#F1F5F9", primary="#6366F1", border="rgba(15,23,42,0.10)")


def get_all_css(dark: bool = True) -> str:
    """Return theme-aware CSS.  *dark* selects the base palette;
    every component colour is derived from it via CSS custom properties."""
    p = _DARK if dark else _LIGHT
    return f"""<style>
/* ── Theme Tokens ─────────────────────────────────────────────────── */
:root,.stApp{{
  /* Override Streamlit's own theme vars so native widgets (dataframes,
     sliders, toggles, etc.) follow our toggle instead of config.toml */
  --text-color:{p['text']};
  --background-color:{p['bg']};
  --secondary-background-color:{p['bg2']};
  --primary-color:{p['primary']};
  /* Our derived tokens */
  --fb-text:{p['text']};
  --fb-bg:{p['bg']};
  --fb-bg2:{p['bg2']};
  --fb-primary:{p['primary']};
  --fb-text-muted:color-mix(in srgb,var(--fb-text) 62%,transparent);
  --fb-text-faint:color-mix(in srgb,var(--fb-text) 42%,transparent);
  --fb-border:color-mix(in srgb,var(--fb-text) 10%,transparent);
  --fb-divider:color-mix(in srgb,var(--fb-text) 8%,transparent);
  --fb-card-bg:color-mix(in srgb,var(--fb-text) 5%,var(--fb-bg));
  --fb-card-hover:color-mix(in srgb,var(--fb-text) 8%,var(--fb-bg));
  --fb-subtle-bg:color-mix(in srgb,var(--fb-text) 3%,var(--fb-bg));
  --fb-primary-bg:color-mix(in srgb,var(--fb-primary) 12%,transparent);
  --fb-primary-border:color-mix(in srgb,var(--fb-primary) 22%,transparent);
  --fb-card-shadow:0 1px 3px color-mix(in srgb,var(--fb-text) 8%,transparent),
                   0 4px 12px color-mix(in srgb,var(--fb-text) 5%,transparent);
}}
/* ── Force page background & text to follow our tokens ── */
[data-testid="stAppViewContainer"],
[data-testid="stApp"]>.main,
.stApp{{background-color:var(--fb-bg)!important;color:var(--fb-text)!important}}
[data-testid="stHeader"]{{background-color:var(--fb-bg)!important}}
[data-testid="stHeader"] button,[data-testid="stToolbarActionButton"]{{color:var(--fb-text-muted)!important}}
[data-testid="stHeader"] button:hover,[data-testid="stToolbarActionButton"]:hover{{color:var(--fb-text)!important;background:var(--fb-card-bg)!important}}
/* ── Sidebar collapse / expand toggle ── */
/* Both buttons use DynamicIcon with color:fadedText60 (white@60% in dark theme).
   Emotion class wins over our color rule, so use filter:brightness to force visibility. */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapseButton"] span,
[data-testid="stExpandSidebarButton"] button,
[data-testid="stExpandSidebarButton"] span{{
  color:{p['text']}!important;
  opacity:1!important;
  filter:{'none' if dark else 'brightness(0)'}!important}}
[data-testid="stSidebar"]{{background:var(--fb-bg2)!important}}
[data-testid="stSidebarContent"]{{background:var(--fb-bg2)!important}}
/* ── Native Streamlit widget overrides ── */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] [data-testid="glideDataEditor"],
[data-testid="stDataFrame"] table{{background-color:var(--fb-bg)!important;color:var(--fb-text)!important}}
[data-testid="stDataFrame"] th{{background-color:var(--fb-card-bg)!important;color:var(--fb-text-muted)!important;border-bottom:1px solid var(--fb-border)!important}}
[data-testid="stDataFrame"] td{{color:var(--fb-text)!important;border-bottom:1px solid var(--fb-border)!important}}
[data-testid="stDataFrame"] [data-testid="glideDataEditor"]>div{{background-color:var(--fb-bg)!important}}
[data-testid="stDataFrame"] [data-testid="glideDataEditor"] .dvn-scroller{{background-color:var(--fb-bg)!important}}
/* ── Widget labels (Streamlit renders these separately from the control) ── */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"],
.stTextInput label,[data-testid="stTextInput"] label,
.stSelectbox label,[data-testid="stSelectbox"] label,
.stMultiSelect label,[data-testid="stMultiSelect"] label,
.stNumberInput label,[data-testid="stNumberInput"] label,
.stSlider label,[data-testid="stSlider"] label,
.stCheckbox label,[data-testid="stCheckbox"] label,
.stRadio label,[data-testid="stRadio"] label{{color:{p['text']}!important}}
/* ── Widget controls ── */
.stTextInput>div>div,
[data-testid="stTextInputRootElement"],
[data-testid="stTextInputRootElement"] [data-baseweb="input"],
[data-testid="stTextInputRootElement"] [data-baseweb="base-input"]{{background-color:{p['bg2']}!important;border-color:{p['border']}!important;color:{p['text']}!important}}
.stTextInput>div>div:focus-within,
[data-testid="stTextInputRootElement"]:focus-within{{border-color:#6366F1!important}}
.stTextInput input,[data-testid="stTextInputRootElement"] input{{background-color:{p['bg2']}!important;color:{p['text']}!important}}
.stTextInput input::placeholder,[data-testid="stTextInputRootElement"] input::placeholder{{color:{p['text']}!important;opacity:.4!important}}
.stSelectbox>div>div,.stSelectbox [data-baseweb="select"]>div,
[data-testid="stSelectbox"] [data-baseweb="select"]>div{{background-color:{p['bg2']}!important;border-color:{p['border']}!important;color:{p['text']}!important}}
.stSelectbox>div>div *,.stSelectbox [data-baseweb="select"]>div *,
[data-testid="stSelectbox"] [data-baseweb="select"]>div *{{color:{p['text']}!important}}
.stMultiSelect>div>div,.stMultiSelect [data-baseweb="select"]>div:first-child,
[data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child{{background-color:{p['bg2']}!important;border-color:{p['border']}!important;color:{p['text']}!important}}
.stSlider>div>div>div{{color:{p['text']}!important}}
.stNumberInput>div>div,
[data-testid="stNumberInputContainer"],
[data-testid="stNumberInputContainer"]>div,
[data-testid="stNumberInputContainer"] [data-baseweb="input"],
[data-testid="stNumberInputContainer"] [data-baseweb="base-input"]{{background-color:{p['bg2']}!important;border-color:{p['border']}!important;color:{p['text']}!important}}
.stNumberInput>div>div>input,
[data-testid="stNumberInputContainer"] input{{background-color:{p['bg2']}!important;color:{p['text']}!important}}
.stNumberInput button,
[data-testid="stNumberInputContainer"] button{{background-color:transparent!important;color:{p['text']}!important;border-color:{p['border']}!important}}
/* ── Streamlit toolbar / hamburger (⋮) menu ── */
/* Use literal hex values here — Streamlit JS overrides CSS vars via
   element.style.setProperty() so var() references lose to inline styles. */
[data-testid="stMainMenuPopover"],
[data-testid="stMainMenuPopover"]>div,
[data-testid="stMainMenu"] [data-baseweb="popover"],
[data-testid="stMainMenu"] [data-baseweb="popover"]>div{{
  background-color:{p['bg2']}!important;
  border:1px solid {p['border']}!important;
  border-radius:10px!important;
  box-shadow:0 8px 24px rgba(0,0,0,0.18)!important;
  color:{p['text']}!important}}
[data-testid="stMainMenuPopover"] *{{color:{p['text']}!important}}
[data-testid="stMainMenuPopover"] li,
[role="menuitem"]{{background-color:transparent!important;color:{p['text']}!important;border-radius:7px!important}}
[data-testid="stMainMenuPopover"] li:hover,
[role="menuitem"]:hover{{background-color:rgba(99,102,241,0.12)!important;color:#6366F1!important}}
[data-testid="stMainMenuPopover"] li *,
[role="menuitem"] *{{color:inherit!important;background-color:transparent!important}}
[data-testid="stMainMenuPopover"] hr,
[role="separator"]{{border-color:{p['border']}!important;opacity:1!important}}
/* ── Dropdown popup (BaseUI + Streamlit 1.55 — literal hex, broadest selector net) ── */
[data-baseweb="popover"],
[data-baseweb="popover"]>div,
[role="listbox"]{{background-color:{p['bg2']}!important;border:1px solid {p['border']}!important;border-radius:10px!important;box-shadow:0 8px 24px rgba(0,0,0,0.18)!important;overflow:hidden!important}}
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [data-baseweb="block"]{{background-color:{p['bg2']}!important}}
[data-baseweb="popover"] ul,
[data-baseweb="popover"] [role="listbox"]{{background-color:{p['bg2']}!important;padding:0!important;margin:0!important}}
[data-baseweb="popover"] li,
[data-baseweb="option"],
[role="option"]{{background-color:transparent!important;color:{p['text']}!important;border-radius:7px!important;padding:8px 12px!important;cursor:pointer!important}}
[data-baseweb="popover"] li:hover,
[data-baseweb="option"]:hover,
[role="option"]:hover{{background-color:rgba(99,102,241,0.12)!important;color:#6366F1!important}}
[data-baseweb="popover"] li[aria-selected="true"],
[data-baseweb="option"][aria-selected="true"],
[role="option"][aria-selected="true"]{{background-color:rgba(99,102,241,0.15)!important;color:#6366F1!important;font-weight:600!important}}
[data-baseweb="popover"] *{{color:{p['text']}!important}}
[data-baseweb="popover"] li *,[data-baseweb="option"] *,[role="option"] *{{color:inherit!important;background-color:transparent!important}}
[data-baseweb="select"]>div{{background-color:{p['bg2']}!important;border-color:{p['border']}!important;color:{p['text']}!important}}
[data-baseweb="select"]>div *{{color:{p['text']}!important}}
[data-baseweb="select"] input{{color:{p['text']}!important;background-color:transparent!important}}
/* ── Spinner ── */
/* Streamlit 1.55: spinning ring is <i data-testid="stSpinnerIcon">
   It uses borderColor=fadedText10 (track) + borderTopColor=bodyText (arc).
   In dark theme bodyText=white → invisible on light bg. Override both. */
[data-testid="stSpinnerIcon"]{{
  border-color:rgba(99,102,241,0.2)!important;
  border-top-color:#6366F1!important;
  opacity:1!important}}
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] span{{color:{p['text']}!important;opacity:1!important}}
/* ── Main-content buttons ── */
[data-testid="baseButton-secondary"],
.stButton>button:not([kind="primary"]){{background-color:{p['bg2']}!important;border:1px solid {p['border']}!important;color:{p['text']}!important;border-radius:9px!important;transition:border-color .15s,background-color .15s!important}}
[data-testid="baseButton-secondary"]:hover,
.stButton>button:not([kind="primary"]):hover{{border-color:#6366F1!important;background-color:{p['bg2']}!important;color:#6366F1!important}}
[data-testid="baseButton-primary"],
.stButton>button[kind="primary"]{{background:linear-gradient(135deg,#6366F1,#7C3AED)!important;border:none!important;color:#F8FAFC!important;border-radius:9px!important;box-shadow:0 4px 14px rgba(99,102,241,.35)!important;transition:opacity .15s,transform .15s!important}}
[data-testid="baseButton-primary"]:hover,
.stButton>button[kind="primary"]:hover{{opacity:.88!important;transform:translateY(-1px)!important}}
/* ── Shared ── */
.page-header{{margin-bottom:28px}}
.page-title{{color:var(--fb-text)!important;font:700 1.6rem/1.2 {_FONT};letter-spacing:-.02em;margin:0 0 4px}}
.page-sub{{color:var(--fb-text-muted)!important;font:400 .875rem/1.4 {_FONT};margin:0 0 14px}}
.badge{{display:inline-flex;align-items:center;gap:5px;background:var(--fb-primary-bg);color:var(--fb-primary)!important;border-radius:20px;padding:3px 10px;font:600 .72rem {_FONT};letter-spacing:.02em}}
.section-label{{color:var(--fb-text-muted)!important;font:700 .72rem {_FONT};letter-spacing:.1em;text-transform:uppercase;margin:28px 0 12px;display:flex;align-items:center;gap:8px}}
.section-label::after{{content:"";flex:1;height:1px;background:var(--fb-divider)}}
.card{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:14px;padding:18px 20px;box-shadow:var(--fb-card-shadow);margin-bottom:12px;font-family:{_FONT}}}
.card:hover{{background:var(--fb-card-hover)}}
.card-title{{color:var(--fb-text)!important;font:600 .875rem {_FONT};letter-spacing:-.01em;margin-bottom:2px}}
.card-sub{{color:var(--fb-text-muted)!important;font:400 .72rem {_FONT};margin-bottom:14px}}
.chart-card{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:14px;padding:20px;box-shadow:var(--fb-card-shadow)}}
.empty-state{{background:color-mix(in srgb,var(--fb-primary) 5%,transparent);border:1px dashed var(--fb-primary-border);border-radius:14px;padding:40px 24px;text-align:center;font-family:{_FONT}}}
.empty-icon{{font-size:2.2rem;margin-bottom:12px}}
.empty-title{{color:var(--fb-primary)!important;font:600 .95rem {_FONT};margin-bottom:6px}}
.empty-sub{{color:var(--fb-text-muted)!important;font-size:.82rem}}
/* ── KPI ── */
.kpi-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:12px}}
.kpi-grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}}
.kpi-card{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:14px;padding:16px 18px;box-shadow:var(--fb-card-shadow);transition:background .15s;font-family:{_FONT}}}
.kpi-card:hover{{background:var(--fb-card-hover)}}
.kpi-icon-wrap{{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:16px;margin-bottom:12px}}
.kpi-label{{color:var(--fb-text-muted)!important;font:600 .68rem {_FONT};letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}
.kpi-value{{color:var(--fb-text)!important;font:700 1.45rem {_FONT};letter-spacing:-.02em;line-height:1.1}}
.kpi-value-sm{{color:var(--fb-text)!important;font:700 1.2rem {_FONT};letter-spacing:-.02em;line-height:1.1}}
.kpi-sub{{color:var(--fb-text-faint)!important;font-size:.7rem;margin-top:4px}}
/* ── Agent Registry ── */
.ar-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:6px}}
.ar-agent-card{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:14px;padding:16px 18px;box-shadow:var(--fb-card-shadow);transition:background .15s;font-family:{_FONT}}}
.ar-agent-card:hover{{background:var(--fb-card-hover)}}
.ar-card-top{{display:flex;align-items:center;gap:12px;margin-bottom:14px}}
.ar-avatar{{width:38px;height:38px;border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1rem;font-weight:700}}
.ar-card-identity{{flex:1;min-width:0}}
.ar-agent-name{{color:var(--fb-text)!important;font:600 .875rem {_FONT};white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.ar-agent-group{{color:var(--fb-text-muted)!important;font-size:.7rem;margin-top:1px}}
.ar-status-badge{{font:600 .65rem {_FONT};padding:3px 8px;border-radius:20px;white-space:nowrap;letter-spacing:.02em;flex-shrink:0}}
.ar-card-body{{border-top:1px solid var(--fb-divider);padding-top:12px}}
.ar-model{{color:var(--fb-text-muted)!important;font-size:.75rem;margin-bottom:10px}}
.ar-card-stats{{display:flex;align-items:center}}
.ar-stat{{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px}}
.ar-stat-num{{color:var(--fb-text-muted)!important;font:600 .8rem {_FONT}}}
.ar-stat-lbl{{color:var(--fb-text-faint)!important;font-size:.6rem;text-transform:uppercase;letter-spacing:.06em}}
.ar-stat-divider{{width:1px;height:24px;background:var(--fb-divider);flex-shrink:0}}
.ar-matrix-wrap{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:14px;padding:18px 20px;box-shadow:var(--fb-card-shadow)}}
.ar-violation-card{{background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.18);border-radius:12px;padding:14px 18px;display:flex;align-items:center;gap:12px;margin-bottom:8px;font-family:{_FONT}}}
.ar-all-clear{{background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.18);border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:12px;font-family:{_FONT}}}
/* ── Scorecards ── */
.sc-group-banner{{display:flex;align-items:center;gap:14px;padding:14px 18px;border-radius:12px;margin-bottom:16px;font-family:{_FONT}}}
/* ── Economics ── */
.ec-roi-banner{{display:flex;align-items:center;gap:20px;background:var(--fb-primary-bg);border:1px solid var(--fb-primary-border);border-radius:14px;padding:16px 20px;margin-bottom:20px;font-family:{_FONT};flex-wrap:wrap}}
.ec-roi-item{{display:flex;flex-direction:column;gap:2px}}
.ec-roi-label{{color:var(--fb-text-muted)!important;font:600 .65rem {_FONT};letter-spacing:.1em;text-transform:uppercase}}
.ec-roi-value{{color:var(--fb-text)!important;font:700 1.1rem {_FONT};letter-spacing:-.02em}}
.ec-roi-divider{{width:1px;height:36px;background:var(--fb-divider);flex-shrink:0}}
/* ── Traces ── */
.tr-selector-wrap{{background:var(--fb-subtle-bg);border:1px solid var(--fb-border);border-radius:14px;padding:20px 24px;margin-bottom:24px}}
.tr-chart-card{{background:var(--fb-subtle-bg);border:1px solid var(--fb-border);border-radius:14px;padding:20px 24px 8px;margin-bottom:24px}}
.tr-table-card{{background:var(--fb-subtle-bg);border:1px solid var(--fb-border);border-radius:14px;padding:20px 24px;margin-bottom:24px}}
.tr-kpi-row{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}
.tr-kpi-row .kpi-card{{flex:1;min-width:140px}}
/* ── V2 ── */
.v2-metric-row{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px}}
.v2-metric{{flex:1;min-width:120px;padding:12px 14px;background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:10px}}
.v2-metric-label{{color:var(--fb-text-muted)!important;font:600 .62rem {_FONT};letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px}}
.v2-metric-val{{color:var(--fb-text)!important;font:700 1.3rem {_FONT};letter-spacing:-.02em}}
.v2-gauge-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}}
.v2-gauge{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:12px;padding:16px;text-align:center}}
.v2-gauge-val{{color:var(--fb-text)!important;font:700 1.6rem {_FONT};letter-spacing:-.02em}}
.v2-gauge-label{{color:var(--fb-text-muted)!important;font:600 .65rem {_FONT};letter-spacing:.06em;text-transform:uppercase;margin-top:6px}}
.v2-waterfall-band{{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;margin-bottom:4px;font:500 .82rem {_FONT}}}
.v2-wf-success{{background:rgba(34,197,94,.1);color:#22C55E}}
.v2-wf-warning{{background:rgba(245,158,11,.1);color:#F59E0B}}
.v2-wf-error{{background:rgba(239,68,68,.1);color:#EF4444}}
.v2-wf-bar{{height:6px;border-radius:3px;flex-shrink:0}}
.v2-wf-count{{font-weight:700;min-width:32px;text-align:right}}
.v2-wf-pct{{font-size:.72rem;opacity:.7;min-width:40px}}
.v2-pattern-card{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:10px;padding:14px 16px;margin-bottom:8px}}
.v2-pattern-sev{{display:inline-block;border-radius:12px;padding:2px 8px;font:600 .65rem {_FONT};text-transform:uppercase}}
.v2-sev-critical{{background:rgba(239,68,68,.15);color:#EF4444}}
.v2-sev-warning{{background:rgba(245,158,11,.15);color:#F59E0B}}
.v2-sev-info{{background:rgba(99,102,241,.15);color:#6366F1}}
.v2-pattern-desc{{color:var(--fb-text)!important;font:500 .82rem {_FONT};margin:6px 0 4px}}
.v2-pattern-fix{{color:var(--fb-text-muted)!important;font:400 .75rem {_FONT};font-style:italic}}
.v2-pipeline{{display:flex;align-items:center;gap:0;margin:20px 0}}
.v2-pipe-step{{flex:1;text-align:center;padding:16px 8px;background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:12px;margin:0 4px}}
.v2-pipe-step.active{{border-color:#6366F1;box-shadow:0 0 12px rgba(99,102,241,.3)}}
.v2-pipe-step.done{{border-color:#22C55E;background:rgba(34,197,94,.06)}}
.v2-pipe-icon{{font-size:1.4rem;margin-bottom:6px}}
.v2-pipe-label{{color:var(--fb-text)!important;font:600 .75rem {_FONT}}}
.v2-pipe-status{{color:var(--fb-text-muted)!important;font:400 .65rem {_FONT};margin-top:4px}}
.v2-pipe-arrow{{color:var(--fb-text-muted);font-size:1.2rem;flex-shrink:0}}
.v2-compare-grid{{display:grid;grid-template-columns:1fr 60px 1fr;gap:0;margin-bottom:16px}}
.v2-compare-col{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:12px;padding:20px}}
.v2-compare-center{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:8px 0}}
.v2-compare-header{{color:var(--fb-text-muted)!important;font:700 .72rem {_FONT};letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px;text-align:center}}
.v2-compare-row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--fb-divider)}}
.v2-compare-label{{color:var(--fb-text-muted)!important;font:500 .78rem {_FONT}}}
.v2-compare-val{{color:var(--fb-text)!important;font:700 .85rem {_FONT}}}
.v2-delta{{font:700 .72rem {_FONT};border-radius:10px;padding:2px 6px}}
.v2-delta-up{{background:rgba(34,197,94,.15);color:#22C55E}}
.v2-delta-down{{background:rgba(239,68,68,.15);color:#EF4444}}
.v2-delta-flat{{background:rgba(100,116,139,.15);color:var(--fb-text-muted)}}
.v2-trend{{display:inline-flex;align-items:center;gap:4px;border-radius:12px;padding:3px 10px;font:600 .72rem {_FONT}}}
.v2-trend-improving{{background:rgba(34,197,94,.12);color:#22C55E}}
.v2-trend-stable{{background:rgba(100,116,139,.12);color:var(--fb-text-muted)}}
.v2-trend-degrading{{background:rgba(239,68,68,.12);color:#EF4444}}
.v2-control-card{{background:var(--fb-card-bg);border:1px solid var(--fb-border);border-radius:12px;padding:16px 18px;margin-bottom:10px}}
.v2-ctrl-label{{color:var(--fb-text)!important;font:600 .82rem {_FONT};margin-bottom:2px}}
.v2-ctrl-desc{{color:var(--fb-text-muted)!important;font:400 .72rem {_FONT};margin-bottom:10px}}
.v2-rec-card{{background:color-mix(in srgb,var(--fb-primary) 6%,transparent);border:1px solid var(--fb-primary-border);border-radius:10px;padding:12px 14px;margin-bottom:8px}}
.v2-rec-param{{color:var(--fb-primary)!important;font:700 .78rem {_FONT}}}
.v2-rec-reason{{color:var(--fb-text-muted)!important;font:400 .75rem {_FONT};margin-top:4px}}
.v2-rec-impact{{color:#22C55E!important;font:600 .72rem {_FONT};margin-top:2px}}
.diff-row{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--fb-divider)}}
.diff-param{{font:500 .82rem {_FONT};color:var(--fb-primary)}}
.diff-old{{color:#EF4444;text-decoration:line-through}}
.diff-arrow{{margin:0 6px;opacity:.4}}
.diff-new{{color:#22C55E;font-weight:600}}
/* ── Data Tables (replaces canvas-based st.dataframe) ── */
.fb-table-wrap{{border:1px solid var(--fb-border);border-radius:12px;overflow:hidden;overflow-x:auto;background:var(--fb-card-bg);margin-bottom:12px}}
.fb-table{{width:100%;border-collapse:collapse;font:400 .82rem {_FONT}}}
.fb-table th{{background:var(--fb-card-bg);color:var(--fb-text-muted)!important;font:700 .68rem {_FONT};letter-spacing:.08em;text-transform:uppercase;padding:10px 14px;border-bottom:1px solid var(--fb-border);text-align:left;white-space:nowrap}}
.fb-table td{{padding:9px 14px;border-bottom:1px solid var(--fb-divider);color:var(--fb-text)!important;vertical-align:middle;white-space:nowrap}}
.fb-table tr:last-child td{{border-bottom:none}}
.fb-table tbody tr:hover td{{background:color-mix(in srgb,var(--fb-primary) 4%,var(--fb-bg))}}
</style>"""


def sidebar_css() -> str:
    """Return sidebar CSS.  Colours adapt via CSS custom properties."""
    return f"""<style>
[data-testid="stSidebar"]{{border-right:1px solid var(--fb-divider);padding-top:0!important}}
[data-testid="stSidebar"]>div:first-child{{padding-top:0!important}}
[data-testid="stSidebar"],[data-testid="stSidebar"] *{{font-family:{_FONT}}}
[data-testid="stSidebar"] [data-testid="stIconMaterial"]{{font-family:"Material Symbols Rounded","Material Icons"!important}}
.sb-section-label{{color:var(--fb-text-muted)!important;font:700 .62rem {_FONT};letter-spacing:.14em;text-transform:uppercase;margin:0 0 6px 2px;display:block}}
.sb-logo-wrap{{display:flex;align-items:center;gap:11px;padding:22px 20px 18px;border-bottom:1px solid var(--fb-divider);margin-bottom:20px}}
.sb-logo-icon{{width:38px;height:38px;background:linear-gradient(135deg,#6366F1,#8B5CF6);border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0;box-shadow:0 4px 14px rgba(99,102,241,.45)}}
.sb-logo-title{{color:var(--fb-text)!important;font:700 .95rem {_FONT};letter-spacing:-.015em;line-height:1.2}}
.sb-logo-sub{{color:var(--fb-text-faint)!important;font-size:.68rem;line-height:1.3}}
[data-testid="stSidebar"] hr{{border:none!important;border-top:1px solid var(--fb-divider)!important;margin:14px 0!important}}
[data-testid="stSidebar"] [data-testid="stRadio"]>div{{gap:2px!important;flex-direction:column!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label{{background:transparent!important;border-radius:9px!important;padding:9px 12px 9px 10px!important;cursor:pointer!important;width:100%!important;display:flex!important;align-items:center!important;transition:background .15s,color .15s!important;font:400 .855rem {_FONT}!important;color:var(--fb-text-muted)!important;text-transform:none!important;letter-spacing:normal!important;border:1px solid transparent!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label *{{color:inherit!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{{color:inherit!important;margin:0!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{{background:var(--fb-primary-bg)!important;color:var(--fb-primary)!important;border-color:var(--fb-primary-border)!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){{background:color-mix(in srgb,var(--fb-primary) 15%,transparent)!important;color:var(--fb-primary)!important;border-color:color-mix(in srgb,var(--fb-primary) 25%,transparent)!important;font-weight:600!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label>div:first-child,[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"]{{display:none!important}}
[data-testid="stSidebar"] [data-testid="stRadio"]>label{{display:none!important}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:linear-gradient(135deg,#6366F1,#7C3AED)!important;border:none!important;color:#F8FAFC!important;border-radius:9px!important;font:600 .82rem {_FONT}!important;padding:9px 14px!important;width:100%!important;transition:opacity .15s,transform .15s!important;box-shadow:0 4px 14px rgba(99,102,241,.35)!important}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{{opacity:.88!important;transform:translateY(-1px)!important}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:active{{transform:translateY(0)!important}}
[data-testid="stSidebar"] .stButton>button:not([kind="primary"]){{background:var(--fb-subtle-bg)!important;border:1px solid var(--fb-border)!important;color:var(--fb-text-muted)!important;border-radius:9px!important;font:500 .78rem {_FONT}!important;padding:7px 14px!important;width:100%!important;transition:border-color .15s!important}}
[data-testid="stSidebar"] .stButton>button:not([kind="primary"]):hover{{border-color:var(--fb-primary-border)!important;color:var(--fb-text)!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"]>div,
[data-testid="stSidebar"] [data-testid="stSelectbox"]>div>div{{background-color:var(--fb-subtle-bg)!important;border:1px solid var(--fb-border)!important;border-radius:9px!important;color:var(--fb-text-muted)!important;font-size:.84rem!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"]>div:hover,
[data-testid="stSidebar"] [data-testid="stSelectbox"]>div>div:hover{{border-color:var(--fb-primary-border)!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"]>div *{{color:var(--fb-text-muted)!important}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,[data-testid="stSidebar"] [data-testid="stMultiSelect"] label{{color:var(--fb-text-muted)!important;font:600 .68rem {_FONT};letter-spacing:.1em;text-transform:uppercase}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child{{background-color:var(--fb-subtle-bg)!important;border:1px solid var(--fb-border)!important;border-radius:9px!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child:hover{{border-color:var(--fb-primary-border)!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"]>div:first-child *{{background-color:transparent!important;color:var(--fb-text-muted)!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] input::placeholder{{color:var(--fb-text-faint)!important}}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"]{{background-color:var(--fb-primary-bg)!important;border:1px solid var(--fb-primary-border)!important;border-radius:5px!important;color:var(--fb-primary)!important}}
[data-testid="stSidebar"] [data-testid="stAlert"]{{background:rgba(34,197,94,.08)!important;border:1px solid rgba(34,197,94,.20)!important;border-radius:9px!important;color:#22C55E!important;font-size:.78rem!important}}
[data-testid="stSidebar"] .block-container{{padding:0!important}}
[data-testid="stSidebar"] section[data-testid="stSidebarContent"]>div{{padding-left:14px!important;padding-right:14px!important}}
</style>"""
