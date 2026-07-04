"""Tab 4 — Smart vs Traditional dispatch.

Same hydrogen, same real day, same tariff — three ways to run the electrolyzer:
optimized (PSO) vs constant baseload vs greedy produce-ASAP. The cost gap is the
value of intelligent timing. Constant/greedy are closed-form-cheap (shown live
across the demand sweep); the optimized curve is the slow PSO, so it runs at the
selected demand by default and the full curve is behind a button (hybrid compute).
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app._shared import (AXIS_TITLE_FONT, BLACK, DAY_KEYS, DAY_LABELS, FONT,
                         LEGEND_STYLE, load_days, run_optimization)
from app._theme import section
from src.day_dispatch import (HOURS, P_MIN_MW, P_RATED_MW, evaluate_day,
                              mdot_fast)


def _const_setpoint(demand_kg):
    target = demand_kg / HOURS
    if mdot_fast(P_MIN_MW) >= target:
        return P_MIN_MW
    lo, hi = P_MIN_MW, P_RATED_MW
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if mdot_fast(mid) < target else (lo, mid)
    return hi


def _constant_schedule(demand_kg):
    return [_const_setpoint(demand_kg)] * HOURS


def _greedy_schedule(demand_kg):
    sched, made = [0.0] * HOURS, 0.0
    for h in range(HOURS):
        remaining = demand_kg - made
        if remaining <= 0:
            break
        if mdot_fast(P_RATED_MW) <= remaining:
            sched[h] = P_RATED_MW
        else:
            lo, hi = P_MIN_MW, P_RATED_MW
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if mdot_fast(mid) < remaining else (lo, mid)
            sched[h] = hi
        made += mdot_fast(sched[h])
    return sched


def _cost_per_kg(hourly, pv):
    r = evaluate_day(hourly, pv)
    return (r["total_cost_da"] / r["total_h2_kg"]) if r["total_h2_kg"] > 0 else 0.0


@st.cache_data(show_spinner=False)
def _baseline_curves(day_name, demands):
    pv = load_days()[day_name]["pv_mw"]
    const = [_cost_per_kg(_constant_schedule(d), pv) for d in demands]
    greedy = [_cost_per_kg(_greedy_schedule(d), pv) for d in demands]
    return const, greedy


@st.cache_data(show_spinner=False)
def _optimized_curve(day_name, demands):
    return [run_optimization(day_name, int(d))["cost_per_kg_da"] for d in demands]


def render():
    section("Smart vs Traditional Dispatch",
            "Same hydrogen, same day, same tariff — the cost of intelligent timing "
            "versus constant baseload and greedy produce-ASAP operation.")

    c_day, c_dem = st.columns([1.4, 1.6])
    with c_day:
        day_name = st.selectbox("Representative day", options=DAY_KEYS,
                                format_func=lambda k: DAY_LABELS[k], key="base_day")
    with c_dem:
        demand_kg = st.slider("Highlighted demand (kg/day)", 60, 340, 200, 20,
                              key="base_demand")

    demands = list(range(60, 341, 20))
    const, greedy = _baseline_curves(day_name, tuple(demands))
    pv = load_days()[day_name]["pv_mw"]

    # selected-demand bars (optimized is a single cached PSO run)
    c_opt = run_optimization(day_name, demand_kg)["cost_per_kg_da"]
    c_con = _cost_per_kg(_constant_schedule(demand_kg), pv)
    c_grd = _cost_per_kg(_greedy_schedule(demand_kg), pv)
    save_con = 100.0 * (c_con - c_opt) / c_con if c_con > 0 else 0.0
    save_grd = 100.0 * (c_grd - c_opt) / c_grd if c_grd > 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Optimized (smart)", f"{c_opt:.1f} DA/kg")
    c2.metric("vs constant baseload", f"{c_con:.1f} DA/kg",
              delta=f"−{save_con:.0f}% with smart", delta_color="inverse")
    c3.metric("vs greedy produce-ASAP", f"{c_grd:.1f} DA/kg",
              delta=f"−{save_grd:.0f}% with smart", delta_color="inverse")

    # ── cost-vs-demand curve ────────────────────────────────────────────────────
    show_opt = st.checkbox("Compute full smart curve (slow — PSO at every demand)",
                           value=False, key="base_full")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=demands, y=const, mode="lines+markers",
                             name="Constant baseload [DA/kg]  (traditional)",
                             line=dict(color="#dc2626", width=2.5, dash="dash"),
                             marker=dict(size=7, symbol="square"),
                             hovertemplate="%{x} kg: %{y:.1f} DA/kg<extra></extra>"))
    fig.add_trace(go.Scatter(x=demands, y=greedy, mode="lines+markers",
                             name="Greedy produce-ASAP [DA/kg]",
                             line=dict(color="#ea580c", width=2.5, dash="dot"),
                             marker=dict(size=7, symbol="triangle-up"),
                             hovertemplate="%{x} kg: %{y:.1f} DA/kg<extra></extra>"))
    if show_opt:
        with st.spinner("Optimizing across the demand sweep…"):
            opt = _optimized_curve(day_name, tuple(demands))
        fig.add_trace(go.Scatter(x=demands, y=opt, mode="lines+markers",
                                 name="Optimized — smart dispatch [DA/kg]",
                                 line=dict(color="#1d4ed8", width=3.5),
                                 marker=dict(size=8),
                                 hovertemplate="%{x} kg: %{y:.1f} DA/kg<extra></extra>"))
    else:
        fig.add_trace(go.Scatter(x=[demand_kg], y=[c_opt], mode="markers",
                                 name="Optimized — smart (selected demand) [DA/kg]",
                                 marker=dict(color="#1d4ed8", size=16,
                                             symbol="star",
                                             line=dict(color="#1e3a8a", width=1.5))))
    fig.add_vline(x=demand_kg, line_width=1.5, line_dash="dot", line_color="#64748b")
    fig.update_layout(
        font=FONT,
        title=dict(text=f"Cost per kg vs daily demand — {DAY_LABELS[day_name]} "
                        f"({load_days()[day_name]['date']})",
                   font=dict(size=13, color=BLACK)),
        xaxis=dict(title=dict(text="Daily H₂ demand [kg/day]", font=AXIS_TITLE_FONT),
                   tickfont=dict(color=BLACK)),
        yaxis=dict(title=dict(text="Cost [DA/kg]", font=AXIS_TITLE_FONT),
                   gridcolor="#e5e7eb", tickfont=dict(color=BLACK)),
        legend=LEGEND_STYLE,
        hovermode="x unified", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=440, margin=dict(t=90, b=50))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Smart dispatch rides free midday solar and dodges the 17–21 h peak. "
               "At low demand it can be fully solar-covered (100 % cheaper); greedy "
               "degrades worst as demand rises and it is forced into peak hours.")
