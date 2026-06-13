"""Stage 1 results: intelligent daily dispatch on real Ghardaïa weather.

Produces the two headline figures for the demand-driven least-cost controller:

  results/figures/day_schedule_ghardaia.png
      For the clear-summer / cloudy-summer / clear-winter representative days, the
      optimal hourly electrolyzer setpoint overlaid on available PV, with the
      time-of-use price bands shaded — showing the controller riding free solar
      and cheap night power and dodging the 17:00-21:00 peak.

  results/figures/cost_vs_demand_ghardaia.png
      Hydrogen cost [DA/kg] vs the daily demand, per day — the "knee" where
      meeting more demand forces production into expensive peak hours.

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

from src.day_dispatch import HOURS, optimize_day, verify_day_feasibility
from src.economics import (PRICE_CREUSES_DA_PER_KWH, PRICE_POINTE_DA_PER_KWH,
                           grid_price_da_per_kwh)
from src.profiles import representative_days

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
HEADLINE_DEMAND_KG = 200.0
DAY_ORDER = ["clear_summer", "cloudy_summer", "clear_winter"]
DAY_TITLES = {
    "clear_summer": "Clear summer day",
    "cloudy_summer": "Cloudy summer day",
    "clear_winter": "Clear winter day",
}


def _shade_price_bands(ax):
    """Light background bands: night (off-peak) blue, evening peak red."""
    ax.axvspan(-0.5, 5.5, color="#cfe8ff", alpha=0.5, zorder=0)    # creuses 00-05
    ax.axvspan(22.5, 23.5, color="#cfe8ff", alpha=0.5, zorder=0)   # creuses 23
    ax.axvspan(16.5, 20.5, color="#ffd6d6", alpha=0.6, zorder=0)   # pointe 17-20


def schedule_figure(results):
    """Stacked per-day schedule plot; results: name -> optimize_day() dict."""
    hours = np.arange(HOURS)
    fig, axes = plt.subplots(len(DAY_ORDER), 1, figsize=(10, 9), sharex=True)
    for ax, name in zip(axes, DAY_ORDER):
        r = results[name]
        _shade_price_bands(ax)
        ax.bar(hours, r["setpoints"], width=0.8, color="#1f77b4",
               label="electrolyzer setpoint", zorder=2)
        ax.plot(hours, r["pv_mw"], "o-", color="#2ca02c", markersize=3,
                label="available PV", zorder=3)
        ax.set_ylabel("Power [MW]")
        ax.set_ylim(0, 0.85)
        ax.set_title(f"{DAY_TITLES[name]} ({r['date_label']}) — "
                     f"{r['total_h2_kg']:.0f} kg at {r['cost_per_kg_da']:.1f} DA/kg",
                     fontsize=10)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(loc="upper center", ncol=2, fontsize=9)
    axes[-1].set_xlabel("Hour of day")
    axes[-1].set_xticks(range(0, 24, 2))
    fig.suptitle(f"Least-cost dispatch to meet {HEADLINE_DEMAND_KG:.0f} kg/day "
                 f"— Ghardaïa (blue = off-peak nights, red = 17–21 h peak)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    path = FIGURES_DIR / "day_schedule_ghardaia.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def cost_vs_demand_figure(days, demands, seed=0):
    """Cost per kg vs daily demand for each representative day (the knee)."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    markers = {"clear_summer": "o-", "cloudy_summer": "s-", "clear_winter": "^-"}
    for name in DAY_ORDER:
        prof = days[name]
        cpk = []
        for d in demands:
            out = optimize_day(prof["g_wm2"], prof["t_amb_c"], d, seed=seed)
            cpk.append(out["cost_per_kg_da"] if out["demand_met"] else np.nan)
        ax.plot(demands, cpk, markers[name], label=DAY_TITLES[name])
    ax.set_xlabel("Daily hydrogen demand [kg/day]")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title("Cost per kg vs demand — Ghardaïa (CREG time-of-use tariff)")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "cost_vs_demand_ghardaia.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    days = representative_days("ghardaia")

    print(f"=== Headline schedules (demand {HEADLINE_DEMAND_KG:.0f} kg/day) ===",
          flush=True)
    results = {}
    for name in DAY_ORDER:
        prof = days[name]
        out = optimize_day(prof["g_wm2"], prof["t_amb_c"], HEADLINE_DEMAND_KG, seed=0)
        out["date_label"] = prof["date"]
        viol = verify_day_feasibility(prof["g_wm2"], prof["t_amb_c"], out["setpoints"])
        results[name] = out
        print(f"  {name:14s} {prof['date']}  produced {out['total_h2_kg']:.1f} kg  "
              f"{out['cost_per_kg_da']:5.1f} DA/kg  "
              f"feasible={'yes' if not viol else viol}", flush=True)
    p1 = schedule_figure(results)
    print(f"saved: {p1}", flush=True)

    print("\n=== Cost vs demand sweep ===", flush=True)
    demands = list(range(40, 341, 20))
    p2 = cost_vs_demand_figure(days, demands)
    print(f"saved: {p2}", flush=True)
    print(f"\ntotal runtime: {time.perf_counter() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
