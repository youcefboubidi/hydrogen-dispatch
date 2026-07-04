"""'A day in the life' animation of the optimal dispatch (defense showpiece).

Animates one representative day's optimal 15-minute dispatch on real Ghardaïa
data: the PV curve filling in, the electrolyzer setpoint riding it, the
time-of-use price bands, and live KPIs (cumulative H2, cumulative grid cost,
current grid import/export). Saves an animated GIF.

Run from the repo root:  python scripts/animate_day.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from pymoo.config import Config

from src.day_dispatch import STEP_H, STEPS, optimize_day
from src.pv_data import representative_days

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
DEMAND_KG = 200.0
DAY = "clear_summer"


def _shade(ax):
    ax.axvspan(0, 6, color="#cfe8ff", alpha=0.5, zorder=0)
    ax.axvspan(22.5, 24, color="#cfe8ff", alpha=0.5, zorder=0)
    ax.axvspan(17, 21, color="#ffd6d6", alpha=0.6, zorder=0)


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    prof = representative_days()[DAY]
    out = optimize_day(prof["pv_mw"], DEMAND_KG, seed=0)
    x = np.arange(STEPS) * STEP_H
    pv = out["pv_mw"]
    sp = out["setpoints"]
    h2_cum = np.cumsum(out["h2_kg"])
    cost_cum = np.cumsum(out["cost_da"])
    grid = out["grid_p_mw"]

    fig, ax = plt.subplots(figsize=(10, 5.6))

    def update(t):
        ax.clear()
        _shade(ax)
        ax.plot(x[:t + 1], pv[:t + 1], color="#2ca02c", lw=1.8,
                label="available PV")
        ax.step(x[:t + 1], sp[:t + 1], where="post", color="#1f77b4",
                lw=1.5, label="electrolyzer setpoint")
        ax.fill_between(x[:t + 1], sp[:t + 1], step="post",
                        color="#1f77b4", alpha=0.2)
        ax.axvline(x[t], color="black", lw=0.8, alpha=0.5)
        ax.set_xlim(0, 24)
        ax.set_ylim(0, 0.85)
        ax.set_xticks(range(0, 25, 2))
        ax.set_xlabel("Hour of day (local time)")
        ax.set_ylabel("Power [MW]")
        flow = ("import" if grid[t] > 1e-4 else
                "export" if grid[t] < -1e-4 else "balanced")
        ax.set_title(f"A day in the life — Ghardaïa clear summer, "
                     f"{DEMAND_KG:.0f} kg/day  ·  t = {int(x[t]):02d}:"
                     f"{int((x[t] % 1) * 60):02d}")
        ax.text(0.015, 0.97,
                f"H2 so far: {h2_cum[t]:6.1f} kg\n"
                f"grid cost: {cost_cum[t]:7.0f} DA\n"
                f"grid now : {grid[t]:+.3f} MW ({flow})",
                transform=ax.transAxes, va="top", ha="left", fontsize=10,
                family="monospace",
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))
        ax.legend(loc="upper right", fontsize=9)
        return []

    anim = FuncAnimation(fig, update, frames=STEPS, interval=120, blit=False)
    out_path = FIGURES_DIR / "day_animation_ghardaia.gif"
    anim.save(out_path, writer=PillowWriter(fps=9))
    plt.close(fig)
    print(f"saved: {out_path}  ({STEPS} frames, "
          f"{out['cost_per_kg_da']:.1f} DA/kg)")


if __name__ == "__main__":
    main()
