"""Tab 1 — Daily Dispatch.

Runs on real Ghardaïa 2023 PV (CAMS→PySAM, 15-min) straight from the dataset.
Pick either one of the three representative days or any specific calendar date in
2023, set an H2 demand, and run the PSO optimizer to inspect the least-cost
24-hour schedule. Optional battery (Stage 2): PSO over setpoints with LP-optimal
storage, overlaying the SOC trajectory.
"""

import datetime

import numpy as np
import streamlit as st

from app._shared import (
    DAY_KEYS, DAY_LABELS, HOURS, STEP_H, STEPS_PER_HOUR,
    all_days, band_name, dispatch_figure, hourly_setpoints_of, load_days,
    run_feasibility_date, run_optimization_battery_date, run_optimization_date,
    solar_metrics,
)
from app._theme import section


def render():
    section("Least-Cost Daily Dispatch",
            "Pick any real 2023 day and an H₂ demand — the PSO finds the cheapest "
            "24-hour schedule, validated on the ETAP network. Add storage to shift "
            "production into cheaper hours.")

    days = all_days()                         # every full real day {iso: {...}}
    iso_dates = sorted(days.keys())
    d_min = datetime.date.fromisoformat(iso_dates[0])
    d_max = datetime.date.fromisoformat(iso_dates[-1])

    # ── controls ────────────────────────────────────────────────────────────────
    c_src, c_dem, c_bat = st.columns([1.7, 1.4, 1.6])
    with c_src:
        source = st.radio("PV day (real Ghardaïa 2023 dataset)",
                          ["Representative", "Any date"], horizontal=True,
                          key="daily_src")
        if source == "Representative":
            key = st.selectbox("Representative day", options=DAY_KEYS,
                               format_func=lambda k: DAY_LABELS[k], key="daily_day")
            date_str = load_days()[key]["date"]
            day_label = DAY_LABELS[key]
        else:
            default = datetime.date.fromisoformat(load_days()["clear_summer"]["date"])
            picked = st.date_input("Calendar date (2023)", value=default,
                                   min_value=d_min, max_value=d_max, key="daily_date")
            date_str = picked.isoformat()
            day_label = picked.strftime("%a %d %b %Y")
    with c_dem:
        demand_kg = st.slider("Daily H₂ demand (kg/day)", 40, 340, 200, 10,
                              key="daily_demand")
    with c_bat:
        use_battery = st.toggle("Add battery storage", value=False, key="daily_batt")
        capacity_mwh = st.slider("Battery capacity (MWh)", 0.0, 8.0, 2.0, 0.5,
                                 key="daily_cap", disabled=not use_battery)

    if date_str not in days:
        st.warning(f"{date_str} has incomplete PV data in the dataset (not a full "
                   "96-step day). Pick another date.")
        return

    run_clicked = st.button("Run Optimization", type="primary", key="daily_run")

    # Recompute on click or when inputs change since the last run
    params = (date_str, demand_kg, use_battery, capacity_mwh if use_battery else None)
    if run_clicked or st.session_state.get("daily_last") != params:
        with st.spinner("Running PSO optimizer on real PV — please wait…"):
            if use_battery and capacity_mwh > 0:
                result = run_optimization_battery_date(date_str, demand_kg, capacity_mwh)
            else:
                result = run_optimization_date(date_str, demand_kg)
            violations = run_feasibility_date(
                date_str, tuple(np.round(hourly_setpoints_of(result), 6)))
        st.session_state["daily_result"]    = result
        st.session_state["daily_viol"]      = violations
        st.session_state["daily_label"]     = day_label
        st.session_state["daily_shown_iso"] = date_str
        st.session_state["daily_last"]      = params

    if "daily_result" not in st.session_state:
        st.info("Pick a real PV day above and click **Run Optimization**.")
        return

    result     = st.session_state["daily_result"]
    violations = st.session_state["daily_viol"]
    shown_date = st.session_state["daily_shown_iso"]
    shown_label = st.session_state["daily_label"]
    day_info   = days[shown_date]
    has_batt   = "batt_mw" in result

    # ── KPI row ─────────────────────────────────────────────────────────────────
    frac, _ = solar_metrics(result)
    cols = st.columns(6 if has_batt else 5)
    cols[0].metric("H₂ Produced",  f"{result['total_h2_kg']:.1f} kg")
    cols[1].metric("Demand met",   "Yes" if result["demand_met"] else "No")
    cols[2].metric("Grid Cost",    f"{result['total_cost_da']:,.0f} DA")
    cols[3].metric("Cost per kg",  f"{result['cost_per_kg_da']:.1f} DA/kg")
    cols[4].metric("Solar Fraction", f"{frac:.1f} %")
    if has_batt:
        peak_soc = float(np.asarray(result["soc_mwh"]).max())
        cols[5].metric("Peak SOC", f"{peak_soc:.2f} MWh")

    # ── dispatch chart ──────────────────────────────────────────────────────────
    title = (f"{shown_label}  ·  {day_info['date']}  ·  "
             f"demand {demand_kg} kg/day  ·  real PV energy "
             f"{day_info['energy_mwh']:.2f} MWh"
             + ("  ·  battery on" if has_batt else ""))
    st.plotly_chart(dispatch_figure(result, title=title, show_battery=has_batt),
                    use_container_width=True)

    # ── network feasibility ─────────────────────────────────────────────────────
    st.markdown("**Network feasibility (pandapower · ETAP-validated)**")
    if not violations:
        st.success("All 96 steps within ETAP limits — "
                   "voltage 0.95–1.05 pu, transformer loading ≤ 100 %")
    else:
        st.warning(f"{len(violations)} step(s) outside limits. First shown below.")
        st.dataframe(
            [{"Step": s, "Time": f"{s * STEP_H:.2f} h",
              "V_secondary [pu]": f"{v:.4f}", "Trafo loading [%]": f"{load:.1f}"}
             for s, v, load in violations[:10]],
            use_container_width=True)
    if has_batt:
        st.caption("Feasibility checks the electrolyzer load + PV on the validated "
                   "network; the battery is dispatched behind the meter (LP-optimal).")

    # ── hourly schedule table ───────────────────────────────────────────────────
    with st.expander("Hourly schedule detail"):
        sp_h   = hourly_setpoints_of(result)
        pv     = np.asarray(result["pv_mw"])
        grid   = np.asarray(result["grid_p_mw"])
        pv_h   = pv.reshape(HOURS, STEPS_PER_HOUR).mean(axis=1)
        grid_h = grid.reshape(HOURS, STEPS_PER_HOUR).mean(axis=1)
        h2_h   = np.asarray(result["h2_kg"]).reshape(HOURS, STEPS_PER_HOUR).sum(axis=1)
        cost_arr = np.asarray(result["cost_da"])
        has_cost_series = cost_arr.ndim == 1 and cost_arr.size == pv.size
        cost_h = (cost_arr.reshape(HOURS, STEPS_PER_HOUR).sum(axis=1)
                  if has_cost_series else None)

        rows = []
        for h in range(HOURS):
            row = {"Hour": f"{h:02d}:00", "Tariff band": band_name(h),
                   "PV avail [MW]": f"{pv_h[h]:.3f}",
                   "Setpoint [MW]": f"{sp_h[h]:.3f}",
                   "Grid [MW]": f"{grid_h[h]:+.3f}",
                   "H₂ [kg]": f"{h2_h[h]:.2f}"}
            if has_cost_series:
                row["Cost [DA]"] = f"{cost_h[h]:.1f}"
            rows.append(row)
        st.dataframe(rows, use_container_width=True, height=350)
