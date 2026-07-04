"""Stage 2 battery results: dispatch with/without storage + economic sizing.

Figures:
  results/figures/battery_day.png
      Clear-summer high-demand day, no-battery vs with-battery: the battery
      charges on cheap night power / surplus solar and discharges through the
      17–21h peak, with its state of charge shown.
  results/figures/battery_sizing.png
      Energy cost/kg AND levelized cost (energy + amortized battery CAPEX) vs
      battery size — the honest techno-economic verdict on whether storage pays.

Run from the repo root:  python scripts/run_battery.py
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

from src.battery_dispatch import Battery, optimize_day_battery
from src.day_dispatch import STEP_H, STEPS, optimize_day
from src.pv_data import representative_days

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
DEMAND_KG = 280.0          # high demand: the no-battery optimum is forced into the peak
DEMO_CAP_MWH = 4.0
BATTERY_HOURS = 4.0        # energy/power ratio (a "4-hour" battery)

# Battery CAPEX (utility Li-ion, installed) — IRENA/BNEF ~2023, stated explicitly.
BESS_CAPEX_USD_PER_KWH = 250.0
USD_TO_DA = 135.0
LIFETIME_YEARS = 12
DISCOUNT = 0.08
_CRF = DISCOUNT * (1 + DISCOUNT) ** LIFETIME_YEARS / ((1 + DISCOUNT) ** LIFETIME_YEARS - 1)
DAILY_CAPEX_DA_PER_KWH = BESS_CAPEX_USD_PER_KWH * USD_TO_DA * _CRF / 365.0


def _shade(ax):
    ax.axvspan(0, 6, color="#cfe8ff", alpha=0.5, zorder=0)
    ax.axvspan(22.5, 24, color="#cfe8ff", alpha=0.5, zorder=0)
    ax.axvspan(17, 21, color="#ffd6d6", alpha=0.6, zorder=0)


def day_figure(pv, base, batt_out):
    x = np.arange(STEPS) * STEP_H
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for ax in (a1, a2):
        _shade(ax)
        ax.set_ylabel("Power [MW]")
        ax.set_ylim(-0.6, 0.85)
        ax.grid(axis="y", alpha=0.3)
    a1.step(x, base["setpoints"], where="post", color="#1f77b4", label="setpoint")
    a1.plot(x, base["pv_mw"], color="#2ca02c", lw=1.5, label="PV")
    a1.set_title(f"No battery — {base['cost_per_kg_da']:.1f} DA/kg")
    a1.legend(loc="upper right", fontsize=9)

    a2.step(x, batt_out["setpoints"], where="post", color="#1f77b4", label="setpoint")
    a2.plot(x, batt_out["pv_mw"], color="#2ca02c", lw=1.5, label="PV")
    a2.fill_between(x, batt_out["batt_mw"], step="post", color="#9467bd",
                    alpha=0.45, label="battery (+disch / −charge)")
    axs = a2.twinx()
    axs.plot(x, batt_out["soc_mwh"], color="#ff7f0e", lw=1.4, label="SOC")
    axs.set_ylabel("State of charge [MWh]", color="#ff7f0e")
    axs.set_ylim(0, DEMO_CAP_MWH * 1.05)
    a2.set_title(f"With {DEMO_CAP_MWH:.0f} MWh battery — {batt_out['cost_per_kg_da']:.1f} DA/kg")
    a2.legend(loc="upper left", fontsize=9)
    a2.set_xlabel("Hour of day (local time)")
    a2.set_xlim(0, 24)
    a2.set_xticks(range(0, 25, 2))
    fig.suptitle(f"Battery dispatch — Ghardaïa clear summer, {DEMAND_KG:.0f} kg/day "
                 f"(real data)\nblue night = cheap power, red = 17–21 h peak",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    p = FIGURES_DIR / "battery_day.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


def sizing_figure(pv, base):
    caps = [0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
    energy_cpk, lcoh = [], []
    for cap in caps:
        if cap == 0.0:
            cost, h2 = base["total_cost_da"], base["total_h2_kg"]
        else:
            out = optimize_day_battery(pv, DEMAND_KG,
                                       Battery.from_hours(cap, BATTERY_HOURS))
            cost, h2 = out["total_cost_da"], out["total_h2_kg"]
        daily_capex = DAILY_CAPEX_DA_PER_KWH * cap * 1000.0
        energy_cpk.append(cost / h2)
        lcoh.append((cost + daily_capex) / h2)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(caps, energy_cpk, "o-", color="#2ca02c",
            label="energy cost only (battery helps)")
    ax.plot(caps, lcoh, "s-", color="#d62728",
            label="energy + amortized battery CAPEX")
    imin = int(np.argmin(lcoh))
    ax.annotate(f"min LCOH at {caps[imin]:.0f} MWh",
                xy=(caps[imin], lcoh[imin]), xytext=(caps[imin] + 1.5, lcoh[imin] + 30),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.set_xlabel("Battery size [MWh] (4-hour)")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title(f"Battery sizing — Ghardaïa clear summer, {DEMAND_KG:.0f} kg/day\n"
                 f"CAPEX {BESS_CAPEX_USD_PER_KWH:.0f} $/kWh, CRF {_CRF:.3f} → "
                 f"{DAILY_CAPEX_DA_PER_KWH:.1f} DA/kWh/day")
    ax.grid(alpha=0.3)
    ax.legend()
    p = FIGURES_DIR / "battery_sizing.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p, caps, energy_cpk, lcoh


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    pv = representative_days()["clear_summer"]["pv_mw"]
    base = optimize_day(pv, DEMAND_KG, seed=0)
    demo = optimize_day_battery(pv, DEMAND_KG,
                                Battery.from_hours(DEMO_CAP_MWH, BATTERY_HOURS))
    print(f"no battery {base['cost_per_kg_da']:.1f} DA/kg -> "
          f"{DEMO_CAP_MWH:.0f} MWh {demo['cost_per_kg_da']:.1f} DA/kg "
          f"(energy saves {100*(base['total_cost_da']-demo['total_cost_da'])/base['total_cost_da']:.1f}%)")
    print(f"saved: {day_figure(pv, base, demo)}", flush=True)

    p, caps, e_cpk, lcoh = sizing_figure(pv, base)
    print(f"saved: {p}")
    print(f"\nbattery daily CAPEX: {DAILY_CAPEX_DA_PER_KWH:.2f} DA/kWh/day")
    print(f"  {'cap_MWh':>7} {'energy/kg':>10} {'LCOH/kg':>9}")
    for c, e, l in zip(caps, e_cpk, lcoh):
        print(f"  {c:>7.0f} {e:>10.1f} {l:>9.1f}")
    # break-even battery CAPEX (where daily savings = daily CAPEX at best size)
    best_e = int(np.argmin(e_cpk))
    sav_da = base["total_cost_da"] - e_cpk[best_e] * base["total_h2_kg"]
    cap_kwh = caps[best_e] * 1000.0
    if cap_kwh > 0:
        be_daily = sav_da / cap_kwh
        be_usd = be_daily * 365.0 / (USD_TO_DA * _CRF)
        print(f"break-even battery CAPEX (pure arbitrage): ~{be_usd:.0f} $/kWh "
              f"(vs assumed {BESS_CAPEX_USD_PER_KWH:.0f})")
    print(f"total runtime: {time.perf_counter() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
