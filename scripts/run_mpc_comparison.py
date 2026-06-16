"""Control-strategy comparison: perfect-foresight vs MPC vs reactive rule-based.

Runs the three controllers on days sampled across 2023 and reports how close the
closed-loop MPC gets to the (unreachable) perfect-foresight optimum and how far
it beats the reactive rule. This is the control-engineering headline result.

Outputs:
  results/tables/mpc_comparison.csv
  results/figures/mpc_comparison.png

Run from the repo root:  python scripts/run_mpc_comparison.py
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
import pandas as pd
from pymoo.config import Config

from src.day_dispatch import STEP_H, optimize_day
from src.mpc import consecutive_days, mpc_dispatch, rule_based_dispatch

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
TABLES_DIR = REPO_ROOT / "results" / "tables"
DEMAND_KG = 200.0
SAMPLE_EVERY = 10        # ~36 days across the year


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    days = consecutive_days()[::SAMPLE_EVERY]
    print(f"comparing 3 controllers on {len(days)} sampled days ...", flush=True)

    rows = []
    for i, (date, today, prev) in enumerate(days, 1):
        pf = optimize_day(today, DEMAND_KG, seed=0)
        mpc = mpc_dispatch(today, prev, DEMAND_KG, seed=0)
        rb = rule_based_dispatch(today, DEMAND_KG)
        rows.append({
            "date": date,
            "doy": pd.Timestamp(date).dayofyear,
            "pv_mwh": round(float(today.sum()) * STEP_H, 2),
            "perfect": pf["cost_per_kg_da"],
            "mpc": mpc["cost_per_kg_da"],
            "rule": rb["cost_per_kg_da"],
        })
        if i % 10 == 0:
            print(f"  {i}/{len(days)} days ...", flush=True)

    df = pd.DataFrame(rows).sort_values("doy")
    df.to_csv(TABLES_DIR / "mpc_comparison.csv", index=False, encoding="utf-8-sig")

    # cost-weighted aggregate gaps (avoid div-by-zero on ~free summer days)
    pf_tot, mpc_tot, rb_tot = df["perfect"].sum(), df["mpc"].sum(), df["rule"].sum()
    gap = 100 * (mpc_tot - pf_tot) / pf_tot
    edge = 100 * (rb_tot - mpc_tot) / rb_tot
    print(f"\n=== CONTROL-STRATEGY COMPARISON ({len(df)} days @ {DEMAND_KG:.0f} kg/day) ===")
    print(f"  mean cost/kg  perfect {df['perfect'].mean():.1f} | "
          f"MPC {df['mpc'].mean():.1f} | rule {df['rule'].mean():.1f} DA/kg")
    print(f"  MPC gap to perfect-foresight optimum: +{gap:.1f}%")
    print(f"  MPC vs reactive rule-based:           {edge:.1f}% cheaper")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(df["doy"], df["rule"], "s--", color="#d62728", label="rule-based (reactive)")
    ax.plot(df["doy"], df["mpc"], "o-", color="#1f77b4", lw=2,
            label="MPC (forecast, closed-loop)")
    ax.plot(df["doy"], df["perfect"], "^-", color="#2ca02c",
            label="perfect-foresight (optimum bound)")
    ax.fill_between(df["doy"], df["perfect"], df["mpc"], color="#1f77b4", alpha=0.12)
    ax.set_xlabel("Day of year (2023, sampled)")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title(f"Supervisory control strategies — Ghardaïa, {DEMAND_KG:.0f} kg/day\n"
                 f"MPC tracks the optimum (+{gap:.1f}%) and beats the reactive rule "
                 f"by {edge:.0f}%")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "mpc_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved: {path}\nsaved: {TABLES_DIR/'mpc_comparison.csv'}")
    print(f"total runtime: {time.perf_counter() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
