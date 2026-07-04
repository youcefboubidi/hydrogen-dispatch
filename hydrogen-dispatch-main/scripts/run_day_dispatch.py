"""Stage 1 results: intelligent daily dispatch on REAL Ghardaïa data.

PV is the real PySAM/CAMS 15-minute generation; the tariff is the real CREG
time-of-use schedule. Produces:

  results/figures/day_schedule_ghardaia.png
      Optimal 15-minute setpoint vs available PV for the clear-summer /
      cloudy-summer / clear-winter representative days, with the time-of-use
      price bands shaded — the controller riding free solar and cheap night
      power and dodging the 17:00-21:00 peak.

  results/figures/cost_vs_demand_ghardaia.png
      Hydrogen cost [DA/kg] vs daily demand, per day — the "knee" where meeting
      more demand forces production into the expensive peak.

Run from the repo root:  python scripts/run_day_dispatch.py
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

from src.day_dispatch import STEP_H, STEPS, optimize_day, verify_day_feasibility
from src.pv_data import representative_days

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
HEADLINE_DEMAND_KG = 200.0
DAY_ORDER = ["clear_summer", "cloudy_summer", "clear_winter"]
DAY_TITLES = {"clear_summer": "Clear summer day",
              "cloudy_summer": "Cloudy summer day",
              "clear_winter": "Clear winter day"}


def _shade_price_bands(ax):
    ax.axvspan(0, 6, color="#cfe8ff", alpha=0.5, zorder=0)      # creuses 00-06
    ax.axvspan(22.5, 24, color="#cfe8ff", alpha=0.5, zorder=0)  # creuses 22:30-24
    ax.axvspan(17, 21, color="#ffd6d6", alpha=0.6, zorder=0)    # pointe 17-21


def schedule_figure(results):
    x = np.arange(STEPS) * STEP_H   # local hour of each 15-min step: 0..23.75
    fig, axes = plt.subplots(len(DAY_ORDER), 1, figsize=(10, 9), sharex=True)
    for ax, name in zip(axes, DAY_ORDER):
        r = results[name]
        _shade_price_bands(ax)
        ax.step(x, r["setpoints"], where="post", color="#1f77b4",
                label="electrolyzer setpoint", zorder=3)
        ax.fill_between(x, r["setpoints"], step="post", color="#1f77b4",
                        alpha=0.20, zorder=2)
        ax.plot(x, r["pv_mw"], color="#2ca02c", linewidth=1.6,
                label="available PV (real)", zorder=4)
        ax.set_ylabel("Power [MW]")
        ax.set_ylim(0, 0.85)
        ax.set_title(f"{DAY_TITLES[name]} ({r['date_label']}) — "
                     f"{r['total_h2_kg']:.0f} kg at {r['cost_per_kg_da']:.1f} DA/kg",
                     fontsize=10)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(loc="upper center", ncol=2, fontsize=9)
    axes[-1].set_xlabel("Hour of day (local time)")
    axes[-1].set_xlim(0, 24)
    axes[-1].set_xticks(range(0, 25, 2))
    fig.suptitle(f"Least-cost dispatch to meet {HEADLINE_DEMAND_KG:.0f} kg/day — "
                 f"Ghardaïa (real CAMS+PySAM, 15-min)\n"
                 f"blue = off-peak nights, red = 17–21 h peak", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    path = FIGURES_DIR / "day_schedule_ghardaia.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def cost_vs_demand_figure(days, demands, seed=0):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    markers = {"clear_summer": "o-", "cloudy_summer": "s-", "clear_winter": "^-"}
    for name in DAY_ORDER:
        pv = days[name]["pv_mw"]
        cpk = []
        for d in demands:
            out = optimize_day(pv, d, seed=seed)
            cpk.append(out["cost_per_kg_da"] if out["demand_met"] else np.nan)
        ax.plot(demands, cpk, markers[name], label=DAY_TITLES[name])
    ax.set_xlabel("Daily hydrogen demand [kg/day]")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title("Cost per kg vs demand — Ghardaïa (real data, CREG time-of-use)")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "cost_vs_demand_ghardaia.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    days = representative_days()

    print(f"=== Headline schedules (demand {HEADLINE_DEMAND_KG:.0f} kg/day) ===",
          flush=True)
    results = {}
    for name in DAY_ORDER:
        pv = days[name]["pv_mw"]
        out = optimize_day(pv, HEADLINE_DEMAND_KG, seed=0)
        out["date_label"] = days[name]["date"]
        viol = verify_day_feasibility(out["hourly_setpoints"], pv)
        results[name] = out
        print(f"  {name:14s} {days[name]['date']}  {out['total_h2_kg']:.0f} kg  "
              f"{out['cost_per_kg_da']:5.1f} DA/kg  "
              f"feasible={'yes (96/96)' if not viol else viol[:3]}", flush=True)
    print(f"saved: {schedule_figure(results)}", flush=True)

    print("\n=== Cost vs demand sweep ===", flush=True)
    demands = list(range(40, 341, 20))
    print(f"saved: {cost_vs_demand_figure(days, demands)}", flush=True)
    print(f"\ntotal runtime: {time.perf_counter() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
