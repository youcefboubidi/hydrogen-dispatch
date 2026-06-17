"""PSO convergence figure — the optimization engine 'at work'.

Runs the daily-dispatch PSO (the inner optimizer that MPC calls each step) on
the clear-summer day at 200 kg/day, with several random seeds, and plots the
best objective (daily grid cost) against generation. Shows the swarm converging
to the least-cost dispatch — and converging to the SAME value across seeds
(reproducible).

Outputs: results/figures/pso_convergence.png

Run from the repo root:  python scripts/run_pso_convergence.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.config import Config
from pymoo.optimize import minimize as pymoo_minimize

from src.day_dispatch import _DayProblem
from src.pv_pysam import representative_days

Config.warnings["not_compiled"] = False

FIGURES_DIR = REPO_ROOT / "results" / "figures"
DEMAND_KG = 200.0


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    prof = representative_days()["clear_summer"]
    pv = prof["pv_mw"]

    fig, ax = plt.subplots(figsize=(9, 5.2))
    colors = ["#1f77b4", "#2ca02c", "#d62728"]
    finals = []
    for seed, c in zip((0, 1, 2), colors):
        res = pymoo_minimize(_DayProblem(pv, DEMAND_KG), PSO(pop_size=60),
                             ("n_gen", 300), seed=seed, save_history=True,
                             verbose=False)
        best = [float(a.opt.get("F")[0, 0]) for a in res.history]
        gens = np.arange(1, len(best) + 1)
        ax.plot(gens, best, color=c, lw=1.8, label=f"seed {seed}")
        finals.append(best[-1])

    ax.set_yscale("log")
    ax.set_xlabel("PSO generation")
    ax.set_ylabel("Best objective — daily grid cost [DA] (log scale)")
    ax.set_title("PSO convergence — least-cost daily dispatch\n"
                 "(clear summer, 200 kg/day; 60 particles, 3 seeds)")
    ax.grid(alpha=0.3, which="both")
    ax.legend(title="random seed")
    ax.annotate(f"converges to ≈ {np.mean(finals):.0f} DA/day\n(same for all seeds)",
                xy=(len(gens) * 0.6, np.mean(finals)),
                xytext=(len(gens) * 0.35, np.mean(finals) * 2.2),
                fontsize=10, arrowprops=dict(arrowstyle="->", color="#555"))
    path = FIGURES_DIR / "pso_convergence.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved: {path}  (final costs: "
          f"{', '.join(f'{x:.0f}' for x in finals)} DA)")


if __name__ == "__main__":
    main()
