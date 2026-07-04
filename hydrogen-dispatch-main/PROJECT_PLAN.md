# Project Plan — Hydrogen Dispatch Optimization

**Thesis:** Automatic Optimization of Hydrogen Production by Dispatching Solar and Grid Power to an Electrolyzer Under Variable Environmental and Operating Conditions, using an ETAP-based electrical digital twin.

**Degree:** M2 Automation, Boumerdes. One-semester, simulation-only, no hardware.

This document is the single source of truth for the restart. Follow the phases in order. The Python side (everything except the ETAP GUI work) can later be handed to Claude Code.

---

## 1. What this project IS

A working, intelligent **power dispatch controller** that, for any operating condition (solar irradiance, ambient temperature, electricity tariff), decides how to split power between the **solar array** and the **utility grid** to feed a **PEM electrolyzer** — while keeping the electrical network within safe limits — and either **minimizes the cost per kilogram of hydrogen** or **maximizes hydrogen output**.

It is demonstrated through a live dashboard and validated against a professional ETAP model.

## 2. What this project is NOT

- Not a hardware build. No prototype, no SCADA, no real-time controller deployment.
- Not an inverter-control study (no GFM/GFL, no LVRT, no fault analysis).
- Not a deep-reinforcement-learning project.
- **Not a surrogate-model project.** The surrogate is dropped from the core. If time remains at the end, it may appear as a short "future work / acceleration experiment," nothing more.
- Not a battery-storage study (mention as future work only).

If a task touches anything in this list beyond a one-paragraph literature mention, stop.

---

## 3. The toolset

**Front of house (what the jury sees — the priority deliverables):**
- **ETAP** — one-line diagram, component configuration, base-case load flow, color-coded results, screenshots and a live run across sunny/cloudy/night. The credibility showpiece.
- **Streamlit** — interactive demo dashboard: sliders for irradiance/temperature/tariff, live charts, optimal dispatch and hydrogen output updating in real time. The highest-impact build.
- **Plotly** — modern, interactive charts inside the dashboard and for key figures.
- **draw.io** — clean system architecture diagram.

**Back of house (the engine — correct but never jury-facing):**
- **pandapower** — the automatable load-flow engine, validated against ETAP. Generates results and provides in-loop feasibility checks.
- **NumPy / SciPy** — PV and electrolyzer physics.
- **pymoo** — the optimizer (PSO or GA). PySwarms is the simpler pure-PSO fallback.
- **pandas** — data handling.

**Writing:** LaTeX on Overleaf, figure-heavy. Zotero for references.

---

## 4. System architecture

```
Inputs:  irradiance G, ambient temp T, tariff
   |
   v
[ PV model ]  -> available solar power P_pv(G, T)
   |
   v
[ Dispatch decision ]  choose electrolyzer setpoint P_elz
   |                    -> P_grid = P_elz - P_pv (import the difference)
   v
[ pandapower load flow ]  -> bus voltages, transformer/line loading
   |                         -> feasibility (limits respected?)
   v
[ Electrolyzer model ]  -> H2 rate (Faraday), efficiency
   |
   v
[ Optimizer (pymoo) ]  search P_elz that minimizes cost/kg (or maximizes H2)
                       subject to: voltages in [0.95, 1.05] pu, loading < 100%
   |
   v
Outputs: optimal dispatch, H2 output, cost/kg, network status
   |
   v
[ Streamlit dashboard ]  live demonstration
```

**Division of labor:** ETAP is the *reference model and the visuals*. pandapower is the *working engine* that runs the numbers, validated to agree with ETAP. The PV physics, the electrolyzer/hydrogen physics, and the optimizer all live in Python.

---

## 5. Repository structure (for Claude Code)

```
hydrogen-dispatch/
├── README.md
├── requirements.txt
├── data/
│   ├── etap_parameters.md        # network params extracted from ETAP (manual)
│   └── scenarios.csv             # generated operating points
├── src/
│   ├── physics/
│   │   ├── pv_model.py           # P_pv from G, T
│   │   └── electrolyzer_model.py # polarization curve, Faraday's law, efficiency
│   ├── network/
│   │   └── grid_model.py         # builds pandapower net, runs load flow, returns feasibility
│   ├── optimization/
│   │   ├── objective.py          # cost/kg and H2 objectives + constraint checks
│   │   └── optimizer.py          # pymoo problem setup and run
│   ├── scenarios.py              # sunny / cloudy / night + parameter sweeps
│   └── pipeline.py               # one operating point end-to-end
├── app/
│   └── dashboard.py              # Streamlit demo
├── notebooks/
│   └── validation.ipynb          # pandapower vs ETAP base-case comparison
└── results/
    ├── figures/
    └── tables/
```

Keep modules small and independently testable. No module imports a surrogate.

---

## 6. Build phases (follow in order)

**Phase 0 — Setup.** Create the repo and Python environment. Install: pandapower, pymoo (or pyswarms), numpy, scipy, pandas, plotly, streamlit. Commit a `requirements.txt`.

**Phase 1 — ETAP model (manual, GUI).** Build the one-line diagram: external grid, transformer, PV array, electrolyzer as a controllable load, buses. Run the base-case load flow. Confirm it is stable and within limits. Record every parameter (ratings, impedances, voltage levels, base values) into `data/etap_parameters.md`. Capture clean screenshots.

**Phase 2 — pandapower replica + validation (critical).** Rebuild the exact same network in `grid_model.py` from the recorded parameters. Run load flow. **Confirm pandapower reproduces ETAP's base-case bus voltages and transformer loading within tolerance** (target: voltages within ~1%, loading within a few %). Document the comparison in `validation.ipynb`. Do not proceed until they match — every later result depends on this.

**Phase 3 — Physics layer.** Implement `pv_model.py` (P_pv = P_stc·(G/G_stc)·[1+γ(Tc−T_stc)]) and `electrolyzer_model.py` (polarization curve → power, Faraday's law → H2 rate, efficiency). Sanity-check each against known values.

**Phase 4 — Single-point pipeline.** In `pipeline.py`, take one (G, T, tariff): compute available solar, set a dispatch, run pandapower for feasibility, compute H2 and cost. Confirm the full chain runs for one point.

**Phase 5 — Optimizer.** In `optimizer.py`, wrap the pipeline with pymoo. Decision variable: electrolyzer setpoint (and grid import). Objective: min cost/kg or max H2. Constraints: voltage and loading limits. Return the optimal dispatch and a convergence record.

**Phase 6 — Scenarios + results.** Run sunny / cloudy / night and a sweep over G and T. Collect metrics, generate figures (Plotly) and tables into `results/`.

**Phase 7 — Dashboard.** Build `dashboard.py`: sliders for G/T/tariff, a "Run optimization" button, live charts of dispatch, H2, cost/kg, network status, and a convergence plot. Polish it — this is the defense centerpiece. Record a 60-second backup demo video.

**Phase 8 — Writing.** Map results into the chapters (Section 7), polish ETAP and dashboard screenshots, rehearse the live demo.

---

## 7. Thesis chapter mapping

- **Ch.1 General Introduction** — exists (general intro).
- **Ch.2 State of the Art** — exists, but **needs a revision pass**: the positioning/gap and "proposed approach" sections were written around the surrogate. Rewrite them around the new framing — professional tools are accurate but GUI-bound and not easily automated for batch optimization; this work delivers an automated, validated dispatch optimizer with a live demonstration. Keep the surrogate review as background only; move it to future work. The electrolyzer, PV, microgrid, digital-twin, and optimization sections stay.
- **Ch.3 Description of the Proposed System** — the ETAP model and overall architecture (Phase 1).
- **Ch.4 Modeling** — PV and electrolyzer math, the pandapower network model, the ETAP-vs-pandapower validation, and the optimization problem formulation (Phases 2–5).
- **Ch.5 Implementation and Results** — the optimizer, the dashboard, and the scenario results (Phases 5–7).
- **Ch.6 Conclusion** — summary, answers to objectives, limitations, future work (surrogate acceleration, battery storage, real weather data).

---

## 8. Key decisions to hold onto

- **Demo-first.** The dashboard and ETAP visuals are the deliverables that win this jury. Build and polish them, don't leave them to the last week.
- **ETAP = reference + visuals; pandapower = engine.** Keep the wording precise in every chapter; never imply ETAP generated the dataset if pandapower did.
- **Surrogate is out of the spine.** Optional bonus at the very end, framed as acceleration/future work.
- **The contribution is real:** a working, validated intelligent dispatch controller with a live demonstration. That is solid M2 work on its own.
- **Validation is non-negotiable:** pandapower must agree with ETAP's base case before any results are trusted.

---

## 9. Notes for Claude Code (read before working)

- You handle the **Python side only**. ETAP is manual GUI work the author does; you consume its parameters from `data/etap_parameters.md`.
- Build strictly **phase by phase**; do not jump ahead.
- Keep each module small, documented, and unit-testable.
- **Do not add a surrogate model** unless explicitly told to.
- Default optimizer is pymoo; only switch to PySwarms if asked.
- Treat the pandapower-vs-ETAP base-case match as a hard gate — flag it loudly if values diverge.
- All charts go through Plotly; the demo is Streamlit.
