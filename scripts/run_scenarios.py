"""Phase 6 scenario characterization of the PSO dispatch optimizer.

Runs, at the REDUCED PSO budget (pop 10 x 15 generations):

    1. BUDGET CHECK (gate) — the six Phase 5 verification cases at both the
       full Phase 5 budget and the reduced budget. The reduced-budget optima
       must land within +/-0.005 MW of the analytic optima or everything
       else is aborted. Verdict recorded in results/tables/budget_check.csv.
    2. NAMED SCENARIOS — SUNNY / HOT / CLOUDY / NIGHT in both modes
       -> results/tables/scenarios.csv
    3. IRRADIANCE SWEEP — G = 0..1200 W/m2 step 50, Ta = 25 degC, both modes,
       with the analytic min-cost optimum overlaid as a validation column
       -> results/tables/sweep_irradiance.csv
    4. TEMPERATURE SWEEP — Ta = 10..45 degC step 5 at G = 1000 W/m2
       -> results/tables/sweep_temperature.csv
    5. FIGURES -> results/figures/sweep_*.png (working figures; thesis
       versions will be restyled from the CSVs)

Usage (from anywhere; paths resolve relative to the repo):

    python scripts/run_scenarios.py                  # everything (default)
    python scripts/run_scenarios.py --stage budget   # gate + named scenarios
    python scripts/run_scenarios.py --stage sweeps   # sweeps + figures;
                                                     # requires a recorded
                                                     # all-PASS budget check
"""

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pymoo.config import Config

from src.optimizer import optimize_dispatch
from src.physics.electrolyzer_model import P_MIN_MW, P_RATED_MW
from src.physics.pv_model import pv_ac_power_mw
from src.pipeline import TARIFF_DA_PER_KWH

Config.warnings["not_compiled"] = False

# Reduced PSO budget for all Phase 6 characterization runs, validated by the
# budget check against the analytic optima before any sweep may run.
POP_REDUCED = 10
NGEN_REDUCED = 15
TOL_P_MW = 0.005   # acceptance tolerance on |p_opt - expected| [MW]
SEED = 0
MODES = ("max_h2", "min_cost")

TABLES_DIR = REPO_ROOT / "results" / "tables"
FIGURES_DIR = REPO_ROOT / "results" / "figures"
BUDGET_CSV = TABLES_DIR / "budget_check.csv"

# The four named operating conditions (G [W/m2], Ta [degC]).
NAMED_SCENARIOS = [
    ("SUNNY", 1000.0, 25.0),
    ("HOT", 1000.0, 45.0),
    ("CLOUDY", 400.0, 25.0),
    ("NIGHT", 0.0, 25.0),
]


def p_expected_min_cost(pv_mw):
    """Analytic min-cost optimum: turndown floor when the PV cannot carry the
    minimum load, otherwise the zero-cost plateau edge min(pv, rated)."""
    return P_MIN_MW if pv_mw < P_MIN_MW else min(pv_mw, P_RATED_MW)


def p_expected(mode, pv_mw):
    """Analytic optimum per mode (max_h2: rated power — H2 is monotonic in P
    and the network never binds in this system, shown in Phase 5)."""
    return P_RATED_MW if mode == "max_h2" else p_expected_min_cost(pv_mw)


def run_point(g_wm2, t_amb_c, mode):
    """One reduced-budget optimization, flattened to a result row."""
    out = optimize_dispatch(g_wm2, t_amb_c, TARIFF_DA_PER_KWH, mode, seed=SEED,
                            pop_size=POP_REDUCED, n_gen=NGEN_REDUCED)
    r = out["result"]
    return {
        "mode": mode,
        "g_wm2": g_wm2,
        "t_amb_c": t_amb_c,
        "p_opt_mw": out["p_elz_mw"],
        "h2_kg_per_h": r["h2_kg_per_h"],
        "cost_per_kg": r["cost_per_kg"],
        "grid_p_mw": r["grid_p_mw"],
        "v_secondary_pu": r["v_secondary_pu"],
        "trafo_loading_percent": r["trafo_loading_percent"],
        "evals": out["n_evaluations"],
    }


def budget_check():
    """Six Phase 5 cases at full and reduced budget; gate on the reduced one."""
    print("=== BUDGET CHECK: full (pop 20 x 40) vs reduced "
          f"(pop {POP_REDUCED} x {NGEN_REDUCED}) ===", flush=True)
    cases = [
        ("max_h2", 1000.0, 0.800),
        ("max_h2", 0.0, 0.800),
        ("max_h2", 400.0, 0.800),
        ("min_cost", 1000.0, 0.5342),
        ("min_cost", 0.0, 0.080),
        ("min_cost", 400.0, pv_ac_power_mw(400.0, 25.0)),
    ]
    rows = []
    for mode, g, expected in cases:
        t0 = time.perf_counter()
        full = optimize_dispatch(g, 25.0, TARIFF_DA_PER_KWH, mode, seed=SEED)
        reduced = optimize_dispatch(g, 25.0, TARIFF_DA_PER_KWH, mode, seed=SEED,
                                    pop_size=POP_REDUCED, n_gen=NGEN_REDUCED)
        err = abs(reduced["p_elz_mw"] - expected)
        status = "PASS" if err <= TOL_P_MW else "FAIL"
        rows.append({
            "mode": mode, "g_wm2": g, "p_expected_mw": expected,
            "p_full_mw": full["p_elz_mw"], "p_reduced_mw": reduced["p_elz_mw"],
            "abs_err_reduced_mw": err, "status": status,
        })
        print(f"  {mode:8s} G={g:6.1f} -> full {full['p_elz_mw']:.6f} | "
              f"reduced {reduced['p_elz_mw']:.6f} | expected {expected:.6f} | "
              f"err {err:.2e} | {status}  ({time.perf_counter() - t0:.1f} s)",
              flush=True)

    table = pd.DataFrame(rows)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(BUDGET_CSV, index=False, encoding="utf-8-sig")
    print(f"\n{table.to_string(index=False)}", flush=True)
    print(f"saved: {BUDGET_CSV}", flush=True)

    if (table["status"] == "FAIL").any():
        print("\nBUDGET CHECK FAILED - the reduced budget misses at least one "
              "analytic optimum. Not running any sweep.", flush=True)
        return False
    print(f"\nBUDGET CHECK PASSED - all six reduced-budget optima within "
          f"{TOL_P_MW} MW. Sweeps use pop {POP_REDUCED} x {NGEN_REDUCED}.\n",
          flush=True)
    return True


def require_recorded_pass():
    """Gate for --stage sweeps: a recorded all-PASS budget check must exist."""
    if not BUDGET_CSV.exists():
        print(f"No budget check recorded at {BUDGET_CSV}.\n"
              "Run 'python scripts/run_scenarios.py --stage budget' first.",
              flush=True)
        return False
    table = pd.read_csv(BUDGET_CSV)
    if (table["status"] != "PASS").any():
        print(f"Recorded budget check at {BUDGET_CSV} contains FAIL rows. "
              "Not running sweeps.", flush=True)
        return False
    print(f"Recorded budget check OK ({BUDGET_CSV}): all "
          f"{len(table)} cases PASS.\n", flush=True)
    return True


def named_scenarios():
    print("=== NAMED SCENARIOS ===", flush=True)
    rows = []
    for name, g, ta in NAMED_SCENARIOS:
        t0 = time.perf_counter()
        for mode in MODES:
            rows.append({"scenario": name, **run_point(g, ta, mode)})
        print(f"  {name:6s} (G={g:6.1f} W/m2, Ta={ta:4.1f} degC) done "
              f"({time.perf_counter() - t0:.1f} s)", flush=True)

    table = pd.DataFrame(rows)[[
        "scenario", "mode", "g_wm2", "t_amb_c", "p_opt_mw", "h2_kg_per_h",
        "cost_per_kg", "grid_p_mw", "v_secondary_pu",
        "trafo_loading_percent", "evals"]]
    out_csv = TABLES_DIR / "scenarios.csv"
    table.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\n{table.to_string(index=False, float_format=lambda v: f'{v:.4f}')}",
          flush=True)
    print(f"saved: {out_csv}\n", flush=True)


def sweep(points, label, csv_name):
    """Sweep optimizer over (G, Ta) points in both modes; analytic overlay."""
    print(f"=== {label} ===", flush=True)
    rows = []
    for k, (g, ta) in enumerate(points, start=1):
        t0 = time.perf_counter()
        pv = pv_ac_power_mw(g, ta)
        per_mode = {}
        for mode in MODES:
            row = run_point(g, ta, mode)
            row["pv_available_mw"] = pv
            row["p_expected_mw"] = p_expected(mode, pv)
            rows.append(row)
            per_mode[mode] = row["p_opt_mw"]
        print(f"  [{k:2d}/{len(points)}] G={g:6.1f} W/m2 Ta={ta:4.1f} degC "
              f"(pv {pv:.4f} MW) -> max_h2 p*={per_mode['max_h2']:.4f} MW | "
              f"min_cost p*={per_mode['min_cost']:.4f} MW "
              f"({time.perf_counter() - t0:.1f} s)", flush=True)

    table = pd.DataFrame(rows)[[
        "mode", "g_wm2", "t_amb_c", "pv_available_mw", "p_opt_mw",
        "p_expected_mw", "h2_kg_per_h", "cost_per_kg", "grid_p_mw",
        "v_secondary_pu", "trafo_loading_percent", "evals"]]
    out_csv = TABLES_DIR / csv_name
    table.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"saved: {out_csv}", flush=True)

    # The analytic overlay turns the sweep into a validation.
    for mode in MODES:
        sub = table[table["mode"] == mode]
        dev = (sub["p_opt_mw"] - sub["p_expected_mw"]).abs().max()
        marker = "" if dev <= TOL_P_MW else "  ** ABOVE TOLERANCE **"
        print(f"  max |p_opt - p_expected| ({mode}): {dev:.2e} MW "
              f"(tol {TOL_P_MW}){marker}", flush=True)
    print(flush=True)
    return table


def figures(df_g, df_t):
    print("=== FIGURES ===", flush=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    g_max = df_g[df_g["mode"] == "max_h2"]
    g_min = df_g[df_g["mode"] == "min_cost"]
    saved = []

    # 1. Optimal setpoint vs irradiance, with PV curve + analytic expectation.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(g_max["g_wm2"], g_max["p_opt_mw"], "o-", label="p* max_h2")
    ax.plot(g_min["g_wm2"], g_min["p_opt_mw"], "s-", label="p* min_cost")
    ax.plot(g_min["g_wm2"], g_min["pv_available_mw"], ":", color="grey",
            label="available PV")
    ax.plot(g_min["g_wm2"], g_min["p_expected_mw"], "--", color="black",
            linewidth=1, label="analytic expectation (min_cost)")
    ax.set_xlabel("Irradiance G [W/m²]")
    ax.set_ylabel("Electrolyzer setpoint [MW]")
    ax.set_title("Optimal dispatch vs irradiance (Ta = 25 °C)")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "sweep_setpoint_vs_g.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    # 2. Cost per kg vs irradiance.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(g_max["g_wm2"], g_max["cost_per_kg"], "o-", label="max_h2")
    ax.plot(g_min["g_wm2"], g_min["cost_per_kg"], "s-", label="min_cost")
    ax.set_xlabel("Irradiance G [W/m²]")
    ax.set_ylabel("Hydrogen cost [DA/kg]")
    ax.set_title("Cost per kg at the optimum vs irradiance (Ta = 25 °C)")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "sweep_cost_vs_g.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    # 3. Hydrogen rate vs irradiance.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(g_max["g_wm2"], g_max["h2_kg_per_h"], "o-", label="max_h2")
    ax.plot(g_min["g_wm2"], g_min["h2_kg_per_h"], "s-", label="min_cost")
    ax.set_xlabel("Irradiance G [W/m²]")
    ax.set_ylabel("Hydrogen production [kg/h]")
    ax.set_title("H₂ rate at the optimum vs irradiance (Ta = 25 °C)")
    ax.grid(alpha=0.3)
    ax.legend()
    path = FIGURES_DIR / "sweep_h2_vs_g.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    # 4. Temperature sweep: setpoint and cost vs Ta.
    t_max = df_t[df_t["mode"] == "max_h2"]
    t_min = df_t[df_t["mode"] == "min_cost"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    ax1.plot(t_max["t_amb_c"], t_max["p_opt_mw"], "o-", label="p* max_h2")
    ax1.plot(t_min["t_amb_c"], t_min["p_opt_mw"], "s-", label="p* min_cost")
    ax1.plot(t_min["t_amb_c"], t_min["pv_available_mw"], ":", color="grey",
             label="available PV")
    ax1.set_ylabel("Electrolyzer setpoint [MW]")
    ax1.grid(alpha=0.3)
    ax1.legend()
    ax2.plot(t_max["t_amb_c"], t_max["cost_per_kg"], "o-", label="max_h2")
    ax2.plot(t_min["t_amb_c"], t_min["cost_per_kg"], "s-", label="min_cost")
    ax2.set_xlabel("Ambient temperature Ta [°C]")
    ax2.set_ylabel("Hydrogen cost [DA/kg]")
    ax2.grid(alpha=0.3)
    ax2.legend()
    fig.suptitle("Optimal dispatch vs ambient temperature (G = 1000 W/m²)")
    path = FIGURES_DIR / "sweep_temperature.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    saved.append(path)

    for p in saved:
        print(f"saved: {p}", flush=True)
    print(flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", choices=("budget", "sweeps", "all"),
                        default="all",
                        help="budget = gate + named scenarios; sweeps = "
                             "irradiance/temperature sweeps + figures "
                             "(requires a recorded all-PASS budget check); "
                             "all = both (default)")
    stage = parser.parse_args().stage
    t_start = time.perf_counter()

    if stage in ("budget", "all"):
        if not budget_check():
            raise SystemExit(1)
        named_scenarios()
    else:  # sweeps only: rely on the recorded verdict
        if not require_recorded_pass():
            raise SystemExit(1)

    if stage in ("sweeps", "all"):
        df_g = sweep([(float(g), 25.0) for g in range(0, 1201, 50)],
                     "IRRADIANCE SWEEP (Ta = 25 degC)", "sweep_irradiance.csv")
        df_t = sweep([(1000.0, float(ta)) for ta in range(10, 46, 5)],
                     "TEMPERATURE SWEEP (G = 1000 W/m2)",
                     "sweep_temperature.csv")
        figures(df_g, df_t)

    print(f"total runtime ({stage}): {time.perf_counter() - t_start:.1f} s",
          flush=True)


if __name__ == "__main__":
    main()
