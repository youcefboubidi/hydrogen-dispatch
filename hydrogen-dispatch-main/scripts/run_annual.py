"""Full-year (2023) dispatch on real Ghardaïa data — annual KPIs + seasonal view.

Runs the least-cost dispatch for every full day of 2023 (real CAMS+PySAM 15-min
PV, real CREG tariff) at a fixed daily hydrogen demand, and aggregates:
  * annual H2, annual grid cost, annual average cost per kg
  * solar (green) fraction of the electrolyzer energy
  * the seasonal pattern (cheap, green summers vs dearer winters)

Outputs:
  results/tables/annual_2023.csv         per-day results
  results/figures/annual_cost_vs_doy.png daily cost/kg through the year
  results/figures/annual_monthly.png     monthly cost/kg + solar fraction
  results/figures/annual_calendar.png    calendar heatmap of daily cost/kg

Run from the repo root:  python scripts/run_annual.py
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import calendar

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pymoo.config import Config

from src.day_dispatch import STEP_H, STEPS, optimize_day
from src.pv_data import load_pv_mw

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
TABLES_DIR = REPO_ROOT / "results" / "tables"
DAILY_DEMAND_KG = 100.0
# Moderate PSO budget: the annual aggregate is robust to tiny per-day noise and
# this keeps 360+ optimizations to a few minutes.
POP, NGEN = 40, 150


def full_year_days():
    """{date: pv_15min(96,)} for every complete 96-step local day in the series."""
    s = load_pv_mw()
    df = pd.DataFrame({"pv": s.to_numpy()}, index=s.index)
    df["date"] = df.index.date
    counts = df.groupby("date")["pv"].count()
    days = {}
    for d, c in counts.items():
        if c == STEPS:
            days[d] = df[df["date"] == d].sort_index()["pv"].to_numpy()
    return days


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    days = full_year_days()
    print(f"optimizing {len(days)} full days at {DAILY_DEMAND_KG:.0f} kg/day "
          f"(PSO {POP}x{NGEN}) ...", flush=True)

    rows = []
    for i, (date, pv) in enumerate(sorted(days.items()), start=1):
        out = optimize_day(pv, DAILY_DEMAND_KG, seed=0, pop_size=POP, n_gen=NGEN)
        sp = out["setpoints"]
        elz_mwh = float(np.sum(sp) * STEP_H)
        solar_to_elz = float(np.sum(np.minimum(sp, out["pv_mw"])) * STEP_H)
        grid_mwh = float(np.sum(np.clip(out["grid_p_mw"], 0, None)) * STEP_H)
        rows.append({
            "date": str(date),
            "month": date.month,
            "day": date.day,
            "h2_kg": out["total_h2_kg"],
            "cost_da": out["total_cost_da"],
            "cost_per_kg_da": out["cost_per_kg_da"],
            "grid_import_mwh": grid_mwh,
            "solar_to_elz_mwh": solar_to_elz,
            "green_fraction": solar_to_elz / elz_mwh if elz_mwh > 0 else 0.0,
            "demand_met": out["demand_met"],
        })
        if i % 60 == 0:
            print(f"  {i}/{len(days)} days ...", flush=True)

    df = pd.DataFrame(rows)
    out_csv = TABLES_DIR / "annual_2023.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # --- annual KPIs ---
    tot_h2 = df["h2_kg"].sum()
    tot_cost = df["cost_da"].sum()
    avg_cpk = tot_cost / tot_h2
    green = df["solar_to_elz_mwh"].sum() / (
        df["solar_to_elz_mwh"].sum() + df["grid_import_mwh"].sum())
    print(f"\n=== ANNUAL 2023 ({len(df)} days @ {DAILY_DEMAND_KG:.0f} kg/day) ===")
    print(f"  hydrogen:        {tot_h2/1000:.1f} t/yr")
    print(f"  grid cost:       {tot_cost/1e6:.2f} M DA/yr")
    print(f"  avg cost/kg:     {avg_cpk:.1f} DA/kg "
          f"(min day {df['cost_per_kg_da'].min():.1f}, "
          f"max day {df['cost_per_kg_da'].max():.1f})")
    print(f"  solar fraction:  {green*100:.1f} % of electrolyzer energy")
    print(f"  all demand met:  {bool(df['demand_met'].all())}")
    print(f"saved: {out_csv}", flush=True)

    # --- fig 1: daily cost/kg through the year ---
    doy = pd.to_datetime(df["date"]).dt.dayofyear
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(doy, df["cost_per_kg_da"], ".", color="#1f77b4", alpha=0.5,
            label="daily")
    ax.plot(doy, df["cost_per_kg_da"].rolling(14, center=True, min_periods=1).mean(),
            color="#d62728", linewidth=2, label="14-day mean")
    ax.set_xlabel("Day of year (2023)")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title(f"Daily least-cost hydrogen — Ghardaïa 2023 ({DAILY_DEMAND_KG:.0f} kg/day)")
    ax.grid(alpha=0.3)
    ax.legend()
    p1 = FIGURES_DIR / "annual_cost_vs_doy.png"
    fig.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- fig 2: monthly cost/kg + solar fraction ---
    monthly = df.groupby("month").agg(
        cost_per_kg=("cost_per_kg_da", "mean"),
        green=("green_fraction", "mean")).reindex(range(1, 13))
    fig, ax1 = plt.subplots(figsize=(10, 5))
    months = [calendar.month_abbr[m] for m in range(1, 13)]
    ax1.bar(months, monthly["cost_per_kg"], color="#1f77b4", alpha=0.8,
            label="avg cost/kg")
    ax1.set_ylabel("Avg hydrogen cost [DA/kg]", color="#1f77b4")
    ax2 = ax1.twinx()
    ax2.plot(months, monthly["green"] * 100, "o-", color="#2ca02c",
             label="solar fraction")
    ax2.set_ylabel("Solar fraction of electrolyzer energy [%]", color="#2ca02c")
    ax2.set_ylim(0, 100)
    ax1.set_title(f"Monthly cost and solar fraction — Ghardaïa 2023 "
                  f"({DAILY_DEMAND_KG:.0f} kg/day)")
    p2 = FIGURES_DIR / "annual_monthly.png"
    fig.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- fig 3: calendar heatmap of daily cost/kg ---
    grid = np.full((12, 31), np.nan)
    for _, r in df.iterrows():
        grid[int(r["month"]) - 1, int(r["day"]) - 1] = r["cost_per_kg_da"]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    im = ax.imshow(grid, aspect="auto", cmap="RdYlGn_r", origin="upper")
    ax.set_yticks(range(12))
    ax.set_yticklabels([calendar.month_abbr[m] for m in range(1, 13)])
    ax.set_xticks(range(0, 31, 2))
    ax.set_xticklabels(range(1, 32, 2))
    ax.set_xlabel("Day of month")
    ax.set_title(f"Daily hydrogen cost [DA/kg] — Ghardaïa 2023 "
                 f"({DAILY_DEMAND_KG:.0f} kg/day)")
    fig.colorbar(im, ax=ax, label="DA/kg")
    p3 = FIGURES_DIR / "annual_calendar.png"
    fig.savefig(p3, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"saved: {p1}\nsaved: {p2}\nsaved: {p3}")
    print(f"total runtime: {time.perf_counter() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
