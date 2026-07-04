"""Hydrogen Dispatch Optimization — Streamlit dashboard (defense centerpiece).

Five tabs telling the thesis story (validate → operate → control → scale):

    1. Daily Dispatch     — least-cost 24-h schedule (+ optional battery storage)
    2. Control Strategy   — MPC vs perfect-foresight vs rule-based (the control core)
    3. Annual Performance — full-year 2023 KPIs, calendar heatmap, monthly pattern
    4. Smart vs Traditional — cost-vs-demand vs constant/greedy baselines
    5. Validation & Plant — ETAP↔pandapower validation + 3D digital-twin link

Run from the repo root:
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

import streamlit as st

# Make `app` and `src` importable whether launched from the repo root or app/.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

st.set_page_config(page_title="Hydrogen Dispatch", page_icon="⚡", layout="wide")

from app import _theme as theme
from app.tabs import annual, baselines, control, daily, validation

theme.apply_theme()

# ── sidebar (global branding / provenance) ──────────────────────────────────────
with st.sidebar:
    theme.sidebar_brand()

# ── hero banner ─────────────────────────────────────────────────────────────────
theme.hero(
    "Hydrogen Dispatch Optimizer",
    "Automated, ETAP-validated power-dispatch control for green-hydrogen "
    "production — driven by real Ghardaïa 2023 weather and the Algerian CREG "
    "time-of-use tariff, with a live supervisory (MPC) controller.",
    ["Ghardaïa 2023 · CAMS→PySAM", "CREG 51NM tariff", "PSO + MPC control",
     "pandapower · ETAP-validated"],
)

# ── tab layout ──────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs([
    "📈  Daily Dispatch",
    "🎛️  Control Strategy",
    "📅  Annual Performance",
    "⚖️  Smart vs Traditional",
    "✅  Validation & Plant",
])

with t1:
    daily.render()
with t2:
    control.render()
with t3:
    annual.render()
with t4:
    baselines.render()
with t5:
    validation.render()
