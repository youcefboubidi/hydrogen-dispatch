"""Demand-driven least-cost daily dispatch (Stage 1) — replaces the mode toggle.

One objective, no mode: **meet a hydrogen demand [kg/day] at minimum grid cost**
over a representative day, by choosing the electrolyzer setpoint each hour. PSO
optimizes the 24-hour setpoint vector against the real CREG time-of-use tariff,
so the intelligent behaviour (run on free solar and cheap night power, dodge the
17:00-21:00 peak) emerges from the prices rather than from a hand-picked mode.

Separation of concerns, on purpose:
  * Economics (cost, H2) are exact arithmetic — the PV model, the electrolyzer
    Faraday law, and the time-of-use price. No load flow in the PSO inner loop,
    so a full optimization is sub-second.
  * Network feasibility (the ETAP-validated limits) is checked on the OPTIMAL
    schedule with the pandapower load flow (verify_day_feasibility). In this
    2-bus topology the limits never bind, so verifying the optimum is exact, not
    an approximation; Stage 3 (a network sized to bind) is where it starts to
    matter and would move into the loop.

CAPEX / levelized cost and the demand charge are deliberately not here yet —
they are the next addition, sourced from IRENA / CREG, so Stage 1 stays a pure
energy-cost-to-meet-demand problem.
"""

import numpy as np
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize as pymoo_minimize

from src.economics import energy_cost_da
from src.physics.electrolyzer_model import P_MIN_MW, P_RATED_MW, mdot_h2_kg_per_h
from src.physics.pv_model import pv_ac_power_mw
from src.pipeline import evaluate_dispatch

HOURS = 24

# Penalty per kg of unmet demand. A full day of grid power at the peak rate
# costs ~1.6e5 DA, so 1e7/kg makes any shortfall dominate cost: PSO first drives
# demand to feasibility, then minimizes cost among feasible schedules.
SHORTFALL_PENALTY_DA_PER_KG = 1.0e7
DEMAND_TOL_KG = 1e-6

# Fast electrolyzer H2 lookup: built once from the exact model (which runs a
# brentq root-find per call) so the PSO inner loop is plain interpolation.
# Knot at 0 (off) plus a dense grid over the operating window [P_MIN, P_RATED].
_P_TABLE = np.concatenate(([0.0], np.linspace(P_MIN_MW, P_RATED_MW, 256)))
_MDOT_TABLE = np.array([0.0] + [mdot_h2_kg_per_h(p) for p in _P_TABLE[1:]])


def _repair(p):
    """Snap a raw setpoint to the physical domain {0} U [P_MIN, P_RATED] MW.

    Below the 10 % turndown floor the electrolyzer cannot run, so anything the
    optimizer proposes there means "off that hour".
    """
    if p < P_MIN_MW:
        return 0.0
    return min(p, P_RATED_MW)


def _mdot_fast(p_mw):
    """H2 rate [kg/h] for a setpoint via interpolation of the exact model."""
    return float(np.interp(p_mw, _P_TABLE, _MDOT_TABLE))


def evaluate_day(setpoints, g_profile, t_profile):
    """Cost and hydrogen for a 24-hour setpoint schedule (exact, no load flow).

    Args:
        setpoints: length-24 iterable of raw electrolyzer setpoints [MW]
            (repaired to {0} U [P_MIN, P_RATED] internally).
        g_profile: length-24 in-plane irradiance [W/m2].
        t_profile: length-24 ambient temperature [degC].

    Returns:
        dict with totals and per-hour breakdown:
            total_h2_kg, total_cost_da, setpoints (repaired),
            pv_mw, grid_p_mw, h2_kg, cost_da  (each a length-24 list)
    """
    sp = [_repair(float(p)) for p in setpoints]
    pv, grid, h2, cost = [], [], [], []
    for h in range(HOURS):
        p = sp[h]
        pv_h = pv_ac_power_mw(g_profile[h], t_profile[h])
        h2_h = _mdot_fast(p) if p > 0.0 else 0.0
        grid_h = p - pv_h                       # + import, - export
        cost_h = energy_cost_da(grid_h, h)      # import billed at the hour's rate
        pv.append(pv_h); grid.append(grid_h); h2.append(h2_h); cost.append(cost_h)
    return {
        "setpoints": sp,
        "pv_mw": pv,
        "grid_p_mw": grid,
        "h2_kg": h2,
        "cost_da": cost,
        "total_h2_kg": float(sum(h2)),
        "total_cost_da": float(sum(cost)),
    }


class _DayProblem(ElementwiseProblem):
    """24-hour setpoint schedule minimizing grid cost subject to a daily demand."""

    def __init__(self, g_profile, t_profile, demand_kg):
        super().__init__(n_var=HOURS, n_obj=1,
                         xl=np.zeros(HOURS), xu=np.full(HOURS, P_RATED_MW))
        self._g = g_profile
        self._t = t_profile
        self._demand = demand_kg

    def _evaluate(self, x, out, *args, **kwargs):
        res = evaluate_day(x, self._g, self._t)
        shortfall = max(0.0, self._demand - res["total_h2_kg"])
        out["F"] = res["total_cost_da"] + SHORTFALL_PENALTY_DA_PER_KG * shortfall


def optimize_day(g_profile, t_profile, demand_kg, seed=0, pop_size=60, n_gen=300):
    """Least-cost 24-hour schedule that produces at least demand_kg of hydrogen.

    Args:
        g_profile, t_profile: length-24 irradiance [W/m2] and temperature [degC].
        demand_kg: required daily hydrogen production [kg/day].
        seed: PSO seed (reproducible).
        pop_size, n_gen: PSO budget (the inner loop is cheap, so default is
            generous for the 24-dimensional search).

    Returns:
        dict: the evaluate_day result at the optimum, plus
            demand_kg, demand_met (bool), shortfall_kg, cost_per_kg_da,
            n_evaluations.
    """
    res = pymoo_minimize(_DayProblem(g_profile, t_profile, demand_kg),
                         PSO(pop_size=pop_size), ("n_gen", n_gen),
                         seed=seed, verbose=False)
    best = evaluate_day(np.atleast_1d(res.X), g_profile, t_profile)
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


def verify_day_feasibility(setpoints, g_profile, t_profile, tariff=4.68):
    """Run the validated pandapower load flow on each hour of a schedule.

    Confirms the optimal schedule respects the ETAP network limits (voltage,
    transformer loading). Returns the list of (hour, reason) for any infeasible
    hour — empty when the whole schedule is within limits.
    """
    violations = []
    for h in range(HOURS):
        p = _repair(float(setpoints[h]))
        r = evaluate_dispatch(g_profile[h], t_profile[h], tariff, p)
        if not r["feasible"]:
            violations.append((h, r["reason"]))
    return violations


if __name__ == "__main__":
    from pymoo.config import Config

    from src.profiles import representative_days

    Config.warnings["not_compiled"] = False

    days = representative_days("ghardaia")
    prof = days["clear_summer"]
    demand = 200.0
    print(f"clear_summer {prof['date']} — demand {demand:.0f} kg/day\n")

    out = optimize_day(prof["g_wm2"], prof["t_amb_c"], demand, seed=0)
    print(f"  produced {out['total_h2_kg']:.1f} kg  "
          f"(demand met: {out['demand_met']}, shortfall {out['shortfall_kg']:.3f} kg)")
    print(f"  total grid cost {out['total_cost_da']:.0f} DA  "
          f"-> {out['cost_per_kg_da']:.1f} DA/kg  ({out['n_evaluations']} evals)\n")

    print(f"  {'h':>2} {'price':>6} {'PV':>6} {'set':>6} {'grid':>7} {'H2':>6}")
    for h in range(HOURS):
        from src.economics import band_name, grid_price_da_per_kwh
        print(f"  {h:02d} {grid_price_da_per_kwh(h):>6.2f} {out['pv_mw'][h]:>6.3f} "
              f"{out['setpoints'][h]:>6.3f} {out['grid_p_mw'][h]:>+7.3f} "
              f"{out['h2_kg'][h]:>6.2f}  {band_name(h)}")

    viol = verify_day_feasibility(prof["g_wm2"], prof["t_amb_c"], out["setpoints"])
    print(f"\n  network feasibility: "
          f"{'all 24 h within limits' if not viol else viol}")
