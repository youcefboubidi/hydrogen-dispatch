# Presenter 1 — Speaking Script (slides 1–14, ≈10:00)

**How to use this:** rehearse at a calm 130–140 words per minute. `⏸` = breathe, count one second.
`[...]` = stage direction, don't read aloud. Bold = hit the word. 
Target: hand over at **10:00**. If you're past 10:30 at the handover, compress slides 4–5 next run — never slides 11 or 14.

---

## SLIDE 1 · Title · 0:00 → 0:30

Honourable president, distinguished members of the jury — good morning, and thank you.

My name is **BOUBIDI Youcef**, and with my colleague **BOUDJADJA Mohamed Akrem** we present our master's thesis:
**Automated Supervisory Dispatch Control of a Solar–Grid–Electrolyzer Hydrogen Plant.**

In one sentence: we built a controller that roughly **halves** the cost of producing green hydrogen — and today, we will show it to you **running**. ⏸

---

## SLIDE 2 · Agenda · 0:30 → 1:00

Our defense has four parts, about twenty minutes in total.

First, the context — what green hydrogen is, and why producing it cheaply is a **control** problem.
Second, our system and method — the plant, the real data, and the controller design.
Then **BOUDJADJA Mohamed Akrem** takes over: the results, the live demonstrations, and our conclusions.

So: I present the plant and the problem — **BOUDJADJA Mohamed Akrem** presents the control and the payoff.

---

## SLIDE 3 · Part I divider · (5 s)

Let's begin with the context.

---

## SLIDE 4 · Hydrogen 101 · 1:00 → 2:00

So — hydrogen. What is it, and why does the world care?

Hydrogen is an energy **carrier**, not an energy source: we make it, store it, ship it — and when we use it, the exhaust is **water**.

[point at the bar chart] One kilogram holds **thirty-three point three** kilowatt-hours — about **three times** a kilogram of diesel.

And it is not a niche product. The world already consumes about **ninety-seven million tonnes** every year — fertiliser, refining, steel. But almost all of it is **grey**: made from fossil gas, at nine to ten kilos of CO₂ per kilo of hydrogen.

The clean version is **green** hydrogen: an electrolyzer splits water with renewable electricity. A real machine consumes about fifty to fifty-five kilowatt-hours per kilogram — roughly **sixty percent** efficient. ⏸

Which means electricity is about **two-thirds of the cost** of every green kilogram.

[point at the banner] So keep this chain: green hydrogen is an **electricity-cost** problem → which is a **timing** problem → which is a **control** problem. Our whole thesis is that one sentence.

---

## SLIDE 5 · Why now, why Algeria · 2:00 → 3:00

Why now — three verifiable facts.

**One**: fossil fuels are finite — proven oil reserves are about **fifty years** at today's production — and increasingly carbon-priced: from **twenty twenty-six**, the European carbon border tax, CBAM, makes exporters pay for embedded CO₂. That touches Algeria's main export market directly.

**Two**: solar became the cheapest electricity in history — down about **ninety percent** since twenty-ten. But only when the sun shines.

**Three**: in the IEA net-zero pathway, hydrogen demand reaches about **four hundred thirty** million tonnes by twenty-fifty — over four times today's market.

[gesture to the satellite image] And here is our site — **Ghardaïa**, seen by Sentinel-2 on the twenty-third of June, twenty twenty-three — the exact day we use as "clear summer" throughout this thesis. World-class sun: about **two thousand one hundred fifty** kilowatt-hours per kilowatt-peak per year.

For a country where hydrocarbons are around ninety percent of export revenue — green hydrogen is how desert sun becomes an **exportable product**.

---

## SLIDE 6 · Three ways to run the plant · 3:00 → 4:10

Now the problem — made concrete. ⏸

Same plant. Same real summer day. Same quota: **two hundred kilograms** of hydrogen. Three ways to run it — and every number here is computed with our validated model.

[point — left card] Strategy one: **ignore the sun**, run flat on the grid. Result: **one hundred forty-one** dinars per kilogram — because a flat schedule pays the evening peak, every single evening. Five times the smart cost. A fortune.

[point — middle card] Strategy two: **solar only**. The energy is free — but you produce **one hundred seventeen** kilograms. Fifty-nine percent of the quota, and the stack sits idle almost half the day. Free — but it starves the demand.

[point — right card] Strategy three: the **smart mix**. Cheap night grid, free midday sun, shut down through the peak: **twenty-seven point eight** dinars per kilogram — and the full two hundred kilograms. ⏸

But — **which** hours? **How** hard? Under weather you cannot predict?

That is twenty-four decisions, every day, automatically, inside network limits. **That** is the control problem of this thesis.

---

## SLIDE 7 · Four promises · 4:10 → 4:55

So here is our contract with you — four promises for the next fifteen minutes.

**One** — a plant model you can trust: validated **twenty-four out of twenty-four** against the industry-standard reference.
**Two** — a controller that decides: measure, forecast, re-optimise — every hour, automatically.
**Three** — proof that it pays: about **half** the cost of naive operation, and ninety-eight percent of what a perfect weather oracle could achieve.
**Four** — something you can touch: **a live demonstration** of the controller.

At the end of the talk, we will come back to this list and tick every box.

---

## SLIDE 8 · Part II divider · (5 s)

Part two — how we built it.

---

## SLIDE 9 · The method in one picture · 5:00 → 5:45

Here is the whole method, in one picture — four stages. And these thumbnails are **real figures** from the thesis; you will see each one up close.

Stage one: **real inputs** — a full measured year of Ghardaïa weather, and the official tariff.
Stage two: **a plant we proved** — the electrical model, validated against the industry reference.
Stage three: **the controller** — forecast, re-optimise, apply. Every hour. Closed loop.
Stage four: **proof, live**.

One promise as we go: each tool is introduced at the moment it does its work — you'll see the small badges at the top of the slides.

---

## SLIDE 10 · Real data & the tariff · 5:45 → 6:50

Stage one — the inputs. And I want to insist on this: **real data, not assumptions**.

[left figure] This is all of twenty twenty-three: satellite irradiance from **CAMS**, temperature and wind from **ERA5**, run through NREL's physical simulator, **PySAM** — fifteen-minute resolution, the whole year. One thousand four hundred thirty-five megawatt-hours — about twenty-one-fifty kilowatt-hours per kilowatt-peak. The three representative days we use are marked on the curve.

[right table] And the prices are the **official Sonelgaz grid** — medium voltage, tariff code fifty-one-N-M, quoted to the centime. Night — **one point two zero five**. Day — **two point one six**. And the evening peak, seventeen hundred to twenty-one hundred: **eight point one one** dinars per kilowatt-hour. ⏸

Peak is **six point seven times** the night rate. That spread is the economic engine of everything that follows.

---

## SLIDE 11 · Prove the model · 6:50 → 7:50

Stage two. Before trusting any result — we prove the model.

The plant's official electrical study lives in **ETAP** — the industry-standard power-system tool. Trusted everywhere. But it is a graphical tool — you cannot script it across a year of dispatch decisions.

So we rebuilt the **same network** in **pandapower**, an open-source load-flow engine we can automate: the grid, the eleven-kV bus, the two-MVA transformer, down to the PV array and the electrolyzer.

Then: same Newton-Raphson load flow, three operating points — sunny, night, and PV-export — and we compared, number by number. [point at the stat card] **Twenty-four out of twenty-four** checks agree. Voltages within one hundredth of a per-unit. Transformer loading within two points. Flows within two percent — **including the direction of reverse power flow**. ⏸

Honestly: we did not trust pandapower until it reproduced ETAP. It does. Everything downstream stands on that anchor.

---

## SLIDE 12 · The electrolyzer · 7:50 → 8:35

Stage two, continued — the machine itself.

[schematic, top right] A PEM electrolyzer. Water enters at the anode; protons cross the membrane; hydrogen leaves at the cathode — driven by the DC power **we** control.

[curves, bottom] We model it from physics: reversible voltage, plus activation, plus ohmic losses — that is the polarisation curve on the left. Faraday's law turns current into hydrogen — that is the map on the right.

Three numbers to keep: at rated **zero point eight megawatts**, it makes **fourteen point six kilos per hour**, at about **fifty-four** kilowatt-hours per kilo. And below **ten percent** load, the stack switches off.

Notice the curve is **non-linear** — hold that thought; it decides our choice of optimiser in a moment.

---

## SLIDE 13 · Dispatch as a control problem · 8:35 → 9:20

And now the heart of the thesis: dispatch, written as a **control problem**.

[walk the table] The **state** — time, storage, and the hydrogen produced so far today. The **control input** — the electrolyzer setpoint. The **disturbance** — and this is the key word — the available solar power: measured now, forecast ahead. The **constraints** — voltages, transformer loading, the daily demand, the turndown limit. And the **cost functional** — the daily grid bill under the time-of-use tariff.

[right box] And why is there no textbook answer? Four reasons. The electrolyzer curve is **non-linear**. The tariff is **discontinuous** — a six-point-seven-times jump at five p.m. The input set has a **hole** — off, or between ten and a hundred percent. And tomorrow's sun is **unknown**.

[bottom strip] So our method has **two parts**, and you will see them in order: first, a **solver** that finds the cheapest possible day. Then, a **loop** that survives being wrong about the weather. ⏸

---

## SLIDE 14 · The problem, formally · 9:20 → 9:55

And formally — because precision matters here.

[left panel] The plant, in discrete-time state-space. One state: **x**, the hydrogen made so far today. **x of k-plus-one equals x of k, plus T times g of u of k** — where g is the electrolyzer map you just saw. The disturbance enters through the grid import: **q equals u minus d, clipped at zero** — clouds never stop the hydrogen; they only change its price.

Note the structure: a static non-linearity feeding an integrator — a **Hammerstein** plant. Locally, it is simply an integrator: **G of z equals K over z minus one**.

[right panel] And the objective is **economic**: minimise the bill — the sum of price times grid import — subject to one terminal constraint: **x at hour twenty-four must reach the demand D**. There is no setpoint to track. The tariff itself shapes the behaviour. ⏸

That is the problem, stated formally.

[turn to your colleague] **BOUDJADJA Mohamed Akrem** will now show you how we solve it — every hour — and what that is worth.

---
---

## The numbers you must own (do not paraphrase these)

| Number | Meaning |
|---|---|
| 33.3 kWh/kg | energy **in** 1 kg of H₂ (LHV) — 3× diesel |
| 50–55 kWh/kg (≈54 at rated) | energy **to make** 1 kg → ≈60 % efficient |
| 97 Mt/yr → ≈430 Mt by 2050 | today's H₂ market → IEA net-zero pathway |
| ≈50 yr / CBAM 2026 / −90 % | oil reserves · EU border tax · solar cost fall |
| 2,150 kWh/kWp · 1,435 MWh | Ghardaïa yield · our 2023 total |
| **141 / 117 (59 %) / 27.8** | grid-flat DA/kg · solar-only kg · smart DA/kg |
| 8.1147 / 2.1645 / 1.2050 · **6.7×** | official 51NM rates · peak-to-night ratio |
| **24/24** | ETAP ↔ pandapower validation checks |
| 14.6 kg/h · 0.080–0.800 MW | rated H₂ rate · operating window |

## If a jury member interrupts you

- **"Is the data real?"** → slide 10 is the answer: CAMS + ERA5 through PySAM, and the official grille to the centime.
- **"Why two network tools?"** → ETAP is the trusted reference; pandapower is what we can script. Validated 24/24 — backup A1 has every row.
- **"33.3 vs 54 — which is it?"** → 33.3 is stored energy; 54 is consumed to make it; ratio ≈ 62 % efficiency. Both on purpose.
- **"Why is d not in your state equation?"** → the stack draws its setpoint regardless of the power's origin; the grid covers u − d. Clouds change the **bill**, not the feasibility.
- Anything deeper on PSO/MPC → "my colleague covers exactly that next" — and let BOUDJADJA Mohamed Akrem take it.

## Delivery notes

- Rehearse to **9:45** so real-time lands at 10:00.
- Look at the jury, not the screen. Point at the slide, then face them to speak.
- The two moments to slow down: the **6.7×** on slide 10, and **24/24** on slide 11. They are your credibility.
- Do not read the slides. The audience reads faster than you speak — say what the slide *means*.
