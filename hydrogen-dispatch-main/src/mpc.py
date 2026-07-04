"""Model-Predictive (receding-horizon) supervisory controller (control core).

The dispatch problem cast as feedback control. Three controllers are compared:

  * perfect_foresight  — open-loop optimum, full knowledge of the day's PV (the
    unreachable lower bound on cost).
  * mpc                — receding-horizon controller: each hour it (i) measures
    the realized PV/production so far, (ii) forecasts the rest of the day
    (day-ahead persistence — yesterday's profile — corrected intraday by the
    realized clearness), (iii) re-optimizes the remaining setpoints to meet the
    remaining demand at least cost, and (iv) applies only the current hour. The
    next hour the *actual* PV is realized (a disturbance vs the forecast) and it
    re-plans. Closed-loop.
  * rule_based         — reactive, time-blind: hold a constant production rate
    that meets the daily demand, using PV first (no foresight, no price awareness).

The control result: MPC recovers most of the perfect-foresight optimum despite
forecast error, and beats the reactive rule — i.e. it rejects the PV disturbance.
The inner optimization reuses the validated economics/electrolyzer model.

Run the comparison with:  python -m src.mpc
"""

import numpy as np
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize as pymoo_minimize

from src.day_dispatch import (HOURS, P_RATED_MW, STEP_H, STEPS_PER_HOUR,
                              _MDOT_TABLE, _P_TABLE, _PRICE_BY_HOUR,
                              _repair_hourly, mdot_fast)
from src.pv_data import STEPS_PER_DAY, load_pv_mw

SHORTFALL_PENALTY = 1.0e7


def _evaluate_horizon(setpoints_h, pv_steps, price_hours):
    """Cost + H2 for `m` hourly setpoints over an m-hour (4m-step) horizon."""
    sp_h = _repair_hourly(setpoints_h)
    sp = np.repeat(sp_h, STEPS_PER_HOUR)
    price_steps = np.repeat(price_hours, STEPS_PER_HOUR)
    h2 = np.interp(sp, _P_TABLE, _MDOT_TABLE) * STEP_H
    grid = sp - pv_steps
    cost = price_steps * np.clip(grid, 0.0, None) * 1000.0 * STEP_H
    return sp_h, float(h2.sum()), float(cost.sum())


class _HorizonProblem(ElementwiseProblem):
    def __init__(self, pv_steps, price_hours, demand_remaining):
        m = len(price_hours)
        super().__init__(n_var=m, n_obj=1, xl=np.zeros(m), xu=np.full(m, P_RATED_MW))
        self._pv, self._price, self._dr = pv_steps, price_hours, demand_remaining

    def _evaluate(self, x, out, *a, **k):
        _, h2, cost = _evaluate_horizon(x, self._pv, self._price)
        out["F"] = cost + SHORTFALL_PENALTY * max(0.0, self._dr - h2)


def optimize_horizon(pv_steps, price_hours, demand_remaining, seed=0,
                     pop_size=40, n_gen=120):
    """Least-cost hourly setpoints over a horizon meeting the remaining demand."""
    m = len(price_hours)
    if demand_remaining <= 1e-9:
        return np.zeros(m)
    res = pymoo_minimize(_HorizonProblem(pv_steps, price_hours, demand_remaining),
                         PSO(pop_size=pop_size), ("n_gen", n_gen),
                         seed=seed, verbose=False)
    return _repair_hourly(np.atleast_1d(res.X))


def _hourly_energy(pv_96):
    """Per-hour PV energy [MWh] from a 96-step profile (for clearness scaling)."""
    return pv_96.reshape(HOURS, STEPS_PER_HOUR).sum(axis=1) * STEP_H


def mpc_dispatch(pv_actual_96, pv_forecast_96, demand_kg, seed=0):
    """Receding-horizon control over one day. Returns realized result dict."""
    realized_sp = np.zeros(HOURS)
    realized_cost = realized_h2 = 0.0
    fc_e = _hourly_energy(pv_forecast_96)            # forecast (yesterday) hourly energy
    ac_e = _hourly_energy(pv_actual_96)              # realized hourly energy

    for k in range(HOURS):
        remaining = demand_kg - realized_h2
        # Horizon PV: actual for the current hour (measured), forecast ahead,
        # corrected by the clearness realized so far today vs the forecast.
        if k > 0 and fc_e[:k].sum() > 1e-6:
            clearness = min(2.0, max(0.0, ac_e[:k].sum() / fc_e[:k].sum()))
        else:
            clearness = 1.0
        pv_horizon = np.concatenate([
            pv_actual_96[k * STEPS_PER_HOUR:(k + 1) * STEPS_PER_HOUR],
            pv_forecast_96[(k + 1) * STEPS_PER_HOUR:] * clearness,
        ])
        prices = _PRICE_BY_HOUR[k:]
        sp_h = optimize_horizon(pv_horizon, prices, remaining, seed=seed)

        # Apply only hour k; realize against the ACTUAL PV.
        sp_k = float(sp_h[0])
        realized_sp[k] = sp_k
        actual_k = pv_actual_96[k * STEPS_PER_HOUR:(k + 1) * STEPS_PER_HOUR]
        realized_h2 += mdot_fast(sp_k) * 1.0
        grid_k = sp_k - actual_k
        realized_cost += float(_PRICE_BY_HOUR[k] * np.clip(grid_k, 0.0, None).sum()
                               * 1000.0 * STEP_H)

    return {
        "controller": "mpc",
        "hourly_setpoints": realized_sp,
        "total_h2_kg": realized_h2,
        "total_cost_da": realized_cost,
        "cost_per_kg_da": realized_cost / realized_h2 if realized_h2 > 0 else 0.0,
        "demand_met": realized_h2 >= demand_kg - 1e-3,
    }


def rule_based_dispatch(pv_actual_96, demand_kg):
    """Reactive, time-blind: constant production rate meeting demand, PV-first."""
    target = demand_kg / HOURS                       # kg per hour
    lo, hi = 0.0, P_RATED_MW
    for _ in range(60):                              # power for the per-hour target
        mid = 0.5 * (lo + hi)
        if mdot_fast(mid) < target:
            lo = mid
        else:
            hi = mid
    sp_h = np.full(HOURS, hi)
    sp = np.repeat(sp_h, STEPS_PER_HOUR)
    grid = sp - pv_actual_96
    cost = float((np.repeat(_PRICE_BY_HOUR, STEPS_PER_HOUR)
                  * np.clip(grid, 0.0, None) * 1000.0 * STEP_H).sum())
    h2 = float(np.interp(sp, _P_TABLE, _MDOT_TABLE).sum() * STEP_H)
    return {"controller": "rule_based", "hourly_setpoints": sp_h,
            "total_h2_kg": h2, "total_cost_da": cost,
            "cost_per_kg_da": cost / h2 if h2 > 0 else 0.0,
            "demand_met": h2 >= demand_kg - 1e-3}


def consecutive_days(min_pairs=1):
    """Yield (date, today_pv_96, yesterday_pv_96) for full local days with a predecessor."""
    s = load_pv_mw()
    df = {}
    import pandas as pd
    d = pd.DataFrame({"pv": s.to_numpy()}, index=s.index)
    d["date"] = d.index.date
    counts = d.groupby("date")["pv"].count()
    full = [dt for dt, c in counts.items() if c == STEPS_PER_DAY]
    full.sort()
    out = []
    for i in range(1, len(full)):
        today = d[d["date"] == full[i]].sort_index()["pv"].to_numpy()
        prev = d[d["date"] == full[i - 1]].sort_index()["pv"].to_numpy()
        out.append((str(full[i]), today, prev))
    return out


if __name__ == "__main__":
    from pymoo.config import Config

    from src.day_dispatch import optimize_day
    Config.warnings["not_compiled"] = False

    days = consecutive_days()
    # a cloudy day preceded by a clearer one => meaningful forecast error
    demand = 200.0
    # pick a day with a large day-to-day PV energy change
    pick = max(days[:120], key=lambda t: abs(t[1].sum() - t[2].sum()))
    date, today, prev = pick
    print(f"day {date} (today {today.sum()*STEP_H:.2f} MWh, "
          f"yesterday {prev.sum()*STEP_H:.2f} MWh) — demand {demand:.0f} kg/day\n")

    pf = optimize_day(today, demand, seed=0)
    mpc = mpc_dispatch(today, prev, demand, seed=0)
    rb = rule_based_dispatch(today, demand)
    print(f"  perfect-foresight (bound): {pf['cost_per_kg_da']:6.2f} DA/kg "
          f"(cost {pf['total_cost_da']:.0f}, met {pf['demand_met']})")
    print(f"  MPC (forecast, closed-loop): {mpc['cost_per_kg_da']:6.2f} DA/kg "
          f"(cost {mpc['total_cost_da']:.0f}, met {mpc['demand_met']})")
    print(f"  rule-based (reactive):       {rb['cost_per_kg_da']:6.2f} DA/kg "
          f"(cost {rb['total_cost_da']:.0f}, met {rb['demand_met']})")
    gap = 100 * (mpc["total_cost_da"] - pf["total_cost_da"]) / pf["total_cost_da"]
    edge = 100 * (rb["total_cost_da"] - mpc["total_cost_da"]) / rb["total_cost_da"]
    print(f"\n  MPC gap to optimum: {gap:+.1f}%   |   MPC vs rule-based: {edge:.1f}% cheaper")
