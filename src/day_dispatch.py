"""Demand-driven least-cost daily dispatch (real-data, 15-min accounting).

One objective, no mode toggle: **meet a daily hydrogen demand [kg/day] at least
grid cost**, choosing the electrolyzer setpoint each HOUR (24 decisions). All
energy / cost / H2 accounting runs at the native **15-minute** resolution of the
real PySAM PV series (4 sub-steps per hour). Hourly decisions keep the PSO
low-dimensional and reproducible; 15-minute accounting keeps the numbers exact.

PV: real PySAM/CAMS generation (src.pv_pysam). Tariff: CREG time-of-use
(src.economics). Network feasibility (validated vs ETAP): checked on the optimal
schedule with the pandapower load flow (non-binding in this topology, so
verifying the optimum is exact).

Run the demo with:  python -m src.day_dispatch
"""

import numpy as np
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize as pymoo_minimize

from src.economics import grid_price_da_per_kwh
from src.network.grid_model import build_network, run_case
from src.physics.electrolyzer_model import P_MIN_MW, P_RATED_MW, mdot_h2_kg_per_h

HOURS = 24
STEPS_PER_HOUR = 4
STEPS = HOURS * STEPS_PER_HOUR    # 96 fifteen-minute steps per day
STEP_H = 0.25                     # hours per step

SHORTFALL_PENALTY_DA_PER_KG = 1.0e7   # dominates cost so demand is met first
DEMAND_TOL_KG = 1e-6

# Time-of-use price per local hour, expanded to the 96 fifteen-minute steps.
_PRICE_BY_HOUR = np.array([grid_price_da_per_kwh(h) for h in range(HOURS)])
_PRICE_BY_STEP = _PRICE_BY_HOUR[np.arange(STEPS) // STEPS_PER_HOUR]

# Fast H2 lookup built once from the exact electrolyzer model (brentq per call).
_P_TABLE = np.concatenate(([0.0], np.linspace(P_MIN_MW, P_RATED_MW, 256)))
_MDOT_TABLE = np.array([0.0] + [mdot_h2_kg_per_h(p) for p in _P_TABLE[1:]])


def _repair_hourly(hourly_setpoints):
    """Snap each hourly setpoint to the domain {0} U [P_MIN, P_RATED] MW."""
    a = np.asarray(hourly_setpoints, dtype=float)
    return np.where(a < P_MIN_MW, 0.0, np.minimum(a, P_RATED_MW))


def mdot_fast(p_mw):
    """Interpolated H2 rate [kg/h] for a setpoint (fast lookup of the exact model)."""
    return float(np.interp(p_mw, _P_TABLE, _MDOT_TABLE))


def evaluate_day(hourly_setpoints, pv_15min):
    """Cost and hydrogen for 24 hourly setpoints over a 96-step PV day (exact).

    Args:
        hourly_setpoints: length-24 electrolyzer setpoints [MW] (repaired here).
        pv_15min: length-96 PV availability [MW] (local time, from PySAM).

    Returns:
        dict with daily totals and per-step (length-96) breakdown:
            hourly_setpoints (24), setpoints (96), pv_mw, grid_p_mw, h2_kg,
            cost_da, total_h2_kg, total_cost_da.
    """
    sp_h = _repair_hourly(hourly_setpoints)
    sp = np.repeat(sp_h, STEPS_PER_HOUR)                 # constant within the hour
    pv = np.asarray(pv_15min, dtype=float)
    h2 = np.interp(sp, _P_TABLE, _MDOT_TABLE) * STEP_H   # kg produced per step
    grid = sp - pv                                       # MW, +import / -export
    cost = _PRICE_BY_STEP * np.clip(grid, 0.0, None) * 1000.0 * STEP_H   # DA
    return {
        "hourly_setpoints": sp_h,
        "setpoints": sp,
        "pv_mw": pv,
        "grid_p_mw": grid,
        "h2_kg": h2,
        "cost_da": cost,
        "total_h2_kg": float(h2.sum()),
        "total_cost_da": float(cost.sum()),
    }


class _DayProblem(ElementwiseProblem):
    """24-hour setpoint schedule minimizing grid cost subject to a daily demand."""

    def __init__(self, pv_15min, demand_kg):
        super().__init__(n_var=HOURS, n_obj=1,
                         xl=np.zeros(HOURS), xu=np.full(HOURS, P_RATED_MW))
        self._pv = np.asarray(pv_15min, dtype=float)
        self._demand = demand_kg

    def _evaluate(self, x, out, *args, **kwargs):
        res = evaluate_day(x, self._pv)
        shortfall = max(0.0, self._demand - res["total_h2_kg"])
        out["F"] = res["total_cost_da"] + SHORTFALL_PENALTY_DA_PER_KG * shortfall


def optimize_day(pv_15min, demand_kg, seed=0, pop_size=60, n_gen=300):
    """Least-cost 24-hour schedule producing >= demand_kg over the PV day.

    Returns the evaluate_day result at the optimum plus demand_kg, demand_met,
    shortfall_kg, cost_per_kg_da, n_evaluations.
    """
    res = pymoo_minimize(_DayProblem(pv_15min, demand_kg), PSO(pop_size=pop_size),
                         ("n_gen", n_gen), seed=seed, verbose=False)
    best = evaluate_day(np.atleast_1d(res.X), pv_15min)
    shortfall = max(0.0, demand_kg - best["total_h2_kg"])
    best.update(
        demand_kg=demand_kg,
        demand_met=shortfall <= DEMAND_TOL_KG,
        shortfall_kg=shortfall,
        cost_per_kg_da=(best["total_cost_da"] / best["total_h2_kg"]
                        if best["total_h2_kg"] > 0 else 0.0),
        n_evaluations=int(res.algorithm.evaluator.n_eval),
    )
    return best


def verify_day_feasibility(hourly_setpoints, pv_15min):
    """Run the validated pandapower load flow on every 15-min step of a schedule.

    Returns a list of (step, v_secondary_pu, loading_pct) for any step outside
    the ETAP limits (0.95-1.05 pu, loading <= 100 %) — empty when all 96 pass.
    """
    sp = np.repeat(_repair_hourly(hourly_setpoints), STEPS_PER_HOUR)
    pv = np.asarray(pv_15min, dtype=float)
    net = build_network()
    violations = []
    for s in range(STEPS):
        p = float(sp[s])
        on = p > 0.0
        case = run_case(net, pv_mw=float(pv[s]), ely_in_service=on,
                        ely_p_mw=p if on else None)
        v = case["v_secondary_pu"]
        loading = case["trafo_loading_percent"]
        if not (0.95 <= v <= 1.05) or loading > 100.0 or not case["converged"]:
            violations.append((s, round(v, 4), round(loading, 1)))
    return violations


if __name__ == "__main__":
    from pymoo.config import Config

    from src.pv_pysam import representative_days

    Config.warnings["not_compiled"] = False

    prof = representative_days()["clear_summer"]
    demand = 200.0
    print(f"clear_summer {prof['date']} (PV energy {prof['energy_mwh']:.2f} MWh) "
          f"— demand {demand:.0f} kg/day\n")

    out = optimize_day(prof["pv_mw"], demand, seed=0)
    print(f"  produced {out['total_h2_kg']:.1f} kg "
          f"(demand met: {out['demand_met']}, shortfall {out['shortfall_kg']:.3f})")
    print(f"  grid cost {out['total_cost_da']:.0f} DA -> "
          f"{out['cost_per_kg_da']:.1f} DA/kg  ({out['n_evaluations']} evals)\n")

    sp_h = out["hourly_setpoints"]
    pv_h = out["pv_mw"].reshape(HOURS, STEPS_PER_HOUR).mean(axis=1)
    print(f"  {'h':>2} {'price':>6} {'PV':>6} {'set':>6}")
    for h in range(HOURS):
        print(f"  {h:02d} {_PRICE_BY_HOUR[h]:>6.2f} {pv_h[h]:>6.3f} {sp_h[h]:>6.3f}")

    viol = verify_day_feasibility(sp_h, prof["pv_mw"])
    print(f"\n  network feasibility: "
          f"{'all 96 steps within limits' if not viol else viol[:5]}")
