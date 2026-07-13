// Murmuration — the controller.
//
// Wires the framework-free flocking engine (flock.js) to the dusk-sky WebGL
// scope (scene.js) and the InstancedMesh birds (bird.js): builds the control
// panel from the model's own parameter schema plus the regime picker, runs the
// step→render loop, projects live telemetry, drives three camera modes, and
// keeps a shareable URL in the hash so any run can be reproduced from a link.

import { createScope } from './scene.js';
import { Flock, PARAMS, defaultParams } from './flock.js';
import { PRESETS, PRESET_BY_ID } from './presets.js';
import { makeFlock, makePredator, orient, makeScratch } from './bird.js';

const $ = (id) => document.getElementById(id);
const clamp = (x, lo, hi) => (x < lo ? lo : x > hi ? hi : x);

// ── boot ────────────────────────────────────────────────────────────────────
const stage = $('stage');
const scope = createScope(stage);
const { THREE, scene, camera, controls, composer } = scope;
const scratch = makeScratch(THREE);
const M = new THREE.Matrix4();

// state restored from the URL (regime + params + camera) or the default regime
const boot = readHash();
let regimeId = boot.regime || 'dusk';
const params = { ...defaultParams(), ...(PRESET_BY_ID[regimeId]?.params || {}), ...boot.params };

const flock = new Flock(params, 0xC0FFEE);
let birdMesh = null;
buildBirdMesh();

const predator = makePredator(THREE);
predator.visible = !!params.predator;
scene.add(predator);

let running = true;
let camMode = boot.cam || 'orbit';
let followIndex = -1;
const fieldEls = {};   // key → { input, val, def } | { toggle } — filled by buildControls()

// ── UI: regime chips + parameter sliders + actions ───────────────────────────
buildRegimes();
buildControls();
bindActions();
syncRegimeUI();
setCamMode(camMode, true);
writeHash();

// ── the loop ─────────────────────────────────────────────────────────────────
let last = performance.now();
const clockStart = last;
const polHist = new Float32Array(160); let polIdx = 0;

function frame(now) {
  const dt = clamp((now - last) / 1000, 0, 0.05); // cap long frames (tab wakeups)
  last = now;

  if (running) flock.step(dt);
  updateInstances();
  updatePredatorMesh();
  birdMesh.userData.tick((now - clockStart) / 1000);
  predator.userData.tick((now - clockStart) / 1000);
  updateCamera(dt);
  controls.update();
  updateHUD();

  composer.render();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// ── write each bird's instance matrix from the flock state ───────────────────
function updateInstances() {
  const n = flock.n;
  for (let i = 0; i < n; i++) {
    const vx = flock.vx[i], vy = flock.vy[i], vz = flock.vz[i];
    orient(THREE, M, scratch, flock.px[i], flock.py[i], flock.pz[i], vx, vy, vz, flock.bank[i], 1);
    birdMesh.setMatrixAt(i, M);
  }
  birdMesh.instanceMatrix.needsUpdate = true;
}

function updatePredatorMesh() {
  predator.visible = !!flock.params.predator;
  if (!predator.visible) return;
  const p = flock.pred;
  orient(THREE, M, scratch, p.x, p.y, p.z, p.vx, p.vy, p.vz, 0, 1);
  predator.matrixAutoUpdate = false;
  predator.matrix.copy(M);
}

// ── camera: orbit (track the flock) · follow (chase a bird) · free ───────────
const camTarget = new THREE.Vector3(0, 40, 0);
const camScratch = { pos: new THREE.Vector3(), look: new THREE.Vector3(), fwd: new THREE.Vector3() };

function setCamMode(mode, silent) {
  camMode = mode;
  const label = { orbit: '◎ Orbit', follow: '➤ Follow', free: '✥ Free' }[mode];
  $('btnCamera').textContent = label;
  if (mode === 'follow') {
    controls.enabled = false;
    followIndex = pickLeadBird();
  } else if (mode === 'free') {
    controls.enabled = true;            // free: user fully owns the camera
  } else {
    controls.enabled = true;            // orbit: user orbits, target eases to flock
  }
  if (!silent) announce(`Camera: ${mode}`);
  writeHash();
}

// the bird nearest the leading edge of the flock (front, along mean heading)
function pickLeadBird() {
  const c = flock.metrics.centroid;
  // mean heading
  let hx = 0, hy = 0, hz = 0;
  for (let i = 0; i < flock.n; i++) {
    const s = Math.hypot(flock.vx[i], flock.vy[i], flock.vz[i]) || 1;
    hx += flock.vx[i] / s; hy += flock.vy[i] / s; hz += flock.vz[i] / s;
  }
  const hl = Math.hypot(hx, hy, hz) || 1; hx /= hl; hy /= hl; hz /= hl;
  let best = 0, bestDot = -Infinity;
  for (let i = 0; i < flock.n; i++) {
    const dx = flock.px[i] - c[0], dy = flock.py[i] - c[1], dz = flock.pz[i] - c[2];
    const d = dx * hx + dy * hy + dz * hz;
    if (d > bestDot) { bestDot = d; best = i; }
  }
  return best;
}

function updateCamera(dt) {
  const c = flock.metrics.centroid;
  if (camMode === 'orbit') {
    // ease the orbit pivot onto the moving flock centroid
    camTarget.lerp(camScratch.look.set(c[0], c[1], c[2]), clamp(dt * 1.2, 0, 1));
    controls.target.copy(camTarget);
  } else if (camMode === 'follow') {
    if (followIndex < 0 || followIndex >= flock.n) followIndex = pickLeadBird();
    const i = followIndex;
    const fx = flock.vx[i], fy = flock.vy[i], fz = flock.vz[i];
    const fl = Math.hypot(fx, fy, fz) || 1;
    camScratch.fwd.set(fx / fl, fy / fl, fz / fl);
    const bird = camScratch.look.set(flock.px[i], flock.py[i], flock.pz[i]);
    // sit behind and slightly above the bird, look where it's going
    const desired = camScratch.pos.copy(bird)
      .addScaledVector(camScratch.fwd, -14)
      .add(new THREE.Vector3(0, 4, 0));
    camera.position.lerp(desired, clamp(dt * 3, 0, 1));
    const aim = bird.clone().addScaledVector(camScratch.fwd, 18);
    controls.target.lerp(aim, clamp(dt * 4, 0, 1));
    camera.lookAt(controls.target);
  }
  // 'free' leaves camera + target entirely to OrbitControls
}

// ── heads-up telemetry ───────────────────────────────────────────────────────
let hudTick = 0;
function updateHUD() {
  const m = flock.metrics;
  // sample the order parameter into the ring buffer every frame
  polHist[polIdx = (polIdx + 1) % polHist.length] = m.polarization;
  if ((hudTick++ % 6) !== 0) return;    // throttle DOM writes to ~10 Hz
  $('polReadout').textContent = m.polarization.toFixed(2);
  $('telCount').textContent = flock.n;
  $('telSpeed').textContent = m.speed.toFixed(1);
  $('telNN').textContent = m.nnDist.toFixed(1);
  $('telBank').textContent = Math.round(m.bank) + '°';
  $('telStalls').textContent = m.stalls;
  drawSpark();
}

const spark = $('polSpark'), sctx = spark.getContext('2d');
function drawSpark() {
  const w = spark.width, h = spark.height;
  sctx.clearRect(0, 0, w, h);
  sctx.strokeStyle = 'rgba(226,170,110,0.85)';
  sctx.lineWidth = 1.5;
  sctx.beginPath();
  for (let k = 0; k < polHist.length; k++) {
    const idx = (polIdx + 1 + k) % polHist.length;
    const x = (k / (polHist.length - 1)) * w;
    const y = h - polHist[idx] * (h - 3) - 1.5;
    k === 0 ? sctx.moveTo(x, y) : sctx.lineTo(x, y);
  }
  sctx.stroke();
  // baseline at polarization = 1 (perfectly aligned)
  sctx.strokeStyle = 'rgba(226,170,110,0.18)';
  sctx.beginPath(); sctx.moveTo(0, 1.5); sctx.lineTo(w, 1.5); sctx.stroke();
}

// ── build the InstancedMesh for the current bird count ───────────────────────
function buildBirdMesh() {
  if (birdMesh) {
    scene.remove(birdMesh);
    birdMesh.geometry.dispose();
    birdMesh.material.dispose();
  }
  birdMesh = makeFlock(THREE, flock.n, { size: 1.3, rng: mulberryUI() });
  scene.add(birdMesh);
}
// a private RNG for the render-only per-bird flap phases (kept out of sim seed)
function mulberryUI() { let a = 0x1234567; return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ── control panel construction ───────────────────────────────────────────────
function buildRegimes() {
  const host = $('regimeChips');
  host.innerHTML = '';
  for (const p of PRESETS) {
    const b = document.createElement('button');
    b.className = 'regime';
    b.textContent = p.name;
    b.dataset.id = p.id;
    b.addEventListener('click', () => applyRegime(p.id));
    host.appendChild(b);
  }
}

function buildControls() {
  const host = $('controls');
  host.innerHTML = '';
  const groups = [...new Set(PARAMS.map((p) => p.group))];
  for (const g of groups) {
    const wrap = document.createElement('div');
    wrap.className = 'grp';
    const head = document.createElement('div');
    head.className = 'grp-head';
    head.textContent = g;
    wrap.appendChild(head);
    for (const def of PARAMS.filter((p) => p.group === g)) wrap.appendChild(buildField(def));
    host.appendChild(wrap);
  }
}

function buildField(def) {
  const f = document.createElement('div');
  f.className = 'field' + (def.bool ? ' bool' : '');
  const label = document.createElement('label');
  label.textContent = def.label;
  label.htmlFor = 'f_' + def.key;
  f.appendChild(label);

  if (def.bool) {
    const t = document.createElement('button');
    t.className = 'toggle';
    t.id = 'f_' + def.key;
    t.setAttribute('aria-pressed', String(!!params[def.key]));
    t.textContent = params[def.key] ? 'on' : 'off';
    t.addEventListener('click', () => {
      const v = params[def.key] ? 0 : 1;
      setParam(def.key, v);
      t.setAttribute('aria-pressed', String(!!v));
      t.textContent = v ? 'on' : 'off';
    });
    f.appendChild(t);
    fieldEls[def.key] = { toggle: t };
    return f;
  }

  const val = document.createElement('span');
  val.className = 'val';
  const input = document.createElement('input');
  input.type = 'range'; input.id = 'f_' + def.key;
  input.min = def.min; input.max = def.max; input.step = def.step;
  input.value = params[def.key];
  val.textContent = fmt(params[def.key], def);
  input.addEventListener('input', () => {
    const v = parseFloat(input.value);
    val.textContent = fmt(v, def);
    setParam(def.key, v);
  });
  f.appendChild(val);
  f.appendChild(input);
  fieldEls[def.key] = { input, val, def };
  return f;
}

function fmt(v, def) {
  const s = (def.step < 1) ? v.toFixed(def.step < 0.1 ? 2 : 1) : String(Math.round(v));
  return def.unit ? `${s} ${def.unit}` : s;
}

// ── parameter + regime application ───────────────────────────────────────────
function setParam(key, value) {
  params[key] = value;
  const wasN = flock.n;
  flock.setParam(key, value);
  if (key === 'birds' && flock.n !== wasN) buildBirdMesh();
  if (key === 'predator') predator.visible = !!value;
  // a manual edit drops us out of a named regime
  markCustom();
  scheduleHash();
}

function applyRegime(id) {
  const p = PRESET_BY_ID[id]; if (!p) return;
  regimeId = id;
  Object.assign(params, defaultParams(), p.params);
  const wasN = flock.n;
  flock.applyParams({ ...defaultParams(), ...p.params });
  if (flock.n !== wasN) buildBirdMesh();
  predator.visible = !!params.predator;
  refreshFields();
  syncRegimeUI();
  announce(`Regime: ${p.name}`);
  writeHash();
}

function markCustom() {
  regimeId = null;
  document.querySelectorAll('.regime').forEach((el) => el.classList.remove('active'));
  $('regimeName').textContent = 'CUSTOM';
  $('regimeBlurb').textContent = 'A hand-tuned flock — pick a regime to return to a named preset.';
}

function syncRegimeUI() {
  document.querySelectorAll('.regime').forEach((el) => el.classList.toggle('active', el.dataset.id === regimeId));
  const p = PRESET_BY_ID[regimeId];
  $('regimeName').textContent = (p ? p.name : 'CUSTOM').toUpperCase();
  $('regimeBlurb').textContent = p ? p.blurb : 'A hand-tuned flock — pick a regime to return to a named preset.';
}

function refreshFields() {
  for (const def of PARAMS) {
    const el = fieldEls[def.key]; if (!el) continue;
    if (def.bool) {
      el.toggle.setAttribute('aria-pressed', String(!!params[def.key]));
      el.toggle.textContent = params[def.key] ? 'on' : 'off';
    } else {
      el.input.value = params[def.key];
      el.val.textContent = fmt(params[def.key], def);
    }
  }
}

// ── actions ──────────────────────────────────────────────────────────────────
function bindActions() {
  $('btnPlay').addEventListener('click', () => {
    running = !running;
    $('btnPlay').textContent = running ? '❚❚ Pause' : '▶ Resume';
    $('btnPlay').setAttribute('aria-pressed', String(running));
    document.body.dataset.running = String(running);
    announce(running ? 'Running' : 'Paused');
  });
  $('btnReset').addEventListener('click', () => { flock.reset(); announce('Flock re-seeded'); });
  $('btnCamera').addEventListener('click', () => {
    const order = ['orbit', 'follow', 'free'];
    setCamMode(order[(order.indexOf(camMode) + 1) % order.length]);
  });
  $('btnShare').addEventListener('click', share);

  const togglePanel = () => {
    const hidden = document.body.dataset.panel === 'hidden';
    document.body.dataset.panel = hidden ? 'shown' : 'hidden';
  };
  $('btnPanel').addEventListener('click', togglePanel);
  $('keyScrim').addEventListener('click', () => { document.body.dataset.panel = 'hidden'; });

  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === ' ') { e.preventDefault(); $('btnPlay').click(); }
    else if (e.key === 'r' || e.key === 'R') $('btnReset').click();
    else if (e.key === 'c' || e.key === 'C') $('btnCamera').click();
    else if (e.key === 'p' || e.key === 'P') setParam('predator', params.predator ? 0 : 1) || refreshFields();
  });
}

async function share() {
  writeHash();
  const url = location.href;
  try { await navigator.clipboard.writeText(url); announce('Link copied'); flashShare('⧉ Copied'); }
  catch { announce('Copy failed — link is in the address bar'); flashShare('⧉ In address bar'); }
}
function flashShare(txt) {
  const b = $('btnShare'), old = b.textContent;
  b.textContent = txt; setTimeout(() => { b.textContent = old; }, 1400);
}

// ── shareable URL hash ───────────────────────────────────────────────────────
let hashTimer = 0;
function scheduleHash() { clearTimeout(hashTimer); hashTimer = setTimeout(writeHash, 250); }
function writeHash() {
  const parts = [];
  if (regimeId) parts.push('r=' + regimeId);
  parts.push('cam=' + camMode);
  // store only params that differ from this regime's baseline (or defaults)
  const base = { ...defaultParams(), ...(PRESET_BY_ID[regimeId]?.params || {}) };
  for (const def of PARAMS) {
    if (params[def.key] !== base[def.key]) parts.push(`${def.key}=${round(params[def.key])}`);
  }
  const h = '#' + parts.join('&');
  if (h !== location.hash) history.replaceState(null, '', h);
}
function round(v) { return Math.round(v * 1000) / 1000; }
function readHash() {
  const out = { params: {} };
  const h = location.hash.replace(/^#/, '');
  if (!h) return out;
  for (const kv of h.split('&')) {
    const [k, v] = kv.split('=');
    if (k === 'r') out.regime = v;
    else if (k === 'cam') out.cam = v;
    else if (v !== undefined && PARAMS.some((p) => p.key === k)) out.params[k] = parseFloat(v);
  }
  return out;
}

// ── a11y ──────────────────────────────────────────────────────────────────────
function announce(msg) { $('srStatus').textContent = msg; }
