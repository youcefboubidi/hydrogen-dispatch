/* ============================================================================
 *  Master's Thesis Defense deck — Automated Supervisory Dispatch Control of a
 *  Solar–Grid–Electrolyzer Hydrogen Plant.  M2 Automation.
 *
 *  Generates Hydrogen_Dispatch_Defense.pptx (16:9) with:
 *    • a full defense narrative (context → method → results → demo → conclusion)
 *    • real result figures (results/figures) + live app screenshots
 *      (results/screenshots), and speaker notes on every slide
 *    • an appendix of backup slides for jury questions.
 *
 *  Build:  node build_deck.js
 * ========================================================================== */

const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";                 // 13.33 x 7.5 in
p.author = "M2 Automation — thesis defense";
p.title  = "Automated Supervisory Dispatch Control of a Solar–Grid–Electrolyzer Hydrogen Plant";

const W = 13.33, H = 7.5;

/* ---- palette ---- */
const NAVY = "0E2233", NAVY2 = "16344B", NAVY3 = "12283C",
      TEAL = "1C7293", GOLD = "F4A623", GREEN = "2A9D8F", CORAL = "E2643B",
      BLUE = "1D4ED8", SKY = "0EA5E9",
      INK = "1A2733", MUTE = "6B7C8F", LIGHT = "F4F7FA", WHITE = "FFFFFF",
      CARD = "EEF3F7", LINE_C = "DCE5EC";

/* ---- assets ---- */
const FIG  = "/home/youc/hydrogen-dispatch/results/figures/";
const SHOT = "/home/youc/hydrogen-dispatch/results/screenshots/";

/* ---- fonts ---- */
const SANS = "Calibri", SERIF = "Cambria";

/* ---- placeholders (edit in PowerPoint or here) ---- */
const PRES1 = "BOUBIDI Youcef";
const PRES2 = "BOUDJADJA Mohamed Akrem";
const SUPERVISOR = "TOUBAL MAAMAR Alla Eddine";
const JURY = "Prof. AKROUM Hamza (President) · MILOUDI Lalia (Examiner)";
const DEFENSE_DATE = "July 4, 2026";

const sh  = () => ({ type: "outer", color: "0E2233", blur: 9, offset: 3, angle: 90, opacity: 0.18 });
const shL = () => ({ type: "outer", color: "0E2233", blur: 14, offset: 5, angle: 90, opacity: 0.28 });

/* ======================= layout helpers ================================== */
let pageNo = 0;

function eyebrow(s, txt, color) {
  s.addText(txt.toUpperCase(), { x: 0.6, y: 0.42, w: 12, h: 0.3, margin: 0,
    fontFace: SANS, fontSize: 12, bold: true, color: color || TEAL, charSpacing: 3 });
}
function heading(s, txt, color) {
  s.addText(txt, { x: 0.6, y: 0.72, w: 12.1, h: 0.85, margin: 0,
    fontFace: SERIF, fontSize: 29, bold: true, color: color || NAVY });
}
function darkEyebrow(s, txt) {
  s.addText(txt.toUpperCase(), { x: 0.6, y: 0.5, w: 12, h: 0.3, margin: 0,
    fontFace: SANS, fontSize: 12, bold: true, color: GOLD, charSpacing: 3 });
}
function darkHeading(s, txt) {
  s.addText(txt, { x: 0.6, y: 0.85, w: 12.1, h: 0.85, margin: 0,
    fontFace: SERIF, fontSize: 29, bold: true, color: WHITE });
}
function fig(s, name, x, y, w, h) {
  s.addImage({ path: FIG + name, x, y, w, h, sizing: { type: "contain", w, h } });
}
/* framed screenshot — white card + border + shadow behind a contained image */
function shot(s, name, x, y, w, h, dark) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: x - 0.08, y: y - 0.08, w: w + 0.16, h: h + 0.16,
    rectRadius: 0.06, fill: { color: WHITE }, line: { color: dark ? "27516E" : LINE_C, width: 1 }, shadow: shL() });
  s.addImage({ path: SHOT + name, x, y, w, h, sizing: { type: "contain", w, h } });
}
function statCard(s, x, y, w, val, label, accent) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.4, rectRadius: 0.08,
    fill: { color: WHITE }, line: { color: LINE_C, width: 1 }, shadow: sh() });
  s.addText(val, { x: x + 0.1, y: y + 0.16, w: w - 0.2, h: 0.66, margin: 0, align: "center",
    fontFace: SERIF, fontSize: 27, bold: true, color: accent || TEAL });
  s.addText(label, { x: x + 0.12, y: y + 0.86, w: w - 0.24, h: 0.46, margin: 0, align: "center",
    fontFace: SANS, fontSize: 11, color: MUTE });
}
/* compact stat chip (smaller, for dark backgrounds) */
function statChip(s, x, y, w, val, label, accent) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.25, rectRadius: 0.08,
    fill: { color: NAVY2 }, line: { color: "27516E", width: 1 } });
  s.addText(val, { x: x + 0.08, y: y + 0.14, w: w - 0.16, h: 0.6, margin: 0, align: "center",
    fontFace: SERIF, fontSize: 24, bold: true, color: accent || GOLD });
  s.addText(label, { x: x + 0.1, y: y + 0.76, w: w - 0.2, h: 0.42, margin: 0, align: "center",
    fontFace: SANS, fontSize: 10.5, color: "AEC2D4" });
}
function bullets(s, items, x, y, w, h, color, size) {
  s.addText(items.map((t) => ({ text: t,
    options: { bullet: { code: "2022", indent: 14 }, breakLine: true, paraSpaceAfter: 8,
      fontSize: size || 14.5, color: color || INK } })),
    { x, y, w, h, margin: 0, fontFace: SANS, valign: "top", lineSpacingMultiple: 1.04 });
}
function demoBadge(s, x, y) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.0, h: 0.5, rectRadius: 0.25, fill: { color: GOLD } });
  s.addText("●  LIVE DEMO", { x, y, w: 2.0, h: 0.5, margin: 0, align: "center", valign: "middle",
    fontFace: SANS, fontSize: 13, bold: true, color: NAVY });
}
function chip(s, txt, x, y, w, fillc, txtc) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.42, rectRadius: 0.21,
    fill: { color: fillc }, line: { color: txtc, width: 0.75 } });
  s.addText(txt, { x, y, w, h: 0.42, margin: 0, align: "center", valign: "middle",
    fontFace: SANS, fontSize: 11.5, bold: true, color: txtc });
}
/* tool badge — introduce a tool at the moment it does its work (header, right) */
function toolBadge(s, items, dark) {
  let x = 12.73;
  items.slice().reverse().forEach((t) => {
    const w = 0.28 + (t[0].length + t[1].length + 3) * 0.062;
    x -= w;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 0.4, w, h: 0.36, rectRadius: 0.18,
      fill: { color: dark ? NAVY2 : CARD }, line: { color: dark ? "27516E" : LINE_C, width: 1 } });
    s.addText([
      { text: t[0] + "  ", options: { bold: true, color: dark ? GOLD : TEAL, fontSize: 9.5 } },
      { text: t[1], options: { color: dark ? "AEC2D4" : MUTE, fontSize: 9 } },
    ], { x: x + 0.05, y: 0.4, w: w - 0.1, h: 0.36, margin: 0, align: "center", valign: "middle", fontFace: SANS });
    x -= 0.12;
  });
}
/* footer line (light slides keep it; the page number is stamped separately) */
function foot(s, dark) {
  s.addText("Supervisory Dispatch Control · Solar–Grid–Electrolyzer H₂ Plant",
    { x: 0.6, y: 7.04, w: 9, h: 0.3, margin: 0, fontFace: SANS, fontSize: 9,
      italic: true, color: dark ? "6E869C" : MUTE });
}
/* every slide gets its true index stamped at creation; helpers that paint over
   the corner afterwards (title, dividers, thank-you) call stampNo again on top */
function stampNo(s, dark) {
  s.addText(String(s._no), { x: 12.4, y: 7.0, w: 0.5, h: 0.32, margin: 0, align: "right",
    fontFace: SANS, fontSize: 10.5, bold: true, color: dark ? "8EA6BC" : MUTE });
}
function newLight() { const s = p.addSlide(); s.background = { color: WHITE }; s._no = ++pageNo; stampNo(s, false); return s; }
function newDark()  { const s = p.addSlide(); s.background = { color: NAVY };  s._no = ++pageNo; stampNo(s, true);  return s; }

/* part-divider slide */
function divider(num, title, subtitle, who) {
  const s = newDark();
  s.addShape(p.shapes.OVAL, { x: 10.4, y: -2.4, w: 6, h: 6, fill: { color: NAVY2 } });
  s.addShape(p.shapes.OVAL, { x: 11.6, y: 4.4, w: 4.4, h: 4.4, fill: { color: NAVY3 } });
  s.addText(num, { x: 0.7, y: 1.7, w: 3, h: 1.6, margin: 0, fontFace: SERIF, fontSize: 88,
    bold: true, color: "27516E" });
  s.addShape(p.shapes.RECTANGLE, { x: 0.78, y: 3.35, w: 0.7, h: 0.07, fill: { color: GOLD } });
  s.addText(title, { x: 0.7, y: 3.55, w: 11.5, h: 1.0, margin: 0, fontFace: SERIF, fontSize: 36,
    bold: true, color: WHITE });
  s.addText(subtitle, { x: 0.72, y: 4.65, w: 10.5, h: 0.9, margin: 0, fontFace: SANS, fontSize: 16,
    color: "AEC2D4", lineSpacingMultiple: 1.1 });
  if (who) s.addText(who, { x: 0.72, y: 5.7, w: 10, h: 0.4, margin: 0, fontFace: SANS, fontSize: 13,
    bold: true, italic: true, color: GOLD });
  stampNo(s, true);
  return s;
}

let s;

/* ============================================================================
 *  TITLE
 * ========================================================================== */
s = newDark();
s.addShape(p.shapes.OVAL, { x: 10.5, y: -2.3, w: 5.6, h: 5.6, fill: { color: NAVY2 } });
s.addShape(p.shapes.OVAL, { x: 11.6, y: 4.5, w: 4.3, h: 4.3, fill: { color: NAVY3 } });
s.addText("MASTER'S THESIS DEFENSE  ·  M2 AUTOMATION  ·  UNIVERSITY OF BOUMERDÈS",
  { x: 0.7, y: 0.72, w: 12, h: 0.4, margin: 0, fontFace: SANS, fontSize: 13, bold: true,
    color: GOLD, charSpacing: 2 });
s.addText("Automated Supervisory Dispatch Control of a\nSolar–Grid–Electrolyzer Hydrogen Plant",
  { x: 0.7, y: 1.45, w: 12.0, h: 1.9, margin: 0, fontFace: SERIF, fontSize: 37, bold: true,
    color: WHITE, lineSpacingMultiple: 1.04 });
s.addText("A receding-horizon (MPC) controller for least-cost green-hydrogen production — validated against an ETAP digital twin and driven by real Ghardaïa weather and the Algerian time-of-use tariff.",
  { x: 0.7, y: 3.45, w: 11.4, h: 0.95, margin: 0, fontFace: SANS, fontSize: 16, color: "AEC2D4",
    lineSpacingMultiple: 1.12 });
/* presenters */
s.addText("PRESENTED BY", { x: 0.7, y: 4.75, w: 5, h: 0.3, margin: 0, fontFace: SANS, fontSize: 11,
  bold: true, color: "6E869C", charSpacing: 2 });
s.addText([
  { text: PRES1 + "\n", options: { color: WHITE, bold: true, fontSize: 20, breakLine: true } },
  { text: PRES2, options: { color: WHITE, bold: true, fontSize: 20 } },
], { x: 0.7, y: 5.05, w: 6.2, h: 1.1, margin: 0, fontFace: SANS, lineSpacingMultiple: 1.12 });
s.addText([
  { text: "Supervisor:  ", options: { color: "8EA6BC" } },
  { text: SUPERVISOR + "\n", options: { color: WHITE, bold: true, breakLine: true } },
  { text: "Jury:  ", options: { color: "8EA6BC" } },
  { text: JURY + "\n", options: { color: WHITE, bold: true, breakLine: true } },
  { text: DEFENSE_DATE, options: { color: "8EA6BC", fontSize: 12.5 } },
], { x: 7.2, y: 5.05, w: 5.5, h: 1.7, margin: 0, fontFace: SANS, fontSize: 14.5, lineSpacingMultiple: 1.15 });
stampNo(s, true);
s.addNotes("OPENING (Presenter 1). 'Honourable jury, thank you. We present an automatic supervisory controller for a solar + grid + electrolyzer hydrogen plant. Every step it decides how much power to draw and from where, to make the required hydrogen at least cost, while keeping the electrical network inside its safe limits. The plant model is validated against ETAP (24/24 checks), the weather is real Ghardaïa 2023 data, and the prices are the real Algerian CREG time-of-use tariff. The controller is Model-Predictive Control; the optimizer inside it is Particle-Swarm Optimization.' Frame it as a CONTROL problem: disturbance = weather, control input = electrolyzer setpoint, constraints = voltage/transformer limits, objective = the tariff. Replace the bracketed placeholders before the defense.");

/* ============================================================================
 *  AGENDA
 * ========================================================================== */
s = newLight();
eyebrow(s, "Outline");
heading(s, "What we will cover");
const agenda = [
  ["I", "Context, problem & objectives", "What green hydrogen is, why dispatch is a control problem, what we deliver.", TEAL, "≈ 4 min"],
  ["II", "System & methodology", "A real-data plant model validated against the industry reference; then the optimiser and the controller.", GOLD, "≈ 8 min"],
  ["III", "Results", "Daily dispatch, value vs traditional operation, MPC performance, full-year & storage.", GREEN, "≈ 4 min"],
  ["IV", "Deliverables, demo & conclusion", "The live dashboard, contributions and future work.", CORAL, "≈ 3 min"],
];
agenda.forEach((a, i) => {
  const y = 1.95 + i * 1.18;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 8.7, h: 1.02, rectRadius: 0.08,
    fill: { color: CARD }, line: { color: LINE_C, width: 1 } });
  s.addShape(p.shapes.RECTANGLE, { x: 0.6, y, w: 0.1, h: 1.02, fill: { color: a[3] } });
  s.addText(a[0], { x: 0.78, y, w: 0.95, h: 1.02, margin: 0, align: "center", valign: "middle",
    fontFace: SERIF, fontSize: 30, bold: true, color: a[3] });
  s.addText([{ text: a[1] + "\n", options: { bold: true, fontSize: 16.5, color: INK, breakLine: true } },
             { text: a[2], options: { fontSize: 12.5, color: MUTE } }],
    { x: 1.85, y: y + 0.1, w: 6.35, h: 0.85, margin: 0, fontFace: SANS, valign: "middle", lineSpacingMultiple: 1.04 });
  s.addText(a[4], { x: 8.25, y, w: 0.9, h: 1.02, margin: 0, align: "right", valign: "middle",
    fontFace: SANS, fontSize: 12.5, bold: true, color: a[3] });
});
/* speaker split panel */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 9.6, y: 1.95, w: 3.15, h: 4.43, rectRadius: 0.1,
  fill: { color: NAVY }, shadow: sh() });
s.addText("WHO PRESENTS", { x: 9.8, y: 2.2, w: 2.8, h: 0.3, margin: 0, fontFace: SANS, fontSize: 11,
  bold: true, color: GOLD, charSpacing: 2 });
s.addText([
  { text: PRES1 + "\n", options: { color: WHITE, bold: true, fontSize: 14, breakLine: true } },
  { text: "The plant & the problem — context, real data, validated model, control formulation\n\n", options: { color: "AEC2D4", fontSize: 12.5, breakLine: true } },
  { text: PRES2 + "\n", options: { color: WHITE, bold: true, fontSize: 14, breakLine: true } },
  { text: "The control & the payoff — PSO, MPC, results, live demo, conclusion", options: { color: "AEC2D4", fontSize: 12.5 } },
], { x: 9.8, y: 2.65, w: 2.8, h: 3.05, margin: 0, fontFace: SANS, valign: "top", lineSpacingMultiple: 1.12 });
s.addText("≈ 20 minutes · then questions", { x: 9.8, y: 5.85, w: 2.8, h: 0.35, margin: 0,
  fontFace: SANS, fontSize: 11.5, bold: true, italic: true, color: GOLD });
foot(s);
s.addNotes("⏱ ~30 s. Read the four parts WITH their minutes — the jury immediately sees a planned, rehearsed talk. Announce the split: Presenter 1 owns the plant and the problem (through the control-formulation slide), Presenter 2 owns the solver, the controller, the results and the demo. The handover is mid-Part II — rehearse the handover sentence (it is written in the A0 run-of-show backup slide).");

/* ============================================================================
 *  PART I divider
 * ========================================================================== */
divider("I", "Context, Problem & Objectives",
  "Casting least-cost hydrogen production as an automatic control problem.",
  "Presented by " + PRES1)
  .addNotes("Transition into the motivation. New structure: the product (what hydrogen is, why green, 3× diesel) → the moment (fossils pricing out, solar pricing in, Algeria's hand) → the problem (three strategies, two fail on real numbers) → objectives. This is the 'why should the jury care' part.");

/* ---- Context 1/2: the product — hydrogen, and why "green" ---- */
s = newLight();
eyebrow(s, "Context (1/2) — the product");
heading(s, "Hydrogen: the densest clean fuel we can make");
bullets(s, [
  "An energy carrier, not a source: you make it, store it, ship it — and using it releases only water.",
  "The world already runs on it quietly: ≈ 97 Mt/yr for fertiliser (ammonia), refining and steel — ~99 % of it made from fossil gas today (IEA).",
  "An electrolyzer makes the clean kind from water + electricity: it consumes ≈ 50–55 kWh per kg (vs the 33.3 kWh a kg stores → ≈ 60 % efficient).",
  "So electricity is roughly two-thirds of the cost of every green kilogram — the whole game is cheap electrons.",
], 0.6, 1.78, 5.95, 3.1, INK, 13.5);
/* colours of hydrogen — compact strip */
s.addText("THE “COLOURS” OF HYDROGEN", { x: 0.6, y: 5.0, w: 5.9, h: 0.28, margin: 0,
  fontFace: SANS, fontSize: 11, bold: true, color: TEAL, charSpacing: 1 });
const hues = [
  ["Grey", "from fossil gas · ≈ 9–10 kg CO₂/kg (IEA)", MUTE, false],
  ["Blue", "grey + carbon capture", SKY, false],
  ["Green", "renewables · ≈ 0 CO₂ — this thesis", GREEN, true],
];
hues.forEach((r, i) => {
  const x = 0.6 + i * 2.02;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 5.34, w: 1.9, h: 0.92, rectRadius: 0.07,
    fill: { color: WHITE }, line: { color: r[3] ? GREEN : LINE_C, width: r[3] ? 1.75 : 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x, y: 5.34, w: 0.09, h: 0.92, fill: { color: r[2] } });
  s.addText([{ text: r[0] + "\n", options: { bold: true, fontSize: 13, color: r[3] ? GREEN : INK, breakLine: true } },
             { text: r[1], options: { fontSize: 9.5, color: MUTE } }],
    { x: x + 0.2, y: 5.4, w: 1.62, h: 0.8, margin: 0, fontFace: SANS, valign: "middle", lineSpacingMultiple: 1.0 });
});
/* right: energy-density comparison (the visual) */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 1.9, w: 5.9, h: 4.42, rectRadius: 0.1,
  fill: { color: CARD }, line: { color: LINE_C, width: 1 }, shadow: sh() });
s.addText("ENERGY IN 1 KG OF FUEL — kWh (LOWER HEATING VALUE)", { x: 7.1, y: 2.1, w: 5.5, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 11, bold: true, color: TEAL, charSpacing: 1 });
const fuels = [
  ["Hydrogen", 33.3, GREEN],
  ["Natural gas", 13.9, MUTE],
  ["Gasoline", 12.1, MUTE],
  ["Diesel", 11.9, MUTE],
];
fuels.forEach((f, i) => {
  const y = 2.56 + i * 0.6;
  s.addText(f[0], { x: 7.1, y, w: 1.2, h: 0.4, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 11, bold: i === 0, color: i === 0 ? GREEN : INK });
  const bw = 3.3 * f[1] / 33.3;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 8.38, y: y + 0.04, w: bw, h: 0.32, rectRadius: 0.05,
    fill: { color: f[2] } });
  s.addText(String(f[1]), { x: 8.38 + bw + 0.08, y, w: 0.75, h: 0.4, margin: 0, valign: "middle",
    fontFace: SERIF, fontSize: 12.5, bold: true, color: i === 0 ? GREEN : INK });
});
s.addText("≈ 3× diesel, kilogram for kilogram — and the exhaust is water.",
  { x: 7.1, y: 5.14, w: 5.4, h: 0.4, margin: 0, align: "center", fontFace: SANS, fontSize: 13.5,
    bold: true, italic: true, color: GREEN });
s.addText("LHV data — U.S. DOE Hydrogen Program / standard engineering references.",
  { x: 7.1, y: 5.72, w: 5.4, h: 0.3, margin: 0, align: "center", fontFace: SANS, fontSize: 9.5,
    italic: true, color: MUTE });
/* the chain that frames the whole talk */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.44, w: 12.13, h: 0.44, rectRadius: 0.08,
  fill: { color: NAVY } });
s.addText([
  { text: "Green hydrogen is  ", options: { color: "D6E3EF", fontSize: 12.5 } },
  { text: "an electricity-cost problem  →  a timing problem  →  a control problem.", options: { color: WHITE, bold: true, fontSize: 12.5 } },
], { x: 0.6, y: 6.44, w: 12.13, h: 0.44, margin: 0, align: "center", valign: "middle", fontFace: SANS });
foot(s);
s.addNotes("⏱ ~60 s. Define the product once so nobody is lost later. Walk the bar chart: 1 kg of hydrogen holds 33.3 kWh (LHV) — three times diesel's 11.9, and the exhaust is water. Then the scale: the world already uses ≈97 Mt/yr (IEA Global Hydrogen Review 2023) — fertiliser, refining, steel — but ~99 % is grey, made from fossil gas at 9–10 kg CO₂ per kg. Green = the same molecule from electrolysis on renewables. Two numbers to say slowly: 33.3 kWh contained vs ≈50–55 kWh consumed to make one kg (≈60 % efficient) — that pre-empts the efficiency question. Land the banner chain: electricity-cost → timing → control. SOURCES if asked: LHV values U.S. DOE/engineering handbooks (H₂ 120 MJ/kg, diesel ≈42.8, gasoline ≈43.4, methane ≈50); demand & emissions IEA Global Hydrogen Review 2023.");

/* ---- Context 2/2: why now, and why Algeria ---- */
s = newLight();
eyebrow(s, "Context (2/2) — why now, and why Algeria");
heading(s, "The window: fossils pricing out, solar pricing in");
bullets(s, [
  "Fossil fuels are finite and increasingly carbon-priced: proven oil reserves ≈ 50 years at today's production rate (Energy Institute Statistical Review).",
  "From 2026 the EU carbon border tax (CBAM) makes exporters pay for embedded CO₂ — fossil-based products lose ground in Algeria's main export market.",
  "Meanwhile utility solar became the cheapest electricity in history: cost down ≈ 90 % since 2010 (IRENA) — but only when the sun shines.",
  "And clean-hydrogen demand is set to explode: ≈ 430 Mt by 2050 in the IEA net-zero pathway — over 4× today's market, nearly all of it low-carbon.",
], 0.6, 1.78, 6.55, 4.0, INK, 13.5);
/* right: Algeria's hand — the site from space */
s.addText("ALGERIA'S HAND — THE SITE FROM SPACE", { x: 7.42, y: 1.78, w: 5.3, h: 0.28, margin: 0,
  fontFace: SANS, fontSize: 11, bold: true, color: GOLD, charSpacing: 1 });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.42, y: 2.1, w: 5.36, h: 3.26, rectRadius: 0.06,
  fill: { color: WHITE }, line: { color: LINE_C, width: 1 }, shadow: shL() });
s.addImage({ path: FIG + "ghardaia_satellite.png", x: 7.5, y: 2.18, w: 5.2, h: 3.1,
  sizing: { type: "contain", w: 5.2, h: 3.1 } });
s.addText("Sentinel-2 (NASA HLS), 23 June 2023 — the very day used as “clear summer” throughout this thesis. Public domain.",
  { x: 7.42, y: 5.44, w: 5.36, h: 0.34, margin: 0, fontFace: SANS, fontSize: 8.5, italic: true, color: MUTE, lineSpacingMultiple: 0.95 });
s.addText([
  { text: "☀ 2,150 kWh/kWp/yr  ·  ", options: { color: GREEN, bold: true, fontSize: 10.5 } },
  { text: "hydrocarbons ≈ 90 % of exports  ·  ", options: { color: INK, fontSize: 10.5 } },
  { text: "H₂ roadmap 2023 · SoutH2 → ambition ≈ 10 % of EU imports by 2040", options: { color: TEAL, bold: true, fontSize: 10.5 } },
], { x: 7.42, y: 5.8, w: 5.36, h: 0.55, margin: 0, fontFace: SANS, valign: "top", lineSpacingMultiple: 1.05 });
/* crossover banner */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.2, w: 12.13, h: 0.62, rectRadius: 0.09,
  fill: { color: NAVY } });
s.addText([
  { text: "Fossils: finite, carbon-taxed", options: { color: CORAL, fontSize: 12.5, bold: true } },
  { text: "   ·   ", options: { color: "6E869C", fontSize: 12.5 } },
  { text: "Solar: −90 % in a decade", options: { color: GREEN, fontSize: 12.5, bold: true } },
  { text: "   →   green H₂ turns desert sun into an exportable fuel.", options: { color: WHITE, fontSize: 12.5, bold: true } },
], { x: 0.6, y: 6.2, w: 12.13, h: 0.62, margin: 0, align: "center", valign: "middle", fontFace: SANS });
foot(s);
s.addNotes("⏱ ~55 s. The 'why now' in three verifiable moves — no crystal-ball claims: (1) fossils are finite (EI Statistical Review: oil R/P ≈ 50 years) and carbon-priced — the EU border tax CBAM enters its definitive regime in 2026, which directly touches Algeria's main export market; (2) solar collapsed in cost — IRENA: utility PV LCOE down ≈89–90 % between 2010 and the early 2020s, the cheapest electricity in history, but intermittent; (3) clean-hydrogen demand grows from ≈97 Mt today to ≈430 Mt by 2050 in the IEA net-zero pathway. Then Algeria's hand: world-class irradiance (the very Ghardaïa data this thesis runs on), a hydrocarbon-dependent export economy (≈90 % of export revenue) that must diversify, and a declared national hydrogen roadmap (2023) with the SoutH2 pipeline corridor to Italy/Germany — ambition ≈10 % of Europe's imports by 2040. Punchline on the banner: green H₂ is how desert sun becomes an export product.");

/* ---- The problem: three ways to run the plant, two fail ---- */
s = newLight();
eyebrow(s, "The problem");
heading(s, "Three ways to run the plant — two of them fail");
s.addText("Quota: 200 kg of H₂ per day. Real clear-summer 2023 day — every number computed with the validated plant model.",
  { x: 0.6, y: 1.52, w: 12.1, h: 0.3, margin: 0, fontFace: SANS, fontSize: 12, italic: true, color: MUTE });
/* per-hour glyph heights (schematic 24-h dispatch shapes) */
const glyphA = Array(24).fill(0.30);
const glyphB = [0,0,0,0,0,0,.07,.18,.28,.38,.46,.51,.53,.50,.44,.35,.24,.12,.04,0,0,0,0,0];
const glyphC = [.42,.42,.42,.42,.42,.42,.20,.35,.50,.50,.50,.50,.50,.50,.50,.50,.50,0,0,0,0,.30,.42,.42];
const strat = [
  ["ALL GRID, RUN FLAT", CORAL, glyphA, "≈ 141 DA/kg", CORAL,
   "Ignores the free sun: 0.41 MW around the clock, paying the grid — including the 8.11 DA evening peak. 5.1× the smart cost.",
   "✗  a fortune", (h) => (h >= 17 && h <= 20) ? CORAL : "B9C6D2"],
  ["SOLAR ONLY", GOLD, glyphB, "117 kg — 59 %", GOLD,
   "Free energy, zero bill — but it starves the quota (117 of 200 kg) and the 0.8 MW stack sits idle 47 % of the day.",
   "✗  starves demand", () => GOLD],
  ["THE SMART MIX", GREEN, glyphC, "27.8 DA/kg ✓", GREEN,
   "Cheap night grid + free midday sun + shut through the peak → the full 200 kg. But which hours, how hard — under weather you can't predict?",
   "→  24 decisions, every day", (h) => (h >= 6 && h <= 16) ? GREEN : TEAL],
];
strat.forEach((c, i) => {
  const x = 0.6 + i * 4.19;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.0, w: 3.95, h: 3.85, rectRadius: 0.09,
    fill: { color: CARD }, line: { color: LINE_C, width: 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x, y: 2.0, w: 3.95, h: 0.09, fill: { color: c[1] } });
  s.addText(c[0], { x: x + 0.25, y: 2.2, w: 3.5, h: 0.34, margin: 0, fontFace: SANS,
    fontSize: 13, bold: true, color: c[1], charSpacing: 1 });
  /* 24-hour mini dispatch glyph */
  c[2].forEach((h, hh) => {
    if (h <= 0) return;
    const bh = h * 1.05;
    s.addShape(p.shapes.RECTANGLE, { x: x + 0.32 + hh * 0.14, y: 3.35 - bh, w: 0.105, h: bh,
      fill: { color: c[7](hh) } });
  });
  s.addShape(p.shapes.LINE, { x: x + 0.3, y: 3.36, w: 3.4, h: 0, line: { color: MUTE, width: 1 } });
  s.addText("0 h", { x: x + 0.3, y: 3.4, w: 0.6, h: 0.22, margin: 0, fontFace: SANS, fontSize: 8.5, color: MUTE });
  s.addText("24 h", { x: x + 3.15, y: 3.4, w: 0.6, h: 0.22, margin: 0, align: "right", fontFace: SANS, fontSize: 8.5, color: MUTE });
  /* verdict */
  s.addText(c[3], { x: x + 0.2, y: 3.68, w: 3.55, h: 0.5, margin: 0, align: "center",
    fontFace: SERIF, fontSize: 22, bold: true, color: c[4] });
  s.addText(c[5], { x: x + 0.28, y: 4.24, w: 3.42, h: 1.06, margin: 0, fontFace: SANS,
    fontSize: 10.8, color: INK, valign: "top", lineSpacingMultiple: 1.05 });
  chip(s, c[6], x + 0.85, 5.32, 2.25, WHITE, c[1]);
});
/* punchline */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.2, w: 12.13, h: 0.62, rectRadius: 0.09,
  fill: { color: NAVY } });
s.addText([
  { text: "The real question:  ", options: { color: GOLD, fontSize: 12.5, bold: true } },
  { text: "choosing those 24 setpoints — every day, automatically, under weather uncertainty, inside network limits. That is the control problem of this thesis.",
    options: { color: WHITE, fontSize: 12.5, bold: true } },
], { x: 0.9, y: 6.2, w: 11.6, h: 0.62, margin: 0, valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.0 });
foot(s);
s.addNotes("⏱ ~70 s — the pivot slide of Part I; all three numbers are OURS, computed on the real clear-summer day (23 June 2023, 5.94 MWh of PV) with the validated model. Card 1: ignore the sun, run flat on grid at 0.409 MW → 141.3 DA/kg — five times the smart cost, because a flat schedule pays the 8.11 DA peak every evening. Card 2: solar-only (respecting the 0.08 MW turndown) → 117.3 kg, only 59 % of the 200 kg quota, with the stack idle 47 % of the day — free but starving. Card 3: the smart mix reaches 27.8 DA/kg AND the full quota — but it requires choosing 24 hourly setpoints, daily, without knowing tomorrow's clouds. IMPORTANT DISTINCTION if a jury member cross-checks with the Results section: the 'constant baseload' baseline there (67.9 DA/kg) still USES the PV passively; card 1 here ignores PV entirely (141) — different strategies, both computed. The mini bar-glyphs are schematic dispatch shapes: flat / sun-bell / night+midday-with-peak-gap.");

/* ---- Objectives: four promises ---- */
s = newLight();
eyebrow(s, "Objectives & contributions");
heading(s, "Four promises for the next fifteen minutes");
const proms = [
  ["1", "A plant model you can trust", "The plant's electrical study, rebuilt in open, scriptable code — and proven to reproduce the industry-standard reference exactly.", "24/24", "checks pass", TEAL],
  ["2", "A controller that decides", "Dispatch cast as closed-loop supervisory control: measure, forecast, re-optimise — every hour, automatically.", "24", "decisions / day", GOLD],
  ["3", "Proof that it pays", "About half the cost of running the plant naively — and ≈ 98 % of what a perfect weather oracle could achieve.", "−51 %", "vs reactive rule", GREEN],
  ["4", "Something you can touch", "An interactive dashboard on the validated engine — running live in this room.", "1", "live demo", CORAL],
];
proms.forEach((o, i) => {
  const y = 1.88 + i * 1.12;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.13, h: 0.98, rectRadius: 0.09,
    fill: { color: WHITE }, line: { color: LINE_C, width: 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x: 0.6, y, w: 0.1, h: 0.98, fill: { color: o[5] } });
  s.addText(o[0], { x: 0.85, y, w: 0.85, h: 0.98, margin: 0, align: "center", valign: "middle",
    fontFace: SERIF, fontSize: 30, bold: true, color: o[5] });
  s.addText([{ text: o[1] + "\n", options: { bold: true, fontSize: 15.5, color: INK, breakLine: true } },
             { text: o[2], options: { fontSize: 11.5, color: MUTE } }],
    { x: 1.85, y: y + 0.09, w: 8.0, h: 0.82, margin: 0, fontFace: SANS, valign: "middle", lineSpacingMultiple: 1.04 });
  s.addText([{ text: o[3] + "\n", options: { bold: true, fontSize: 19, color: o[5], breakLine: true } },
             { text: o[4], options: { fontSize: 9.5, color: MUTE } }],
    { x: 10.15, y: y + 0.08, w: 2.35, h: 0.84, margin: 0, align: "center", valign: "middle",
      fontFace: SERIF, lineSpacingMultiple: 0.98 });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.44, w: 12.13, h: 0.44, rectRadius: 0.08,
  fill: { color: NAVY } });
s.addText([
  { text: "The gap we fill:  ", options: { color: GOLD, fontSize: 12, bold: true } },
  { text: "existing tools are accurate but manual, and dispatch studies rarely close the loop — ours is automated · network-checked · closed-loop, on real data.",
    options: { color: "D6E3EF", fontSize: 12 } },
], { x: 0.6, y: 6.44, w: 12.13, h: 0.44, margin: 0, align: "center", valign: "middle", fontFace: SANS });
foot(s);
s.addNotes("⏱ ~45 s. Four promises, framed so the conclusion slide can tick them off one by one at the end. Deliberately NO tool names yet — 'industry-standard reference' and 'open, scriptable code' are enough; each tool is introduced in Part II at the moment it does its work. The navy strip quietly carries the state-of-the-art positioning (full table now in backup A11 if an examiner wants the literature discussion): commercial tools = accurate but GUI-bound; techno-economic dispatch studies = rarely network-checked or closed-loop. The contribution sentence to land: 'a working, validated, automated supervisory controller, on real data, with a live demonstration.'");

/* ============================================================================
 *  PART II divider
 * ========================================================================== */
divider("II", "System & Methodology",
  "A validated digital twin on real data, an optimiser, and a feedback controller.",
  "Presented by " + PRES1)
  .addNotes("Now the engineering. Order: the method in one picture → real data & tariff → validation → electrolyzer physics → then the control core in three numbered acts: ① the problem (formulation + formal statement) → ② the solver (PSO ×2) → ③ the loop (MPC diagram + hour-by-hour). Tools are introduced one at a time, at the moment each does its work — watch the small badges in the slide headers.");

/* ---- The method in one picture (roadmap of Part II) ---- */
s = newDark();
darkEyebrow(s, "The method — one picture");
darkHeading(s, "From real desert sun to least-cost hydrogen");
const stages = [
  ["①", "REAL INPUTS", FIG + "pv_year_2023.png",
   "A full year of measured Ghardaïa weather, and the official tariff.", TEAL],
  ["②", "A PLANT WE PROVED", FIG + "net_sunny.png",
   "The electrical model, validated 24/24 against the industry reference.", GOLD],
  ["③", "A CONTROLLER", FIG + "pso_convergence.png",
   "Closed-loop dispatch: forecast, re-optimise, apply — every hour.", GREEN],
  ["④", "PROOF, LIVE", SHOT + "dashboard_daily.png",
   "Every claim shown running — a live dashboard on the validated engine.", CORAL],
];
stages.forEach((st, i) => {
  const x = 0.6 + i * 3.08;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 1.95, w: 2.86, h: 4.3, rectRadius: 0.1,
    fill: { color: NAVY2 }, line: { color: st[4], width: 1.5 } });
  s.addText([{ text: st[0] + "  ", options: { fontSize: 15, bold: true, color: st[4] } },
             { text: st[1], options: { fontSize: 12.5, bold: true, color: st[4], charSpacing: 1 } }],
    { x: x + 0.18, y: 2.1, w: 2.55, h: 0.34, margin: 0, fontFace: SANS, valign: "middle" });
  /* framed thumbnail of the real artefact */
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: x + 0.16, y: 2.52, w: 2.54, h: 1.62, rectRadius: 0.05,
    fill: { color: WHITE }, line: { color: "27516E", width: 1 } });
  s.addImage({ path: st[2], x: x + 0.23, y: 2.59, w: 2.4, h: 1.48,
    sizing: { type: "contain", w: 2.4, h: 1.48 } });
  s.addText(st[3], { x: x + 0.2, y: 4.28, w: 2.5, h: 1.15, margin: 0, fontFace: SANS,
    fontSize: 11, color: "D6E3EF", valign: "top", lineSpacingMultiple: 1.1 });
  s.addText("real figure from this thesis", { x: x + 0.2, y: 5.62, w: 2.5, h: 0.24, margin: 0,
    fontFace: SANS, fontSize: 8, italic: true, color: "6E869C" });
  if (i < 3) s.addShape(p.shapes.LINE, { x: x + 2.9, y: 4.05, w: 0.15, h: 0,
    line: { color: GOLD, width: 2.5, endArrowType: "triangle" } });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.45, w: 12.13, h: 0.55, rectRadius: 0.09,
  fill: { color: NAVY3 }, line: { color: GOLD, width: 1 } });
s.addText([
  { text: "Four stages, four slides ahead.  ", options: { color: GOLD, fontSize: 12, bold: true } },
  { text: "Each tool is introduced the moment it does its work — and every figure you will see comes out of this pipeline.",
    options: { color: "D6E3EF", fontSize: 12 } },
], { x: 0.9, y: 6.45, w: 11.6, h: 0.55, margin: 0, valign: "middle", fontFace: SANS });
s.addNotes("⏱ ~45 s. This is the map of Part II — four stages, and the thumbnails are REAL artefacts from the thesis, previewed before each is explained: the 2023 PV year, the validated load-flow diagram, the PSO convergence, the live dashboard. Promise the structure out loud: 'we will walk these four stages left to right, and every tool gets introduced when it starts working — watch the badges in the top-right of the coming slides.' One breath per stage: real measured inputs → a plant model proven against the industry reference → an hourly closed-loop controller → live proof. Do NOT explain the thumbnails here; they each get their own slide.");

/* ---- Real data inputs ---- */
s = newLight();
eyebrow(s, "Method — real data, not assumptions");
heading(s, "Real Ghardaïa weather and the real Algerian tariff");
toolBadge(s, [["CAMS + ERA5", "real weather"], ["PySAM · NREL", "PV physics"]]);
bullets(s, [
  "Solar: real CAMS satellite irradiance + ERA5 temperature/wind for Ghardaïa (32.59° N, 3.73° E), run through NREL's SAM (PySAM) → 15-minute AC power for all of 2023.",
  "Plant PV ≈ 669 kWp DC / 534 kW AC, single-axis tracking — matched to the ETAP interconnect; ≈ 2,150 kWh/kWp/yr, peak ≈ 0.53 MW.",
  "Prices: the official CREG / Sonelgaz medium-voltage time-of-use grid — three rates by hour of day (table →).",
], 0.6, 1.72, 6.6, 2.3, INK, 12.5);
fig(s, "pv_year_2023.png", 0.45, 4.15, 6.9, 2.5);
/* official tariff table (grille tarifaire 51NM) */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.55, y: 1.72, w: 5.2, h: 4.78, rectRadius: 0.1,
  fill: { color: CARD }, line: { color: LINE_C, width: 1 }, shadow: sh() });
s.addText("GRILLE TARIFAIRE MT — CREG / SONELGAZ · CODE 51NM", { x: 7.8, y: 1.9, w: 4.8, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 10.5, bold: true, color: TEAL, charSpacing: 1 });
s.addText("PÉRIODE", { x: 7.8, y: 2.28, w: 1.6, h: 0.26, margin: 0, fontFace: SANS, fontSize: 9.5, bold: true, color: MUTE, charSpacing: 1 });
s.addText("HEURES", { x: 9.4, y: 2.28, w: 1.8, h: 0.26, margin: 0, fontFace: SANS, fontSize: 9.5, bold: true, color: MUTE, charSpacing: 1 });
s.addText("DA/kWh", { x: 11.15, y: 2.28, w: 1.35, h: 0.26, margin: 0, align: "right", fontFace: SANS, fontSize: 9.5, bold: true, color: MUTE, charSpacing: 1 });
const rates = [
  ["Pointe", "17h00 – 21h00", "8.1147", CORAL],
  ["Pleines", "06h00 – 17h00\n21h00 – 22h30", "2.1645", GOLD],
  ["Creuses", "22h30 – 06h00", "1.2050", TEAL],
];
rates.forEach((r, i) => {
  const y = 2.6 + i * 0.94;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.8, y, w: 4.7, h: 0.82, rectRadius: 0.07,
    fill: { color: WHITE }, line: { color: LINE_C, width: 1 } });
  s.addShape(p.shapes.RECTANGLE, { x: 7.8, y, w: 0.1, h: 0.82, fill: { color: r[3] } });
  s.addText(r[0], { x: 8.02, y, w: 1.4, h: 0.82, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 13.5, bold: true, color: INK });
  s.addText(r[1], { x: 9.4, y, w: 1.85, h: 0.82, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 10, color: MUTE, lineSpacingMultiple: 1.05 });
  s.addText(r[2], { x: 10.9, y, w: 1.6, h: 0.82, margin: 0, align: "right", valign: "middle",
    fontFace: SERIF, fontSize: 18, bold: true, color: r[3] });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.8, y: 5.44, w: 4.7, h: 0.5, rectRadius: 0.07,
  fill: { color: LIGHT }, line: { color: LINE_C, width: 1 } });
s.addText("Prime de puissance (demand charge)", { x: 8.02, y: 5.44, w: 3.0, h: 0.5, margin: 0,
  valign: "middle", fontFace: SANS, fontSize: 10, color: INK });
s.addText("4.37 DA/kW/mois", { x: 10.7, y: 5.44, w: 1.8, h: 0.5, margin: 0, align: "right",
  valign: "middle", fontFace: SANS, fontSize: 10.5, bold: true, color: INK });
s.addText("Source : CREG, « Comment lire votre facture » — grille moyenne tension, code tarif 51NM.",
  { x: 7.8, y: 6.04, w: 4.72, h: 0.36, margin: 0, fontFace: SANS, fontSize: 8.5, italic: true, color: MUTE, lineSpacingMultiple: 1.0 });
s.addText("Pointe = 6.7 × Creuses — the spread that makes timing pay.",
  { x: 7.55, y: 6.58, w: 5.2, h: 0.32, margin: 0, align: "center", fontFace: SANS, fontSize: 11.5,
    bold: true, italic: true, color: CORAL });
foot(s);
s.addNotes("Pre-empt the obvious question — 'is the data real?'. Yes, twice over: the LEFT figure is the full 2023 PV series (CAMS + ERA5 through NREL SAM, 1,435 MWh ≈ 2,150 kWh/kWp) with the three representative days marked; the RIGHT table is the official CREG/Sonelgaz grille, quoted to the exact centime — 811.47 / 216.45 / 120.50 cDA/kWh — with the true 22h30 night boundary. The 6.7× pointe-to-creuses ratio is the economic driver of the whole thesis. Two technicalities if probed: (1) the hourly model samples the hour start, so the 22h00–23h00 hour is billed pleines (conservative); (2) the prime de puissance is fixed by subscribed power, independent of dispatch, so it is excluded from the optimisation (backup A3). Note honestly if asked: an initial PySAM test run used a non-Ghardaïa weather file; it was replaced with real Ghardaïa CAMS data before any result was used.");

/* ---- Plant & ETAP validation ---- */
s = newLight();
eyebrow(s, "Method — the validated digital twin");
heading(s, "Prove the model before trusting it");
toolBadge(s, [["ETAP", "industry reference"], ["pandapower", "open-source engine"]]);
fig(s, "net_sunny.png", 7.45, 1.55, 5.5, 4.6);
bullets(s, [
  "The plant's official electrical study lives in ETAP — the industry-standard power-system tool. Trusted, but GUI-bound: it cannot be scripted across a year of dispatch.",
  "So we rebuilt the same network in pandapower, an open-source load-flow engine we can automate: grid → 11 kV → 2 MVA transformer → 0.415 kV → PV + electrolyzer.",
  "Same Newton-Raphson load flow, three operating points (sunny / night / PV-export): 24/24 checks agree — voltages ±0.01 pu, loading within 2 pts, flows within 2 %.",
  "The credibility anchor: everything downstream runs on a model that matches the professional reference — including the reverse-power-flow sign.",
], 0.6, 1.72, 6.55, 3.5, INK, 13.2);
statCard(s, 0.6, 5.45, 2.45, "24 / 24", "validation checks pass", GREEN);
foot(s);
s.addNotes("This is the gate. Say plainly: 'I did not trust pandapower until it reproduced our ETAP load flow — and it does, to 4 decimal places on voltage.' The figure is the validated single-line load flow for the sunny case (the full 24-check table is a backup slide). If asked why two tools: ETAP is the trusted reference and the visuals; pandapower is what we can script for a full year and put inside the optimiser.");

/* ---- Electrolyzer physics ---- */
s = newLight();
eyebrow(s, "Method — the hydrogen physics");
heading(s, "PEM electrolyzer: power in, hydrogen out");
toolBadge(s, [["src/physics", "our model, in Python"]]);
bullets(s, [
  "A PEM stack modelled from physics: reversible voltage + Tafel activation + ohmic loss give V(i); Faraday's law turns current into hydrogen mass flow.",
  "Rated 0.800 MW at ≈ 2 A/cm² → ≈ 14.6 kg H₂/h at ≈ 54 kWh/kg; a 10 % minimum turndown (0.080 MW) — below it the stack switches off.",
  "The optimiser calls a fast lookup table of this exact curve, so a full year of dispatch is cheap to evaluate.",
], 0.6, 1.75, 6.3, 2.45, INK, 12.5);
fig(s, "pem_cell_schematic.png", 7.05, 1.6, 5.7, 2.75);
fig(s, "electrolyzer_curves.png", 1.8, 4.28, 9.72, 2.67);
foot(s);
s.addNotes("This is the Chapter-4 physics in 30 seconds, now with the actual curves — both figures are generated from src/physics/electrolyzer_model.py, the same code the optimiser calls. TOP-RIGHT: the cell — water split at the anode, protons cross the membrane, H₂ evolved at the cathode, electrons driven by the DC power u(k) we control. BOTTOM-LEFT panel: the polarisation curve with the loss decomposition (reversible 1.198 V at 60 °C + Tafel activation + ohmic r·i → 2.03 V at the rated 2 A/cm²). BOTTOM-RIGHT panel: the map g(u) the optimiser uses — 14.6 kg/h at rated, 54.6 kWh/kg, OFF below 10 % turndown. Note the dashed specific-energy line RISES with load (higher V at higher i): part load is MORE efficient per kg. If asked 'so why not always run at part load?' — because you also need throughput to meet 200 kg/day; the optimiser trades efficiency against schedule inside the tariff. Efficiency cross-check: 33.3 kWh/kg contained (LHV) ÷ ≈54 consumed ≈ 62 % — numbers agree with the primer.");

/* ---- Control formulation ---- */
s = newDark();
darkEyebrow(s, "The control core — ① the problem");
darkHeading(s, "Dispatch written as a control problem");
const cc = [
  ["State", "time, battery charge, cumulative H₂ made"],
  ["Control input", "electrolyzer setpoint (+ battery power)"],
  ["Disturbance", "available PV — measured, forecast ahead"],
  ["Constraints", "V ∈ 0.95–1.05 pu, transformer ≤ 100 %, demand, turndown"],
  ["Cost functional", "daily grid energy cost (time-of-use)"],
];
cc.forEach((r, i) => {
  const y = 2.05 + i * 0.86;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 7.0, h: 0.72, rectRadius: 0.07,
    fill: { color: NAVY2 }, line: { color: "27516E", width: 1 } });
  s.addText(r[0], { x: 0.8, y, w: 2.3, h: 0.72, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 14.5, bold: true, color: GOLD });
  s.addText(r[1], { x: 3.1, y, w: 4.4, h: 0.72, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 13, color: "D6E3EF" });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.95, y: 2.05, w: 4.8, h: 4.25, rectRadius: 0.1,
  fill: { color: NAVY3 }, line: { color: "27516E", width: 1 } });
s.addText("WHY NO TEXTBOOK SOLVER FITS", { x: 8.2, y: 2.25, w: 4.3, h: 0.3, margin: 0, fontFace: SANS,
  fontSize: 12, bold: true, color: GOLD, charSpacing: 1 });
const hard = [
  ["Non-linear", "the electrolyzer map g(u) bends — efficiency shifts with load"],
  ["Discontinuous", "the tariff jumps between 3 rates — a 6.7× cliff at 17h00"],
  ["Disjoint input", "off, or 10–100 % — a hole in the feasible set"],
  ["Uncertain", "tomorrow's sun is unknown — plans go stale within hours"],
];
hard.forEach((r, i) => {
  const y = 2.7 + i * 0.9;
  s.addText([{ text: r[0] + "\n", options: { fontSize: 12.5, bold: true, color: CORAL, breakLine: true } },
             { text: r[1], options: { fontSize: 11, color: "D6E3EF" } }],
    { x: 8.2, y, w: 4.35, h: 0.84, margin: 0, fontFace: SANS, valign: "top", lineSpacingMultiple: 1.05 });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.48, w: 12.13, h: 0.5, rectRadius: 0.09,
  fill: { color: NAVY3 }, line: { color: GOLD, width: 1 } });
s.addText([
  { text: "So the method has two parts:  ", options: { color: GOLD, fontSize: 12.5, bold: true } },
  { text: "② a solver that finds the cheapest possible day  —  then  ③ a loop that survives imperfect forecasts.",
    options: { color: "D6E3EF", fontSize: 12.5 } },
], { x: 0.9, y: 6.48, w: 11.6, h: 0.5, margin: 0, valign: "middle", fontFace: SANS });
s.addNotes("This slide IS the control-engineering identity of the thesis. Read the table as a control problem the jury will recognise — state, input, disturbance, constraints, cost. Then the right box answers 'why not a textbook method': non-linear plant map, discontinuous (3-rate) cost, a disjoint input set, and an unknown disturbance. Land the roadmap strip hard — it is the outline of the next five slides: ② a solver for one perfect day, ③ a loop for imperfect forecasts. Deliberately NO acronyms yet: PSO and MPC each get named when they appear. Next: the same problem in equations — P1 delivers it, handover comes after.");

/* ---- The problem, formally: state-space + least-cost objective ---- */
s = newDark();
darkEyebrow(s, "The control core — ① the problem, formally");
darkHeading(s, "The problem, formally");

/* left: plant model */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.95, w: 6.05, h: 4.0, rectRadius: 0.1,
  fill: { color: NAVY2 }, line: { color: TEAL, width: 1.5 } });
s.addText("PLANT — DISCRETE-TIME STATE-SPACE", { x: 0.88, y: 2.1, w: 5.5, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 12, bold: true, color: TEAL, charSpacing: 1 });
s.addText("x(k+1) = x(k) + T·g(u(k))", { x: 0.88, y: 2.44, w: 5.5, h: 0.38, margin: 0,
  fontFace: "Consolas", fontSize: 16, bold: true, color: WHITE });
s.addText("q(k)   = [u(k) − d(k)]⁺", { x: 0.88, y: 2.88, w: 3.1, h: 0.3, margin: 0,
  fontFace: "Consolas", fontSize: 13, bold: true, color: WHITE });
s.addText("grid import — where d acts", { x: 3.95, y: 2.9, w: 2.4, h: 0.26, margin: 0,
  fontFace: SANS, fontSize: 10, italic: true, bold: true, color: CORAL });
s.addText("y(k)   = x(k)", { x: 0.88, y: 3.22, w: 3.1, h: 0.28, margin: 0,
  fontFace: "Consolas", fontSize: 12, color: "AEC2D4" });
s.addText("measured every hour", { x: 3.95, y: 3.23, w: 2.4, h: 0.26, margin: 0,
  fontFace: SANS, fontSize: 10, italic: true, color: "8EA6BC" });
const sym = [
  ["x", "hydrogen produced so far today [kg] — one state", WHITE],
  ["u", "electrolyzer setpoint ∈ {0} ∪ [0.08, 0.80] MW", GOLD],
  ["d", "available PV [MW] — disturbance: enters q (the bill), not the dynamics", CORAL],
  ["g(·)", "electrolyzer map: polarisation curve + Faraday", TEAL],
];
sym.forEach((r, i) => {
  const y = 3.6 + i * 0.44;
  s.addText(r[0], { x: 0.88, y, w: 0.72, h: 0.4, margin: 0, valign: "middle",
    fontFace: "Consolas", fontSize: 12.5, bold: true, color: r[2] });
  s.addText(r[1], { x: 1.62, y, w: 4.9, h: 0.4, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 11, color: "D6E3EF" });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.88, y: 5.4, w: 5.5, h: 0.48, rectRadius: 0.07,
  fill: { color: NAVY3 }, line: { color: "27516E", width: 1 } });
s.addText([
  { text: "Hammerstein plant — locally an integrator:  ", options: { fontSize: 10.5, color: "AEC2D4" } },
  { text: "G(z) = K/(z−1),  K = T·g'(u₀) ≈ 15–22 kg/MW", options: { fontSize: 10.5, bold: true, color: WHITE } },
], { x: 1.02, y: 5.4, w: 5.25, h: 0.48, margin: 0, valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.0 });

/* right: objective */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.95, y: 1.95, w: 5.78, h: 4.0, rectRadius: 0.1,
  fill: { color: NAVY2 }, line: { color: GOLD, width: 1.5 } });
s.addText("OBJECTIVE — LEAST-COST DISPATCH", { x: 7.23, y: 2.1, w: 5.2, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 12, bold: true, color: GOLD, charSpacing: 1 });
s.addText("min  J = Σ p(k)·[u(k) − d(k)]⁺·Δt", { x: 7.23, y: 2.48, w: 5.3, h: 0.4, margin: 0,
  fontFace: "Consolas", fontSize: 16, bold: true, color: WHITE });
s.addText("= Σ p(k)·q(k)·Δt — pay only for net import · 96 × 15-min steps",
  { x: 7.23, y: 2.92, w: 5.3, h: 0.28, margin: 0, fontFace: SANS, fontSize: 10.5, italic: true, color: "AEC2D4" });
s.addText("s.t.  x(24) ≥ D", { x: 7.23, y: 3.32, w: 5.3, h: 0.36, margin: 0,
  fontFace: "Consolas", fontSize: 14.5, bold: true, color: WHITE });
s.addText("terminal demand constraint — softened as  + λ·[D − x(24)]⁺,  λ = 10⁷ DA/kg",
  { x: 7.23, y: 3.7, w: 5.3, h: 0.28, margin: 0, fontFace: SANS, fontSize: 10.5, italic: true, color: "AEC2D4" });
const objRows = [
  ["p(k) ∈ {1.21, 2.16, 8.11} DA/kWh — the 3-rate CREG tariff (discontinuous in time)", 4.1, 0.48],
  ["V ∈ [0.95, 1.05] pu · transformer ≤ 100 % — verified on the ETAP-validated load flow (never binding at this PV size)", 4.66, 0.62],
  ["Input set {0} ∪ [0.08, 0.80] is disjoint and g is non-linear → non-convex → solved with PSO", 5.36, 0.48],
];
objRows.forEach((r) => {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.23, y: r[1], w: 5.25, h: r[2], rectRadius: 0.06,
    fill: { color: NAVY3 }, line: { color: "27516E", width: 1 } });
  s.addText(r[0], { x: 7.38, y: r[1], w: 4.95, h: r[2], margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 10, color: "D6E3EF", lineSpacingMultiple: 0.98 });
});

/* bottom strip */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.18, w: 12.13, h: 0.62, rectRadius: 0.09,
  fill: { color: NAVY3 }, line: { color: GOLD, width: 1 } });
s.addText([
  { text: "A bill, not a setpoint:  ", options: { color: GOLD, fontSize: 12.5, bold: true } },
  { text: "the cost is money and the only reference is the end-of-day quota x(24) ≥ D — there is nothing to 'track'; the tariff itself shapes the optimal behaviour.", options: { color: "D6E3EF", fontSize: 12.5 } },
], { x: 0.9, y: 6.18, w: 11.6, h: 0.62, margin: 0, valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.0 });
s.addNotes("⏱ ~55 s — this slide exists for the MPC examiner; deliver it slowly and own the notation. TERMINOLOGY DISCIPLINE: do NOT say 'MPC' yet — on this slide it is just 'the least-cost dispatch problem'; the acronym arrives when the loop is drawn (slide ③), and there it becomes textbook 'economic MPC'. LEFT: one state x = cumulative H₂; the plant seen by the supervisory layer is a static nonlinearity g (the electrolyzer polarisation curve + Faraday's law) feeding an integrator — a Hammerstein structure. Say: 'locally, the supervisory plant is an integrator, G(z) = K/(z−1) with K = T·g-prime between 15 and 22 kg/MW across the window.' RIGHT: an economic objective — the stage cost is the actual bill p·[u−d]⁺, the demand enters as a TERMINAL constraint x(24) ≥ D, softened with λ = 10⁷ DA/kg so the program is always well-posed. PREPARED ANSWERS: (1) Recursive feasibility — shrinking horizon over a finite day; feasible whenever remaining capability Σ g(u_max)·T over the hours left ≥ remaining demand; the soft constraint keeps it well-posed even on a freak day. (2) Stability — not the relevant notion for a finite-horizon batch/economic problem with no equilibrium to stabilise; we measure performance against the perfect-foresight bound instead (+2.4 %). (3) Why PSO, not QP/MILP — disjoint input set {0}∪[0.08,0.8] (mixed-integer), non-linear g, discontinuous tariff; PSO handles all three directly and reproducibly (3 seeds, same optimum). (4) Why is d not in the state equation? — hydrogen depends only on u: the stack draws its setpoint whether the electrons are solar or grid, and the grid automatically covers u − d. So d is a disturbance on the COST, through the grid-import output q = [u − d]⁺, not on the dynamics. Line for the jury: 'clouds can never make the day infeasible — only expensive.' (5) What happens to surplus PV (u < d)? — q clips at zero: exported/curtailed at zero revenue; no feed-in tariff is assumed, which is conservative. HANDOVER to Presenter 2 after this slide.");

/* ---- PSO — what it is (concept / explainer) ---- */
s = newLight();
eyebrow(s, "The control core — ② the solver (PSO), 1/2");
heading(s, "What is particle-swarm optimisation?");
toolBadge(s, [["pymoo", "the PSO engine"]]);
bullets(s, [
  "A population-based optimiser inspired by how a flock searches for food: many candidate solutions explore the search space together.",
  "Each particle is one complete candidate day-plan, with a position (the solution itself) and a velocity (how it is changing).",
  "Every iteration a particle is pulled two ways — toward its own best find, and toward the whole swarm's best. That balance of exploring and exploiting converges on the global optimum.",
  "It is gradient-free: it needs no derivatives, so it copes with our non-linear electrolyzer and the discontinuous 3-rate tariff.",
], 0.6, 1.7, 6.7, 2.55, INK, 12.5);
fig(s, "pso_swarm_concept.png", 0.5, 4.32, 6.85, 2.16);
/* right: update-rule card */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.55, y: 1.9, w: 5.2, h: 4.55, rectRadius: 0.1,
  fill: { color: CARD }, line: { color: LINE_C, width: 1 }, shadow: sh() });
s.addText("THE UPDATE, EACH ITERATION", { x: 7.8, y: 2.1, w: 4.7, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 11.5, bold: true, color: TEAL, charSpacing: 1 });
s.addText("vᵢ ← w·vᵢ + c₁r₁(pᵢ − xᵢ) + c₂r₂(g − xᵢ)", { x: 7.8, y: 2.5, w: 4.75, h: 0.45, margin: 0,
  fontFace: "Consolas", fontSize: 13.5, bold: true, color: NAVY });
s.addText("xᵢ ← xᵢ + vᵢ", { x: 7.8, y: 3.0, w: 4.75, h: 0.4, margin: 0,
  fontFace: "Consolas", fontSize: 13.5, bold: true, color: NAVY });
const pulls = [["w·vᵢ", "inertia — keep exploring", TEAL],
               ["c₁r₁(pᵢ−xᵢ)", "pull toward its personal best", GOLD],
               ["c₂r₂(g−xᵢ)", "pull toward the swarm's best", GREEN]];
pulls.forEach((t, i) => {
  const y = 3.6 + i * 0.84;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.8, y, w: 4.7, h: 0.68, rectRadius: 0.06,
    fill: { color: WHITE }, line: { color: LINE_C, width: 1 } });
  s.addShape(p.shapes.RECTANGLE, { x: 7.8, y, w: 0.09, h: 0.68, fill: { color: t[2] } });
  s.addText(t[0], { x: 8.0, y, w: 1.95, h: 0.68, margin: 0, valign: "middle",
    fontFace: "Consolas", fontSize: 13, bold: true, color: t[2] });
  s.addText(t[1], { x: 9.95, y, w: 2.45, h: 0.68, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 12, color: INK });
});
s.addText("r₁, r₂ ~ U(0,1), fresh each step · |v| capped at 20 % of range · pymoo: w = 0.9, c₁ = c₂ = 2.0, adapted online.",
  { x: 7.8, y: 6.0, w: 4.7, h: 0.44, margin: 0, fontFace: SANS, fontSize: 10, italic: true, color: MUTE, lineSpacingMultiple: 1.0 });
foot(s);
s.addNotes("If asked about r₁, r₂: uniform random in (0,1), redrawn per particle per dimension per step — the stochastic weighting that keeps the swarm exploring; with a fixed seed the whole run is still reproducible. pymoo's PSO adapts w, c₁, c₂ online (starting 0.9 / 2.0 / 2.0) and caps velocity at 20 % of the variable range. Explain PSO before we apply it. Use the flock metaphor: each 'particle' is a full 24-hour plan; the swarm shares the best plan found so far. The update rule shows the three pulls — momentum (inertia), memory of its own best, and the social pull to the swarm's best. The one point that matters for a control jury: it is gradient-free, which is exactly why it suits our non-linear electrolyzer and the 3-rate discontinuous tariff (a gradient method would struggle). The NEXT slide shows it actually converging on our problem.");

/* ---- PSO — applied to our problem (convergence) ---- */
s = newLight();
eyebrow(s, "The control core — ② the solver (PSO), 2/2");
heading(s, "PSO applied: how each daily plan is solved");
fig(s, "pso_convergence.png", 0.45, 1.75, 8.0, 4.9);
statCard(s, 9.0, 1.95, 3.75, "3 / 3", "random seeds reach the same optimum", GREEN);
bullets(s, [
  "The search is hard: 24 hourly setpoints, a non-linear electrolyzer, a discontinuous 3-rate tariff — no gradients to follow.",
  "PSO flies a swarm of ~60 candidate day-plans; each is pulled toward its own best and the swarm's best.",
  "Fitness = exactly the J of the formal statement: the 15-min grid bill + 10⁷ × any shortfall. Converges in ≈150 generations; 3 seeds, one optimum.",
  "But note what we assumed: the day's weather, known in advance. Tomorrow's never is — closing that gap is the loop's job, next.",
], 9.0, 3.6, 3.85, 3.0, INK, 13);
foot(s);
s.addNotes("Explain PSO as a flock settling on the best feeding ground. The convergence curve drops from a random ~30,000 DA start to ~5,565 DA, and all three seeds land on the same value → reproducible, which matters for a thesis. Why not MILP/gradient methods? The electrolyzer curve is non-linear, the tariff discontinuous, the input set disjoint; PSO needs no derivatives. END ON THE LIMITATION — it is the segue: PSO alone is an open-loop planner that must know the whole day; given the true day it IS the perfect-foresight bound we benchmark against later. Real weather is never known → step ③, the loop.");

/* ---- MPC in control terms: block diagram + receding horizon ---- */
s = newDark();
darkEyebrow(s, "The control core — ③ the loop (MPC)");
darkHeading(s, "MPC, as a control engineer draws it");
toolBadge(s, [["src/mpc.py", "our controller"]], true);
s.addText([
  { text: "PSO runs inside this loop, ~24× a day — not “PSO then MPC”.  ", options: { color: GOLD, fontSize: 12, bold: true } },
  { text: "Like a GPS: plan the whole route, drive one block, re-route as the sky changes.",
    options: { color: "AEC2D4", fontSize: 12, italic: true } },
], { x: 0.6, y: 1.52, w: 12.1, h: 0.34, margin: 0, fontFace: SANS });

/* ── left panel: the closed loop ── */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.95, w: 6.35, h: 4.0, rectRadius: 0.1,
  fill: { color: NAVY2 }, line: { color: "27516E", width: 1 } });
s.addText("THE CLOSED LOOP", { x: 0.85, y: 2.08, w: 3.5, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 12, bold: true, color: GOLD, charSpacing: 1 });
/* forecast (feedforward), dashed — equation + comment */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 1.05, y: 2.44, w: 2.3, h: 0.76, rectRadius: 0.07,
  fill: { color: NAVY3 }, line: { color: SKY, width: 1, dashType: "dash" } });
s.addText([
  { text: "d(j|k) = α(k)·d_yday(j)\n", options: { fontFace: "Consolas", fontSize: 10, bold: true, color: "9CCFEC", breakLine: true } },
  { text: "PV forecast — yesterday + clearness fix", options: { fontSize: 7.5, italic: true, color: "6E9FBE" } },
], { x: 1.1, y: 2.44, w: 2.2, h: 0.76, margin: 0, align: "center", valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.05 });
s.addShape(p.shapes.LINE, { x: 2.2, y: 3.2, w: 0, h: 0.3, line: { color: SKY, width: 1.5, dashType: "dash", endArrowType: "triangle" } });
/* disturbance into plant — equation + comment */
s.addText([
  { text: "d(k)\n", options: { fontFace: "Consolas", fontSize: 10.5, bold: true, color: CORAL, breakLine: true } },
  { text: "clouds — the disturbance", options: { fontSize: 7.5, italic: true, color: CORAL } },
], { x: 4.4, y: 2.5, w: 2.25, h: 0.5, margin: 0, align: "center", fontFace: SANS, lineSpacingMultiple: 1.0 });
s.addShape(p.shapes.LINE, { x: 5.51, y: 3.02, w: 0, h: 0.48, line: { color: CORAL, width: 2, endArrowType: "triangle" } });
/* reference in — equation + comment */
s.addText([
  { text: "r = D\n", options: { fontFace: "Consolas", fontSize: 10, bold: true, color: "AEC2D4", breakLine: true } },
  { text: "daily quota", options: { fontSize: 7.5, italic: true, color: "8EA6BC" } },
], { x: 0.5, y: 3.32, w: 0.7, h: 0.55, margin: 0, align: "center", fontFace: SANS, lineSpacingMultiple: 1.0 });
s.addShape(p.shapes.LINE, { x: 0.85, y: 4.02, w: 0.4, h: 0, line: { color: "AEC2D4", width: 1.75, endArrowType: "triangle" } });
/* controller block — equation + comment */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 1.25, y: 3.5, w: 2.35, h: 1.06, rectRadius: 0.08,
  fill: { color: NAVY3 }, line: { color: GOLD, width: 2 } });
s.addText([
  { text: "min Σ p·[u − d(j|k)]⁺·T\n", options: { fontFace: "Consolas", fontSize: 10.5, bold: true, color: WHITE, breakLine: true } },
  { text: "MPC supervisor\n", options: { fontSize: 8, bold: true, color: GOLD, breakLine: true } },
  { text: "re-solves with PSO every hour", options: { fontSize: 7.5, italic: true, color: "AEC2D4" } },
], { x: 1.3, y: 3.5, w: 2.25, h: 1.06, margin: 0, align: "center", valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.08 });
/* u(k) arrow — equation above, comment below */
s.addShape(p.shapes.LINE, { x: 3.6, y: 4.02, w: 0.7, h: 0, line: { color: GOLD, width: 2, endArrowType: "triangle" } });
s.addText("u(k)", { x: 3.52, y: 3.7, w: 0.86, h: 0.28, margin: 0, align: "center",
  fontFace: "Consolas", fontSize: 10.5, bold: true, color: GOLD });
s.addText("first hour\nonly", { x: 3.52, y: 4.1, w: 0.86, h: 0.42, margin: 0, align: "center",
  fontFace: SANS, fontSize: 7.5, italic: true, color: GOLD, lineSpacingMultiple: 0.95 });
/* plant block — equation + comment */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 4.3, y: 3.5, w: 2.42, h: 1.06, rectRadius: 0.08,
  fill: { color: NAVY3 }, line: { color: TEAL, width: 2 } });
s.addText([
  { text: "x(k+1) = x(k) + T·g(u(k))\n", options: { fontFace: "Consolas", fontSize: 10.5, bold: true, color: WHITE, breakLine: true } },
  { text: "PLANT — PV · grid · electrolyzer", options: { fontSize: 7.5, italic: true, color: "AEC2D4" } },
], { x: 4.35, y: 3.5, w: 2.32, h: 1.06, margin: 0, align: "center", valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.1 });
/* output stub + measured outputs */
s.addShape(p.shapes.LINE, { x: 6.72, y: 4.02, w: 0.16, h: 0, line: { color: "AEC2D4", width: 1.75, endArrowType: "triangle" } });
s.addText([
  { text: "y(k) = x(k) · q(k) = [u−d]⁺\n", options: { fontFace: "Consolas", fontSize: 9, bold: true, color: "AEC2D4", breakLine: true } },
  { text: "H₂ made · grid import", options: { fontSize: 7.5, italic: true, color: "8EA6BC" } },
], { x: 4.3, y: 4.66, w: 2.5, h: 0.5, margin: 0, align: "center", fontFace: SANS, lineSpacingMultiple: 1.05 });
/* feedback path: down, across, up into controller */
s.addShape(p.shapes.LINE, { x: 6.66, y: 4.02, w: 0, h: 1.26, line: { color: GREEN, width: 1.75 } });
s.addShape(p.shapes.LINE, { x: 2.3, y: 5.28, w: 4.36, h: 0, line: { color: GREEN, width: 1.75 } });
s.addShape(p.shapes.LINE, { x: 2.3, y: 5.28, w: 0, h: -0.72, line: { color: GREEN, width: 1.75, endArrowType: "triangle" } });
s.addText([
  { text: "x(k), α(k)", options: { fontFace: "Consolas", fontSize: 10, bold: true, color: GREEN } },
  { text: "  — measured H₂ · realised clearness", options: { fontSize: 9, italic: true, color: GREEN } },
], { x: 2.45, y: 5.33, w: 4.2, h: 0.26, margin: 0, align: "center", fontFace: SANS });
s.addText("Every box is the formal slide's math, wired into a loop — measure x, correct the forecast by α, re-solve, apply one hour.",
  { x: 0.85, y: 5.62, w: 5.95, h: 0.3, margin: 0, fontFace: SANS, fontSize: 9.5, italic: true, color: "8EA6BC" });

/* ── right panel: the receding horizon ── */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.18, y: 1.95, w: 5.55, h: 4.0, rectRadius: 0.1,
  fill: { color: NAVY2 }, line: { color: "27516E", width: 1 } });
s.addText("THE RECEDING HORIZON", { x: 7.43, y: 2.08, w: 4.0, h: 0.3, margin: 0,
  fontFace: SANS, fontSize: 12, bold: true, color: GOLD, charSpacing: 1 });
s.addText("optimise the rest of the day · commit one hour · slide forward",
  { x: 7.43, y: 2.4, w: 5.1, h: 0.28, margin: 0, fontFace: SANS, fontSize: 10.5, italic: true, color: "AEC2D4" });
const rhRows = [["12:00", 0], ["13:00", 1], ["14:00", 2]];
rhRows.forEach((row, ri) => {
  const ry = 2.85 + ri * 0.72;
  s.addText(row[0], { x: 7.43, y: ry, w: 0.78, h: 0.48, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 11, bold: true, color: WHITE });
  for (let c = 0; c < 12; c++) {
    const cx = 8.3 + c * 0.345;
    const state = c < row[1] ? "done" : (c === row[1] ? "now" : "plan");
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: cx, y: ry, w: 0.3, h: 0.48, rectRadius: 0.04,
      fill: { color: state === "now" ? GOLD : (state === "done" ? NAVY3 : NAVY2) },
      line: state === "plan" ? { color: "5C7C96", width: 1, dashType: "dash" }
                             : { color: state === "now" ? GOLD : "27516E", width: 1 } });
  }
});
/* legend */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 7.45, y: 5.02, w: 0.22, h: 0.22, rectRadius: 0.03, fill: { color: GOLD } });
s.addText("committed", { x: 7.72, y: 4.98, w: 1.05, h: 0.3, margin: 0, valign: "middle", fontFace: SANS, fontSize: 10, color: "AEC2D4" });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 8.85, y: 5.02, w: 0.22, h: 0.22, rectRadius: 0.03,
  fill: { color: NAVY2 }, line: { color: "5C7C96", width: 1, dashType: "dash" } });
s.addText("planned — replaced next hour", { x: 9.12, y: 4.98, w: 2.5, h: 0.3, margin: 0, valign: "middle", fontFace: SANS, fontSize: 10, color: "AEC2D4" });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 11.68, y: 5.02, w: 0.22, h: 0.22, rectRadius: 0.03,
  fill: { color: NAVY3 }, line: { color: "27516E", width: 1 } });
s.addText("done", { x: 11.95, y: 4.98, w: 0.62, h: 0.3, margin: 0, valign: "middle", fontFace: SANS, fontSize: 10, color: "AEC2D4" });
s.addText("Only the first hour is ever executed; the tail is a plan, refreshed as the real sky arrives.",
  { x: 7.43, y: 5.42, w: 5.15, h: 0.5, margin: 0, fontFace: SANS, fontSize: 10.5, italic: true, color: "8EA6BC", lineSpacingMultiple: 1.0 });

/* ── bottom strip: where this sits in the automation hierarchy ── */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.18, w: 12.13, h: 0.62, rectRadius: 0.09,
  fill: { color: NAVY3 }, line: { color: GOLD, width: 1 } });
s.addText([
  { text: "Supervisory, not low-level:  ", options: { color: GOLD, fontSize: 12.5, bold: true } },
  { text: "the MPC sends one setpoint per hour; the electrolyzer's own fast controllers track it underneath — we command the plant, we don't micro-manage it.", options: { color: "D6E3EF", fontSize: 12.5 } },
], { x: 0.9, y: 6.18, w: 11.6, h: 0.62, margin: 0, valign: "middle", fontFace: SANS, lineSpacingMultiple: 1.0 });
s.addNotes("⏱ ~60 s. HERE is where MPC is named for the first time — introduce it as the answer to the PSO slide's closing limitation. The kicker line carries the relationship: PSO is the SOLVER (a function: horizon in, cheapest plan out); MPC is the CONTROLLER — the loop that calls that solver every hour, ~24 times a day. The GPS line seals it: plan the whole route, drive one block, re-route as reality arrives. LEFT: a standard closed loop. r = the daily H₂ target; the MPC block re-solves with PSO each hour; u(k) = the hourly setpoint; the plant is PV + grid + electrolyzer; clouds enter as the disturbance d; the green path is the measured feedback (what the sun and the stack actually did); the dashed blue box is the forecast feedforward. Say 'feedforward plus feedback' out loud — that phrase wins the room. And now the objective panel from the formal slide has its proper name: this is textbook ECONOMIC MPC — the stage cost is a bill, the reference a terminal quota. RIGHT: the receding horizon — gold cell = the one hour we commit; dashed cells = the plan we deliberately throw away; dark cells = history. BOTTOM: pre-empts 'where does this sit?' — a SUPERVISORY layer above the stack's own controllers, like an EMS above the PLCs. Next slide: the same loop in five plain words as the take-away.");

/* ---- MPC hour by hour: five steps + the law ---- */
s = newDark();
darkEyebrow(s, "The control core — ③ the loop, hour by hour");
darkHeading(s, "Receding-horizon MPC: plan, act, re-plan");
const mpcSteps = [
  ["1", "Measure", "realised solar & H₂ made so far today"],
  ["2", "Forecast", "rest of day from yesterday + intraday correction"],
  ["3", "Optimise", "PSO over remaining hours to meet remaining demand"],
  ["4", "Apply first", "commit only the next hour's setpoint"],
  ["5", "Re-plan", "real weather arrives → back to step 1"],
];
mpcSteps.forEach((m, i) => {
  const x = 0.6 + i * 2.48;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.3, w: 2.28, h: 2.3, rectRadius: 0.1,
    fill: { color: NAVY2 }, line: { color: i === 4 ? GOLD : "27516E", width: i === 4 ? 1.75 : 1 } });
  s.addShape(p.shapes.OVAL, { x: x + 0.9, y: 2.05, w: 0.5, h: 0.5, fill: { color: GOLD } });
  s.addText(m[0], { x: x + 0.9, y: 2.05, w: 0.5, h: 0.5, margin: 0, align: "center", valign: "middle",
    fontFace: SERIF, fontSize: 18, bold: true, color: NAVY });
  s.addText(m[1], { x: x + 0.1, y: 2.78, w: 2.08, h: 0.4, margin: 0, align: "center",
    fontFace: SANS, fontSize: 15, bold: true, color: WHITE });
  s.addText(m[2], { x: x + 0.18, y: 3.2, w: 1.92, h: 1.3, margin: 0, align: "center", valign: "top",
    fontFace: SANS, fontSize: 11.5, color: "AEC2D4", lineSpacingMultiple: 1.06 });
  if (i < 4) s.addShape(p.shapes.LINE, { x: x + 2.28, y: 3.45, w: 0.2, h: 0,
    line: { color: GOLD, width: 2, endArrowType: "triangle" } });
});
s.addShape(p.shapes.LINE, { x: 11.46, y: 4.85, w: -10.86, h: 0,
  line: { color: GOLD, width: 1.5, dashType: "dash", endArrowType: "triangle" } });
s.addText("receding horizon — repeats every hour", { x: 0.6, y: 4.9, w: 11, h: 0.4, margin: 0,
  align: "center", fontFace: SANS, fontSize: 12.5, italic: true, color: GOLD });
/* the law, in one line */
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.38, w: 12.13, h: 0.98, rectRadius: 0.09,
  fill: { color: NAVY2 }, line: { color: GOLD, width: 1 } });
s.addText("u*(k) = arg min  Σ p(j)·[u(j) − d(j|k)]⁺·T  +  λ·[D − x(k) − Σ g(u(j))·T]⁺",
  { x: 0.9, y: 5.48, w: 9.35, h: 0.4, margin: 0, fontFace: "Consolas", fontSize: 13, bold: true, color: WHITE });
s.addText("over u(k) … u(23) — the horizon shrinks · d(j|k) = α(k)·d_yesterday(j), α = today's realised clearness · apply only u*(k)",
  { x: 0.9, y: 5.92, w: 9.35, h: 0.32, margin: 0, fontFace: SANS, fontSize: 10.5, italic: true, color: "AEC2D4" });
s.addText("u(k) = κ(x(k), α(k))\nan implicit feedback law", { x: 10.3, y: 5.38, w: 2.3, h: 0.98, margin: 0,
  align: "center", valign: "middle", fontFace: SANS, fontSize: 11, bold: true, italic: true, color: GOLD, lineSpacingMultiple: 1.05 });
s.addText("Benchmarks:  perfect-foresight (unreachable lower bound)   ·   reactive rule-based (time-blind constant rate)",
  { x: 0.6, y: 6.55, w: 12.1, h: 0.4, margin: 0, align: "center", fontFace: SANS, fontSize: 12,
    bold: true, color: "D6E3EF" });
s.addNotes("⏱ ~25 s — a quick verbal recap of the block diagram, in plain words; don't re-explain. Walk the five steps as a loop. The key idea: MPC never sees the future perfectly — it forecasts, acts on the first step, and corrects when reality differs. That correction is disturbance rejection. End by naming the two benchmarks so the results slide lands: perfect-foresight is the bound nobody can reach; the rule-based controller is what a plant does without us.");

/* ============================================================================
 *  PART III divider
 * ========================================================================== */
divider("III", "Results",
  "What the controller does, and what it is worth — on real 2023 data.",
  "Presented by " + PRES2)
  .addNotes("Hand over to Presenter 2. The results are the payoff — slow down here.");

/* ---- Result 1: daily dispatch ---- */
s = newLight();
eyebrow(s, "Result — what the controller does");
heading(s, "It rides free solar and dodges the evening peak");
fig(s, "day_schedule_ghardaia.png", 0.45, 1.6, 8.5, 5.5);
statCard(s, 9.35, 1.85, 3.4, "≈ 27.8", "DA/kg — clear summer, 200 kg/day", TEAL);
bullets(s, [
  "Full power on cheap night grid (1.21 DA).",
  "Setpoint tracks the PV mid-day → near-zero grid import.",
  "Backs off / shuts down through the 8.11 DA peak.",
  "Cloudy day shows real 15-min cloud transients — the optimiser still finds the cheap windows.",
], 9.35, 3.45, 3.5, 3.4, INK, 13.5);
foot(s);
s.addNotes("Nobody told it to avoid the peak — it derives that from the price signal. Three real 2023 days: clear summer, cloudy summer, clear winter. Point at the blue (cheap night) and red (peak) bands and show the setpoint following them. This is the qualitative 'it behaves intelligently' result; the next slide quantifies the value.");

/* ---- Result 2: vs traditional ---- */
s = newLight();
eyebrow(s, "Result — value vs traditional operation");
heading(s, "50–59 % cheaper than time-blind operation");
fig(s, "baseline_comparison_ghardaia.png", 0.45, 1.65, 8.0, 5.0);
statCard(s, 9.0, 1.9, 1.85, "−59%", "vs constant baseload", GOLD);
statCard(s, 10.95, 1.9, 1.85, "−51%", "vs greedy ASAP", GOLD);
bullets(s, [
  "Same hydrogen, same plant, same tariff — only the dispatch timing differs.",
  "Up to 100 % cheaper at low demand fully covered by solar.",
  "Naive rules degrade as demand rises; the optimiser stays cheapest across the whole range.",
], 9.0, 3.55, 3.85, 3.0, INK, 13.5);
foot(s);
s.addNotes("This quantifies the contribution against how a plant would actually run: a constant baseload, or greedily producing as soon as possible. At 200 kg/day the optimiser is ≈27.8 DA/kg vs 67.9 (constant) and 55.8 (greedy) — quote it as ≈28 so it matches the previous slide's card exactly. That is the measurable value of the controller. RELATION TO THE NEXT SLIDE: the optimiser here KNOWS the whole day (perfect foresight) — this slide establishes the SIZE OF THE PRIZE that timing intelligence is worth. The next slide removes the oracle and asks how much of that prize a deployable, forecast-driven closed loop actually collects. Careful: the −51 % here (vs greedy, this day) and the −51 % there (MPC vs reactive rule, across the year) are numerically coincidental — different comparisons.");

/* ---- Result 3: control comparison (headline) ---- */
s = newLight();
eyebrow(s, "Result — control-strategy comparison (headline)");
heading(s, "MPC nearly matches the optimum, beats reactive control");
fig(s, "mpc_comparison.png", 0.45, 1.7, 8.55, 4.9);
statCard(s, 9.5, 1.95, 3.3, "+2.4%", "MPC gap to perfect-foresight", GREEN);
statCard(s, 9.5, 3.55, 3.3, "−51%", "MPC vs reactive rule", TEAL);
s.addText("Closed-loop MPC recovers ≈ 98 % of an unreachable optimum and roughly halves the cost of reactive control — across the year, with imperfect forecasts.",
  { x: 9.5, y: 5.25, w: 3.3, h: 1.5, margin: 0, fontFace: SANS, fontSize: 13, color: MUTE,
    valign: "top", lineSpacingMultiple: 1.1 });
foot(s);
s.addNotes("This is the strongest control-engineering result and the headline of the defense. The blue (MPC) line sits almost on top of the green (optimum) line and far below the red (reactive rule), day after day. Message: feedback control tracks the optimal bound and far exceeds the reactive baseline, even though it never sees the weather perfectly. On a single worst-forecast day MPC can be ~+10 %; averaged it is ~+2.4 %. RELATION TO THE PREVIOUS SLIDE: slide 'vs traditional' priced the naive-to-optimal gap with the weather KNOWN; this slide is the same idea in the real world — that optimum becomes the unreachable green bound, the rule is what plants actually do, and closed-loop MPC lands within +2.4 % of the bound. The NEXT slide dissects one real cloudy day to show the mechanism that makes this possible.");

/* ---- Result 3b: disturbance anatomy — what a cloud actually does ---- */
s = newLight();
eyebrow(s, "Result — behaviour to disturbances");
heading(s, "What a passing cloud actually does");
fig(s, "mpc_cloud_anatomy.png", 0.45, 1.5, 12.4, 3.72);
const cloudCards = [
  ["WITHIN THE HOUR — PHYSICS", CORAL,
   "u(k) is held; the grid absorbs every dip instantly: q = [u − d]⁺. A cloud costs money, never hydrogen — g(u) does not see the weather."],
  ["AT THE HOUR — FEEDBACK", GREEN,
   "Realised energy updates the clearness α(k), and the rest of the day is re-optimised. α integrates energy: fast transients are filtered out; a persistent overcast shifts the whole plan."],
  ["THE PRICE — SMALL", TEAL,
   "This real cloudy day: 200 kg delivered, 55.6 vs 54.4 DA/kg — only +2.1 % above perfect foresight. Year average +2.4 %; worst day ≈ +10 %."],
];
cloudCards.forEach((c, i) => {
  const x = 0.6 + i * 4.19;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 5.42, w: 3.95, h: 1.38, rectRadius: 0.08,
    fill: { color: CARD }, line: { color: LINE_C, width: 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x, y: 5.42, w: 3.95, h: 0.08, fill: { color: c[1] } });
  s.addText(c[0], { x: x + 0.22, y: 5.56, w: 3.55, h: 0.26, margin: 0, fontFace: SANS,
    fontSize: 10.5, bold: true, color: c[1], charSpacing: 1 });
  s.addText(c[2], { x: x + 0.22, y: 5.84, w: 3.55, h: 0.9, margin: 0, fontFace: SANS,
    fontSize: 9.8, color: INK, valign: "top", lineSpacingMultiple: 1.03 });
});
foot(s);
s.addNotes("⏱ ~45 s. This answers the question every practical examiner asks: 'and what happens when a cloud passes?' — with a REAL logged episode (3 July 2023, our cloudy representative day; MPC re-run with full logging). THREE TIMESCALES: (1) Within the committed hour, the setpoint is deliberately held constant — the grid covers every 15-minute dip automatically (the coral slivers in the figure), and when the cloud clears, any brief surplus is exported at zero revenue. Hydrogen output g(u) never sees the weather: a cloud costs money, never hydrogen — feasibility is untouchable. (2) At the next hour boundary, feedback acts: the realised solar energy updates the clearness ratio α(k) — watch the lower panel: a sunny start pushes α above 1, the midday clouds pull it to ≈0.75, and by evening it settles near 0.95 — and the remaining day is re-optimised with PSO. Because α integrates ENERGY, a fast transient barely moves it (no chattering, stack-friendly), while a persistent overcast genuinely re-shapes the plan. (3) The price of all this unpredictability, on this genuinely cloudy day: +2.1 % over perfect foresight, with the full 200 kg delivered. If asked 'what if the cloud stays all afternoon?' — α drops persistently, the re-plan hedges into the remaining cheap hours, and demand is still met because rated capability over the remaining hours far exceeds the remaining quota. If asked 'why not react sub-hourly?' — prices change hourly and there is no storage, so sub-hourly reaction adds nothing (backup A8); it would only chase noise.");

/* ---- Result 4: annual ---- */
s = newLight();
eyebrow(s, "Result — full-year 2023 performance");
heading(s, "A whole year: cheap green summers, dear winters");
fig(s, "annual_calendar.png", 0.45, 1.65, 7.7, 2.95);
fig(s, "annual_monthly.png", 0.55, 4.55, 7.5, 2.55);
statCard(s, 8.45, 1.85, 2.15, "72.8 t", "H₂ / year", TEAL);
statCard(s, 10.65, 1.85, 2.1, "364/364", "days demand met", GREEN);
statCard(s, 8.45, 3.45, 2.15, "45.8", "DA/kg avg (28–82)", TEAL);
statCard(s, 10.65, 3.45, 2.1, "37 %", "solar-powered", GREEN);
bullets(s, [
  "364 days simulated end-to-end on real PV.",
  "Total 3.33 M DA/yr; strong seasonal pattern.",
  "Summer ≈ 28 DA/kg, winter ≈ 82 DA/kg — the calendar heatmap shows it at a glance.",
], 8.45, 5.05, 4.35, 2.0, INK, 13);
foot(s);
s.addNotes("The controller is not a one-day demo — it runs the whole year unattended and meets demand every single day. The calendar heatmap (green = cheap) makes the seasonality obvious. Use the KPIs as the headline numbers: 72.8 t/yr at 45.8 DA/kg average, 37 % directly solar-powered.");

/* ---- Result 5: battery (honest) ---- */
s = newLight();
eyebrow(s, "Result — storage feasibility (an honest finding)");
heading(s, "A battery helps the bill but not the business case");
fig(s, "battery_day.png", 0.45, 1.65, 7.3, 5.3);
fig(s, "battery_sizing.png", 7.95, 1.75, 5.0, 3.35);
bullets(s, [
  "With a 4 MWh battery, energy cost falls 53.2 → 39.2 DA/kg (−26 %): it charges on cheap night power + surplus solar and discharges through the peak — real control behaviour.",
  "But with amortised CAPEX (250 $/kWh), LCOH is minimised at 0 MWh — storage is not cost-justified under the CREG tariff. Break-even ≈ 20 $/kWh (≈ 12× below today).",
], 7.95, 5.2, 5.0, 1.9, INK, 12.5);
foot(s);
s.addNotes("Present this as an honest feasibility result, not a sales pitch. Technically the battery works and behaves exactly as control intuition says (charge cheap, discharge at peak). Economically it does not pay back at the Algerian tariff spread — it would only pay under much higher price volatility or far cheaper batteries. Juries respect a negative result that is clearly reasoned. Optimiser detail (PSO + LP decomposition) is a backup slide.");

/* ============================================================================
 *  PART IV divider
 * ========================================================================== */
divider("IV", "Deliverables, Demo & Conclusion",
  "The live dashboard, and what it all adds up to.",
  "Presented by " + PRES2)
  .addNotes("Energy up — this is the part the jury remembers. Have the laptop ready.");

/* ---- Deliverable: dashboard ---- */
s = newDark();
darkEyebrow(s, "Deliverable — interactive dashboard");
darkHeading(s, "The controller, live");
demoBadge(s, 10.85, 0.6);
shot(s, "dashboard_daily.png", 0.6, 1.75, 5.1, 5.05, true);
bullets(s, [
  "A Streamlit dashboard with five tabs: daily dispatch, control strategy, annual performance, smart-vs-traditional, and validation.",
  "Pick any real 2023 day and an H₂ demand; the PSO runs live and returns the least-cost 24-hour schedule.",
  "Every run is checked on the ETAP-validated network — feasibility is shown alongside the cost.",
  "An optional battery toggle overlays the LP-optimal storage trajectory.",
], 6.15, 1.95, 6.6, 3.9, "D6E3EF", 14.5);
s.addText("Backup if the live demo fails: this screenshot is the Daily-Dispatch tab on the clear-summer day (200 kg/day → ≈ 27.8 DA/kg).",
  { x: 6.15, y: 6.0, w: 6.6, h: 0.8, margin: 0, fontFace: SANS, fontSize: 12, italic: true, color: "8EA6BC",
    valign: "top", lineSpacingMultiple: 1.1 });
s.addNotes("THE LIVE DEMO — the only one, so give it ~2 minutes. Run:  streamlit run app/dashboard.py  — then drag the demand slider and hit Run Optimization to show the schedule recompute live; flip to the Control Strategy tab to show MPC vs the optimum vs the rule; flip to Validation to show 24/24 PASS. If the laptop/projector misbehaves, this screenshot is the fallback.");

/* ---- Conclusion ---- */
s = newDark();
darkEyebrow(s, "Conclusion");
darkHeading(s, "What we delivered");
const concl = [
  ["✓", "An ETAP-validated, automatable plant model (24/24 checks)."],
  ["✓", "A real-data pipeline: CAMS+ERA5 → PySAM and the real CREG tariff, full 2023."],
  ["✓", "Least-cost dispatch via PSO, and a supervisory MPC controller with feedback."],
  ["✓", "Quantified value: 50–59 % cheaper than time-blind operation; MPC within ≈2.4 % of the optimum."],
  ["✓", "A full-year study (72.8 t/yr, 45.8 DA/kg) and an honest storage-feasibility finding."],
  ["✓", "A live deliverable: an interactive dashboard on the validated engine."],
];
concl.forEach((c, i) => {
  const y = 2.05 + i * 0.78;
  s.addText(c[0], { x: 0.7, y, w: 0.5, h: 0.6, margin: 0, fontFace: SANS, fontSize: 18, bold: true, color: GREEN });
  s.addText(c[1], { x: 1.25, y, w: 11.4, h: 0.6, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 15.5, color: "D6E3EF" });
});
s.addText("In one line:  a validated, automated supervisory controller that makes hydrogen for about half the cost of running the plant blindly — and you can watch it work.",
  { x: 0.7, y: 6.6, w: 11.5, h: 0.42, margin: 0, fontFace: SERIF, fontSize: 14, italic: true, bold: true, color: GOLD });
s.addNotes("Reaffirm the contribution as completed work (this is a defense, not a progress update). Tie the ticks back to the FOUR PROMISES of the objectives slide — trusted model (ticks 1–2), controller that decides (tick 3), proof it pays (ticks 4–5), something you can touch (tick 6). Land the one-liner with confidence.");

/* ---- Limitations & future work ---- */
s = newLight();
eyebrow(s, "Critical reflection");
heading(s, "Limitations & future work");
s.addText("LIMITATIONS", { x: 0.7, y: 1.85, w: 5.8, h: 0.35, margin: 0, fontFace: SANS, fontSize: 14,
  bold: true, color: CORAL, charSpacing: 2 });
bullets(s, [
  "Single weather year (2023) and one site — robustness across years/sites not yet swept.",
  "The network is comfortably within limits, so voltage/loading constraints rarely bind at this PV size.",
  "Forecast model is a simple persistence + clearness correction, not a learned predictor.",
  "Decisions are hourly; sub-hourly control only matters once storage is added.",
], 0.7, 2.25, 5.85, 4.2, INK, 13.5);
s.addText("FUTURE WORK", { x: 6.9, y: 1.85, w: 5.8, h: 0.35, margin: 0, fontFace: SANS, fontSize: 14,
  bold: true, color: GREEN, charSpacing: 2 });
bullets(s, [
  "Sensitivity / robustness across multiple weather years and sites.",
  "Size the PV larger so network limits activate — then constraints truly drive the control.",
  "Learned PV forecasting; a policy-based 15-min controller with storage.",
  "Multi-objective dispatch (cost vs CO₂) and surrogate-model acceleration.",
], 6.9, 2.25, 5.85, 4.2, INK, 13.5);
foot(s);
s.addNotes("Show you know where the work stops. State limitations before the jury does — it builds credibility. Each future-work item maps to a limitation. The 'size PV so limits bind' item is the most control-interesting next step and a good thing to volunteer.");

/* ---- Thank you / questions ---- */
s = newDark();
s.addShape(p.shapes.OVAL, { x: 10.3, y: -2.5, w: 6.2, h: 6.2, fill: { color: NAVY2 } });
s.addShape(p.shapes.OVAL, { x: 11.4, y: 4.2, w: 4.6, h: 4.6, fill: { color: NAVY3 } });
s.addText("THANK YOU", { x: 0.7, y: 2.0, w: 11, h: 1.0, margin: 0, fontFace: SERIF, fontSize: 50,
  bold: true, color: WHITE });
s.addText("We welcome your questions.", { x: 0.72, y: 3.25, w: 11, h: 0.6, margin: 0, fontFace: SANS,
  fontSize: 20, color: "AEC2D4" });
s.addText([
  { text: PRES1 + "   ·   " + PRES2 + "\n", options: { color: WHITE, bold: true, fontSize: 15, breakLine: true } },
  { text: "M2 Automation · University of Boumerdès · " + DEFENSE_DATE + "\n", options: { color: "8EA6BC", fontSize: 13, breakLine: true } },
  { text: "All code, data and figures are versioned and reproducible (one script per figure).", options: { color: "8EA6BC", fontSize: 12.5, italic: true } },
], { x: 0.72, y: 4.5, w: 11.5, h: 1.6, margin: 0, fontFace: SANS, lineSpacingMultiple: 1.2 });
s.addText("Backup slides follow ▸", { x: 0.72, y: 6.6, w: 6, h: 0.4, margin: 0, fontFace: SANS,
  fontSize: 12, italic: true, color: GOLD });
stampNo(s, true);
s.addNotes("Closing. Thank the jury, invite questions, and stay calm — the appendix slides that follow are there to answer the common ones (validation table, PSO/MPC detail, tariff, electrolyzer, resolution choice, storage architecture, provenance). Jump to them by slide number when relevant.");

/* ============================================================================
 *  APPENDIX
 * ========================================================================== */
function appendixDivider() {
  const sd = newDark();
  sd.addText("APPENDIX", { x: 0.7, y: 2.7, w: 11, h: 1.0, margin: 0, fontFace: SERIF, fontSize: 46,
    bold: true, color: WHITE });
  sd.addText("Backup slides for jury questions", { x: 0.72, y: 3.85, w: 11, h: 0.5, margin: 0,
    fontFace: SANS, fontSize: 18, color: "AEC2D4" });
  sd.addText("Validation · network · tariff · PSO · MPC · electrolyzer · resolution · storage · reproducibility",
    { x: 0.72, y: 4.5, w: 11.5, h: 0.5, margin: 0, fontFace: SANS, fontSize: 13, italic: true, color: GOLD });
  sd.addNotes("Not presented in the main talk — use these to answer questions precisely.");
}
appendixDivider();

function appHead(s, kicker, title) {
  s.addText("APPENDIX · " + kicker.toUpperCase(), { x: 0.6, y: 0.42, w: 12, h: 0.3, margin: 0,
    fontFace: SANS, fontSize: 11.5, bold: true, color: GOLD, charSpacing: 2 });
  s.addText(title, { x: 0.6, y: 0.72, w: 12.1, h: 0.8, margin: 0, fontFace: SERIF, fontSize: 26,
    bold: true, color: NAVY });
}

/* A1 — validation table */
/* ---- A0: run of show (rehearsal sheet) ---- */
s = newLight();
appHead(s, "A0 — run of show", "Minute-by-minute plan (rehearsal sheet — not presented)");
const ros = [
  ["0:00", "P1", "Title & hook — “a controller that roughly halves the cost of green hydrogen — shown running live.”"],
  ["0:30", "P1", "Agenda + who presents what (30 s, don't dwell)"],
  ["1:00", "P1", "The product — 3× diesel per kg · 97 Mt industry · the colours · electricity = the cost"],
  ["2:00", "P1", "Why now (reserves ≈ 50 yr, CBAM 2026, solar −90 %) → three strategies (141 / 117 kg / 27.8) → the four promises"],
  ["5:15", "P1", "Part II — the method in one picture (4 stages, real thumbnails) → real data & the official tariff"],
  ["7:15", "P1", "Validation vs the industry reference (24/24) → electrolyzer physics (54 kWh/kg, 10 % turndown)"],
  ["9:00", "P1", "① the problem: formulation + formal statement (state-space, Hammerstein, least-cost J) → HANDOVER"],
  ["10:00", "P2", "PSO — concept & true update rule → convergence (3 seeds, same ≈5,565 DA optimum)"],
  ["11:30", "P2", "③ the loop — MPC named at last: block diagram in equations + receding horizon → the law in one line"],
  ["13:30", "P2", "Results — day plan → vs traditional → MPC (+2.4 %, −51 %) → cloud anatomy (+2.1 %) → annual → battery"],
  ["17:20", "P2", "Demo — dashboard live (~2 min: slider → optimise → control tab → validation; screenshot fallback ready)"],
  ["19:10", "P2", "Conclusion → limitations → thank you at 20:00"],
];
ros.forEach((r, i) => {
  const y = 1.7 + i * 0.41;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.1, h: 0.36, rectRadius: 0.05,
    fill: { color: i % 2 ? LIGHT : CARD }, line: { color: LINE_C, width: 0.5 } });
  s.addText(r[0], { x: 0.78, y, w: 0.7, h: 0.36, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 11.5, bold: true, color: TEAL });
  s.addText(r[1], { x: 1.52, y, w: 0.45, h: 0.36, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 11, bold: true, color: r[1] === "P1" ? TEAL : CORAL });
  s.addText(r[2], { x: 2.05, y, w: 10.5, h: 0.36, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 10.8, color: INK });
});
s.addText("Running long?  Compress in this order: battery → cloud anatomy → hydrogen 101.  Never compress: validation, the MPC comparison, the conclusion.",
  { x: 0.6, y: 6.72, w: 12.1, h: 0.35, margin: 0, fontFace: SANS, fontSize: 11.5, italic: true, bold: true, color: CORAL });
s.addNotes("Not presented — a rehearsal artefact for the two of you. Print it or keep it on a phone during practice runs. The timestamps assume a strict 20-minute slot; rehearse to 19:30 so questions never start late. The handover sentence (P1 → P2 at ≈9:20): 'That is the problem, stated formally — [Name] will now show you how we solve it, every hour, and what that is worth.'");

s = newLight();
appHead(s, "A1 — validation", "ETAP ↔ pandapower: 24/24 checks");
fig(s, "etap_validation_table.png", 0.5, 1.6, 8.35, 5.45);
bullets(s, [
  "Three operating points × eight quantities = 24 checks.",
  "Voltages within ±0.01 pu; transformer loading within 2 pts; flows/losses within 2 %.",
  "PV-export case reproduces the reverse-power-flow sign (grid P = −0.533 MW).",
  "Newton-Raphson solver, matching ETAP's.",
  "Every number: results/tables/validation_pandapower_vs_etap.csv, regenerated by one script.",
], 9.1, 1.95, 3.7, 4.6, INK, 12);
s.addNotes("If the jury wants proof of the validation, this is the full 24-row comparison, typeset from the CSV the validation script writes. Every row PASS — worst absolute voltage error 4.3 × 10⁻⁶ pu. The PV-export row is worth pointing at: the negative slack power (−0.5328 vs −0.53274 MW) shows the model reproduces the reverse-power-flow direction, not just magnitudes.");

/* A2 — network & parameters */
s = newLight();
appHead(s, "A2 — network", "Single-line model & key parameters");
const np = [
  ["Utility grid U1", "11 kV slack, 500 MVAsc, X/R = 10"],
  ["Transformer T1", "2 MVA, 11 / 0.415 kV, Z = 6.25 %, X/R = 6"],
  ["Electrolyzer ELY", "0.800 MW, pf 0.95, constant-power load"],
  ["PV array PVA1", "≈ 600 kWp DC / 630 kVA inv → 534 kW AC full sun"],
  ["Limits", "V 0.95–1.05 pu · transformer ≤ 100 %"],
];
np.forEach((r, i) => {
  const y = 1.95 + i * 0.92;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 7.4, h: 0.78, rectRadius: 0.07,
    fill: { color: CARD }, line: { color: LINE_C, width: 1 } });
  s.addText(r[0], { x: 0.8, y, w: 2.7, h: 0.78, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 13.5, bold: true, color: TEAL });
  s.addText(r[1], { x: 3.5, y, w: 4.4, h: 0.78, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 12.5, color: INK });
});
fig(s, "net_night.png", 8.3, 1.75, 4.5, 3.7);
s.addText("NIGHT case: PV off, grid supplies the full 0.8 MW load.",
  { x: 8.3, y: 5.6, w: 4.5, h: 0.5, margin: 0, align: "center", fontFace: SANS, fontSize: 12,
    italic: true, color: MUTE });
s.addNotes("All parameters were taken from the ETAP project and recorded before the pandapower rebuild. The electrolyzer is a constant-power load (a regulated rectifier holds commanded power), which is why it draws exactly 0.8 MW at every operating point.");

/* A3 — tariff detail */
s = newLight();
appHead(s, "A3 — economics", "The CREG 51NM time-of-use tariff");
bullets(s, [
  "Official Algerian MT schedule (code 51NM) — exact energy rates: 1.2050 (creuses) / 2.1645 (pleines) / 8.1147 (pointe) DA/kWh.",
  "Windows: pointe 17h00–21h00 · pleines 06h00–17h00 & 21h00–22h30 · creuses 22h30–06h00.",
  "Prime de puissance 4.37 DA/kW/month on subscribed power — dispatch-independent, so excluded from the optimisation; imported energy is what the controller can move.",
  "UTC weather aligned to local time; hourly decisions sample the hour start (22h00–23h00 billed pleines — conservative).",
], 0.6, 1.75, 8.3, 2.75, INK, 12);
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 9.25, y: 1.8, w: 3.5, h: 2.55, rectRadius: 0.1,
  fill: { color: NAVY }, shadow: sh() });
s.addText("6.7×", { x: 9.25, y: 2.05, w: 3.5, h: 1.0, margin: 0, align: "center", fontFace: SERIF,
  fontSize: 52, bold: true, color: GOLD });
s.addText("peak-to-night ratio — the spread that makes timing a real decision",
  { x: 9.45, y: 3.15, w: 3.1, h: 1.0, margin: 0, align: "center", fontFace: SANS, fontSize: 12,
    color: "D6E3EF", lineSpacingMultiple: 1.1 });
fig(s, "tariff_51nm_day.png", 0.7, 4.55, 8.35, 2.45);
s.addText("One day of the official grille, to the centime — the dashed line is the old flat 4.68 DA/kWh tariff the study replaced.",
  { x: 9.25, y: 4.85, w: 3.5, h: 1.6, margin: 0, fontFace: SANS, fontSize: 11.5, italic: true, color: MUTE, lineSpacingMultiple: 1.15 });
s.addNotes("Source URL is in src/economics.py (CREG, 'Comment lire votre facture'). The staircase figure shows the official day to the centime, including the 22h30 boundary. The peak ratio is the single most important economic fact in the thesis — it is why shifting load off the evening peak is worth so much. If asked about the demand charge: it is levied on SUBSCRIBED power, a contract constant — no dispatch decision changes it, so the optimisation correctly ignores it.");

/* A4 — PSO detail */
s = newLight();
appHead(s, "A4 — optimiser", "PSO — formulation & settings");
bullets(s, [
  "Decision vector: 24 hourly setpoints ∈ {0} ∪ [0.08, 0.80] MW — searched in [0, 0.8], snapped by a repair operator (below turndown → off).",
  "Objective: J = Σ p·[u − d]⁺·Δt (15-min accounting) + 10⁷ DA/kg × any demand shortfall.",
  "Update: vᵢ ← w·vᵢ + c₁r₁(pᵢ−xᵢ) + c₂r₂(g−xᵢ) with r₁, r₂ ~ U(0,1); |v| ≤ 20 % of range; pymoo adapts w, c₁, c₂ online (0.9 / 2.0 / 2.0 start).",
  "Runs: day plan 60 particles × 300 generations (converged by ≈150); inside the MPC loop 40 × 120 per re-plan (speed).",
  "3 random seeds reach the same ≈5,565 DA optimum → reproducible. Gradient-free → handles the non-linear g and the discontinuous tariff directly.",
], 0.6, 1.85, 7.0, 4.7, INK, 13);
fig(s, "pso_convergence.png", 7.85, 2.0, 5.0, 3.1);
s.addNotes("This is the algorithmic backbone. If asked 'why PSO and not MILP', the answer is the non-linearity and the discontinuity — and that PSO converges reproducibly here, which we demonstrate with the three-seed plot.");

/* A5 — MPC detail */
s = newLight();
appHead(s, "A5 — controller", "MPC — forecast, horizon, feedback");
bullets(s, [
  "Day-ahead forecast: yesterday's PV profile as persistence, corrected intraday by how clear today has actually been so far.",
  "Receding horizon: at hour h, re-optimise hours h…24 (PSO) to meet the remaining H₂ demand at least cost.",
  "Apply only hour h's setpoint; discard the rest; advance and re-plan when the real PV arrives.",
  "Benchmarks: perfect-foresight (optimise the known day = lower bound) and rule-based (constant rate = reactive).",
  "Across the year: MPC ≈ +2.4 % vs the bound, −51 % vs the rule — disturbance rejection with feedback.",
], 0.6, 1.85, 8.0, 4.6, INK, 14);
statCard(s, 8.85, 2.0, 3.9, "+2.4% / −51%", "MPC vs optimum / vs rule", GREEN);
s.addText("Code: src/mpc.py — mpc_dispatch(), rule_based_dispatch().",
  { x: 8.85, y: 3.6, w: 3.9, h: 0.5, margin: 0, fontFace: SANS, fontSize: 12, italic: true, color: MUTE });
s.addNotes("The forecast is deliberately simple (persistence + clearness correction), which makes the disturbance-rejection result honest — MPC does well despite a naive forecast. A learned forecaster is future work.");

/* A6 — electrolyzer detail */
s = newLight();
appHead(s, "A6 — physics", "PEM electrolyzer model");
bullets(s, [
  "Cell voltage V(i) = E_rev (1.198 V at 60 °C) + Tafel activation (RT/αF)·ln(i/i₀) + ohmic r·i.",
  "Hydrogen from Faraday's law: ṁ = η_F · n_cells · I / (zF) · M_H₂ — with η_F = 0.99, 200 cells.",
  "Stack sized for exactly 0.800 MW at 2 A/cm² (≈ 2.03 V/cell); operating window 10 %–100 %.",
  "Part-load is MORE efficient (lower V at lower i) — the dashed specific-energy curve; the optimiser exploits it within the schedule.",
], 0.6, 1.8, 8.2, 2.6, INK, 12);
statCard(s, 9.0, 1.95, 3.75, "≈ 54", "kWh per kg H₂ at rated", TEAL);
statCard(s, 9.0, 3.5, 3.75, "14.6", "kg H₂/h at 0.8 MW", TEAL);
fig(s, "electrolyzer_curves.png", 0.5, 4.6, 8.4, 2.3);
s.addNotes("This is the conversion physics, with the curves generated from src/physics/electrolyzer_model.py — the exact code the optimiser calls. The two numbers — ≈54 kWh/kg and 14.6 kg/h at rated — let you sanity-check any hydrogen figure in the talk on the spot. Parameters are literature-sourced (Carmo et al. 2013; García-Valverde et al. 2012): α = 0.5, i₀ = 10⁻³ A/cm², r = 0.20 Ω·cm², 60 °C; the cell area is back-solved so rated power is exactly 0.800 MW.");

/* A7 — cost vs demand */
s = newLight();
appHead(s, "A7 — results", "Cost per kg vs daily demand");
fig(s, "cost_vs_demand_ghardaia.png", 0.6, 1.7, 8.0, 5.0);
bullets(s, [
  "Low demand can be met almost entirely from free solar → near-zero cost.",
  "A clear 'knee' where demand outgrows the solar window and grid import (incl. some peak) becomes unavoidable.",
  "Clear-summer cheapest; cloudy-summer and clear-winter cost more for the same demand.",
  "This curve is what the dashboard recomputes live when you move the demand slider.",
], 8.8, 1.95, 4.0, 4.4, INK, 13);
s.addNotes("Good slide to explain the economics intuitively: the controller is essentially free until demand exceeds the solar that fits in cheap hours, then cost rises as it is forced into more expensive grid windows.");

/* A8 — resolution choice */
s = newLight();
appHead(s, "A8 — modelling choice", "Hourly decisions, 15-minute accounting");
bullets(s, [
  "Data, PV, energy, cost and network feasibility are all evaluated at the native 15-minute resolution of the real series.",
  "The dispatch decision is hourly — 24 setpoints, not 96.",
  "Why: hourly commitment is the power-industry day-ahead standard and keeps the PSO low-dimensional and reproducible (24 vs 96 variables).",
  "Sub-hourly control adds negligible value while prices are hourly and there is no storage.",
  "It becomes worthwhile with the Stage-2 battery, where a policy-based 15-min controller is the planned upgrade.",
], 0.6, 1.85, 12.1, 4.5, INK, 15);
s.addNotes("A classic methodology question — defend it explicitly. Decisions at the operator-realistic hourly cadence; accounting at the data's native 15-min resolution. This is a deliberate, justified choice, not a shortcut.");

/* A9 — battery architecture */
s = newLight();
appHead(s, "A9 — storage optimiser", "Decomposed dispatch: PSO + LP");
bullets(s, [
  "The storage problem is decomposed, not solved jointly.",
  "PSO searches only the 24 hourly electrolyzer setpoints (the non-linear, demand-constrained part).",
  "For each candidate, the battery is operated optimally by a linear program (scipy HiGHS): charge/discharge/SOC that minimise grid cost vs the time-of-use price, subject to power and energy limits.",
  "Why: a joint 48-variable PSO converged unreliably (non-monotonic sizing). The decomposition gives provably-optimal storage per candidate, reproducible and monotone results, and a low-dimensional PSO.",
], 0.6, 1.85, 8.1, 4.6, INK, 14);
fig(s, "battery_sizing.png", 8.4, 2.0, 4.4, 3.0);
s.addNotes("If asked how the battery is optimised: emphasise the decomposition. It is the clean engineering answer — PSO for the hard non-linear part, an exact LP for the part that is linear given the setpoints.");

/* A10 — provenance & reproducibility */
s = newLight();
appHead(s, "A10 — reproducibility", "Data provenance & software stack");
const prov = [
  ["Solar irradiance", "CAMS Radiation Service v4.6 (Copernicus), satellite-derived, 15-min"],
  ["Temperature / wind", "ERA5 reanalysis (Copernicus CDS), 2023, nearest cell to Ghardaïa"],
  ["PV model", "NREL SAM via PySAM — single-axis tracking, 15-min AC series"],
  ["Tariff", "Algerian CREG medium-voltage time-of-use (code 51NM)"],
  ["Network / load flow", "pandapower (Newton-Raphson), validated against ETAP 20.6"],
  ["Optimiser", "pymoo / PSO; battery LP via scipy HiGHS"],
  ["Apps", "Streamlit dashboard (daily · control · annual · baselines · validation)"],
];
prov.forEach((r, i) => {
  const y = 1.7 + i * 0.68;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.1, h: 0.58, rectRadius: 0.06,
    fill: { color: i % 2 ? LIGHT : CARD }, line: { color: LINE_C, width: 0.75 } });
  s.addText(r[0], { x: 0.8, y, w: 3.3, h: 0.58, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 13, bold: true, color: TEAL });
  s.addText(r[1], { x: 4.2, y, w: 8.3, h: 0.58, margin: 0, valign: "middle", fontFace: SANS,
    fontSize: 12.5, color: INK });
});
s.addText("Every figure in this deck is regenerated by a single script from the real data — the study is fully reproducible.",
  { x: 0.6, y: 6.55, w: 12.1, h: 0.4, margin: 0, fontFace: SANS, fontSize: 13, italic: true, color: TEAL });
s.addNotes("The reproducibility / integrity slide. Each source is real and cited in code. Note the early-PySAM integrity point if asked: a test run used a non-Ghardaïa weather file and was replaced with real Ghardaïa CAMS data before any result was used — no location was misrepresented.");

/* A11 — positioning / state of the art (moved from the main deck) */
s = newLight();
appHead(s, "A11 — positioning", "Where this work sits (state of the art)");
const sota = [
  ["Professional load-flow tools (ETAP)", "Accurate and trusted, but GUI-bound — not easily scripted for batch optimisation over a whole year.", "GAP: automation"],
  ["Green-H₂ dispatch & techno-economics", "Rich literature on sizing and economics; fewer works close the loop with a real network feasibility check each step.", "GAP: network-aware"],
  ["Metaheuristics for energy scheduling", "PSO / GA widely used for unit commitment; we apply PSO to a non-linear electrolyzer under a discontinuous tariff.", "USED: PSO engine"],
  ["MPC for supervisory energy control", "Established in microgrids; we apply receding-horizon MPC to electrolyzer dispatch with a measured weather disturbance.", "OUR FRAMING"],
];
sota.forEach((r, i) => {
  const y = 1.8 + i * 1.18;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 9.0, h: 1.02, rectRadius: 0.07,
    fill: { color: CARD }, line: { color: LINE_C, width: 1 } });
  s.addText([{ text: r[0] + "\n", options: { bold: true, fontSize: 14.5, color: INK, breakLine: true } },
             { text: r[1], options: { fontSize: 12, color: MUTE } }],
    { x: 0.8, y: y + 0.08, w: 8.6, h: 0.88, margin: 0, fontFace: SANS, valign: "middle", lineSpacingMultiple: 1.03 });
  s.addText(r[2], { x: 9.75, y, w: 3.0, h: 1.02, margin: 0, valign: "middle",
    fontFace: SANS, fontSize: 12.5, bold: true, color: i >= 2 ? GREEN : CORAL });
});
s.addText("Our gap, in one line: an automated, ETAP-validated dispatch optimiser with a feedback (MPC) controller and a live demonstration — on real data.",
  { x: 0.6, y: 6.6, w: 12.1, h: 0.4, margin: 0, fontFace: SANS, fontSize: 13, italic: true, color: TEAL });
s.addNotes("Backup for a literature/positioning question. Professional tools are accurate but not automatable; techno-economic dispatch studies rarely check the network each step or close the loop; we use PSO where it is established and frame the control explicitly. The surrogate-model line of work from the earlier project is deliberately demoted to future work.");

/* ============================================================================ */
p.writeFile({ fileName: "/home/youc/hydrogen-dispatch/Hydrogen_Dispatch_Defense.pptx" })
  .then(f => console.log("WROTE " + f))
  .catch(e => { console.error(e); process.exit(1); });
