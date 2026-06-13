"""Quantify the value of the smart dispatch vs traditional, time-blind operation.

Same hydrogen demand, same real Ghardaïa day, same real CREG time-of-use tariff —
three ways to run the electrolyzer:

  optimized  - our PSO least-cost schedule (shifts load to cheap/solar hours,
               dodges the 17-21 h peak)
  constant   - "traditional baseload": one steady setpoint sized to meet the
               daily demand, no awareness of the time-of-use price
  greedy     - "produce ASAP": run flat-out from midnight until the demand is
               made, then stop

All three are billed identically and all meet the same daily kg, so the cost
difference is purely the value of *intelligent timing*. Lower cost for the same
hydrogen = higher margin, i.e. more profitable.

Run from the repo root:  python scripts/compare_baselines.py
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pymoo.config import Config

from src.day_dispatch import (HOURS, P_MIN_MW, P_RATED_MW, _mdot_fast,
                              evaluate_day, optimize_day)
from src.profiles import representative_days

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
HEADLINE_DEMAND_KG = 200.0


def _power_for_total(demand_kg):
    """Constant setpoint whose 24 h output equals demand_kg (bisection)."""
    target_hourly = demand_kg / HOURS
    if _mdot_fast(P_MIN_MW) >= target_hourly:
        return P_MIN_MW  # cannot run below the turndown floor
    lo, hi = P_MIN_MW, P_RATED_MW
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if _mdot_fast(mid) < target_hourly:
            lo = mid
        else:
            hi = mid
    return hi


def constant_schedule(demand_kg):
    """Traditional baseload: one steady setpoint, all 24 h, time-blind."""
    return [_power_for_total(demand_kg)] * HOURS


def greedy_schedule(demand_kg):
    """Produce ASAP: full blast from hour 0 until the demand is met, then off."""
    sched = [0.0] * HOURS
    made = 0.0
    for h in range(HOURS):
        remaining = demand_kg - made
        if remaining <= 0:
            break
        if _mdot_fast(P_RATED_MW) <= remaining:
            sched[h] = P_RATED_MW
            made += _mdot_fast(P_RATED_MW)
        else:
            # partial last hour: smallest setpoint that finishes the demand
            lo, hi = P_MIN_MW, P_RATED_MW
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if _mdot_fast(mid) < remaining:
                    lo = mid
                else:
                    hi = mid
            sched[h] = hi
            made += _mdot_fast(hi)
    return sched


def cost_per_kg(schedule, g, ta):
    r = evaluate_day(schedule, g, ta)
    return (r["total_cost_da"] / r["total_h2_kg"]) if r["total_h2_kg"] > 0 else 0.0


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    prof = representative_days("ghardaia")["clear_summer"]
    g, ta = prof["g_wm2"], prof["t_amb_c"]

    # Headline comparison at the demo demand.
    opt = optimize_day(g, ta, HEADLINE_DEMAND_KG, seed=0)
    c_opt = opt["cost_per_kg_da"]
    c_con = cost_per_kg(constant_schedule(HEADLINE_DEMAND_KG), g, ta)
    c_grd = cost_per_kg(greedy_schedule(HEADLINE_DEMAND_KG), g, ta)
    print(f"=== {HEADLINE_DEMAND_KG:.0f} kg/day, clear summer ({prof['date']}) ===")
    print(f"  optimized (smart) : {c_opt:6.1f} DA/kg")
    print(f"  constant baseload : {c_con:6.1f} DA/kg  "
          f"(smart saves {100*(c_con-c_opt)/c_con:4.1f} %)")
    print(f"  greedy produce-ASAP: {c_grd:6.1f} DA/kg  "
          f"(smart saves {100*(c_grd-c_opt)/c_grd:4.1f} %)\n")

    # Savings across the demand range.
    demands = list(range(60, 341, 20))
    rows = {"optimized": [], "constant": [], "greedy": []}
    print(f"  {'demand':>6}  {'opt':>6} {'const':>6} {'greedy':>6}  "
          f"{'save_vs_const':>13} {'save_vs_greedy':>14}")
    for d in demands:
        co = optimize_day(g, ta, d, seed=0)["cost_per_kg_da"]
        cc = cost_per_kg(constant_schedule(d), g, ta)
        cg = cost_per_kg(greedy_schedule(d), g, ta)
        rows["optimized"].append(co)
        rows["constant"].append(cc)
        rows["greedy"].append(cg)
        sv_c = 100 * (cc - co) / cc if cc > 0 else 0.0
        sv_g = 100 * (cg - co) / cg if cg > 0 else 0.0
        print(f"  {d:>6}  {co:>6.1f} {cc:>6.1f} {cg:>6.1f}  "
              f"{sv_c:>12.1f}% {sv_g:>13.1f}%")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(demands, rows["constant"], "s--", color="#d62728",
            label="constant baseload (traditional)")
    ax.plot(demands, rows["greedy"], "^--", color="#ff7f0e",
            label="greedy produce-ASAP")
    ax.plot(demands, rows["optimized"], "o-", color="#1f77b4", linewidth=2,
            label="optimized (our controller)")
    ax.set_xlabel("Daily hydrogen demand [kg/day]")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title("Smart dispatch vs traditional operation — Ghardaïa clear "
                 "summer day\n(same demand, same weather, same CREG tariff)")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "baseline_comparison_ghardaia.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nsaved: {path}")
    print(f"total runtime: {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
