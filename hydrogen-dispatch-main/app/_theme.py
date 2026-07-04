"""Visual theme for the dashboard — custom CSS, a hero header, and section
headers. Import and call apply_theme() once at the top of dashboard.py, then use
hero() for the page banner and section() in each tab instead of st.subheader.

All styling is CSS injected via st.markdown; it degrades gracefully (the app
still works with styling stripped). Selectors use stable data-testid / baseweb
hooks so they survive Streamlit minor versions.
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
  --hd-primary:#1d4ed8; --hd-accent:#0ea5e9;
  --hd-bg:#f4f6fb; --hd-card:#ffffff; --hd-border:#e6eaf1;
  --hd-text:#0f172a; --hd-muted:#64748b;
}

html, body, .stApp, .block-container, [data-testid="stMarkdownContainer"]{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}
.stApp{ background:var(--hd-bg); }
.block-container{ padding-top:1.1rem; padding-bottom:3rem; max-width:1400px; }

/* ---------- hero banner ---------- */
.hd-hero{ position:relative; overflow:hidden;
  background:linear-gradient(120deg,#0b2a6b 0%,#1d4ed8 50%,#0ea5e9 100%);
  border-radius:18px; padding:26px 32px; margin:2px 0 20px 0;
  box-shadow:0 12px 30px rgba(29,78,216,.20); }
.hd-hero:after{ content:""; position:absolute; right:-70px; top:-70px;
  width:280px; height:280px; border-radius:50%;
  background:radial-gradient(circle,rgba(255,255,255,.20),transparent 70%); }
.hd-hero-title{ color:#fff; font-size:31px; font-weight:800; letter-spacing:-.02em;
  margin:0; line-height:1.1; position:relative; z-index:1; }
.hd-hero-sub{ color:#dbeafe; font-size:14.5px; margin-top:8px; max-width:780px;
  line-height:1.55; position:relative; z-index:1; }
.hd-chips{ margin-top:15px; display:flex; flex-wrap:wrap; gap:8px;
  position:relative; z-index:1; }
.hd-chip{ background:rgba(255,255,255,.15); color:#fff;
  border:1px solid rgba(255,255,255,.28); padding:4px 12px; border-radius:999px;
  font-size:12.5px; font-weight:600; }

/* ---------- section headers ---------- */
.hd-sec{ margin:10px 0 14px 0; }
.hd-sec-title{ font-size:21px; font-weight:700; color:var(--hd-text);
  letter-spacing:-.01em; display:flex; align-items:center; gap:10px; }
.hd-sec-title:before{ content:""; width:5px; height:23px; border-radius:3px;
  background:linear-gradient(180deg,var(--hd-primary),var(--hd-accent)); }
.hd-sec-sub{ color:var(--hd-muted); font-size:13.5px; margin:4px 0 0 15px; }

/* ---------- metric cards ---------- */
[data-testid="stMetric"]{ background:var(--hd-card); border:1px solid var(--hd-border);
  border-left:4px solid var(--hd-primary); border-radius:14px;
  padding:14px 16px 12px 16px;
  box-shadow:0 1px 2px rgba(15,23,42,.04),0 2px 6px rgba(15,23,42,.05);
  transition:transform .15s ease, box-shadow .15s ease; }
[data-testid="stMetric"]:hover{ transform:translateY(-2px);
  box-shadow:0 10px 22px rgba(15,23,42,.10); }
[data-testid="stMetricLabel"] p{ font-size:11.5px !important; font-weight:600;
  text-transform:uppercase; letter-spacing:.045em; color:var(--hd-muted); }
[data-testid="stMetricValue"]{ font-size:26px; font-weight:800; color:var(--hd-text);
  letter-spacing:-.02em; }

/* ---------- chart / dataframe cards ---------- */
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"]{
  background:var(--hd-card); border:1px solid var(--hd-border); border-radius:14px;
  padding:6px; box-shadow:0 1px 3px rgba(15,23,42,.06); }

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"]{ gap:4px; background:transparent;
  border-bottom:1px solid var(--hd-border); }
.stTabs [data-baseweb="tab"]{ height:auto; padding:10px 18px;
  border-radius:10px 10px 0 0; font-weight:600; font-size:14.5px;
  color:var(--hd-muted); background:transparent; }
.stTabs [data-baseweb="tab"]:hover{ color:var(--hd-primary);
  background:rgba(37,99,235,.06); }
.stTabs [aria-selected="true"]{ color:var(--hd-primary) !important;
  background:var(--hd-card); box-shadow:inset 0 -3px 0 var(--hd-primary); }

/* ---------- buttons ---------- */
.stButton > button{ border-radius:10px; font-weight:600; padding:.5rem 1.2rem;
  border:1px solid var(--hd-border); transition:all .15s ease; }
.stButton > button:hover{ transform:translateY(-1px);
  box-shadow:0 5px 14px rgba(15,23,42,.10); }
.stButton > button[kind="primary"]{ background:linear-gradient(120deg,#1d4ed8,#0ea5e9);
  border:none; color:#fff; }
.stButton > button[kind="primary"]:hover{ box-shadow:0 7px 20px rgba(29,78,216,.38); }

/* ---------- alerts / expander ---------- */
[data-testid="stAlert"]{ border-radius:12px; }
[data-testid="stExpander"]{ border:1px solid var(--hd-border); border-radius:12px;
  background:var(--hd-card); }

/* ---------- sidebar (dark) ---------- */
[data-testid="stSidebar"]{ background:#0b1424; }
[data-testid="stSidebar"] *{ color:#cbd5e1; }
[data-testid="stSidebar"] hr{ border-color:rgba(255,255,255,.10); }
.hd-brand{ display:flex; align-items:center; gap:11px; padding:4px 0 2px; }
.hd-brand-badge{ width:42px; height:42px; border-radius:12px;
  background:linear-gradient(135deg,#1d4ed8,#0ea5e9); display:flex;
  align-items:center; justify-content:center; font-size:22px;
  box-shadow:0 5px 14px rgba(14,165,233,.45); }
.hd-brand-name{ font-size:17px; font-weight:800; color:#fff !important; line-height:1.15; }
.hd-brand-tag{ font-size:11.5px; color:#7dd3fc !important; font-weight:600;
  letter-spacing:.02em; }
.hd-side-card{ background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.09);
  border-radius:12px; padding:12px 14px; margin-top:14px; font-size:12.7px;
  line-height:1.55; }
.hd-side-card b{ color:#fff !important; }
.hd-side-k{ color:#7dd3fc !important; font-weight:700; }
</style>
"""


def apply_theme():
    """Inject the dashboard CSS. Call once, before rendering anything."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title, subtitle, chips):
    """Render the page hero banner with a title, subtitle and a row of chips."""
    chip_html = "".join(f'<span class="hd-chip">{c}</span>' for c in chips)
    st.markdown(
        f'<div class="hd-hero"><div class="hd-hero-title">{title}</div>'
        f'<div class="hd-hero-sub">{subtitle}</div>'
        f'<div class="hd-chips">{chip_html}</div></div>',
        unsafe_allow_html=True,
    )


def section(title, subtitle=None):
    """Styled section header (use instead of st.subheader)."""
    sub = f'<div class="hd-sec-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="hd-sec"><div class="hd-sec-title">{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


def sidebar_brand():
    """Branded sidebar header + provenance cards (dark sidebar)."""
    st.markdown(
        '<div class="hd-brand"><div class="hd-brand-badge">⚡</div>'
        '<div><div class="hd-brand-name">Hydrogen Dispatch</div>'
        '<div class="hd-brand-tag">ETAP-validated optimizer</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hd-side-card"><b>Data</b><br>'
        'Ghardaïa 2023 — real <span class="hd-side-k">CAMS+ERA5</span> weather '
        '→ <span class="hd-side-k">NREL SAM</span> (PySAM) PV.</div>'
        '<div class="hd-side-card"><b>Tariff</b><br>'
        'Algerian <span class="hd-side-k">CREG 51NM</span> medium-voltage '
        'time-of-use.</div>'
        '<div class="hd-side-card"><b>Engine</b><br>'
        '<span class="hd-side-k">PSO</span> over hourly setpoints · '
        '<span class="hd-side-k">pandapower</span> feasibility '
        '(ETAP-validated).</div>'
        '<div class="hd-side-card">Each tab has its own controls. Live tabs cache '
        'results, so a repeated run is instant.</div>',
        unsafe_allow_html=True,
    )
