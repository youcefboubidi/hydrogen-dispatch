const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";            // 13.33 x 7.5 in
p.author = "youcefboubidi";
p.title = "Automated Supervisory Dispatch Control — Progress Update";

const W = 13.33, H = 7.5;
const NAVY = "0E2233", NAVY2 = "16344B", TEAL = "1C7293", GOLD = "F4A623",
      INK = "1A2733", MUTE = "6B7C8F", LIGHT = "F4F7FA", WHITE = "FFFFFF",
      GREEN = "2A9D8F", CARD = "EEF3F7";
const FIG = "D:/Projects/hydrogen-dispatch/results/figures/";
const sh = () => ({ type: "outer", color: "0E2233", blur: 9, offset: 3, angle: 90, opacity: 0.18 });
const SANS = "Calibri", SERIF = "Cambria";

// ---- helpers ----
function eyebrow(s, txt) {
  s.addText(txt.toUpperCase(), { x: 0.6, y: 0.42, w: 11, h: 0.3, margin: 0,
    fontFace: SANS, fontSize: 12, bold: true, color: TEAL, charSpacing: 3 });
}
function heading(s, txt) {
  s.addText(txt, { x: 0.6, y: 0.72, w: 12.1, h: 0.8, margin: 0,
    fontFace: SERIF, fontSize: 30, bold: true, color: NAVY });
}
function fig(s, name, x, y, w, h) {
  s.addImage({ path: FIG + name, x, y, w, h, sizing: { type: "contain", w, h } });
}
function statCard(s, x, y, w, val, label, accent) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.45, rectRadius: 0.08,
    fill: { color: WHITE }, line: { color: "DCE5EC", width: 1 }, shadow: sh() });
  s.addText(val, { x: x + 0.1, y: y + 0.18, w: w - 0.2, h: 0.72, margin: 0, align: "center",
    fontFace: SERIF, fontSize: 30, bold: true, color: accent || TEAL });
  s.addText(label, { x: x + 0.12, y: y + 0.95, w: w - 0.24, h: 0.42, margin: 0, align: "center",
    fontFace: SANS, fontSize: 11.5, color: MUTE });
}
function bullets(s, items, x, y, w, h, color) {
  s.addText(items.map((t, i) => ({ text: t,
    options: { bullet: { code: "2022" }, breakLine: true, paraSpaceAfter: 9,
      fontSize: 15, color: color || INK } })),
    { x, y, w, h, margin: 0, fontFace: SANS, valign: "top" });
}

// ============ Slide 1 — Title (dark) ============
let s = p.addSlide(); s.background = { color: NAVY };
s.addShape(p.shapes.OVAL, { x: 10.6, y: -2.2, w: 5.5, h: 5.5, fill: { color: NAVY2 } });
s.addShape(p.shapes.OVAL, { x: 11.7, y: 4.6, w: 4.2, h: 4.2, fill: { color: "12283C" } });
s.addText("M2 AUTOMATION · UNIVERSITY OF BOUMERDÈS", { x: 0.7, y: 0.9, w: 11, h: 0.4, margin: 0,
  fontFace: SANS, fontSize: 13, bold: true, color: GOLD, charSpacing: 3 });
s.addText("Automated Supervisory Dispatch Control of a\nSolar–Grid–Electrolyzer Hydrogen Plant",
  { x: 0.7, y: 1.7, w: 11.6, h: 2.0, margin: 0, fontFace: SERIF, fontSize: 38, bold: true,
    color: WHITE, lineSpacingMultiple: 1.05 });
s.addText("An optimization-based (MPC) controller, validated against an ETAP digital twin and driven by real Ghardaïa weather and the Algerian time-of-use tariff.",
  { x: 0.7, y: 3.9, w: 10.8, h: 0.9, margin: 0, fontFace: SANS, fontSize: 16, color: "AEC2D4" });
s.addText([
  { text: "Progress update for supervisor", options: { color: WHITE, bold: true, breakLine: true } },
  { text: "youcefboubidi  ·  June 2026", options: { color: "8EA6BC", fontSize: 13 } },
], { x: 0.7, y: 5.6, w: 9, h: 1.0, margin: 0, fontFace: SANS, fontSize: 15 });
s.addNotes("One-line pitch: I built an automatic supervisory controller that decides how to dispatch solar and grid power to the electrolyzer under changing weather and prices, validated against ETAP and run on real data. Frame it as a CONTROL problem first.");

// ============ Slide 2 — Objective (light) ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "The problem");
heading(s, "An automatic controller for power dispatch");
bullets(s, [
  "Plant: a PEM electrolyzer fed by a solar array and the utility grid, through a 2 MVA / 11–0.415 kV substation.",
  "Decision, every step: how much power to draw, and from where — under variable irradiance, temperature and electricity price.",
  "Goal: meet a hydrogen demand at least cost while keeping the network within safe limits (voltage, transformer loading).",
  "This is a supervisory / optimal-control problem — not a one-off optimization study.",
], 0.6, 1.75, 6.6, 3.6);
// simple flow on the right
const fx = 8.0, fw = 4.6;
const flow = [["Weather + price", TEAL], ["Controller (MPC)", GOLD], ["Electrolyzer → H₂", GREEN]];
flow.forEach((b, i) => {
  const y = 2.0 + i * 1.35;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: fx, y, w: fw, h: 0.95, rectRadius: 0.1,
    fill: { color: i === 1 ? NAVY : CARD }, line: { color: "DCE5EC", width: 1 }, shadow: sh() });
  s.addText(b[0], { x: fx, y, w: fw, h: 0.95, margin: 0, align: "center", valign: "middle",
    fontFace: SANS, fontSize: 17, bold: true, color: i === 1 ? WHITE : INK });
  if (i < 2) s.addShape(p.shapes.LINE, { x: fx + fw / 2, y: y + 0.95, w: 0, h: 0.4,
    line: { color: MUTE, width: 2, endArrowType: "triangle" } });
});
s.addNotes("Stress the word 'controller'. The inputs (weather, prices) are disturbances and the objective; the electrolyzer setpoint is the control action; the network limits are hard constraints.");

// ============ Slide 3 — Method / validated twin (light) ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "Method — a validated digital twin on real data");
heading(s, "ETAP-validated model, real Ghardaïa inputs");
fig(s, "net_sunny.png", 7.1, 1.7, 5.7, 4.4);
bullets(s, [
  "Electrical network rebuilt in pandapower and validated against the professional ETAP load flow — 24/24 checks pass.",
  "Solar: real CAMS satellite irradiance + ERA5 temperature → NREL SAM (PySAM), 15-min, full-year 2023.",
  "Prices: the real Algerian CREG time-of-use tariff (1.21 / 2.16 / 8.11 DA/kWh, night / day / 17–21 h peak).",
  "Site: Ghardaïa (32.59° N, 3.73° E). Every result rests on measured data, not assumptions.",
], 0.6, 1.75, 6.2, 4.0);
s.addNotes("The ETAP validation is the credibility anchor — pandapower reproduces ETAP exactly, so the automatable engine is trustworthy. The figure is the validated single-line load flow.");

// ============ Slide 4 — Control formulation (dark) ============
s = p.addSlide(); s.background = { color: NAVY };
s.addText("THE CONTROL CORE", { x: 0.6, y: 0.5, w: 11, h: 0.3, margin: 0, fontFace: SANS,
  fontSize: 12, bold: true, color: GOLD, charSpacing: 3 });
s.addText("Receding-horizon (MPC) supervisory controller", { x: 0.6, y: 0.85, w: 12, h: 0.8,
  margin: 0, fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
const cc = [
  ["State", "time, battery charge, cumulative H₂"],
  ["Control input", "electrolyzer setpoint (+ battery power)"],
  ["Disturbance", "PV (weather) — measured, forecast ahead"],
  ["Constraints", "voltage 0.95–1.05 pu, transformer ≤ 100 %, demand"],
  ["Objective", "minimize grid energy cost (time-of-use)"],
];
cc.forEach((r, i) => {
  const y = 1.95 + i * 0.92;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 6.7, h: 0.78, rectRadius: 0.07,
    fill: { color: NAVY2 }, line: { color: "27516E", width: 1 } });
  s.addText(r[0], { x: 0.8, y, w: 2.2, h: 0.78, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 15, bold: true, color: GOLD });
  s.addText(r[1], { x: 3.0, y, w: 4.2, h: 0.78, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 14, color: "D6E3EF" });
});
s.addText([
  { text: "How it works\n", options: { bold: true, fontSize: 17, color: WHITE, breakLine: true } },
  { text: "Each hour the controller re-optimizes the remaining day on a forecast, applies only the next setpoint, then re-plans as the actual PV is realized — closed-loop feedback that rejects the weather disturbance.",
    options: { fontSize: 15, color: "AEC2D4" } },
], { x: 7.7, y: 2.0, w: 5.0, h: 3.6, margin: 0, fontFace: SANS, valign: "top", lineSpacingMultiple: 1.1 });
s.addNotes("This slide is the heart of the control-engineering framing. Benchmarks: perfect-foresight (the bound) and a reactive rule-based controller.");

// ============ Slide 5 — The optimization engine: PSO (light) ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "Method — the optimization engine");
heading(s, "How each plan is solved: particle-swarm optimization");
fig(s, "pso_convergence.png", 0.4, 1.7, 8.1, 5.1);
statCard(s, 9.1, 1.95, 3.7, "3 / 3", "random seeds reach the same optimum — reproducible", GREEN);
bullets(s, [
  "Re-planning is a hard search: 24 hourly setpoints, a non-linear electrolyzer and a 3-rate tariff — no closed-form solution.",
  "PSO = a swarm of candidate day-plans that 'fly' through the search space, each pulled toward its own best and the swarm's best.",
  "Fitness = grid energy cost + a penalty when the H₂ demand is missed.",
  "Converges to the least-cost plan in ~150 generations.",
], 9.1, 3.65, 3.8, 3.2);
s.addNotes("PSO is the engine the MPC calls at every re-plan. It is gradient-free, so it handles the non-linear electrolyzer curve and the discontinuous (3-rate) tariff directly, with no derivatives. The convergence curve shows the best plan dropping from a random start (~30,000 DA, demand unmet) down to the least-cost feasible plan (~5,565 DA) — and all three random seeds land on the same value, so the optimizer is reproducible, which matters for a thesis.");

// ============ Slide 6 — Result: intelligent dispatch (light) ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "Result — what the controller does");
heading(s, "Rides free solar, dodges the evening peak");
fig(s, "day_schedule_ghardaia.png", 0.5, 1.65, 8.4, 5.4);
statCard(s, 9.4, 1.9, 3.4, "27.8", "DA / kg  (clear summer, 200 kg/day)", TEAL);
bullets(s, [
  "Full power on cheap night grid (1.21 DA).",
  "Setpoint tracks the PV mid-day (≈ zero grid).",
  "Shuts down through the 8.11 DA peak.",
  "Cloudy day shows real 15-min cloud transients.",
], 9.4, 3.6, 3.5, 3.2);
s.addNotes("Nobody told it to avoid the peak — it derives that from the price signal. Three real 2023 days: clear summer, cloudy summer, clear winter.");

// ============ Slide 7 — vs traditional (light) ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "Result — value vs traditional operation");
heading(s, "50–59 % cheaper than time-blind operation");
fig(s, "baseline_comparison_ghardaia.png", 0.5, 1.7, 7.9, 5.2);
statCard(s, 9.0, 1.95, 1.85, "−59%", "vs constant baseload", GOLD);
statCard(s, 11.0, 1.95, 1.85, "−51%", "vs greedy ASAP", GOLD);
bullets(s, [
  "Same hydrogen, same plant, same tariff — only the dispatch timing differs.",
  "Up to 100 % cheaper at low demand fully covered by solar.",
  "Naive rules degrade at high demand; the optimizer stays best.",
], 9.0, 3.7, 3.9, 3.0);
s.addNotes("This quantifies the contribution: the controller is measurably, substantially cheaper than how a plant would run without it.");

// ============ Slide 8 — MPC comparison (light) — control headline ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "Result — control-strategy comparison");
heading(s, "MPC nearly matches the optimum, beats reactive control");
fig(s, "mpc_comparison.png", 0.5, 1.7, 8.5, 5.1);
statCard(s, 9.5, 1.95, 3.3, "+2.4%", "MPC gap to perfect-foresight optimum", GREEN);
statCard(s, 9.5, 3.6, 3.3, "−51%", "MPC vs reactive rule-based", TEAL);
s.addText("Closed-loop MPC rejects the PV forecast disturbance and recovers ~98 % of the unreachable optimum — across 37 days of 2023.",
  { x: 9.5, y: 5.35, w: 3.4, h: 1.4, margin: 0, fontFace: SANS, fontSize: 13.5, color: MUTE, valign: "top" });
s.addNotes("This is the strongest control-engineering result: feedback control (MPC) tracks the optimal bound and far exceeds the reactive baseline, even with imperfect forecasts.");

// ============ Slide 9 — annual + battery (light) ============
s = p.addSlide(); s.background = { color: WHITE };
eyebrow(s, "Results — full year & storage feasibility");
heading(s, "Year-round operation and a storage verdict");
fig(s, "annual_calendar.png", 0.5, 1.7, 7.4, 2.9);
fig(s, "battery_sizing.png", 0.7, 4.7, 6.9, 2.5);
statCard(s, 8.3, 1.85, 2.3, "72.8 t", "H₂ / year (2023)", TEAL);
statCard(s, 10.8, 1.85, 2.1, "37%", "solar-powered", GREEN);
statCard(s, 8.3, 3.5, 2.3, "45.8", "DA/kg annual avg", TEAL);
statCard(s, 10.8, 3.5, 2.1, "0 MWh", "optimal battery", GOLD);
bullets(s, [
  "Calendar heatmap: cheap, green summers vs dearer winters.",
  "Battery cuts energy cost (−26%) but does NOT pay back its CAPEX at this tariff — break-even ≈ $20/kWh (≈12× below today).",
  "An honest techno-economic / feasibility finding.",
], 8.3, 5.2, 4.6, 2.0);
s.addNotes("The battery result is deliberately honest: technically it works, economically it is not justified at the Algerian tariff spread. Present it as a feasibility insight, not a sales pitch.");

// ============ Slide 10 — 3D digital twin (dark) ============
s = p.addSlide(); s.background = { color: NAVY };
s.addText("DELIVERABLE", { x: 0.6, y: 0.5, w: 8, h: 0.3, margin: 0, fontFace: SANS, fontSize: 12,
  bold: true, color: GOLD, charSpacing: 3 });
s.addText("Interactive 3D digital twin", { x: 0.6, y: 0.85, w: 9, h: 0.8, margin: 0,
  fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 10.9, y: 0.6, w: 1.9, h: 0.55, rectRadius: 0.1,
  fill: { color: GOLD } });
s.addText("LIVE DEMO", { x: 10.9, y: 0.6, w: 1.9, h: 0.55, margin: 0, align: "center",
  valign: "middle", fontFace: SANS, fontSize: 13, bold: true, color: NAVY });
// mini single-line topology of the twin
const nodes = [["U1\nGrid", TEAL], ["11 kV\nbus", TEAL], ["T1\n2 MVA", GOLD],
  ["0.415 kV\nbus", TEAL], ["PV\narray", GREEN], ["Electro-\nlyzer", GREEN]];
const ny = 2.3, nw = 1.7, gap = 0.32; let nx = 0.7;
nodes.forEach((nd, i) => {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: nx, y: ny, w: nw, h: 1.2, rectRadius: 0.1,
    fill: { color: NAVY2 }, line: { color: nd[1], width: 2 } });
  s.addText(nd[0], { x: nx, y: ny, w: nw, h: 1.2, margin: 0, align: "center", valign: "middle",
    fontFace: SANS, fontSize: 13, bold: true, color: WHITE });
  s.addShape(p.shapes.OVAL, { x: nx + nw / 2 - 0.08, y: ny - 0.22, w: 0.16, h: 0.16, fill: { color: GREEN } });
  if (i < nodes.length - 1) s.addShape(p.shapes.LINE, { x: nx + nw, y: ny + 0.6, w: gap, h: 0,
    line: { color: GOLD, width: 2 } });
  nx += nw + gap;
});
bullets(s, [
  "Three.js 3D scene of the plant with a time slider stepping through the day in 15-minute steps.",
  "ETAP-style floating labels per device — bus voltage, transformer loading, currents, power — colour-coded green/amber/red against the limits.",
  "Every value comes from the validated pandapower load flow (no invented numbers). Animated power-flow arrows show import / solar / load.",
  "Self-contained: opens by double-clicking — works offline, no server.",
], 0.7, 4.15, 12.0, 3.0, "C8D6E4");
s.addNotes("Show this live if there's a laptop: open app/plant_3d/index.html, drag the slider across the day, point out the peak shutdown and the voltages staying green. It mirrors how ETAP shows load flow, but animated over time.");

// ============ Slide 11 — Status & next (dark) ============
s = p.addSlide(); s.background = { color: NAVY };
s.addText("STATUS & NEXT STEPS", { x: 0.6, y: 0.6, w: 11, h: 0.4, margin: 0, fontFace: SANS,
  fontSize: 12, bold: true, color: GOLD, charSpacing: 3 });
s.addText("Where the project stands", { x: 0.6, y: 1.0, w: 12, h: 0.8, margin: 0,
  fontFace: SERIF, fontSize: 30, bold: true, color: WHITE });
s.addText("DONE", { x: 0.7, y: 2.1, w: 5.8, h: 0.35, margin: 0, fontFace: SANS, fontSize: 14,
  bold: true, color: GREEN, charSpacing: 2 });
bullets(s, [
  "ETAP-validated network model (24/24 checks).",
  "Real-data pipeline: CAMS + ERA5 → PySAM, full 2023.",
  "MPC supervisory controller + strategy comparison.",
  "Dispatch, full-year and battery results.",
  "Interactive 3D digital twin (live).",
], 0.7, 2.5, 5.9, 4.2, "D6E3EF");
s.addText("NEXT", { x: 6.9, y: 2.1, w: 5.8, h: 0.35, margin: 0, fontFace: SANS, fontSize: 14,
  bold: true, color: GOLD, charSpacing: 2 });
bullets(s, [
  "Tighten the control write-up (Ch. 4–5) around the MPC.",
  "Sensitivity / robustness across more weather years.",
  "Optional: bind the network (larger PV) so limits activate.",
  "Polish dashboard + 3D twin for the defense.",
], 6.9, 2.5, 5.8, 4.2, "D6E3EF");
s.addText("All code, data and figures versioned on GitHub · youcefboubidi/hydrogen-dispatch",
  { x: 0.7, y: 6.8, w: 12, h: 0.4, margin: 0, fontFace: SANS, fontSize: 12, italic: true, color: "8EA6BC" });
s.addNotes("Close by reaffirming the contribution: a working, validated, automated supervisory controller — solid control-engineering work — with real data and a live demonstration.");

p.writeFile({ fileName: "D:/Projects/hydrogen-dispatch/Hydrogen_Dispatch_Supervisor_Update.pptx" })
  .then(f => console.log("WROTE " + f));
