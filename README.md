# hydrogen-dispatch

Automatic optimization of hydrogen production by dispatching solar and grid power to a PEM
electrolyzer under variable environmental and operating conditions, validated against an
ETAP-based electrical digital twin. M2 Automation thesis project (Boumerdes), simulation-only.

**Status:** Phase 0 (scaffolding + environment) and Phase 2 (pandapower replica of the ETAP
network, validated against the ETAP base cases) are complete. Phases 3-7 (physics models,
pipeline, pymoo optimizer, scenarios, Streamlit dashboard) exist as documented stubs only.

Authoritative documents:

- [PROJECT_PLAN.md](PROJECT_PLAN.md) — the single source of truth (scope, phases, architecture).
- [data/etap_parameters.md](data/etap_parameters.md) — every ETAP network parameter and the
  load-flow results the pandapower model must reproduce.

## Layout

```
hydrogen-dispatch/
├── requirements.txt              # Phase 0-2 deps (pymoo/streamlit/plotly come in later phases)
├── data/
│   └── etap_parameters.md        # ETAP parameters + validation targets (scenarios.csv: Phase 6)
├── src/
│   ├── physics/                  # pv_model.py, electrolyzer_model.py        (Phase 3 stubs)
│   ├── network/
│   │   └── grid_model.py         # pandapower replica of the ETAP network    (IMPLEMENTED)
│   ├── optimization/             # objective.py, optimizer.py                (Phase 5 stubs)
│   ├── scenarios.py              # operating-condition scenarios             (Phase 6 stub)
│   └── pipeline.py               # one operating point end-to-end            (Phase 4 stub)
├── app/
│   └── dashboard.py              # Streamlit demo                            (Phase 7 stub)
├── notebooks/
│   └── validation.ipynb          # pandapower vs ETAP comparison             (IMPLEMENTED)
└── results/
    ├── figures/
    └── tables/                   # validation table CSV lands here
```

## Setup

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Run the Phase 2 validation

Headless (executes the notebook in place, outputs saved into it):

```powershell
.venv\Scripts\jupyter nbconvert --to notebook --execute --inplace notebooks\validation.ipynb
```

Interactive:

```powershell
.venv\Scripts\jupyter lab notebooks\validation.ipynb
```

The notebook rebuilds the two-bus network from `src/network/grid_model.py`, runs the three ETAP
operating points (SUNNY / NIGHT / PV_EXPORT) with a Newton-Raphson load flow, and prints a
side-by-side PASS/FAIL comparison against the ETAP targets in
[data/etap_parameters.md](data/etap_parameters.md) section 4. Hard gate: voltages within
±0.01 pu, transformer loading within 2 percentage points, flows within 2 %, and negative grid P
(reverse power flow) in PV_EXPORT.
