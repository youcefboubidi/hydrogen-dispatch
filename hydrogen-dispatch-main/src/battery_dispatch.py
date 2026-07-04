"""Battery-augmented least-cost dispatch (Stage 2) — PSO + optimal-LP storage.

Architecture (chosen for reliability and defensibility):
  * PSO searches only the 24 hourly **electrolyzer setpoints** — low-dimensional,
    reproducible, the part with the non-linear H2 curve and the demand constraint.
  * For each candidate setpoint schedule, the **battery is operated optimally**
    by a linear program (scipy HiGHS): given the net load (setpoint − PV) at each
    15-min step and the time-of-use price, the LP finds the charge/discharge/SOC
    trajectory that minimizes grid cost, subject to power and energy limits and a
    start-empty state of charge.

This decomposition avoids the unreliable high-dimensional PSO of a joint
setpoint+battery search: the storage operation is provably optimal per candidate,
so the sizing curve is naturally monotone and the results are reproducible. The
battery arbitrages the tariff (charge on cheap night power / surplus solar,
discharge through the 8.11 DA peak) and shifts production into cheaper hours.

Run the demo with:  python -m src.battery_dispatch
"""

from dataclasses import dataclass

import numpy as np
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize as pymoo_minimize
from scipy.optimize import linprog

from src.day_dispatch import (HOURS, P_MIN_MW, P_RATED_MW, STEP_H, STEPS,
                              STEPS_PER_HOUR, _MDOT_TABLE, _P_TABLE,
                              _PRICE_BY_STEP, _repair_hourly)

SHORTFALL_PENALTY_DA_PER_KG = 1.0e7
DEMAND_TOL_KG = 1e-6


@dataclass(frozen=True)
class Battery:
    """Battery energy store. eff is the one-way efficiency (round-trip = eff²)."""
    capacity_mwh: float
    power_mw: float
    eff: float = 0.9487            # ≈ sqrt(0.90) round-trip

    @staticmethod
    def from_hours(capacity_mwh, hours=4.0, round_trip=0.90):
        return Battery(capacity_mwh=capacity_mwh,
                       power_mw=capacity_mwh / hours,
                       eff=round_trip ** 0.5)


def _build_lp(battery):
    """Prebuild the constant LP pieces for a battery (only the net-load RHS varies).

    Variables (length 3*STEPS): charge c[t]>=0, discharge d[t]>=0, import g[t]>=0.
    Minimize  sum price[t]*g[t]*dt.
    Subject to (all 15-min steps t, SOC starts empty):
      import:    c[t] - d[t] - g[t] <= -net_load[t]        (g >= net_load + c - d)
      SOC<=cap:  cumsum(eff*c - d/eff)*dt <= capacity
      SOC>=0:   -cumsum(eff*c - d/eff)*dt <= 0
      0<=c,d<=P ; g>=0
    """
    n = STEPS
    P, cap, eff = battery.power_mw, battery.capacity_mwh, battery.eff
    obj = np.zeros(3 * n)
    obj[2 * n:] = _PRICE_BY_STEP * 1000.0 * STEP_H      # cost of import [DA per MW-step]

    A_imp = np.zeros((n, 3 * n))
    A_imp[np.arange(n), np.arange(n)] = 1.0             # +c
    A_imp[np.arange(n), n + np.arange(n)] = -1.0        # -d
    A_imp[np.arange(n), 2 * n + np.arange(n)] = -1.0    # -g

    tril = np.tril(np.ones((n, n)))
    soc = np.zeros((n, 3 * n))
    soc[:, :n] = tril * (eff * STEP_H)
    soc[:, n:2 * n] = tril * (-STEP_H / eff)

    A_ub = np.vstack([A_imp, soc, -soc])
    bounds = [(0, P)] * n + [(0, P)] * n + [(0, None)] * n
    return {"obj": obj, "A_ub": A_ub, "cap": cap, "n": n,
            "soc_rows": soc[:, :2 * n], "bounds": bounds}


def optimal_battery_operation(net_load, lp):
    """Solve the storage LP for a given net-load profile. Returns (g, c, d, cost)."""
    n = lp["n"]
    b_ub = np.concatenate([-np.asarray(net_load),
                           np.full(n, lp["cap"]),
                           np.zeros(n)])
    res = linprog(lp["obj"], A_ub=lp["A_ub"], b_ub=b_ub, bounds=lp["bounds"],
                  method="highs")
    if not res.success:
        return None
    x = res.x
    return x[2 * n:], x[:n], x[n:2 * n], float(res.fun)


def evaluate_day_battery(setpoints_hourly, pv_15min, battery, lp=None):
    """Cost / H2 / battery operation for an hourly setpoint schedule (LP-optimal storage)."""
    if lp is None:
        lp = _build_lp(battery)
    sp = np.repeat(_repair_hourly(setpoints_hourly), STEPS_PER_HOUR)
    pv = np.asarray(pv_15min, dtype=float)
    net_load = sp - pv
    g, c, d, cost = optimal_battery_operation(net_load, lp)
    soc = np.cumsum(battery.eff * c - d / battery.eff) * STEP_H
    h2 = np.interp(sp, _P_TABLE, _MDOT_TABLE) * STEP_H
    return {
        "setpoints": sp, "pv_mw": pv, "batt_mw": d - c, "soc_mwh": soc,
        "grid_p_mw": sp - pv - (d - c), "import_mw": g,
        "h2_kg": h2, "cost_da": cost,
        "total_h2_kg": float(h2.sum()), "total_cost_da": float(cost),
    }


class _SetpointProblem(ElementwiseProblem):
    """PSO over 24 hourly setpoints; battery operated optimally by LP per candidate."""

    def __init__(self, pv_15min, demand_kg, battery, lp):
        super().__init__(n_var=HOURS, n_obj=1,
                         xl=np.zeros(HOURS), xu=np.full(HOURS, P_RATED_MW))
        self._pv = np.asarray(pv_15min, dtype=float)
        self._demand = demand_kg
        self._batt = battery
        self._lp = lp

    def _evaluate(self, x, out, *args, **kwargs):
        res = evaluate_day_battery(x, self._pv, self._batt, self._lp)
        shortfall = max(0.0, self._demand - res["total_h2_kg"])
        out["F"] = res["total_cost_da"] + SHORTFALL_PENALTY_DA_PER_KG * shortfall


def optimize_day_battery(pv_15min, demand_kg, battery, seeds=(0, 1),
                         pop_size=40, n_gen=150):
    """Least-cost dispatch with a battery: PSO over setpoints, LP-optimal storage."""
    lp = _build_lp(battery)
    problem = _SetpointProblem(pv_15min, demand_kg, battery, lp)
    best_x, best_f, n_eval = None, np.inf, 0
    for sd in seeds:
        res = pymoo_minimize(problem, PSO(pop_size=pop_size), ("n_gen", n_gen),
                             seed=sd, verbose=False)
        n_eval += int(res.algorithm.evaluator.n_eval)
        f = float(np.atleast_1d(res.F)[0])
        if f < best_f:
            best_f, best_x = f, np.atleast_1d(res.X)

    best = evaluate_day_battery(best_x, pv_15min, battery, lp)
    shortfall = max(0.0, demand_kg - best["total_h2_kg"])
    best.update(
        demand_kg=demand_kg,
        demand_met=shortfall <= DEMAND_TOL_KG,
        shortfall_kg=shortfall,
        cost_per_kg_da=(best["total_cost_da"] / best["total_h2_kg"]
                        if best["total_h2_kg"] > 0 else 0.0),
        n_evaluations=n_eval,
    )
    return best


if __name__ == "__main__":
    from pymoo.config import Config

    from src.day_dispatch import optimize_day
    from src.pv_data import representative_days

    Config.warnings["not_compiled"] = False

    prof = representative_days()["clear_summer"]
    demand = 280.0
    print(f"clear_summer {prof['date']} — demand {demand:.0f} kg/day\n")

    base = optimize_day(prof["pv_mw"], demand, seed=0)
    print(f"  no battery     : {base['cost_per_kg_da']:6.2f} DA/kg  "
          f"(cost {base['total_cost_da']:.0f} DA, met={base['demand_met']})")

    for cap in (1.0, 2.0, 4.0):
        batt = Battery.from_hours(cap, hours=4.0)
        out = optimize_day_battery(prof["pv_mw"], demand, batt)
        saved = 100 * (base["total_cost_da"] - out["total_cost_da"]) / base["total_cost_da"]
        print(f"  battery {cap:.0f} MWh  : {out['cost_per_kg_da']:6.2f} DA/kg  "
              f"(cost {out['total_cost_da']:.0f} DA, met={out['demand_met']}, "
              f"SOC max {out['soc_mwh'].max():.2f}/{cap:.0f} MWh, saves {saved:.1f}%)")
