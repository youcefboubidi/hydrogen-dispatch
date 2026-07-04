# Thesis change log

**Purpose.** The thesis (`Thesis_3_1*.docx`, kept local) gets rewritten **once, at
the end**, after the system is complete. Until then, every code/system change is
logged here with its thesis implication, so the final rewrite is a precise
checklist instead of a memory exercise. **Update this file after every change we
apply.**

> Section/equation numbers below come from `PROJECT_PLAN.md` §7 and our code
> references; reconcile them against the actual `.docx` during the rewrite (the
> document has not yet been read line-by-line — deferred by request).

**Chapter map (PROJECT_PLAN.md §7).**
Ch.1 Introduction · Ch.2 State of the Art · Ch.3 Proposed System (ETAP +
architecture) · Ch.4 Modeling (PV, electrolyzer, pandapower + ETAP validation,
optimization formulation, eqs 4.6–4.11) · Ch.5 Implementation & Results · Ch.6
Conclusion.

---

## Pending changes by chapter (the rewrite checklist)

### Ch.2 — State of the Art
- **DEMOTE** the surrogate model from the core to "future work / acceleration"
  background only. (Predates this work; per PROJECT_PLAN.)
- **REWRITE** the positioning/gap and "proposed approach": *professional tools
  (ETAP) are accurate but GUI-bound and not easily automated for batch
  optimization → this work delivers an automated, ETAP-validated dispatch
  optimizer with a live demonstration.*
- **ADD** literature: electricity time-of-use tariffs / demand-side management;
  green-hydrogen dispatch & techno-economics; metaheuristics (PSO) for energy
  scheduling.
- **KEEP** the electrolyzer, PV, microgrid, digital-twin, optimization sections.

### Ch.3 — Proposed System
- **ADD** real-data inputs to the architecture: real weather (PVGIS) and the
  real Algerian MV time-of-use tariff (CREG 51NM) now feed the controller.
  Update the architecture diagram to show the weather + tariff inputs.
- **CITE the data provenance** (data/methodology section) — the production PV chain:
  real **CAMS Radiation Service v4.6** all-sky irradiance for Ghardaïa
  (32.5873 N, 3.7314 E; 15-min; satellite-derived, Copernicus/CAMS) → fed through
  **NREL SAM (PySAM)** PV-system model → 15-min AC generation; air temperature +
  wind from **ERA5** reanalysis (Copernicus CDS). Refs: CAMS/SoDa; NREL SAM;
  Hersbach et al. 2020 (ERA5). (PVGIS-SARAH2, used earlier, is now superseded for
  the dispatch but remains a valid cross-check source.)
- **UPDATE** the site description: plant sited at **Ghardaïa** (high-irradiance
  southern site, national solar-program region, well-documented reference solar
  station).

### Ch.4 — Modeling
- **CONTROL FORMULATION (the control-engineering core — lead with this).** Cast
  the dispatch as feedback control of the validated plant: *state* = time,
  battery SOC, cumulative H₂; *control inputs* = electrolyzer setpoint (+ battery
  power); *measured disturbance* = PV (weather), with deterministic time-of-use
  prices; *constraints* = bus voltage 0.95–1.05 pu, transformer ≤ 100 %,
  electrolyzer operating window, daily H₂ demand; *cost functional* = daily grid
  cost. *Controller* = **receding-horizon MPC** (re-optimize over the remaining
  horizon on a forecast, apply the first action, re-plan on realized PV).
  Benchmarks: perfect-foresight (bound) and a reactive rule-based controller.
- **PV:** the **production** PV is **NREL SAM (PySAM)** — single-axis tracking,
  ~669 kWp DC / 534 kW AC inverter (matched to the ETAP 0.5342 MW interconnect),
  driven by the real CAMS irradiance → 15-min AC time series. The engineering
  model (eq 2.8 + NOCT, γ = −0.35 %/°C, anchored to 0.5342 MW full-sun) is
  **retained as the documented, ETAP-anchored model and a full-sun cross-check**,
  no longer in the dispatch loop.
- **Electrolyzer:** polarization curve (E_rev + Tafel activation + ohmic),
  Faraday H₂ rate, specific energy, part-load efficiency; stack sized for
  0.800 MW at 2 A/cm².
- **Network:** **KEEP** the pandapower↔ETAP validation (24/24 checks PASS) — solid.
- **ADD** an economics section: the CREG MV time-of-use tariff (pointe 8.11 /
  pleines 2.16 / creuses 1.21 DA/kWh; demand charge 4.37 DA/kW/month) and the
  UTC→local-time alignment.
- **REWRITE the optimization formulation (eqs 4.6–4.11).** The OLD formulation
  (single variable `p_elz`, two modes `max_h2` / `min_cost`) is **REPLACED** by:
  decision = the 24-hour hourly setpoint vector; objective = minimize daily grid
  energy cost; constraint = total daily H₂ ≥ demand (plus network feasibility and
  the electrolyzer operating window); solver = PSO over the 24-vector. **SCRAP**
  the mode-toggle description entirely.
- **DOCUMENT the resolution choice** (defend it explicitly): the data, PV, energy,
  cost, and network feasibility are all evaluated at the **native 15-minute**
  resolution of the real series; the dispatch *decision* is **hourly** (24
  setpoints). Rationale: hourly commitment is the power-industry day-ahead
  standard and keeps the PSO low-dimensional and **reproducible** (24 vs 96
  variables); 15-min control adds negligible value while prices are hourly and
  there is no storage yet — it becomes worthwhile with the Stage-2 battery, where
  a policy-based 15-min controller is the planned upgrade.

### Ch.5 — Implementation & Results
- **SCRAP** the old headline results (monotonic `max_h2` = always full blast,
  `min_cost` = ride the sun). They were an artifact of the over-simple
  single-operating-point model.
- **REPLACE** with the Stage 1 real-data results (real **CAMS+PySAM 15-min** PV,
  2023 representative days — clear-summer 2023-06-23, cloudy-summer 2023-07-03,
  clear-winter 2023-01-31):
  - the intelligent 15-minute schedules visibly riding free midday solar and
    dodging the 17–21h peak (clear-summer 200 kg/day ≈ 27.7 DA/kg);
  - the cost-vs-demand curve with its knee;
  - the **smart-vs-traditional baseline comparison** (constant baseload / greedy
    produce-ASAP): on real data, the optimizer is **~50–59 % cheaper** at
    200 kg/day (27.7 vs 67.9 constant, vs 55.8 greedy) and up to 100 % cheaper at
    low demand fully covered by solar; greedy degrades badly at high demand.
  - the **full-year 2023 simulation** (364 days, **100 kg/day** demand): **36.4 t
    H₂/yr at 18.4 DA/kg average** (6.3 summer → 33.1 winter), **71 % solar-powered**,
    0.67 M DA/yr grid cost, demand met every day; a calendar heatmap
    (`annual_calendar.png`) and a monthly cost/solar-fraction chart
    (`annual_monthly.png`) show the strong seasonal pattern — cheap, green
    summers vs dear winters. (Demand lowered 200→100 kg/day on 2026-06-20; at
    100 kg the plant's real PV covers far more of the load, so cost/kg roughly
    halves and the solar fraction rises from 37 % to 71 %.)
  - a **"day in the life" animation** of the optimal dispatch (`day_animation_
    ghardaia.gif`) for the live defense.
- **UPDATE** the dashboard description: supervisory Streamlit view (demand input,
  schedule, network feasibility).

### Ch.4 — Modeling (Stage 2 addition: battery)
- **ADD a battery/ESS model and its dispatch.** Battery: energy capacity, power
  rating, round-trip efficiency, starts empty. **Optimizer architecture (document
  and defend):** the dispatch is **decomposed** — PSO searches only the 24 hourly
  electrolyzer setpoints (the non-linear, demand-constrained part), and for each
  candidate the **battery is operated optimally by a linear program** (charge /
  discharge / SOC minimizing grid cost vs the time-of-use price, subject to power
  and energy limits). Rationale to state: a joint 48-variable PSO over
  setpoints+battery was found to converge unreliably (non-monotonic sizing); the
  decomposition gives provably-optimal storage per candidate, reproducible and
  monotone results, and a low-dimensional PSO.
- **Ch.5 battery results.** Day with/without battery: it charges on cheap night
  power + surplus solar and discharges through the peak, cutting energy cost
  53.2 → 39.2 DA/kg (−26 % at 4 MWh, high-demand day) — a real dispatch/control
  behaviour. **Economic verdict (supporting feasibility, NOT a headline):** with
  amortized CAPEX (250 $/kWh, CRF 0.133), LCOH is minimized at **0 MWh** — storage
  is **not cost-justified under the CREG tariff**; break-even on pure arbitrage is
  ~20 $/kWh (≈12× below today's ~250). It pays only under much higher price
  volatility (spot/wholesale) or far cheaper batteries.
- **Discipline framing:** keep battery *economics* as a supporting section; the
  *dispatch behaviour* is the control-relevant part. Pending decision: re-frame
  the whole thesis around the **supervisory/MPC controller** (states, inputs,
  disturbances, constraints, cost functional) so it reads as Control Engineering.

### Ch.6 — Conclusion
- **UPDATE** the contribution statement: an automated, ETAP-validated dispatch
  optimizer that, on real weather and the real tariff, finds non-obvious
  least-cost schedules measurably cheaper than traditional operation.
- **Future work:** battery/ESS (Stage 2), network sized to bind / hosting
  capacity (Stage 3), surrogate acceleration (demoted from the core),
  multi-objective Pareto (cost vs CO₂).

---

## Change log (chronological)

### 2026-06-20 — Dashboard visual redesign (defense polish)
- Added `app/_theme.py` (injected CSS + `hero()`/`section()`/`sidebar_brand()`
  helpers) and `.streamlit/config.toml` (base palette). The app now has a gradient
  hero banner, a dark branded sidebar with data/tariff/engine provenance cards,
  icon tabs with an active-underline, KPI **metric cards** (accent border, shadow,
  hover lift), chart/table cards, and styled buttons/alerts/expanders. Each tab
  uses a styled section header with a one-line subtitle. Verified by live Chrome
  screenshots (Daily + Annual) and `AppTest` (5 tabs, 0 exceptions). Cosmetic only
  — no result or model change. Thesis impact: Ch.5 dashboard screenshots refresh.

### 2026-06-20 — Annual run lowered to 100 kg/day
- `scripts/run_annual.py` `DAILY_DEMAND_KG` 200 → **100**; regenerated
  `results/tables/annual_2023.csv` + the three annual figures. New annual KPIs:
  **36.4 t H₂/yr, 18.4 DA/kg avg, 71 % solar, 0.67 M DA/yr**, all days met
  (was 72.8 t / 45.8 DA/kg / 37 % at 200 kg/day). The Annual dashboard tab reads
  the CSV, so it now shows 100 kg/day automatically (with a caption derived from
  the data). Thesis impact: Ch.5 annual-performance numbers updated (see above).

### 2026-06-20 — Dashboard expanded to the 5-tab defense centerpiece
- `app/dashboard.py` refactored from one tab into a slim router over a new
  `app/tabs/` package (`daily`, `control`, `annual`, `baselines`, `validation`)
  with shared loaders/palette/chart in `app/_shared.py`. Tabs: **(1) Daily
  Dispatch** — an optional battery toggle (PSO setpoints + LP-optimal storage,
  SOC overlay) and a **real-data PV-day picker** ("Representative / Any date"
  toggle) that drives the dispatch off any of the 364 full real days in the
  Ghardaïa 2023 CAMS→PySAM dataset (2023-01-02 … 12-31), not just the three
  presets; **(2) Control Strategy** — MPC vs perfect-foresight vs
  rule-based on a forecast-error day, the control-engineering core; **(3) Annual
  Performance** — full-year 2023 KPIs + calendar heatmap + monthly pattern (reads
  `annual_2023.csv`); **(4) Smart vs Traditional** — cost-vs-demand vs
  constant/greedy baselines; **(5) Validation & Plant** — 24/24 ETAP↔pandapower
  PASS table + network figures + link-out to the three.js 3D twin.
- Hybrid compute: live PSO/MPC for single-day tabs (cached, Run-gated), precomputed
  CSVs for annual/baseline. Verified end-to-end via Streamlit `AppTest` (5 tabs,
  0 exceptions; clear-summer 200 kg = 27.8 DA/kg, annual 72.8 t/yr @ 45.8 DA/kg,
  MPC 38 % cheaper than rule-based). Plan recorded in `DASHBOARD_PLAN.md`.
- Thesis impact: **Ch.5 dashboard description** is now the full supervisory view
  (demand/battery input, schedule, control-strategy comparison, annual scaling,
  network feasibility) — the live defense centerpiece (PROJECT_PLAN Phase 7).

### 2026-06-15 — Control core: MPC supervisory controller + 3D digital twin
- `src/mpc.py`: the dispatch **recast as feedback control**. Three controllers:
  perfect-foresight (open-loop optimum, the bound); **MPC** (receding-horizon —
  day-ahead persistence forecast + intraday clearness correction, re-optimize
  each hour, apply the first action, re-plan as actual PV is realized);
  reactive rule-based (time-blind constant rate). Demo day 2023-04-08 (clear day
  forecast from a cloudy one — large forecast error): MPC **35.2 vs 33.0 DA/kg
  optimum (+6.4 %)** and **56 % cheaper than rule-based** — i.e. it rejects the
  PV disturbance. `scripts/run_mpc_comparison.py` → multi-day figure + CSV.
- `scripts/export_plant_state.py` + `app/`: the real per-timestep load-flow state
  (bus voltages, T1 loading, device currents/powers) from the ETAP-validated
  pandapower model → `plant_state.json` / `plant_data.js`; a **3D three.js web
  app** (`app/viz_*`) renders it ETAP-style with a time slider — every value real.
- Thesis impact: **re-frames the thesis as Control Engineering.** Ch.4 gains the
  control formulation; Ch.5 gains the control-strategy comparison + the live demo;
  Ch.6 contribution becomes "a supervisory (MPC) controller", with the economics
  and data as the objective/disturbance inputs.

### 2026-06-15 — ERA5 temp/wind: real 2023 replaces the placeholder
- `data/make_sam_weather.py` now fuses CAMS irradiance with **real ERA5 2023**
  temperature + wind (nearest cell to Ghardaïa, wind = √(u²+v²)), not the
  PVGIS-TMY placeholder. Regenerated `data/ghardaia_sam_2023_15min.csv`
  (temp mean 22.9 °C, max 47.5; irradiance unchanged). **Action:** re-run PySAM
  on this file to get the final fully-actual-2023 generation, then the dispatch /
  annual / battery results regenerate on it. Provenance is now CAMS + ERA5 + SAM.

### 2026-06-15 — Stage 2: battery (PSO setpoints + optimal-LP storage)
- `src/battery_dispatch.py`: battery dispatch by decomposition — 24-var PSO over
  electrolyzer setpoints, battery operated optimally by a scipy-HiGHS linear
  program per candidate. Verified monotone: on the clear-summer day at 280 kg,
  energy cost falls 53.2 → 46.5 → 43.1 → 39.2 DA/kg for 1/2/4 MWh (−12.6/−19/−26 %),
  SOC bounded, demand met. (First attempt — a joint 48-var PSO — under-converged
  and gave a non-monotonic sizing curve; switched to the decomposition.)
- `scripts/run_battery.py`: day with/without battery + economic sizing figure
  (energy cost vs LCOH including amortized battery CAPEX).
- Thesis impact: Ch.4 gains the battery model + optimizer-architecture rationale;
  Ch.5 gains the battery results + the economic verdict on storage (see below).

### 2026-06-15 — Full-year analysis + day-in-the-life animation
- `scripts/run_annual.py`: full-year 2023 dispatch (364 days) → annual KPIs
  (72.8 t/yr, 3.33 M DA/yr, 45.8 DA/kg avg, 37 % solar) and seasonal figures
  (`annual_cost_vs_doy.png`, `annual_monthly.png`, `annual_calendar.png`) +
  `results/tables/annual_2023.csv`.
- `scripts/animate_day.py`: animated GIF of the optimal clear-summer dispatch.
- Thesis impact: Ch.5 gains an "annual performance" subsection (seasonal cost
  and solar-fraction) and a live-demo animation.

### 2026-06-15 — Real PV: CAMS irradiance → PySAM, 15-min accounting
- Replaced the engineering-model/PVGIS PV path in the dispatch with the **real
  PySAM (NREL SAM) AC generation** for Ghardaïa 2023 (`ghardaia_solar_generation.csv`,
  35,040 rows, 15-min, peak 0.529 MW, 1,436 MWh/yr, 2,147 kWh/kWp). Driven by real
  **CAMS** irradiance; temperature/wind currently a **PVGIS-TMY placeholder**
  (ERA5 2023 download pending — re-run `data/make_sam_weather.py` + PySAM when it
  lands). Built `data/make_sam_weather.py` (CAMS+temp → SAM weather file),
  `src/pv_pysam.py` (load + representative days), refactored `src/day_dispatch.py`
  to **hourly decisions / 15-min accounting** (vectorized), updated the runners.
- Brief integrity note for the methodology: an initial PySAM run used Texas
  (NSRDB) weather; it was **replaced with real Ghardaïa CAMS data** before any
  result was used — no location was misrepresented.
- Thesis impact: Ch.3 (PV provenance = CAMS→PySAM, ERA5), Ch.4 (PV = NREL SAM;
  resolution choice documented), Ch.5 (results now on real 2023 data).

### 2026-06-14 — Stage 1: real-data time-of-use dispatch
- Added: real CREG MV ToU tariff (`src/economics.py`); real PVGIS weather
  (`data/fetch_weather.py`, Ghardaïa in-plane); representative days
  (`src/profiles.py`); demand-driven least-cost 24-hour PSO dispatch
  (`src/day_dispatch.py`); figures (schedules, cost-vs-demand); smart-vs-traditional
  comparison (`scripts/compare_baselines.py`).
- Fixed: UTC→local timezone alignment between weather and tariff.
- Thesis impact: Ch.3 (real inputs), Ch.4 (economics layer + **rewritten**
  optimization formulation), Ch.5 (new results **replace** the old sweeps),
  Ch.6 (contribution + future work). Removed the manual `max_h2`/`min_cost`
  toggle → single objective (least-cost to meet demand); the flat 4.68 DA/kWh
  assumption is replaced by the time-of-use tariff.

### Earlier — Phases 0–7 (already on `main`)
- Phase 2: ETAP↔pandapower validation, 24/24 PASS → Ch.4 validation (**keep**).
- Phases 3–5: PV + electrolyzer physics, single-point pipeline, PSO → Ch.4
  modeling (note: the single-point optimization is **superseded** by Stage 1's
  time-of-use formulation).
- Phase 6: scenario sweeps → Ch.5 (the monotonic sweeps are now **demoted /
  replaced**).
- Phase 7: Streamlit dashboard → Ch.5 implementation.
