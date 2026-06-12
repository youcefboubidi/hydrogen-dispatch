"""PSO dispatch optimizer (Phase 5) — thesis eqs (4.6)-(4.11).

Solves, for one operating point (irradiance, ambient temperature, tariff),

    "max_h2":   max  h2_kg_per_h(p_elz)
    "min_cost": min  cost_per_kg(p_elz)

over the decision variable p_elz in {0} U [P_MIN_MW, P_RATED_MW] MW, subject
to the electrolyzer operating window and the network limits (0.95-1.05 pu,
T1 loading <= 100 %). The objective function is src.pipeline's
evaluate_dispatch(); constraints are handled by rejection (death penalty):
any candidate it flags feasible=False gets worst-possible fitness.

"min_cost" is lexicographic, not a weighted sum: minimize cost_per_kg first,
then — among candidates within COST_TOL_PER_KG of that optimum — maximize
h2_kg_per_h. Implemented as preemptive two-stage PSO: stage 1 finds the best
cost c*; stage 2 maximizes H2 under a death penalty on
cost_per_kg > c* + COST_TOL_PER_KG. The tie-break is what resolves the
zero-cost plateau: every setpoint the PV can cover alone costs 0 DA/kg, and
stage 2 pushes the setpoint to the plateau edge, soaking up all available
solar. A feasible but non-producing candidate (h2 = 0) has no defined cost
per kg and ranks between the producing candidates and the infeasible ones —
it can only win when nothing produces.

The discrete OFF option (p_elz = 0) lies outside the PSO box
[P_MIN_MW, P_RATED_MW] and is compared against the continuous optimum
lexicographically at the end.

Run the verification cases with:  python -m src.optimizer   (from the repo root)
"""

import numpy as np
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize as pymoo_minimize

from src.physics.electrolyzer_model import P_MIN_MW, P_RATED_MW
from src.pipeline import evaluate_dispatch

MODES = ("max_h2", "min_cost")
DEATH_PENALTY = 1.0e9    # fitness of rejected candidates (infeasible / wrong tier)
COST_TOL_PER_KG = 1e-6   # cost tie tolerance for the lexicographic tie-break [DA/kg]

# PSO budget: one decision variable, so a small swarm and few iterations are
# plenty (the 1-D parabola converges to ~1e-8 with this budget).
POP_SIZE = 20
N_GEN = 40


class _SetpointProblem(ElementwiseProblem):
    """1-D pymoo problem over the continuous setpoint box [P_MIN_MW, P_RATED_MW]."""

    def __init__(self, fitness):
        super().__init__(n_var=1, n_obj=1,
                         xl=np.array([P_MIN_MW]), xu=np.array([P_RATED_MW]))
        self._fitness = fitness

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = self._fitness(float(x[0]))


def _run_pso(fitness, seed):
    """One PSO stage; returns (best setpoint, best fitness, generations run)."""
    res = pymoo_minimize(_SetpointProblem(fitness), PSO(pop_size=POP_SIZE),
                         ("n_gen", N_GEN), seed=seed, verbose=False)
    p_mw = float(np.atleast_1d(res.X)[0])
    f = float(np.atleast_1d(res.F)[0])
    return p_mw, f, int(res.algorithm.n_gen)


def _candidate_key(mode, result):
    """Lexicographic comparison key over evaluate_dispatch results, lower is better.

    Tier 0: feasible candidates, ordered by the mode's objective with its
            tie-break (min_cost: cost first, then more H2; max_h2: H2 first,
            then cheaper). For min_cost, a candidate must produce (h2 > 0)
            to enter tier 0 — cost per kg is undefined without kilograms.
    Tier 1: feasible but non-producing (the OFF option under min_cost).
    Tier 2: infeasible (death penalty).
    """
    if not result["feasible"]:
        return (2, 0.0, 0.0)
    h2 = result["h2_kg_per_h"]
    if mode == "max_h2":
        return (0, -h2, result["cost_per_kg"])
    if h2 > 0.0:
        return (0, result["cost_per_kg"], -h2)
    return (1, 0.0, 0.0)


def optimize_dispatch(g_wm2, t_amb_c, tariff_per_kwh, mode, seed=0):
    """Optimal electrolyzer setpoint for one operating condition.

    Args:
        g_wm2: plane-of-array irradiance G [W/m²].
        t_amb_c: ambient temperature Ta [°C].
        tariff_per_kwh: grid import tariff [currency/kWh].
        mode: "max_h2" (maximize hydrogen rate) or "min_cost" (minimize cost
            per kg, lexicographically tie-broken toward more hydrogen).
        seed: random seed for the PSO stages (stage 2 uses seed + 1), making
            runs bit-reproducible.

    Returns:
        dict with keys
            mode           the optimization mode (str)
            p_elz_mw       optimal electrolyzer setpoint [MW] (0.0 = OFF)
            objective      h2_kg_per_h [kg/h] for max_h2, cost_per_kg
                           [currency/kg] for min_cost; None if even OFF is
                           infeasible
            result         full evaluate_dispatch() dict at the optimum
            n_iterations   PSO generations run (summed over stages)
            n_evaluations  evaluate_dispatch() calls (PSO + OFF + re-check)
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")

    n_evals = {"n": 0}

    def ev(p_elz_mw):
        n_evals["n"] += 1
        return evaluate_dispatch(g_wm2, t_amb_c, tariff_per_kwh, p_elz_mw)

    n_iterations = 0
    p_win = None

    if mode == "max_h2":
        def fit_h2(p_mw):
            r = ev(p_mw)
            return -r["h2_kg_per_h"] if r["feasible"] else DEATH_PENALTY

        p1, f1, gens = _run_pso(fit_h2, seed)
        n_iterations += gens
        if f1 < DEATH_PENALTY:
            p_win = p1
    else:
        # Stage 1: best achievable cost per kg over producing candidates.
        def fit_cost(p_mw):
            r = ev(p_mw)
            if r["feasible"] and r["h2_kg_per_h"] > 0.0:
                return r["cost_per_kg"]
            return DEATH_PENALTY

        p1, c_star, gens = _run_pso(fit_cost, seed)
        n_iterations += gens

        if c_star < DEATH_PENALTY:
            # Stage 2: most hydrogen among candidates within COST_TOL_PER_KG
            # of c* (the lexicographic tie-break).
            def fit_h2_at_best_cost(p_mw):
                r = ev(p_mw)
                if (r["feasible"] and r["h2_kg_per_h"] > 0.0
                        and r["cost_per_kg"] <= c_star + COST_TOL_PER_KG):
                    return -r["h2_kg_per_h"]
                return DEATH_PENALTY

            p2, f2, gens = _run_pso(fit_h2_at_best_cost, seed + 1)
            n_iterations += gens
            p_win = p2 if f2 < DEATH_PENALTY else p1

    # Discrete OFF option vs continuous optimum, compared lexicographically.
    candidates = [(0.0, ev(0.0))]
    if p_win is not None:
        candidates.append((p_win, ev(p_win)))
    p_opt, r_opt = min(candidates, key=lambda c: _candidate_key(mode, c[1]))

    if r_opt["feasible"]:
        objective = (r_opt["h2_kg_per_h"] if mode == "max_h2"
                     else r_opt["cost_per_kg"])
    else:
        objective = None

    return {"mode": mode, "p_elz_mw": p_opt, "objective": objective,
            "result": r_opt, "n_iterations": n_iterations,
            "n_evaluations": n_evals["n"]}


if __name__ == "__main__":
    from pymoo.config import Config

    from src.physics.pv_model import pv_ac_power_mw
    from src.pipeline import TARIFF_DA_PER_KWH

    Config.warnings["not_compiled"] = False  # keep the PASS/FAIL table clean

    TOL_P_MW = 0.005
    # Expected analytic optima: max_h2 -> rated power (H2 monotonic in P,
    # network never binding here); min_cost -> the zero-cost plateau edge
    # min(pv, rated) when the PV can carry the minimum load, else the
    # turndown floor (cost/kg = tariff x specific energy rises with load).
    cases = [
        ("max_h2", 1000.0, 0.800),
        ("max_h2", 0.0, 0.800),
        ("max_h2", 400.0, 0.800),
        ("min_cost", 1000.0, 0.5342),
        ("min_cost", 0.0, 0.080),
        ("min_cost", 400.0, pv_ac_power_mw(400.0, 25.0)),
    ]
    failures = []
    for mode, g, p_expected in cases:
        out = optimize_dispatch(g, 25.0, TARIFF_DA_PER_KWH, mode, seed=0)
        dp = abs(out["p_elz_mw"] - p_expected)
        ok = dp <= TOL_P_MW
        unit = "kg/h" if mode == "max_h2" else "DA/kg"
        shown = "n/a" if out["objective"] is None else f"{out['objective']:.4f}"
        print(f"{mode:8s} G={g:6.1f} W/m2 -> p* = {out['p_elz_mw']:.4f} MW "
              f"(expected {p_expected:.4f}, diff {dp:.2e}) | "
              f"objective {shown} {unit} | "
              f"{out['n_evaluations']} evals, {out['n_iterations']} gens | "
              f"{'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append((mode, g))

    if failures:
        print(f"\n{len(failures)} CASE(S) MISSED THE EXPECTED OPTIMUM: {failures}")
        raise SystemExit(1)
    print("\nAll optimizer verification cases PASS.")
