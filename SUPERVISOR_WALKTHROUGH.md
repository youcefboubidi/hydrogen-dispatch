# Supervisor walkthrough — code tour & talking points

A guided script for walking your supervisor through the project: the big
picture, **what PSO and MPC are**, how the **inputs become the outputs**, and a
file-by-file tour with "what to say" for each. Read it top to bottom, or jump to
a section. Files are linked so you can open them as you talk.

---

## 0. The 30-second opening (say this first)

> "I built an **automatic supervisory controller** for a solar + grid +
> electrolyzer hydrogen plant. Every step, it decides *how much power to draw
> and from where* to make the required hydrogen at **least cost**, while keeping
> the electrical network inside its safe limits. The plant model is **validated
> against ETAP** (24/24 checks), the solar and weather are **real Ghardaïa 2023
> data**, and the prices are the **real Algerian CREG time-of-use tariff**. The
> controller is **Model-Predictive Control (MPC)**, and the optimizer inside it
> is **Particle-Swarm Optimization (PSO)**."

Then frame it as a **control problem**, not a data study: disturbance (weather),
control input (electrolyzer setpoint), constraints (voltage / transformer), and
a cost objective (the tariff).

---

## 1. The big picture — how inputs become outputs

```
   REAL INPUTS                    THE ENGINE                       OUTPUTS
 ─────────────────         ───────────────────────────       ──────────────────
 CAMS irradiance  ─┐
 ERA5 temp/wind   ─┼─►  PySAM  ─►  PV(t), 15-min   ─┐
                   │   (make_sam_weather.py)         │
 CREG tariff      ─┼─►  price(hour)  ────────────────┼─►  PSO optimizer    ─►  least-cost
 (economics.py)    │                                 │   (day_dispatch.py)     setpoints + DA/kg
 ETAP ratings     ─┼─►  pandapower network  ─────────┤        │
 (grid_model.py)   │   (validated vs ETAP)           │        ▼
 PEM physics      ─┼─►  P ↔ H₂ curve  ───────────────┘   MPC controller    ─►  closed-loop
 (electrolyzer)    │                                     (mpc.py)              dispatch, 37 days
 H₂ demand (kg/day)┘                                          │
                                                              ▼
                                                    load flow per 15 min  ─►  3D digital twin
                                                    (export_plant_state.py)   (app/plant_3d)
```

One sentence: **real weather + real prices + a validated plant model** go in;
a **controller that decides the dispatch** turns them into **least-cost hydrogen**,
and we visualize the result as an **animated 3D load-flow twin**.

---

## 2. What is PSO? (the optimizer)

**Particle-Swarm Optimization** is how we find the cheapest dispatch plan for a
day. Explain it like this:

- A "plan" is **24 numbers**: how hard to run the electrolyzer in each hour.
- There is **no formula** that gives the best plan directly — the electrolyzer
  curve is non-linear and the tariff jumps between three rates. So we **search**.
- PSO releases a **swarm of ~60 candidate plans** ("particles") into the space
  of possible plans. Each particle remembers the best plan it personally found,
  and the swarm shares the best plan anyone found. Every step, each particle
  **moves toward both** — so the swarm collectively "flies" toward the cheapest
  plan, like a flock settling on the best feeding ground.
- The score for each plan is **grid energy cost + a big penalty if it misses the
  hydrogen demand**. PSO minimizes that score.
- **Show the convergence graph (slide 5 / `results/figures/pso_convergence.png`):**
  it drops from a random ~30,000 DA start to the optimum ~5,565 DA in ~150
  generations, and **all three random seeds land on the same value** → the
  result is reproducible.

Why PSO and not calculus? It's **gradient-free** — it needs no derivatives, so
it handles the non-linear electrolyzer and the discontinuous price directly.

> Code: [`src/day_dispatch.py`](src/day_dispatch.py) — `optimize_day(pv, demand_kg)`.

---

## 3. What is MPC? (the controller)

**Model-Predictive Control** is the actual control strategy — PSO is just the
solver it calls. The problem: we don't know tomorrow's clouds perfectly. MPC
handles that with **feedback**:

1. **Measure** what really happened so far today (realized solar, hydrogen made).
2. **Forecast** the rest of the day (start from yesterday's solar profile,
   then correct it by how clear today has actually been so far).
3. **Re-optimize** the remaining hours with PSO to meet the *remaining* demand
   at least cost.
4. **Apply only the next hour's** setpoint — then throw the rest away.
5. Next hour, the **real** weather arrives (a disturbance vs the forecast), and
   it **re-plans from scratch**. This is the "receding horizon."

This is textbook supervisory control: it **rejects the weather disturbance**
through feedback. We benchmark it against two references:

- **Perfect-foresight** — cheats by knowing the whole day in advance. The
  unreachable *lower bound* on cost.
- **Rule-based** — reactive, time-blind: just run at a constant rate. What a
  plant does *without* a smart controller.

**The headline result (slide 8 / `results/figures/mpc_comparison.png`):** across
37 days of 2023, MPC lands **+2.4 %** above the perfect-foresight optimum (so it
recovers ~98 % of an unreachable bound) and is **−51 % cheaper** than the
reactive rule — despite imperfect forecasts.

> Code: [`src/mpc.py`](src/mpc.py) — `mpc_dispatch(...)`, `rule_based_dispatch(...)`.

---

## 4. File-by-file tour

Open each file as you reach it. Grouped by role; the order is a good narration order.

### A. The validated plant model — *the credibility anchor*
**[`src/network/grid_model.py`](src/network/grid_model.py)** — builds the
electrical network in **pandapower**: utility grid (U1) → 11 kV bus → 2 MVA
transformer (T1) → 0.415 kV bus → solar array (PVA1) + electrolyzer (ELY).
`build_network()` assembles it; `run_case(net, pv_mw, ely_p_mw, …)` runs a
Newton-Raphson load flow.
> **Say:** "I rebuilt our ETAP network in open-source pandapower and checked it
> against the professional ETAP load flow — **24/24 checks pass** on voltages,
> currents and transformer loading. That's what makes everything downstream
> trustworthy and *automatable*."

### B. The real solar input
**[`data/make_sam_weather.py`](data/make_sam_weather.py)** — fuses **real CAMS
satellite irradiance** with **real ERA5 temperature/wind** into one weather file
for NREL's solar model. **[`src/pv_pysam.py`](src/pv_pysam.py)** — runs that
weather through **NREL SAM (PySAM)** to get the plant's AC solar power every 15
minutes for all of 2023; `representative_days()` pulls out a clear-summer,
cloudy-summer and clear-winter day.
> **Say:** "The solar isn't invented — it's CAMS satellite irradiance plus ERA5
> reanalysis for **Ghardaïa**, run through the same engine (PySAM) that industry
> uses, at 15-minute resolution."

### C. The real price input
**[`src/economics.py`](src/economics.py)** — the **CREG time-of-use tariff**
(code 51NM): `grid_price_da_per_kwh(hour)` returns **1.21 DA/kWh** at night,
**2.16** in the day, **8.11** during the 17:00–21:00 peak. `energy_cost_da(...)`
bills only imported power.
> **Say:** "This is the official Algerian medium-voltage tariff. The peak is
> **6.7× the night rate** — that price gap is *why* timing the electrolyzer
> matters, and it's what makes 'least-cost dispatch' a real decision."

### D. The hydrogen physics
**[`src/physics/electrolyzer_model.py`](src/physics/electrolyzer_model.py)** —
the **PEM electrolyzer**: a polarization curve (reversible voltage + Tafel
activation + ohmic loss) and **Faraday's law** for hydrogen output.
`mdot_h2_kg_per_h(p_mw)` gives kg/h for any power; rated 0.800 MW → ~14–15 kg/h
at ~54 kWh/kg, with a 10 % minimum turndown (0.080 MW).
**[`src/physics/pv_model.py`](src/physics/pv_model.py)** — an engineering PV
model (NOCT temperature correction) from the earlier phase; PySAM is the
production solar source now.
> **Say:** "This is the Chapter-2 physics: how electrical power converts to
> hydrogen, non-linearly. The optimizer calls a fast lookup-table version of
> this curve."

### E. The optimizer — PSO
**[`src/day_dispatch.py`](src/day_dispatch.py)** — the core daily optimizer.
`evaluate_day(setpoints_24, pv_96)` scores one plan (vectorized, 15-min
accounting); `optimize_day(pv_96, demand_kg)` runs **PSO** over the 24 hourly
setpoints to find the **least-cost plan that meets the demand**. (See §2.)
> **Say:** "Decisions are hourly — realistic for an operator — but the energy
> accounting is every 15 minutes for accuracy. PSO searches the 24-hour plan."

### F. The controller — MPC
**[`src/mpc.py`](src/mpc.py)** — the supervisory controller and its benchmarks:
`mpc_dispatch(...)` (closed-loop, forecast-driven) and `rule_based_dispatch(...)`
(reactive baseline); the perfect-foresight bound is `optimize_day` on the known
day. (See §3.)
> **Say:** "This is the control contribution: MPC nearly matches an unreachable
> optimum and crushes the reactive rule, using only a forecast plus feedback."

### G. The storage study (honest result)
**[`src/battery_dispatch.py`](src/battery_dispatch.py)** — adds a battery: PSO
picks the electrolyzer setpoints, then a **linear program** (`scipy` HiGHS)
finds the *optimal* battery charge/discharge for that plan.
> **Say:** "I tested adding a battery. It cuts the energy bill ~26 %, but at the
> Algerian tariff spread it **doesn't pay back its cost** — break-even is around
> \$20/kWh, ~12× below today's price. An honest feasibility finding, not a sales
> pitch."

### H. Result generators (the scripts that make the figures)
- **[`scripts/run_day_dispatch.py`](scripts/run_day_dispatch.py)** → the 3-day
  dispatch schedule (slide 6).
- **[`scripts/compare_baselines.py`](scripts/compare_baselines.py)** → −50–59 %
  vs traditional operation (slide 7).
- **[`scripts/run_mpc_comparison.py`](scripts/run_mpc_comparison.py)** → the MPC
  vs optimum vs rule comparison (slide 8).
- **[`scripts/run_annual.py`](scripts/run_annual.py)** → full-year heatmap +
  72.8 t/yr (slide 9).
- **[`scripts/run_battery.py`](scripts/run_battery.py)** → battery-sizing curve.
- **[`scripts/run_pso_convergence.py`](scripts/run_pso_convergence.py)** → the
  PSO convergence figure (slide 5).
> **Say:** "Every figure in the slides is reproducible — one script each, all
> from the real data."

### I. The 3D digital twin (the deliverable to demo)
**[`app/plant_3d/`](app/plant_3d/)** — an interactive Three.js 3D model of the
plant. **[`scripts/export_plant_state.py`](scripts/export_plant_state.py)** runs
the validated load flow at every 15-min step and writes the real numbers the app
displays.
> **Say:** "This is like an ETAP load-flow run, but **animated over the whole
> day**. Drag the time slider — voltages, currents and transformer loading
> update live, colour-coded against the limits. **Every number comes from the
> validated load flow — nothing is faked.**"

> *(Earlier-phase scaffolding — `src/pipeline.py`, `src/optimizer.py`,
> `src/optimization/`, `src/scenarios.py` — predates the real-data pivot; mention
> only if asked. The live path is the files above.)*

---

## 5. Suggested live-demo order (if you have a laptop)

1. **Open the 3D twin** — `app/plant_3d/index.html` (just double-click it).
   Drag the time slider from midnight to the 17:00 peak and show the
   electrolyzer **shut down** while voltages stay green.
2. **Show `results/figures/day_schedule_ghardaia.png`** — the controller riding
   solar mid-day and dodging the red peak band.
3. **Show `pso_convergence.png`** — "this is the optimizer settling on the
   cheapest plan."
4. **Show `mpc_comparison.png`** — "and this is the controller tracking the
   optimum across the year."

---

## 6. Questions he may ask — short answers

- **"Why not just run it at full power whenever the sun shines?"** → That's the
  reactive rule, and it's **51 % more expensive**: it ignores the night/peak
  price gap and over-imports during expensive hours. (slide 7/8)
- **"Is the tariff real?"** → Yes — CREG code 51NM, the official MV time-of-use
  schedule. See [`src/economics.py`](src/economics.py) header for the source URL.
- **"Is the solar real?"** → Yes — CAMS + ERA5 for Ghardaïa, through NREL PySAM,
  15-min, full 2023.
- **"How do I know the electrical model is right?"** → It reproduces our ETAP
  load flow exactly — **24/24 checks**.
- **"Why PSO instead of gradient methods / MILP?"** → The electrolyzer curve is
  non-linear and the tariff is discontinuous; PSO is gradient-free and robust,
  and it converges reproducibly (same answer across seeds).
- **"What's the control novelty?"** → Casting plant dispatch as **receding-horizon
  MPC** with a real disturbance (weather) and hard network constraints, and
  showing it recovers ~98 % of the perfect-foresight optimum with feedback.
- **"What's left?"** → Tighten the Ch. 4–5 control write-up, robustness across
  more weather years, optionally bind the network so limits activate, polish the
  demo for the defense.

---

## 7. One-line close

> "It's a **validated, automated supervisory controller** running on **real
> Ghardaïa data and real Algerian prices** — it makes hydrogen for **half the
> cost** of running the plant blindly, and you can **watch it work** in the 3D
> twin."
