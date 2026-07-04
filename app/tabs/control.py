"""Tab 2 — Control Strategy (the control-engineering core).

Casts the dispatch as feedback control and compares three controllers on the same
real day, where yesterday's PV is the day-ahead forecast and today's PV is the
realized disturbance:

  • perfect-foresight  — open-loop optimum (the unreachable lower bound),
  • MPC                — receding-horizon, re-plans each hour on realized PV,
  • rule-based         — reactive, time-blind constant rate.

The story: MPC recovers most of the optimum despite forecast error and beats the
reactive rule — it rejects the PV disturbance.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app._shared import (
    AXIS_TITLE_FONT, BLACK, COLOR_GRID, COLOR_PV, COLOR_SETPOINT, COLOR_TARIFF,
    FONT, LEGEND_STYLE, PRICE_STEPS, STEP_H, STEPS_PER_HOUR, X_STEPS,
)
from app._theme import section
from src.day_dispatch import optimize_day
from src.mpc import consecutive_days, mpc_dispatch, rule_based_dispatch


@st.cache_data(show_spinner=False)
def _pairs():
    """{date: (today_pv96, yesterday_pv96)} for full days with a predecessor."""
    return {date: (today, prev) for date, today, prev in consecutive_days()}


@st.cache_data(show_spinner=False)
def _day_options():
    """Dates sorted by forecast error (|today − yesterday| PV energy), descending."""
    rows = []
    for date, (today, prev) in _pairs().items():
        et, ey = today.sum() * STEP_H, prev.sum() * STEP_H
        rows.append((date, et, ey, abs(et - ey)))
    rows.sort(key=lambda r: r[3], reverse=True)
    return rows


@st.cache_data(show_spinner=False)
def _run_controllers(date, demand_kg, seed=0):
    today, prev = _pairs()[date]
    pf  = optimize_day(today, demand_kg, seed=seed)
    mpc = mpc_dispatch(today, prev, demand_kg, seed=seed)
    rb  = rule_based_dispatch(today, demand_kg)
    return today, prev, pf, mpc, rb


def render():
    section("Control Strategy",
            "The dispatch as feedback control: MPC re-plans each hour as real PV is "
            "revealed, recovering most of the perfect-foresight optimum and beating "
            "the reactive rule — it rejects the PV disturbance.")

    options = _day_options()
    labels = {d: f"{d}  ·  today {et:.2f} / forecast {ey:.2f} MWh  (Δ {dd:.2f})"
              for d, et, ey, dd in options}

    c_day, c_dem = st.columns([2.4, 1.4])
    with c_day:
        date = st.selectbox(
            "Day (sorted by forecast error — largest first)",
            options=[d for d, *_ in options],
            format_func=lambda d: labels[d], key="ctrl_day")
    with c_dem:
        demand_kg = st.slider("Daily H₂ demand (kg/day)", 40, 340, 200, 10,
                              key="ctrl_demand")

    run_clicked = st.button("Run Controllers", type="primary", key="ctrl_run")
    params = (date, demand_kg)
    if run_clicked or st.session_state.get("ctrl_last") != params:
        with st.spinner("Running MPC (24 receding-horizon solves) + baselines…"):
            st.session_state["ctrl_data"] = _run_controllers(date, demand_kg)
            st.session_state["ctrl_last"] = params

    if "ctrl_data" not in st.session_state:
        st.info("Pick a day and click **Run Controllers**.")
        return

    today, prev, pf, mpc, rb = st.session_state["ctrl_data"]

    # ── headline metrics ────────────────────────────────────────────────────────
    gap  = 100.0 * (mpc["total_cost_da"] - pf["total_cost_da"]) / max(pf["total_cost_da"], 1e-9)
    edge = 100.0 * (rb["total_cost_da"]  - mpc["total_cost_da"]) / max(rb["total_cost_da"], 1e-9)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Perfect-foresight (bound)", f"{pf['cost_per_kg_da']:.1f} DA/kg")
    c2.metric("MPC (closed-loop)", f"{mpc['cost_per_kg_da']:.1f} DA/kg",
              delta=f"{gap:+.1f}% vs optimum", delta_color="inverse")
    c3.metric("Rule-based (reactive)", f"{rb['cost_per_kg_da']:.1f} DA/kg")
    c4.metric("MPC vs rule-based", f"{edge:.1f}% cheaper")

    # ── setpoint comparison chart ───────────────────────────────────────────────
    def steps(hourly):
        return np.repeat(np.asarray(hourly), STEPS_PER_HOUR)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=X_STEPS, y=today, mode="lines",
                             name="PV realized [MW]  (disturbance)",
                             line=dict(color=COLOR_PV, width=3),
                             hovertemplate="%{y:.3f} MW<extra>PV today</extra>"))
    fig.add_trace(go.Scatter(x=X_STEPS, y=prev, mode="lines",
                             name="PV forecast [MW]  (day-ahead)",
                             line=dict(color="#86efac", width=2.5, dash="dot"),
                             hovertemplate="%{y:.3f} MW<extra>PV forecast</extra>"))
    fig.add_trace(go.Scatter(x=X_STEPS, y=steps(pf["hourly_setpoints"]), mode="lines",
                             name="Perfect-foresight setpoint [MW]  (optimum)",
                             line=dict(color="#334155", width=2.5, shape="hv",
                                       dash="dash"),
                             hovertemplate="%{y:.3f} MW<extra>PF</extra>"))
    fig.add_trace(go.Scatter(x=X_STEPS, y=steps(mpc["hourly_setpoints"]), mode="lines",
                             name="MPC setpoint [MW]  (closed-loop)",
                             line=dict(color=COLOR_SETPOINT, width=3.5, shape="hv"),
                             hovertemplate="%{y:.3f} MW<extra>MPC</extra>"))
    fig.add_trace(go.Scatter(x=X_STEPS, y=steps(rb["hourly_setpoints"]), mode="lines",
                             name="Rule-based setpoint [MW]  (reactive)",
                             line=dict(color=COLOR_GRID, width=2.5, shape="hv",
                                       dash="dot"),
                             hovertemplate="%{y:.3f} MW<extra>Rule</extra>"))
    fig.add_trace(go.Scatter(x=X_STEPS, y=PRICE_STEPS, mode="lines",
                             name="CREG tariff [DA/kWh]", yaxis="y2",
                             line=dict(color=COLOR_TARIFF, width=2.5, dash="dot"),
                             hovertemplate="%{y:.3f} DA/kWh<extra>Tariff</extra>"))
    fig.update_layout(
        font=FONT,
        title=dict(text=f"Electrolyzer setpoints by controller — {date}",
                   font=dict(size=13, color=BLACK)),
        xaxis=dict(title=dict(text="Hour of day (local time)", font=AXIS_TITLE_FONT),
                   range=[0, 24], tickvals=list(range(0, 25, 2)),
                   tickfont=dict(color=BLACK)),
        yaxis=dict(title=dict(text="Power [MW]", font=AXIS_TITLE_FONT),
                   gridcolor="#e5e7eb", tickfont=dict(color=BLACK)),
        yaxis2=dict(title=dict(text="Tariff [DA/kWh]", font=AXIS_TITLE_FONT),
                    overlaying="y", side="right", range=[0, 10], showgrid=False,
                    tickfont=dict(color=BLACK)),
        legend=LEGEND_STYLE,
        hovermode="x unified", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=480, margin=dict(t=110, b=50))
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"**MPC rejects the PV disturbance.** Using only yesterday's profile as the "
        f"day-ahead forecast, MPC re-optimizes the remaining horizon each hour as the "
        f"actual PV is realized. It lands within **{gap:+.1f}%** of the perfect-foresight "
        f"optimum and is **{edge:.1f}% cheaper** than the reactive rule-based controller, "
        f"all while meeting demand "
        f"(MPC {'✓' if mpc['demand_met'] else '✗'}, "
        f"rule {'✓' if rb['demand_met'] else '✗'}).")
