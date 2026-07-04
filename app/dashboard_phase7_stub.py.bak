"""Supervisory dashboard for the hydrogen dispatch controller (Phase 7).

A presentation layer over the existing controller. It imports
optimize_dispatch() (src.optimizer) and the constants from src.pipeline,
takes one operating point from the sidebar, runs the PSO optimizer at the
reduced Phase-6 budget, and visualizes the optimal dispatch, the power
balance at the LV bus, and the network feasibility against the ETAP limits.

It changes no engine code: every number shown comes straight from
optimize_dispatch() and the evaluate_dispatch() result it carries.

Launch from the repo root:
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

# app/ is not the import root; put the repo root on sys.path so "src.*"
# resolves the same way it does for scripts/run_scenarios.py.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")  # headless backend: we render through st.pyplot, no GUI
import matplotlib.pyplot as plt
import streamlit as st
from pymoo.config import Config

from src.optimizer import MODES, optimize_dispatch
from src.pipeline import (LOADING_MAX_PERCENT, TARIFF_DA_PER_KWH, V_MAX_PU,
                          V_MIN_PU)

Config.warnings["not_compiled"] = False  # silence pymoo's JIT notice in logs

# Reduced PSO budget. The Phase-6 budget check confirmed all six analytic
# optima land within 0.005 MW at this budget, so the optimizer returns in a
# few seconds — fast enough for an interactive slider-driven demo.
POP_REDUCED = 10
NGEN_REDUCED = 15

MODE_LABELS = {
    "max_h2": "Maximize hydrogen (max H₂)",
    "min_cost": "Minimize cost per kg",
}

# Flow colours (consistent across the app): generation green, load blue,
# grid import red, grid export green.
C_PV = "#2ca02c"
C_LOAD = "#1f77b4"
C_IMPORT = "#d62728"
C_EXPORT = "#2ca02c"


def run_optimizer(g_wm2, t_amb_c, tariff, mode):
    """Call the controller at the reduced budget; return its result dict."""
    return optimize_dispatch(g_wm2, t_amb_c, tariff, mode,
                             pop_size=POP_REDUCED, n_gen=NGEN_REDUCED)


def describe_regime(res, p_elz_mw):
    """One-line statement of the dispatch decision, derived from the numbers."""
    pv = res["pv_mw"]
    grid = res["grid_p_mw"]
    if p_elz_mw <= 0.0:
        return ("Electrolyzer **off** — no feasible producing setpoint at "
                "this operating point.")
    if pv <= 1e-6:
        return (f"**Night / no sun** — the grid supplies the entire "
                f"{p_elz_mw:.3f} MW electrolyzer load.")
    if grid < -1e-4:
        return (f"**PV surplus** — the {pv:.3f} MW array covers the load and "
                f"{-grid:.3f} MW is exported; hydrogen produced at zero grid "
                f"cost.")
    if grid > 1e-4:
        return (f"**PV-assisted import** — solar supplies {pv:.3f} MW and the "
                f"grid imports the remaining {grid:.3f} MW.")
    return ("**PV-balanced** — solar output matches the load almost exactly; "
            "negligible grid exchange.")


def power_balance_figure(pv_mw, grid_p_mw, p_elz_mw):
    """Horizontal signed-bar view of the three flows at the 0.415 kV bus."""
    labels = ["PV generation", "Grid exchange", "Electrolyzer load"]
    values = [pv_mw, grid_p_mw, p_elz_mw]
    grid_color = C_IMPORT if grid_p_mw >= 0 else C_EXPORT
    colors = [C_PV, grid_color, C_LOAD]

    fig, ax = plt.subplots(figsize=(7, 2.7))
    bars = ax.barh(labels, values, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Power [MW]")
    ax.invert_yaxis()  # first label (PV) on top

    span = max(0.05, max(abs(v) for v in values))
    ax.set_xlim(min(-0.1 * span, min(values) - 0.1 * span), span * 1.25)
    for bar, v in zip(bars, values):
        offset = 0.01 * span
        ax.text(v + (offset if v >= 0 else -offset),
                bar.get_y() + bar.get_height() / 2,
                f"{v:+.3f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=10)
    fig.tight_layout()
    return fig


def _limit_badge(ok, detail):
    """Colored inline status badge (used with unsafe_allow_html=True)."""
    color = C_PV if ok else C_IMPORT
    mark = "✓" if ok else "✗"
    text = "within limits" if ok else "VIOLATION"
    return (f"<span style='color:{color};font-weight:600'>{mark} {text}</span> "
            f"<span style='color:gray'>({detail})</span>")


def render_network(res):
    """Network-state panel: SecondaryBus voltage and T1 loading vs their limits."""
    st.markdown("**Network feasibility**")
    v = res["v_secondary_pu"]
    loading = res["trafo_loading_percent"]
    if v is None or loading is None:
        st.write("No load-flow result available for this point.")
        return None, None

    v_ok = V_MIN_PU <= v <= V_MAX_PU
    l_ok = loading <= LOADING_MAX_PERCENT

    st.metric("SecondaryBus voltage", f"{v:.4f} pu")
    st.markdown(_limit_badge(v_ok, f"limits {V_MIN_PU}–{V_MAX_PU} pu"),
                unsafe_allow_html=True)
    st.metric("Transformer T1 loading", f"{loading:.1f} %")
    st.markdown(_limit_badge(l_ok, f"limit ≤ {LOADING_MAX_PERCENT:.0f} %"),
                unsafe_allow_html=True)
    return v_ok, l_ok


# --- Page setup ---------------------------------------------------------------
st.set_page_config(page_title="Hydrogen Dispatch Controller",
                   page_icon="⚡", layout="wide")

st.title("⚡ Hydrogen Dispatch Controller")
st.caption("Supervisory view of the PV + grid → PEM electrolyzer dispatch "
           "optimizer, validated against the ETAP digital twin.")

# --- Sidebar inputs -----------------------------------------------------------
with st.sidebar:
    st.header("Operating conditions")
    g_wm2 = st.slider("Irradiance G [W/m²]", 0, 1200, 1000, step=10)
    t_amb_c = st.slider("Ambient temperature Ta [°C]", 0, 50, 25, step=1)
    tariff = st.slider("Grid tariff [DA/kWh]", 0.0, 20.0,
                       float(TARIFF_DA_PER_KWH), step=0.01)
    st.divider()
    mode = st.radio("Optimization objective", options=list(MODES),
                    format_func=lambda m: MODE_LABELS[m])
    compute = st.button("Compute optimal dispatch", type="primary",
                        width="stretch")
    st.caption(f"PSO at the reduced budget (pop {POP_REDUCED} × {NGEN_REDUCED} "
               f"generations); a few seconds per run.")

# --- Compute on click, persist across reruns ---------------------------------
if compute:
    try:
        with st.spinner("Optimizing dispatch…"):
            out = run_optimizer(float(g_wm2), float(t_amb_c), float(tariff), mode)
        st.session_state["out"] = out
        st.session_state["inputs"] = {"G": g_wm2, "Ta": t_amb_c,
                                      "tariff": tariff, "mode": mode}
    except Exception as exc:  # never leave the UI on a traceback
        st.session_state.pop("out", None)
        st.error(f"Optimization failed: {exc}")

# --- Render -------------------------------------------------------------------
if "out" not in st.session_state:
    st.info("Set the operating conditions in the sidebar and click "
            "**Compute optimal dispatch**.")
    st.stop()

out = st.session_state["out"]
res = out["result"]
p_elz = out["p_elz_mw"]
inp = st.session_state["inputs"]

st.subheader(f"Optimum · G = {inp['G']} W/m², Ta = {inp['Ta']} °C, "
             f"tariff = {inp['tariff']:.2f} DA/kWh · "
             f"{MODE_LABELS[inp['mode']]}")

if not res["feasible"]:
    st.error(f"No feasible dispatch found. Reason: "
             f"{res['reason'] or 'unknown'}")
    render_network(res)  # show the offending voltage/loading if available
    st.stop()

# Regime decision line.
st.info(describe_regime(res, p_elz))

# Headline metric cards.
c1, c2, c3 = st.columns(3)
c1.metric("Optimal setpoint P*", f"{p_elz:.3f} MW")
c2.metric("Hydrogen production", f"{res['h2_kg_per_h']:.2f} kg/h")
c3.metric("Hydrogen cost", f"{res['cost_per_kg']:.2f} DA/kg")

st.divider()
left, right = st.columns([3, 2])

with left:
    fig = power_balance_figure(res["pv_mw"], res["grid_p_mw"], p_elz)
    st.pyplot(fig)
    plt.close(fig)  # release from pyplot's global registry — reruns rebuild it
    grid = res["grid_p_mw"]
    flow = "import" if grid >= 0 else "export"
    st.caption(f"PV {res['pv_mw']:.3f} MW · grid {grid:+.3f} MW ({flow}) · "
               f"load {p_elz:.3f} MW.  Sign convention: **+ import / − "
               f"export**; PV + grid = electrolyzer load.")

with right:
    v_ok, l_ok = render_network(res)
    if v_ok is not None:
        if v_ok and l_ok:
            st.success("Operating point within all network limits.")
        else:
            st.error("Network limit violated at this dispatch.")

with st.expander("Optimizer details"):
    st.write({
        "mode": out["mode"],
        "optimal setpoint p_elz_mw": p_elz,
        "objective": out["objective"],
        "PV available [MW]": res["pv_mw"],
        "grid exchange [MW] (+import/-export)": res["grid_p_mw"],
        "grid cost [DA/h]": res["cost_per_h"],
        "PSO generations (summed over stages)": out["n_iterations"],
        "evaluate_dispatch calls": out["n_evaluations"],
        "PSO budget": f"pop {POP_REDUCED} × {NGEN_REDUCED} gen",
    })
