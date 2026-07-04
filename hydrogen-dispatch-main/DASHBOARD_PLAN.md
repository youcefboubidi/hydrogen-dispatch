# Dashboard Plan — Streamlit defense centerpiece

**Goal.** Grow `app/dashboard.py` from one tab into the 5-tab live demo that tells the
full thesis story: *validate → operate → control → scale*. Scope confirmed:
**full 5-tab build**, **hybrid compute** (live PSO/MPC for single-day tabs, precomputed
CSVs for annual/baseline), **3D twin linked out** (not embedded).

Decisions held from `PROJECT_PLAN.md` / `THESIS_CHANGES.md`: ETAP = reference + visuals;
pandapower = engine; all charts via Plotly; demo-first polish; the **MPC supervisory
controller is the control-engineering spine** and gets a dedicated tab.

---

## Architecture

```
app/dashboard.py            # tab router + shared sidebar + cached runners
app/tabs/
  ├─ daily.py               # Tab 1  (refactor existing body out of dashboard.py)
  ├─ control.py             # Tab 2  MPC vs perfect-foresight vs rule-based
  ├─ annual.py              # Tab 3  full-year 2023 (reads CSV)
  ├─ baselines.py           # Tab 4  smart vs traditional + cost-vs-demand
  └─ validation.py          # Tab 5  ETAP↔pandapower + 3D twin link
app/_shared.py              # cached loaders, palette, x-axis helpers, KPI/chart utils
```

Refactor first: lift the current Tab-1 body and the cached helpers (`_load_days`,
`_run_optimization`, `_run_feasibility`, band colours, `_X_STEPS`) into `app/_shared.py`
so every tab reuses one PV loader, one palette, one dispatch chart builder. No behaviour
change — just extraction. Keep `streamlit run app/dashboard.py` as the entry point.

### Caching strategy (the hybrid contract)
- `@st.cache_data` keyed on `(day, demand, seed, battery_mwh)` for every live solve.
- Tab 1/2 solve live (PSO ~ pop60×gen300; MPC = 24 sequential horizon solves — slower,
  so **cache hard** and gate behind the Run button, never recompute on every rerun).
- Tab 3/4 read `results/tables/*.csv` only → instant, demo-safe. Add a small
  "↻ Recompute (slow)" button that shells the script, off by default.
- `@st.cache_resource` for the prebuilt battery LP (`_build_lp`) so it's not rebuilt per run.

---

## Tab-by-tab spec (with real data contracts)

### Tab 1 — Daily Dispatch  *(exists; extend)*
- **Keep** the KPI row, dispatch chart, feasibility check, hourly table.
- **Add** a sidebar **battery toggle + capacity slider** (0–8 MWh, `Battery.from_hours`).
  - OFF → `optimize_day(pv, demand)` → `{setpoints, pv_mw, grid_p_mw, h2_kg, cost_da,
    total_h2_kg, total_cost_da, cost_per_kg_da, demand_met, hourly_setpoints}`.
  - ON  → `optimize_day_battery(pv, demand, battery)` → same fields **plus**
    `batt_mw (d−c)`, `soc_mwh`, `import_mw`. Overlay a **SOC line on yaxis2** and a
    charge/discharge band; KPI row gains "Battery cycles" / "Peak SOC".
- Feasibility: `verify_day_feasibility(hourly_setpoints, pv)` unchanged.

### Tab 2 — Control Strategy ⭐  *(new; the thesis core)*
- Day picker over `consecutive_days()` (days that have a predecessor for the forecast).
  Default to a high-forecast-error day (cloudy→clear) for the disturbance-rejection story.
- Run three controllers on the same day + demand:
  - `optimize_horizon(pv_actual, prices, demand)` → **perfect-foresight bound**,
  - `mpc_dispatch(pv_actual, pv_forecast, demand)` → realized MPC,
  - `rule_based_dispatch(pv_actual, demand)` → reactive baseline.
  - Each returns `{controller, hourly_setpoints, total_h2_kg, total_cost_da,
    cost_per_kg_da, demand_met}`.
- Visuals: (a) three setpoint step-curves over PV; (b) a cost-bar with the
  **MPC gap vs optimum (%)** and **MPC saving vs rule-based (%)** called out;
  (c) one-line narrative ("MPC re-plans each hour as PV is realized → rejects the
  forecast disturbance"). Cross-check against `results/tables/mpc_comparison.csv`
  (`date,doy,pv_mwh,perfect,mpc,rule`).

### Tab 3 — Annual Performance  *(new; precomputed)*
- Read `results/tables/annual_2023.csv`
  (`date,month,day,h2_kg,cost_da,cost_per_kg_da,grid_import_mwh,solar_to_elz_mwh,green_fraction,demand_met`).
- KPIs: **72.8 t H₂/yr, 45.8 DA/kg avg, 37 % solar** (compute from the CSV, don't
  hard-code). Plotly **calendar heatmap** of cost_per_kg_da (mirrors `annual_calendar.png`)
  + monthly cost & green-fraction bars (mirrors `annual_monthly.png`). Month filter.

### Tab 4 — Smart vs Traditional  *(new; mostly precomputed)*
- The **cost-vs-demand curve with its knee** + baseline bars (constant baseload / greedy
  produce-ASAP vs optimizer): "~50–59 % cheaper at 200 kg/day, up to 100 % at low demand."
- Source from `compare_baselines.py` outputs / `baseline_comparison_ghardaia.png` data;
  optionally re-solve the optimizer point live for the currently selected demand so the
  marker tracks Tab 1.

### Tab 5 — Validation & Plant  *(new; static + link)*
- Render `results/tables/validation_pandapower_vs_etap.csv` as a **24/24 PASS** table
  (green check column). One paragraph: "pandapower reproduces the ETAP base case within
  ±0.01 pu / 2 % — every downstream result rests on this gate."
- A prominent **"Open 3D plant twin ↗"** button/link to `app/plant_3d/index.html`
  (served separately, e.g. `python -m http.server` in `app/plant_3d/`). Show
  `net_sunny.png / net_night.png / net_pv_export.png` as static previews.

---

## Build sequence
1. **Refactor** Tab-1 body + helpers into `app/_shared.py` + `app/tabs/daily.py`; verify
   `streamlit run` still renders identically. *(no new features — safety net first)*
2. **Tab 1 battery** toggle (smallest new feature, reuses the existing chart).
3. **Tab 2 Control Strategy** — highest thesis value; the reason to do this at all.
4. **Tab 3 Annual** (CSV-only, fast win).
5. **Tab 4 Baselines**, then **Tab 5 Validation + 3D link**.
6. **Demo polish**: consistent palette, "Run" gating, a 60-sec scripted click-path, and
   the backup demo video (per PROJECT_PLAN Phase 7).

## Risks / watch-items
- **MPC latency** — 24 sequential `optimize_horizon` solves per run. Cache aggressively;
  consider a reduced `n_gen` for the live demo and note it.
- **CSV BOM** — the result CSVs are UTF-8-BOM (`﻿date`); read with `encoding="utf-8-sig"`.
- **PySAM data dependency** — Tabs 1/2 need `data/ghardaia_solar_generation.csv` present;
  fail loudly with a clear message if missing (don't silently fall back).
- **3D twin assets** — keep it link-out; embedding via `components.html` breaks the
  three.js relative `lib/` paths under Streamlit's static server.
