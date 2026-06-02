// web4 controller — wires the lab scene, the stage registry, and the UI.
//
// P1 ships the lab shell + the Stage 0 Miller–Urey hero (hand-built photoreal
// glassware). Every other stage shows a placeholder until its GLB is baked via
// the touch-app / Tripo backend (see docs/PRD_LAB_EXPERIMENTS.md).

import * as THREE from 'three';
import { createLab } from './scene.js';
import { buildPlaceholder } from './apparatus/placeholder.js';
import { meta as millerUrey } from './apparatus/miller_urey.js';
import { meta as grayscott } from './apparatus/grayscott_dish.js';
import { meta as raf } from './apparatus/raf_flask.js';
import { meta as vesicles } from './apparatus/vesicle_microscope.js';
import { meta as vent } from './apparatus/vent_reactor.js';
import { meta as minerals } from './apparatus/mineral_flask.js';
import { meta as chirality } from './apparatus/chirality_polarimeter.js';
import { meta as rna } from './apparatus/rna_thermocycler.js';
import { meta as code } from './apparatus/code_bench.js';
import { meta as coacervate } from './apparatus/coacervate_microscope.js';
import { meta as selection } from './apparatus/microfluidic_chip.js';
import { meta as luca } from './apparatus/luca_console.js';
import { meta as stromatolite } from './apparatus/stromatolite.js';

// ── Stage registry (order = Stage 0 → the 12-stage pipeline → capstone) ─────
const STAGES = [
  millerUrey, grayscott, raf, vesicles, vent, minerals, chirality,
  rna, code, coacervate, selection, luca, stromatolite,
];
// buildPlaceholder remains the fallback for any meta missing a build() (e.g.
// a future stage stubbed before its apparatus exists).

const lab = createLab(document.getElementById('viewport'));
let current = null;
let currentMeta = null;

// ── Live SEM experiment driver ──────────────────────────────────────────────
// Beside the photoreal apparatus we run the MATCHING origin-of-life simulation
// (a web3 rule) stepping in real time, rendered through web3's SEM depth-
// shading pipeline (window.SEM, loaded as a classic script) onto a 2-D canvas.
// Apparatus = "the experiment I set up"; this = "what it produces under the
// microscope". The two run on independent RAF loops.
const expCanvas  = document.getElementById('expCanvas');
const expCtx     = expCanvas.getContext('2d');
const expCaption = document.getElementById('expCaption');
const expEmpty   = document.getElementById('expEmpty');
let expRule = null, expImageData = null, expHeightBuf = null;
let expScale = 1, expW2 = 0, expH2 = 0, expHeightHi = null;
let expRunning = false, expRaf = 0, expLastStep = 0;

// Bilinear upscale of a Float32 height field (w×h) → dst (W2×H2). Used so the
// SEM shader runs at a high backing resolution from a smoothly-interpolated
// field — crisp normals instead of a blocky grid-resolution blit.
function _upscaleHeight(src, w, h, dst, W2, H2) {
  const sx = (w - 1) / Math.max(1, W2 - 1);
  const sy = (h - 1) / Math.max(1, H2 - 1);
  for (let y = 0; y < H2; y++) {
    const fy = y * sy;
    const y0 = fy | 0;
    const y1 = y0 + 1 < h ? y0 + 1 : y0;
    const ty = fy - y0;
    for (let x = 0; x < W2; x++) {
      const fx = x * sx;
      const x0 = fx | 0;
      const x1 = x0 + 1 < w ? x0 + 1 : x0;
      const tx = fx - x0;
      const a = src[y0 * w + x0], b = src[y0 * w + x1];
      const c = src[y1 * w + x0], d = src[y1 * w + x1];
      dst[y * W2 + x] = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
    }
  }
}
let apparatusRunning = false;          // single source of truth for Run/Stop
const EXP_STEPS_PER_SEC = 30;          // == web3 default speed
const EXP_PALETTE = 'warm-sepia';      // == web3 default + brass-lab aesthetic

// web4 stage id → web3 rule id (registered key). Note 'natural-selection' uses
// a HYPHEN (the registered key) though its file is natural_selection.js.
const STAGE_MAP = {
  'stage0-miller-urey': 'soup',  'stage1-grayscott': 'grayscott', 'stage2-raf': 'raf',
  'stage3-vesicles': 'vesicles', 'stage4-vent': 'vents',          'stage5-minerals': 'grayscott',
  'stage6-chirality': 'chirality', 'stage7-rna': 'rna',           'stage8-code': 'code',
  'stage9-coacervate': 'coacervate', 'stage10-selection': 'natural-selection',
  'stage11-luca': 'luca',        'capstone-stromatolite': 'life',
};

function currentView() { return document.querySelector('.stage').dataset.view; }

// Swap in the rule for stage m. Called inside loadStage AFTER currentMeta=m.
function selectExperiment(m) {
  stopExperiment();                                    // cancel any prior loop
  expRule = null;                                      // drop old rule (GC reclaims)
  const ruleId = STAGE_MAP[m.id];
  const factory = ruleId && window.CA && CA.RULES && CA.RULES[ruleId];
  if (!factory || !window.SEM) {                       // unmapped / globals missing → tasteful empty state
    expEmpty.hidden = false;
    expCanvas.style.display = 'none';
    expCaption.textContent = 'LIVE SEM · —';
    return;
  }
  expEmpty.hidden = true;
  expCanvas.style.display = '';
  expRule = factory();                                 // instantiate web3 rule
  expRule.reset();
  // Hi-res backing: SEM rules render the height field supersampled (~760px on
  // the long edge) so every experiment reads crisp instead of a blocky upscaled
  // grid. Non-SEM fallback rules stay at native grid (their render() writes a
  // grid-sized RGBA buffer).
  const hasSem = window.SEM && typeof expRule.renderHeight === 'function';
  expScale = hasSem ? Math.max(1, Math.round(760 / Math.max(expRule.width, expRule.height))) : 1;
  expW2 = expRule.width * expScale;
  expH2 = expRule.height * expScale;
  expCanvas.width  = expW2;
  expCanvas.height = expH2;
  expImageData = expCtx.createImageData(expW2, expH2);
  expHeightBuf = new Float32Array(expRule.width * expRule.height);
  expHeightHi  = new Float32Array(expW2 * expH2);
  expCaption.textContent = 'LIVE SEM · ' + (m.label || ruleId);
  renderExperimentFrame();                             // paint one frame immediately (even if paused)
}

// EXACT web3 render() SEM branch (main.js:551-558), verbatim convention.
function renderExperimentFrame() {
  if (!expRule) return;
  if (window.SEM && typeof expRule.renderHeight === 'function') {
    expRule.renderHeight(expHeightBuf);
    if (expScale > 1) {
      // supersample: shade the SEM at the hi-res backing from an interpolated
      // height field → smooth normals, crisp result.
      _upscaleHeight(expHeightBuf, expRule.width, expRule.height, expHeightHi, expW2, expH2);
      SEM.render(expHeightHi, expW2, expH2, expImageData.data, { palette: EXP_PALETTE });
    } else {
      SEM.render(expHeightBuf, expRule.width, expRule.height,
                 expImageData.data, { palette: EXP_PALETTE });
    }
  } else {
    expRule.render(expImageData.data);                 // defensive fallback to rule's own RGBA
  }
  expCtx.putImageData(expImageData, 0, 0);
}

// Fixed-timestep loop, copied structurally from web3 tick() (safety cap so a
// stutter can't spiral). Steps cheaply even when hidden; only SEM+blits when
// the exp pane is visible.
function expTick(now) {
  if (!expRunning || !expRule) { expRaf = 0; return; }
  const interval = 1000 / EXP_STEPS_PER_SEC;
  if (!expLastStep) expLastStep = now;
  let advanced = false, safety = 4;
  while (now - expLastStep >= interval && safety-- > 0) {
    expRule.step(); expLastStep += interval; advanced = true;
  }
  if (advanced && currentView() !== 'lab') renderExperimentFrame();
  expRaf = requestAnimationFrame(expTick);
}
function startExperiment() {
  if (expRunning || !expRule) return;
  expRunning = true; expLastStep = 0; expRaf = requestAnimationFrame(expTick);
}
function stopExperiment() {
  expRunning = false; if (expRaf) cancelAnimationFrame(expRaf); expRaf = 0;
}

function loadStage(m) {
  if (current) { lab.scene.remove(current); disposeTree(current); }
  current = m.build ? m.build() : buildPlaceholder(m);
  currentMeta = m;
  lab.scene.add(current);
  frameTo(current);
  buildPartsPanel(current);
  // header / blurb
  document.getElementById('apTitle').textContent = m.title;
  document.getElementById('apLabel').textContent = m.label;
  document.getElementById('apBlurb').textContent = m.blurb;
  const isSpecimen = m.id?.startsWith('capstone');
  selectExperiment(m);   // swap the live SEM experiment to match this stage (sets expRule)
  // Run/Stop drives BOTH the apparatus anim AND the live SEM sim, so show it
  // whenever there's EITHER to drive: a non-placeholder apparatus, OR a live
  // experiment (incl. the capstone specimen, whose 'life' SEM feed is runnable).
  const hasExperiment = !!expRule;
  document.getElementById('runBtn').style.display =
    (m.placeholder && !hasExperiment) || (isSpecimen && !hasExperiment) ? 'none' : '';
  document.getElementById('explodeRow').style.display = (m.placeholder || isSpecimen) ? 'none' : '';
  setRunning(true);      // auto-run BOTH apparatus + experiment on stage select
  // active nav button
  document.querySelectorAll('.stage-btn').forEach(b => b.classList.toggle('active', b.dataset.id === m.id));
}

// ── Camera framing ──────────────────────────────────────────────────────────
function frameTo(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(lab.camera.fov) / 2)) * 1.35;
  lab.controls.target.copy(center);
  lab.camera.position.set(center.x + dist * 0.7, center.y + dist * 0.35, center.z + dist);
  lab.controls.update();
}

// ── Parts panel (named GLB parts, à la an exploded lab diagram) ─────────────
function buildPartsPanel(obj) {
  const list = document.getElementById('partsList');
  list.innerHTML = '';
  const named = [];
  obj.traverse(o => { if (o.isMesh && o.name && !o.name.startsWith('placeholder')) named.push(o); });
  if (!named.length) { list.innerHTML = '<div class="muted">No named parts</div>'; return; }
  document.getElementById('partCount').textContent = `${named.length} parts`;
  for (const m of named) {
    const row = document.createElement('button');
    row.className = 'part-row';
    row.textContent = m.name;
    row.onmouseenter = () => highlight(m, true);
    row.onmouseleave = () => highlight(m, false);
    row.onclick = () => { m.visible = !m.visible; row.classList.toggle('hidden', !m.visible); };
    list.appendChild(row);
  }
}
let emissiveCache = null;
function highlight(mesh, on) {
  if (!mesh.material || !mesh.material.emissive) return;
  if (on) { emissiveCache = mesh.material.emissive.getHex(); mesh.material.emissive.setHex(0x2a6cff); }
  else if (emissiveCache !== null) { mesh.material.emissive.setHex(emissiveCache); emissiveCache = null; }
}

// ── Run + explode controls ──────────────────────────────────────────────────
// One button drives BOTH the photoreal apparatus animation AND the live SEM
// experiment sim. apparatusRunning is the single source of truth so the two
// can never desync. The exp loop only spins when its pane is visible.
function setRunning(on) {
  apparatusRunning = on;
  current?.userData?.anim?.setRunning(on);
  if (on && currentView() !== 'lab') startExperiment(); else stopExperiment();
  const btn = document.getElementById('runBtn');
  btn.textContent = on ? '■ Stop experiment' : '▶ Run experiment';
  btn.classList.toggle('running', on);
}
document.getElementById('runBtn').onclick = () => {
  const running = !document.getElementById('runBtn').classList.contains('running');
  setRunning(running);
};
const explodePartsCache = new WeakMap();
document.getElementById('explode').oninput = (e) => {
  const f = parseFloat(e.target.value);
  const center = new THREE.Box3().setFromObject(current).getCenter(new THREE.Vector3());
  current.traverse(o => {
    if (!o.isMesh) return;
    if (!explodePartsCache.has(o)) explodePartsCache.set(o, o.position.clone());
    const home = explodePartsCache.get(o);
    const dir = o.getWorldPosition(new THREE.Vector3()).sub(center).normalize();
    o.position.copy(home).add(dir.multiplyScalar(f * 1.5));
  });
};

// ── View toggle (Lab | Split | Experiment) ──────────────────────────────────
// The data-view attribute on .stage is the single source of truth; CSS does
// ALL pane show/hide. JS only sets it + handles two perf concerns: refit the
// WebGL renderer (its container width changed without a window resize) and
// pause the exp loop whenever its pane is hidden.
function setView(v) {
  const stage = document.querySelector('.stage');
  stage.dataset.view = v;
  document.querySelectorAll('#viewToggle .vt-btn').forEach(b => {
    const sel = b.dataset.view === v;
    b.classList.toggle('active', sel);
    b.setAttribute('aria-pressed', String(sel));   // expose selected state to AT
  });
  // #viewport width changed without a window 'resize' → refit WebGL after reflow.
  requestAnimationFrame(() => lab.setSize());
  if (v === 'lab') {
    stopExperiment();                          // exp pane hidden → stop the 2-D loop
  } else {
    if (apparatusRunning) startExperiment();   // resume if Run is active
    renderExperimentFrame();                   // paint one immediate frame so it's never blank
  }
}
document.querySelectorAll('#viewToggle .vt-btn')
  .forEach(b => b.onclick = () => setView(b.dataset.view));

// ── Build the stage nav ─────────────────────────────────────────────────────
const nav = document.getElementById('stageNav');
for (const m of STAGES) {
  const b = document.createElement('button');
  b.className = 'stage-btn' + (m.placeholder ? ' pending' : '');
  b.dataset.id = m.id;
  b.innerHTML = `<span>${m.label}</span><small>${m.title}</small>`;
  b.onclick = () => loadStage(m);
  nav.appendChild(b);
}

// Per-stage readout label (defaults to "experiment progress").
const READOUT_LABEL = {
  'stage0-miller-urey': 'organics collected',
  'stage4-vent': 'reaction extent',
  'stage7-rna': 'replication cycles',
  'stage10-selection': 'mean fitness',
  'stage11-luca': 'core distilled',
};

// ── Render loop ─────────────────────────────────────────────────────────────
const clock = new THREE.Clock();
function tick() {
  const dt = Math.min(clock.getDelta(), 0.05);
  current?.userData?.anim?.update(dt, clock.elapsedTime);
  lab.controls.update();   // keep damping alive even when the lab pane is hidden
  // Skip the heavy composer pass (UnrealBloom) when the apparatus is hidden.
  if (currentView() !== 'exp') lab.composer.render();
  // live readout
  const p = current?.userData?.anim?.getProgress?.() ?? 0;
  const ro = document.getElementById('readout');
  const isSpecimen = currentMeta?.id?.startsWith('capstone');
  if (ro && !currentMeta?.placeholder && !isSpecimen) {
    const label = READOUT_LABEL[currentMeta?.id] || 'experiment progress';
    ro.textContent = `${label}: ${(p * 100).toFixed(0)}%`;
  } else if (ro) { ro.textContent = ''; }
  requestAnimationFrame(tick);
}

function disposeTree(obj) {
  obj.traverse(o => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(mt => mt.dispose());
  });
}

loadStage(STAGES[0]);
tick();
