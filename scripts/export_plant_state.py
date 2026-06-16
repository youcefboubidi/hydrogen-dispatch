"""Export the real per-timestep plant state to JSON for the 3D web app.

Takes a representative day's optimal dispatch (real CAMS+PySAM PV, least-cost
hourly setpoints), runs the ETAP-validated pandapower load flow at every 15-min
step, and writes the full electrical state — bus voltages, transformer loading,
and device currents/powers — to app/plant_state.json.

Every number the web app shows comes from this file, i.e. from the validated
load flow — nothing is invented.

Run from the repo root:  python scripts/export_plant_state.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from pymoo.config import Config

from src.day_dispatch import STEP_H, STEPS, optimize_day
from src.network.grid_model import build_network, run_case
from src.pv_pysam import representative_days

Config.warnings["not_compiled"] = False

APP_DIR = REPO_ROOT / "app" / "plant_3d"
SQRT3 = 3.0 ** 0.5
DAY = "clear_summer"
DEMAND_KG = 200.0


def _current_a(p_mw, q_mvar, v_ll_kv):
    """3-phase line current [A] from P,Q [MW,Mvar] and line-line voltage [kV]."""
    s_kva = (p_mw ** 2 + q_mvar ** 2) ** 0.5 * 1000.0
    return s_kva / (SQRT3 * v_ll_kv) if v_ll_kv > 0 else 0.0


def main():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    prof = representative_days()[DAY]
    pv96 = prof["pv_mw"]
    out = optimize_day(pv96, DEMAND_KG, seed=0)
    sp96 = out["setpoints"]

    net = build_network()
    bi = {n: net.bus.index[net.bus["name"] == n][0] for n in ("MainBus", "SecondaryBus")}
    ti = net.trafo.index[net.trafo["name"] == "T1"][0]
    li = net.load.index[net.load["name"] == "ELY"][0]
    gi = net.sgen.index[net.sgen["name"] == "PVA1"][0]
    ei = net.ext_grid.index[net.ext_grid["name"] == "U1"][0]

    series = []
    for s in range(STEPS):
        pv = float(pv96[s])
        p = float(sp96[s])
        on = p > 0.0
        run_case(net, pv_mw=pv, ely_in_service=on, ely_p_mw=p if on else None)

        v_main = float(net.res_bus.at[bi["MainBus"], "vm_pu"])
        v_sec = float(net.res_bus.at[bi["SecondaryBus"], "vm_pu"])
        vll_main = 11.0 * v_main
        vll_sec = 0.415 * v_sec
        loading = float(net.res_trafo.at[ti, "loading_percent"])
        i_hv = float(net.res_trafo.at[ti, "i_hv_ka"]) * 1000.0
        i_lv = float(net.res_trafo.at[ti, "i_lv_ka"]) * 1000.0
        grid_p = float(net.res_ext_grid.at[ei, "p_mw"])
        grid_q = float(net.res_ext_grid.at[ei, "q_mvar"])
        ely_p = float(net.res_load.at[li, "p_mw"]) if on else 0.0
        ely_q = float(net.res_load.at[li, "q_mvar"]) if on else 0.0
        pv_p = float(net.res_sgen.at[gi, "p_mw"])

        hour = s // 4
        minute = (s % 4) * 15
        series.append({
            "t": f"{hour:02d}:{minute:02d}",
            "step": s,
            "MainBus": {"vm_pu": round(v_main, 4), "kv": round(vll_main, 3)},
            "SecondaryBus": {"vm_pu": round(v_sec, 4), "kv": round(vll_sec, 4)},
            "T1": {"loading_pct": round(loading, 1),
                   "i_hv_a": round(i_hv, 1), "i_lv_a": round(i_lv, 1)},
            "U1": {"p_mw": round(grid_p, 4), "q_mvar": round(grid_q, 4),
                   "i_a": round(_current_a(grid_p, grid_q, vll_main), 1),
                   "flow": "import" if grid_p > 1e-4 else
                           ("export" if grid_p < -1e-4 else "idle")},
            "PVA1": {"p_mw": round(pv_p, 4),
                     "i_a": round(_current_a(pv_p, 0.0, vll_sec), 1)},
            "ELY": {"p_mw": round(ely_p, 4), "q_mvar": round(ely_q, 4),
                    "i_a": round(_current_a(ely_p, ely_q, vll_sec), 1),
                    "on": on},
        })

    doc = {
        "meta": {
            "site": "Ghardaia, Algeria (32.59N, 3.73E)",
            "day": prof["date"], "demand_kg_day": DEMAND_KG,
            "cost_per_kg_da": round(out["cost_per_kg_da"], 1),
            "total_h2_kg": round(out["total_h2_kg"], 1),
            "source": "real CAMS+ERA5 -> PySAM PV; ETAP-validated pandapower load flow",
            "limits": {"v_min_pu": 0.95, "v_max_pu": 1.05, "loading_max_pct": 100.0},
            "step_minutes": int(STEP_H * 60),
        },
        "topology": {
            "ratings": {"transformer_mva": 2.0, "hv_kv": 11.0, "lv_kv": 0.415,
                        "electrolyzer_mw": 0.8, "pv_ac_mw": 0.5342,
                        "inverter_mva": 0.63},
            "nodes": ["U1", "MainBus", "T1", "SecondaryBus", "PVA1", "ELY"],
        },
        "timeseries": series,
    }
    out_path = APP_DIR / "plant_state.json"
    out_path.write_text(json.dumps(doc, indent=1))
    # Also bake into a JS file so the web app runs by opening index.html (no
    # server / no CORS): the single real data source for the visualization.
    (APP_DIR / "plant_data.js").write_text(
        "window.PLANT_STATE = " + json.dumps(doc) + ";\n")
    peak_load = max(d["T1"]["loading_pct"] for d in series)
    vmin = min(d["SecondaryBus"]["vm_pu"] for d in series)
    print(f"wrote {out_path}  ({len(series)} steps)")
    print(f"  day {prof['date']}, {out['cost_per_kg_da']:.1f} DA/kg, "
          f"{out['total_h2_kg']:.0f} kg")
    print(f"  T1 loading peak {peak_load:.1f} %, SecondaryBus min {vmin:.4f} pu "
          f"(limits 0.95-1.05 pu, <=100%)")


if __name__ == "__main__":
    main()
