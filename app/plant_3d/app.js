// 3D digital twin of the Ghardaïa solar-hydrogen plant.
// Every displayed value comes from window.PLANT_STATE (real CAMS+ERA5 -> PySAM
// PV, ETAP-validated pandapower load flow). No invented numbers.
// three.js, OrbitControls and CSS2DRenderer/CSS2DObject are loaded as classic
// global scripts in index.html and live on the THREE namespace — no ES-module
// imports (ES modules do not load from file:// due to browser CORS).

const DATA = window.PLANT_STATE;
if (!DATA || !DATA.timeseries) {
  const e = document.getElementById('errbox');
  e.hidden = false;
  e.innerHTML = '<h3>No data</h3>plant_data.js (window.PLANT_STATE) failed to load. ' +
    'Regenerate with: python scripts/export_plant_state.py';
  throw new Error('PLANT_STATE missing');
}
const TS = DATA.timeseries, LIM = DATA.meta.limits, N = TS.length;

// ---------- header ----------
document.getElementById('h-site').textContent =
  DATA.meta.site + '  ·  ' + DATA.meta.day;
document.getElementById('src-cap').textContent = 'data: ' + DATA.meta.source;
document.getElementById('h-meta').innerHTML = [
  ['demand', DATA.meta.demand_kg_day + ' kg/d'],
  ['H₂ / day', DATA.meta.total_h2_kg + ' kg'],
  ['cost', DATA.meta.cost_per_kg_da + ' DA/kg'],
].map(([k, v]) => `<div class="kpi"><div class="v">${v}</div><div class="k">${k}</div></div>`).join('');

// ---------- scene ----------
const root = document.getElementById('scene-root');
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x0c1118, 28, 70);
const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.1, 200);
camera.position.set(13, 11, 18);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
root.appendChild(renderer.domElement);

const labelRenderer = new THREE.CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0';
labelRenderer.domElement.style.pointerEvents = 'none';
root.appendChild(labelRenderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 1.5, 0);
controls.maxPolarAngle = Math.PI / 2.05;

scene.add(new THREE.HemisphereLight(0xbdd7ff, 0x2a3340, 0.9));
const sun = new THREE.DirectionalLight(0xfff2d8, 1.5);
sun.castShadow = true;
scene.add(sun);
const sunBall = new THREE.Mesh(
  new THREE.SphereGeometry(0.7, 24, 24),
  new THREE.MeshBasicMaterial({ color: 0xffe08a }));
scene.add(sunBall);

// ground
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(60, 64),
  new THREE.MeshStandardMaterial({ color: 0x141d28, roughness: 1 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);
const grid = new THREE.GridHelper(120, 120, 0x223046, 0x172230);
grid.position.y = 0.01;
scene.add(grid);

const COL = { import: 0xff7a45, export: 0x36d399, pv: 0xffd23f, load: 0x46b1ff };

// ---------- device positions (single-line, left -> right) ----------
const POS = {
  U1: new THREE.Vector3(-13, 0, 0),
  MainBus: new THREE.Vector3(-7.5, 0, 0),
  T1: new THREE.Vector3(-2.5, 0, 0),
  SecondaryBus: new THREE.Vector3(2.5, 0, 0),
  PVA1: new THREE.Vector3(9, 0, -5),
  ELY: new THREE.Vector3(9, 0, 5),
};

function busBar(x, z, kvLabelColor) {
  const g = new THREE.Group();
  const bar = new THREE.Mesh(
    new THREE.BoxGeometry(0.25, 0.25, 4.5),
    new THREE.MeshStandardMaterial({ color: kvLabelColor, metalness: 0.6, roughness: 0.4 }));
  bar.position.set(x, 2.2, z); bar.castShadow = true; g.add(bar);
  for (const dz of [-1.6, 1.6]) {
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 2.2),
      new THREE.MeshStandardMaterial({ color: 0x3a4a60 }));
    post.position.set(x, 1.1, z + dz); g.add(post);
  }
  return g;
}

function buildScene() {
  // U1 — grid pylon
  const pylon = new THREE.Group();
  const tower = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.32, 6),
    new THREE.MeshStandardMaterial({ color: 0x6b7a90 }));
  tower.position.set(POS.U1.x, 3, 0); tower.castShadow = true; pylon.add(tower);
  for (const y of [4.2, 5.2]) {
    const arm = new THREE.Mesh(new THREE.BoxGeometry(3, 0.18, 0.18),
      new THREE.MeshStandardMaterial({ color: 0x6b7a90 }));
    arm.position.set(POS.U1.x, y, 0); pylon.add(arm);
  }
  scene.add(pylon);

  scene.add(busBar(POS.MainBus.x, 0, 0xff6b6b));      // 11 kV
  scene.add(busBar(POS.SecondaryBus.x, 0, 0x46b1ff)); // 0.415 kV

  // T1 — transformer
  const trafo = new THREE.Group();
  const tank = new THREE.Mesh(new THREE.BoxGeometry(2.2, 2.4, 2.2),
    new THREE.MeshStandardMaterial({ color: 0x8a949f, metalness: 0.5, roughness: 0.5 }));
  tank.position.set(POS.T1.x, 1.3, 0); tank.castShadow = true; trafo.add(tank);
  for (const dx of [-0.6, 0.6]) {
    const bush = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 1),
      new THREE.MeshStandardMaterial({ color: 0xcdd6e0 }));
    bush.position.set(POS.T1.x + dx, 2.9, 0); trafo.add(bush);
  }
  scene.add(trafo);

  // PVA1 — tilted panel array (tilt updated with the sun)
  const pvGroup = new THREE.Group();
  pvGroup.position.copy(POS.PVA1);
  for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
    const panel = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.06, 0.8),
      new THREE.MeshStandardMaterial({ color: 0x16335c, metalness: 0.3, roughness: 0.35,
        emissive: 0x0a1a33 }));
    panel.position.set((c - 1.5) * 1.3, 0.7, (r - 1) * 1.0);
    panel.rotation.x = -0.5; panel.castShadow = true; pvGroup.add(panel);
  }
  scene.add(pvGroup);
  window._pvPanels = pvGroup;

  // ELY — electrolyzer stack
  const ely = new THREE.Group();
  const stack = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 2.6, 24),
    new THREE.MeshStandardMaterial({ color: 0x2f6f6a, metalness: 0.4, roughness: 0.5 }));
  stack.position.set(POS.ELY.x, 1.3, 0); stack.castShadow = true; ely.add(stack);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.05, 0.25, 24),
    new THREE.MeshStandardMaterial({ color: 0x9fd8c8 }));
  cap.position.set(POS.ELY.x, 2.7, 0); ely.add(cap);
  scene.add(ely);
}
buildScene();

// ---------- connections + animated flow ----------
const CONN = [
  { a: 'U1', b: 'MainBus', type: 'grid' },
  { a: 'MainBus', b: 'T1', type: 'grid' },
  { a: 'T1', b: 'SecondaryBus', type: 'grid' },
  { a: 'PVA1', b: 'SecondaryBus', type: 'pv' },
  { a: 'SecondaryBus', b: 'ELY', type: 'load' },
];
const FLOWS = [];
function tubePoint(name) { const p = POS[name].clone(); p.y = 2.2; return p; }
for (const c of CONN) {
  const pa = tubePoint(c.a), pb = tubePoint(c.b);
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([pa, pb]),
    new THREE.LineBasicMaterial({ color: 0x3a4a60 }));
  scene.add(line);
  const dots = [];
  for (let i = 0; i < 6; i++) {
    const d = new THREE.Mesh(new THREE.SphereGeometry(0.13, 10, 10),
      new THREE.MeshBasicMaterial({ color: 0xffffff }));
    scene.add(d); dots.push(d);
  }
  FLOWS.push({ ...c, pa, pb, dots, dir: 1, mag: 0, color: 0x46b1ff });
}

// ---------- labels ----------
const LABELS = {};
const NAMES = { U1: 'U1 · Utility grid', MainBus: 'MainBus 11 kV', T1: 'T1 · 2 MVA',
  SecondaryBus: 'SecondaryBus 0.415 kV', PVA1: 'PVA1 · Solar array', ELY: 'ELY · Electrolyzer' };
const LABEL_Y = { U1: 6, MainBus: 3.2, T1: 3.6, SecondaryBus: 3.2, PVA1: 3.2, ELY: 3.6 };
for (const id of Object.keys(POS)) {
  const div = document.createElement('div');
  div.className = 'dev-label';
  const obj = new THREE.CSS2DObject(div);
  obj.position.set(POS[id].x, LABEL_Y[id], POS[id].z);
  scene.add(obj);
  LABELS[id] = div;
}

function busStatus(vm) {
  if (vm < LIM.v_min_pu || vm > LIM.v_max_pu) return 'st-red';
  if (vm < 0.98 || vm > 1.02) return 'st-amber';
  return 'st-green';
}
function loadStatus(pct) {
  if (pct > LIM.loading_max_pct) return 'st-red';
  if (pct > 95) return 'st-amber';
  return 'st-green';
}
const row = (label, val, unit) =>
  `<div class="dl-row">${label} <b>${val}</b> <span class="u">${unit}</span></div>`;

function renderLabels(d) {
  const set = (id, status, name, body, tag) => {
    LABELS[id].className = 'dev-label ' + status;
    LABELS[id].innerHTML =
      `<div class="dl-name"><span class="dot"></span>${name}` +
      (tag ? `<span class="tag ${tag.cls}">${tag.txt}</span>` : '') + `</div>` + body;
  };
  set('U1', 'st-green', NAMES.U1,
    row('P', Math.abs(d.U1.p_mw).toFixed(3), 'MW') + row('I', d.U1.i_a.toFixed(0), 'A'),
    { cls: 'tag-' + d.U1.flow, txt: d.U1.flow });
  set('MainBus', busStatus(d.MainBus.vm_pu), NAMES.MainBus,
    row('V', d.MainBus.vm_pu.toFixed(4), 'pu') + row('', d.MainBus.kv.toFixed(2), 'kV'));
  set('T1', loadStatus(d.T1.loading_pct), NAMES.T1,
    row('load', d.T1.loading_pct.toFixed(1), '%') +
    row('I', d.T1.i_lv_a.toFixed(0), 'A (LV)'));
  set('SecondaryBus', busStatus(d.SecondaryBus.vm_pu), NAMES.SecondaryBus,
    row('V', d.SecondaryBus.vm_pu.toFixed(4), 'pu') + row('', d.SecondaryBus.kv.toFixed(3), 'kV'));
  set('PVA1', 'st-green', NAMES.PVA1,
    row('P', d.PVA1.p_mw.toFixed(3), 'MW') + row('I', d.PVA1.i_a.toFixed(0), 'A'));
  set('ELY', 'st-green', NAMES.ELY,
    row('P', d.ELY.p_mw.toFixed(3), 'MW') + row('I', d.ELY.i_a.toFixed(0), 'A'),
    { cls: d.ELY.on ? 'tag-on' : 'tag-off', txt: d.ELY.on ? 'ON' : 'OFF' });
}

function updateFlows(d) {
  const gridDir = d.U1.flow === 'export' ? -1 : 1;           // import: U1->plant
  const gridCol = d.U1.flow === 'export' ? COL.export : COL.import;
  const gridMag = Math.abs(d.U1.p_mw);
  for (const f of FLOWS) {
    if (f.type === 'grid') { f.dir = gridDir; f.mag = gridMag; f.color = gridCol; }
    else if (f.type === 'pv') { f.dir = 1; f.mag = d.PVA1.p_mw; f.color = COL.pv; }   // PVA1->bus
    else { f.dir = 1; f.mag = d.ELY.p_mw; f.color = COL.load; }                        // bus->ELY
    f.dots.forEach(dot => dot.material.color.setHex(f.color));
  }
}

// ---------- sun position by time of day ----------
function updateSun(step) {
  const h = step * 15 / 60;                       // local hour 0..24
  const day = Math.min(1, Math.max(0, (h - 6) / 14));   // 06:00..20:00 -> 0..1
  const ang = Math.PI * day;                      // sunrise(E) -> sunset(W)
  const up = Math.sin(ang) * 14 + 0.5;
  sun.position.set(-Math.cos(ang) * 18, Math.max(up, -2), 6);
  sunBall.position.copy(sun.position);
  sun.intensity = up > 0 ? 1.6 : 0.05;
  sunBall.visible = up > 0;
  if (window._pvPanels) window._pvPanels.children.forEach(p => {
    p.rotation.z = -Math.cos(ang) * 0.5;          // panels track the sun E->W
  });
}

// ---------- step control ----------
let cur = 0;
function showStep(i) {
  cur = ((i % N) + N) % N;
  const d = TS[cur];
  renderLabels(d); updateFlows(d); updateSun(cur);
  document.getElementById('clock').textContent = d.t;
  document.getElementById('step-num').textContent = cur;
  slider.value = cur;
}
const slider = document.getElementById('slider');
slider.max = N - 1;
slider.addEventListener('input', () => { pause(); showStep(+slider.value); });

let playing = false, acc = 0, interval = 250;
const btn = document.getElementById('btn-play');
function play() { playing = true; btn.innerHTML = '&#10074;&#10074;'; }
function pause() { playing = false; btn.innerHTML = '&#9658;'; }
btn.addEventListener('click', () => playing ? pause() : play());
document.getElementById('speed').addEventListener('change', e => interval = +e.target.value);

// ---------- animate ----------
let last = performance.now();
function animate(now) {
  requestAnimationFrame(animate);
  const dt = now - last; last = now;
  controls.update();

  // advance time when playing
  if (playing) { acc += dt; if (acc >= interval) { acc = 0; showStep(cur + 1); } }

  // move flow dots along their lines
  const tsec = now / 1000;
  for (const f of FLOWS) {
    const active = f.mag > 0.003;
    const speed = 0.15 + Math.min(f.mag, 0.8) * 0.9;
    f.dots.forEach((dot, k) => {
      dot.visible = active;
      if (!active) return;
      let u = ((tsec * speed + k / f.dots.length) % 1);
      if (f.dir < 0) u = 1 - u;
      dot.position.lerpVectors(f.pa, f.pb, u);
    });
  }
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}
showStep(0);
play();
requestAnimationFrame(animate);

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  labelRenderer.setSize(innerWidth, innerHeight);
});
