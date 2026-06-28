// cellauto · web7 controller — "Catalytic Silence" shell over web6's engine.
//
// The engine (photoreal Three.js apparatus + the live web3 SEM physics) is
// reused byte-identical from web6. This module wires that engine to the new
// museum-vitrine DOM and adds the presentation layer: Roman-numeral plates, a
// playback "breath", keyboard navigation of the stage index, screen-reader
// announcements, and reduced-motion awareness. All engine semantics (the
// STAGE_MAP, the fixed-timestep SEM loop, the single Run source-of-truth that
// keeps apparatus + micrograph in lockstep) are preserved exactly.

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

const $ = (id) => document.getElementById(id);
const vitrine = document.querySelector('.vitrine');
const srStatus = $('srStatus');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// ── Resilience: probe WebGL and guard the engine bootstrap ──────────────────
function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}
function failLab(msg) {   // on-brand offline notice in the viewport + accessible announcement
  const vp = $('viewport');
  if (vp) vp.innerHTML =
    '<div class="plate-empty" style="position:absolute;inset:0">' +
    '<span class="empty-mark">✦</span><span class="empty-line">instrument offline</span>' +
    '<span class="empty-sub">' + msg + '</span></div>';
  if (srStatus) srStatus.textContent = 'The lab could not be loaded. ' + msg;
  window.__labReady = true;   // we handled it — suppress the inline failsafe in index.html
}

let lab = null;
try {
  if (!hasWebGL()) throw new Error('WebGL unavailable');
  lab = createLab($('viewport'));
} catch (e) {
  console.error('[cellauto] lab init failed:', e);   // bootstrap guard at the foot of the file shows the notice
}
let current = null;
let currentMeta = null;

// ── Live SEM experiment driver (verbatim engine semantics from web6) ────────
const expCanvas  = $('expCanvas');
const expCtx     = expCanvas.getContext('2d');
const expCaption = $('expCaption');
const expEmpty   = $('expEmpty');
let expRule = null, expImageData = null, expHeightBuf = null;
let expRunning = false, expRaf = 0, expLastStep = 0;
let expRetry = 0;                       // poll counter while the classic exp scripts wire up
let apparatusRunning = false;           // single source of truth for Run/Stop
const EXP_STEPS_PER_SEC = 30;           // == web3 default speed
const EXP_PALETTE = 'warm-sepia';       // == web3 default + the warm SEM substrate
let expPalette = EXP_PALETTE;           // live, tunable via the Parameters panel
let expSpeedOverride = 0;               // 0 → use the rule's own cadence

// web4/web6 stage id → web3 rule id (registered key). 'natural-selection' is
// hyphenated (the registered key) though its file is natural_selection.js.
const STAGE_MAP = {
  'stage0-miller-urey': 'soup',  'stage1-grayscott': 'grayscott', 'stage2-raf': 'raf',
  'stage3-vesicles': 'vesicles', 'stage4-vent': 'vents',          'stage5-minerals': 'minerals',
  'stage6-chirality': 'chirality', 'stage7-rna': 'rna',           'stage8-code': 'code',
  'stage9-coacervate': 'coacervate', 'stage10-selection': 'natural-selection',
  'stage11-luca': 'luca',        'capstone-stromatolite': 'life',
};

function currentView() { return vitrine.dataset.view; }
function announce(msg) { if (srStatus) srStatus.textContent = msg; }

// ── Museum plate numerals ───────────────────────────────────────────────────
const ROMAN = [
  [1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],
  [50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I'],
];
function toRoman(n) { let s = ''; for (const [v, sym] of ROMAN) while (n >= v) { s += sym; n -= v; } return s; }

// Parse "Stage 0 — Miller–Urey" → { numeral:"0", name:"Miller–Urey" }; capstone
// (no "Stage N" prefix) → { numeral:"✦", name:<label> }.
function plateOf(meta) {
  const m = /^Stage\s+(\d+)\s*[—–-]\s*(.+)$/.exec(meta.label || '');
  if (m) { const n = +m[1]; return { numeral: n === 0 ? '0' : toRoman(n), name: m[2] }; }
  return { numeral: '✦', name: (meta.label || '').replace(/^Capstone\s*[—–-]\s*/i, '') || meta.label };
}

// The plate's resting state. `failed` distinguishes a true load failure (the
// live feed never initialised) from a stage that simply has no mapped rule.
function showExpEmpty(failed) {
  buildParamPanel(null);                 // nothing to tune when there's no live rule
  expEmpty.hidden = false;
  expCanvas.style.display = 'none';
  expCaption.textContent = '';
  const line = expEmpty.querySelector('.empty-line');
  const sub = expEmpty.querySelector('.empty-sub');
  if (failed) {
    if (line) line.textContent = 'micrograph unavailable';
    if (sub) sub.textContent = 'the live feed did not initialise';
    announce('The live micrograph could not be initialised.');
  } else {
    if (line) line.textContent = 'specimen pending';
    if (sub) sub.textContent = 'no instrument is yet mapped to this plate';
  }
}

// Swap in the rule for stage m. Called inside loadStage AFTER currentMeta=m.
function selectExperiment(m) {
  stopExperiment();
  expRule = null;
  if (!expCtx) { showExpEmpty(true); return; }   // 2-D context unavailable → honest failure state
  const ruleId = STAGE_MAP[m.id];
  if (!ruleId) { expRetry = 0; showExpEmpty(); return; }

  // The live experiment is driven by CLASSIC scripts (sem.js + the rule files)
  // that wire window.SEM and window.CA.RULES. They precede this deferred module
  // in the HTML, so they're normally ready — but a slow/transient load can leave
  // a global momentarily absent. Poll briefly for readiness, then decide
  // (rather than latching the empty state forever).
  const factory = window.CA && CA.RULES && CA.RULES[ruleId];
  const needsSEM = ruleId !== 'life';                  // only the photoreal LIFE feed skips the SEM pipeline
  if (!factory || (needsSEM && !window.SEM)) {
    if (expRetry++ < 60) {                             // ~3s of 50ms polls before giving up
      expEmpty.hidden = true;
      expCanvas.style.display = 'none';
      expCaption.textContent = 'calibrating the instrument';
      setTimeout(() => { if (currentMeta === m) selectExperiment(m); }, 50);
      return;
    }
    showExpEmpty(true);   // globals never arrived → honest failure state
    return;
  }
  expRetry = 0;
  const rule = factory();
  expEmpty.hidden = true;
  expCanvas.style.display = '';
  expRule = rule;
  expRule.reset();
  expCanvas.classList.toggle('smooth', !!expRule.hiRes);  // LIFE scales smooth; grids stay crisp/pixelated
  if (expRule.hiRes) {
    expCanvas.width = 720; expCanvas.height = 720;
  } else {
    expCanvas.width  = expRule.width;
    expCanvas.height = expRule.height;
  }
  expImageData = expCtx.createImageData(expRule.width, expRule.height);
  expHeightBuf = new Float32Array(expRule.width * expRule.height);
  expCaption.textContent = plateOf(m).name;
  buildParamPanel(expRule);                            // surface this stage's own tunable knobs
  renderExperimentFrame();                             // paint one frame immediately (even if paused)
}

// EXACT web3 render() SEM-branch convention.
function renderExperimentFrame() {
  if (!expRule) return;
  if (expRule.hiRes && typeof expRule.renderPhotoreal === 'function') {
    expRule.renderPhotoreal(expCtx, expCanvas.width, expCanvas.height,
      function (w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; });
    return;
  }
  if (window.SEM && typeof expRule.renderHeight === 'function') {
    expRule.renderHeight(expHeightBuf);
    SEM.render(expHeightBuf, expRule.width, expRule.height, expImageData.data, { palette: expPalette });
  } else {
    expRule.render(expImageData.data);                 // defensive fallback to rule's own RGBA
  }
  expCtx.putImageData(expImageData, 0, 0);
}

// Fixed-timestep loop (structural copy of web3 tick(), with a safety cap).
function expTick(now) {
  if (!expRunning || !expRule) { expRaf = 0; return; }
  const sps = expSpeedOverride > 0 ? expSpeedOverride : (expRule.stepsPerSec || EXP_STEPS_PER_SEC);
  const interval = 1000 / sps;
  if (!expLastStep) expLastStep = now;
  let advanced = false, safety = 4;
  while (now - expLastStep >= interval && safety-- > 0) {
    expRule.step(); expLastStep += interval; advanced = true;
  }
  if (currentView() !== 'lab') {
    if (expRule.hiRes || advanced) renderExperimentFrame();
  }
  expRaf = requestAnimationFrame(expTick);
}
function startExperiment() {
  if (expRunning || !expRule) return;
  expRunning = true; expLastStep = 0; expRaf = requestAnimationFrame(expTick);
}
function stopExperiment() {
  expRunning = false; if (expRaf) cancelAnimationFrame(expRaf); expRaf = 0;
}

// ── Stage load ──────────────────────────────────────────────────────────────
function loadStage(m) {
  if (!lab) return;   // engine failed to boot — failLab() already showed the notice
  if (current) { lab.scene.remove(current); disposeTree(current); }
  current = m.build ? m.build() : buildPlaceholder(m);
  currentMeta = m;
  lab.scene.add(current);
  frameTo(current);
  buildPartsPanel(current);

  const plate = plateOf(m);
  $('apLabel').textContent = m.label;
  $('apTitle').textContent = m.title;
  $('apBlurb').textContent = m.blurb || '';
  $('plateNo').textContent = 'PL. ' + plate.numeral;
  retriggerCaption();

  const isSpecimen = m.id?.startsWith('capstone');
  selectExperiment(m);
  // keep the canvases' accessible names current with the specimen
  viewportEl.setAttribute('aria-label',
    `Interactive 3D apparatus — ${plate.name}. Arrow keys orbit; plus and minus zoom; drag to rotate.`);
  expCanvas.setAttribute('aria-label', `Live SEM micrograph — ${plate.name}`);
  const hasExperiment = !!expRule;
  $('runBtn').style.display = (m.placeholder && !hasExperiment) || (isSpecimen && !hasExperiment) ? 'none' : '';
  $('explodeRow').style.display = (m.placeholder || isSpecimen) ? 'none' : '';
  // reset any prior exploded view so a new specimen reads whole
  const ex = $('explode'); if (ex) { ex.value = '0'; applyExplode(0); }
  // Auto-run on select, EXCEPT under prefers-reduced-motion: WCAG 2.2.2 says
  // auto-updating motion must not start without user consent. Reduced-motion
  // users get a still specimen and press Run themselves.
  setRunning(!reduceMotion.matches);

  document.querySelectorAll('.stage-btn').forEach(b => {
    const sel = b.dataset.id === m.id;
    b.classList.toggle('active', sel);
    if (sel) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
  });
  // Mark X timeline scrubber — keep the node row + provenance in lockstep.
  document.querySelectorAll('.tl-node').forEach(n => {
    const sel = n.dataset.id === m.id;
    n.classList.toggle('is-current', sel);
    if (sel) n.setAttribute('aria-current', 'true'); else n.removeAttribute('aria-current');
  });
  const prov = $('tlProv');
  if (prov) { const idx = STAGES.findIndex(s => s.id === m.id); prov.textContent = `PL.${plate.numeral} · ${idx + 1}/${STAGES.length} · BUILD MK X`; }
  const ss = $('stageSelect'); if (ss) ss.value = m.id;   // keep the mobile switcher in sync
  announce(`${m.label}. ${m.title}.`);
}

// Replay the caption-rise animation on each stage change (skipped under reduce-motion).
function retriggerCaption() {
  if (reduceMotion.matches) return;
  const cap = document.querySelector('.caption');
  if (!cap) return;
  cap.style.animation = 'none'; void cap.offsetWidth; cap.style.animation = '';
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

// ── Specimen key (named apparatus parts) ────────────────────────────────────
function buildPartsPanel(obj) {
  const list = $('partsList');
  list.innerHTML = '';
  const named = [];
  obj.traverse(o => { if (o.isMesh && o.name && !o.name.startsWith('placeholder')) named.push(o); });
  if (!named.length) {
    list.innerHTML = '<div class="key-empty">No named parts on this specimen.</div>';
    $('partCount').textContent = '—';
    return;
  }
  $('partCount').textContent = `${named.length}`;
  for (const mesh of named) {
    const row = document.createElement('button');
    row.className = 'part-row';
    row.type = 'button';
    row.setAttribute('aria-pressed', 'true');   // pressed === part shown (visible)
    const lbl = document.createElement('span');
    lbl.textContent = mesh.name;
    row.appendChild(lbl);
    row.onmouseenter = () => highlight(mesh, true);
    row.onmouseleave = () => highlight(mesh, false);
    row.onfocus = () => highlight(mesh, true);
    row.onblur = () => highlight(mesh, false);
    row.onclick = () => {
      mesh.visible = !mesh.visible;
      row.classList.toggle('hidden', !mesh.visible);
      row.setAttribute('aria-pressed', String(mesh.visible));
    };
    list.appendChild(row);
  }
}
// Per-mesh emissive cache (stored on the mesh) so overlapping hover/focus on
// different parts can't clobber a single shared register and strand a highlight.
function highlight(mesh, on) {
  if (!mesh.material || !mesh.material.emissive) return;
  if (on) {
    if (mesh.userData.__emis === undefined) mesh.userData.__emis = mesh.material.emissive.getHex();
    mesh.material.emissive.setHex(0x1f8f86);   // a quiet teal illumination
  } else if (mesh.userData.__emis !== undefined) {
    mesh.material.emissive.setHex(mesh.userData.__emis);
    mesh.userData.__emis = undefined;
  }
}

// ── Live-experiment parameter panel ─────────────────────────────────────────
// Reads the running rule's OWN params schema ({label,min,max,step,value} or
// {type:'enum',options}) — the same knobs web2/web3 exposed — its curated named
// regimes (rule.presets), plus two global controls (speed, SEM palette). Every
// control is genuinely wired:
// PDE rules read params.X.value live each step(), so a slider takes effect
// mid-run; rule.onParamChange(key) handles side-effects (e.g. a Gray–Scott
// preset setting F and k). No fabricated/disconnected sliders.
const paramList = $('paramList');
let paramRefs = {};   // key → {input,val,fmt} so a preset change can re-sync F/k sliders
let regimeRef = null; // the "Regime" preset <select>, so a manual slider edit drops back to "custom"

function paramHead(label, valText) {
  const row = document.createElement('div'); row.className = 'param-row';
  const head = document.createElement('div'); head.className = 'p-head';
  const l = document.createElement('span'); l.className = 'p-label'; l.textContent = label;
  const val = document.createElement('span'); val.className = 'p-val'; val.textContent = valText || '';
  head.append(l, val); row.appendChild(head);
  return { row, val };
}
function addSlider(label, min, max, step, value, fmt, onInput, tip) {
  const { row, val } = paramHead(label, fmt(value));
  const r = document.createElement('input');
  r.type = 'range'; r.min = min; r.max = max; r.step = step; r.value = value;
  r.setAttribute('aria-label', label); if (tip) r.title = tip;
  r.oninput = () => { const v = parseFloat(r.value); val.textContent = fmt(v); onInput(v); };
  row.appendChild(r); paramList.appendChild(row);
  return { input: r, val, fmt };
}
function addSelect(label, options, value, onChange, tip) {
  const { row } = paramHead(label, '');
  const s = document.createElement('select');
  s.setAttribute('aria-label', label); if (tip) s.title = tip;
  for (const o of options) {
    const opt = document.createElement('option'); opt.value = o; opt.textContent = o || '—';
    if (o === value) opt.selected = true; s.appendChild(opt);
  }
  s.onchange = () => onChange(s.value);
  row.appendChild(s); paramList.appendChild(row);
}
// A rule's curated named regimes (rule.presets: [{label, hint, values:{key:val}, reseed?}]).
// web2/web3 authored these per stage but the panel never surfaced them — every rule but
// Gray–Scott (which re-encodes its own as an enum param) shipped them as dead data. Wire
// them as a first-class "Regime" picker: applying one writes the underlying params (firing
// onParamChange cascades), optionally re-seeds, re-syncs the sliders, and shows its hint.
function applyPreset(rule, p) {
  const vals = (p && p.values) || {};
  for (const k of Object.keys(vals)) {
    if (rule.params && rule.params[k]) {
      rule.params[k].value = vals[k];
      if (rule.onParamChange) rule.onParamChange(k);
    }
  }
  if (p && p.reseed && typeof rule.reset === 'function') rule.reset();
  syncParams(rule);
  renderExperimentFrame();
}
function addPresetPicker(rule) {
  const presets = Array.isArray(rule.presets) ? rule.presets : null;
  if (!presets || !presets.length) return;
  const { row } = paramHead('Regime', '');
  const s = document.createElement('select');
  s.setAttribute('aria-label', 'Experiment regime preset');
  const blank = document.createElement('option'); blank.value = ''; blank.textContent = 'custom'; s.appendChild(blank);
  presets.forEach((p, i) => {
    const o = document.createElement('option'); o.value = String(i); o.textContent = p.label || `regime ${i + 1}`; s.appendChild(o);
  });
  const hint = document.createElement('p'); hint.className = 'param-hint';
  s.onchange = () => {
    const p = presets[+s.value];
    if (!p) { hint.textContent = ''; return; }
    applyPreset(rule, p);
    hint.textContent = p.hint || '';
    announce((p.label || 'Regime') + ' regime applied.');
  };
  row.appendChild(s); paramList.appendChild(row); paramList.appendChild(hint);
  regimeRef = s;
}
function buildParamPanel(rule) {
  if (!paramList) return;
  paramList.innerHTML = ''; paramRefs = {}; regimeRef = null;
  if (!rule) { paramList.innerHTML = '<div class="param-empty">No live experiment to tune on this plate.</div>'; return; }
  // Named scientific regimes (rule.presets) — the most prominent, stage-specific control.
  addPresetPicker(rule);
  // Global — simulation speed (drives the fixed-timestep loop)
  expSpeedOverride = rule.stepsPerSec || EXP_STEPS_PER_SEC;
  addSlider('Speed', 1, 60, 1, expSpeedOverride, (v) => `${v | 0} s⁻¹`, (v) => { expSpeedOverride = v; });
  // Global — SEM tone-map palette (irrelevant to the photoreal LIFE feed)
  if (!rule.hiRes && window.SEM && typeof SEM.paletteNames === 'function') {
    addSelect('Palette', SEM.paletteNames(), expPalette, (v) => { expPalette = v; renderExperimentFrame(); });
  }
  // Per-stage scientific knobs, straight from the rule's own params schema
  const P = rule.params || {};
  for (const key of Object.keys(P)) {
    const p = P[key];
    const tip = (rule.controlConsequence && rule.controlConsequence[key]) || '';
    if (p.type === 'enum') {
      addSelect(p.label || key, p.options, p.value, (v) => {
        p.value = v; if (rule.onParamChange) rule.onParamChange(key); syncParams(rule); renderExperimentFrame();
        if (regimeRef) regimeRef.value = '';
      }, tip);
    } else {
      const dec = (p.step && p.step < 1) ? (String(p.step).split('.')[1] || '').length : 0;
      const fmt = (v) => Number(v).toFixed(dec);
      paramRefs[key] = addSlider(p.label || key, p.min, p.max, p.step, p.value, fmt, (v) => {
        p.value = v; if (rule.onParamChange) rule.onParamChange(key); syncParams(rule); renderExperimentFrame();
        if (regimeRef) regimeRef.value = '';   // a hand-tuned knob drops us out of the named regime
      }, tip);
    }
  }
}
// Re-sync slider positions when one change cascades to others (preset → F, k).
function syncParams(rule) {
  const P = rule.params || {};
  for (const key of Object.keys(paramRefs)) {
    const ref = paramRefs[key];
    if (P[key] && ref) { ref.input.value = P[key].value; ref.val.textContent = ref.fmt(P[key].value); }
  }
}

// Right-rail tabs (Parameters | Apparatus) + experiment transport.
function setRailTab(showParams) {
  $('tabParams').setAttribute('aria-selected', String(showParams)); $('tabParams').tabIndex = showParams ? 0 : -1;
  $('tabParts').setAttribute('aria-selected', String(!showParams)); $('tabParts').tabIndex = showParams ? -1 : 0;
  $('paramPanel').hidden = !showParams; $('partsPanel').hidden = showParams;
}
$('tabParams').onclick = () => setRailTab(true);
$('tabParts').onclick = () => setRailTab(false);
$('resetBtn').onclick = () => { if (expRule) { expRule.reset(); renderExperimentFrame(); announce('Specimen reset.'); } };
$('stepBtn').onclick = () => { if (expRule) { expRule.step(); renderExperimentFrame(); } };

// ── Narrow-screen controls drawer ────────────────────────────────────────────
// ≤1180px the rail is off-canvas (styles.css); without a launcher the Parameters
// and Apparatus panels would be unreachable — the pre-existing `.key{display:none}`
// hid every control on phones/tablets/small laptops. Keep them one tap away.
const railEl = $('rail'), keyToggle = $('keyToggle'), keyScrim = $('keyScrim'), keyClose = $('keyClose');
function setKeyOpen(open) {
  if (!railEl) return;
  railEl.classList.toggle('open', open);
  if (keyScrim) keyScrim.classList.toggle('open', open);
  if (keyToggle) keyToggle.setAttribute('aria-expanded', String(open));
  if (open) { const t = $('tabParams'); if (t) t.focus(); }   // move focus into the drawer
  else if (keyToggle) keyToggle.focus();                      // return focus to the launcher
}
if (keyToggle) keyToggle.onclick = () => setKeyOpen(!railEl.classList.contains('open'));
if (keyClose) keyClose.onclick = () => setKeyOpen(false);
if (keyScrim) keyScrim.onclick = () => setKeyOpen(false);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && railEl && railEl.classList.contains('open')) setKeyOpen(false);
});

// ── Run + explode controls ──────────────────────────────────────────────────
// One control drives BOTH the apparatus animation AND the live SEM sim;
// apparatusRunning is the single source of truth so the two never desync.
function setRunning(on) {
  apparatusRunning = on;
  current?.userData?.anim?.setRunning(on);
  if (on && currentView() !== 'lab') startExperiment(); else stopExperiment();
  const btn = $('runBtn');
  btn.setAttribute('aria-pressed', String(on));
  btn.querySelector('.run-lbl').textContent = on ? 'Stop experiment' : 'Run experiment';
  vitrine.classList.toggle('is-running', on);
  const dot = $('statusDot'); if (dot) dot.title = on ? 'instrument running' : 'instrument idle';
}
$('runBtn').onclick = () => setRunning($('runBtn').getAttribute('aria-pressed') !== 'true');

const explodePartsCache = new WeakMap();
function applyExplode(f) {
  if (!current) return;
  const center = new THREE.Box3().setFromObject(current).getCenter(new THREE.Vector3());
  current.traverse(o => {
    if (!o.isMesh) return;
    if (!explodePartsCache.has(o)) explodePartsCache.set(o, o.position.clone());
    const home = explodePartsCache.get(o);
    const dir = o.getWorldPosition(new THREE.Vector3()).sub(center).normalize();
    o.position.copy(home).add(dir.multiplyScalar(f * 1.5));
  });
}
$('explode').oninput = (e) => applyExplode(parseFloat(e.target.value));

// ── View toggle (Lab | Split | Micrograph) ──────────────────────────────────
const MODE_LABEL = { lab: 'LAB', split: 'SPLIT', exp: 'LIVE · SEM' };
const VIEW_NAME  = { lab: 'Lab', split: 'Split', exp: 'Micrograph' };
function setView(v) {
  vitrine.dataset.view = v;
  // radiogroup: aria-checked + roving tabindex so the group is one Tab stop.
  document.querySelectorAll('#viewToggle button').forEach(b => {
    const sel = b.dataset.view === v;
    b.setAttribute('aria-checked', String(sel));
    b.tabIndex = sel ? 0 : -1;
  });
  $('modeLabel').textContent = MODE_LABEL[v] || v.toUpperCase();
  requestAnimationFrame(() => { if (lab) lab.setSize(); });   // #viewport size changed without a window resize
  if (v === 'lab') {
    stopExperiment();
  } else {
    if (apparatusRunning) startExperiment();
    renderExperimentFrame();                    // paint one immediate frame so it's never blank
  }
}
const viewToggle = $('viewToggle');
viewToggle.querySelectorAll('button').forEach(b => {
  b.onclick = () => { setView(b.dataset.view); announce(VIEW_NAME[b.dataset.view] + ' view.'); };
});
// Arrow keys move selection within the radiogroup (ARIA APG pattern).
viewToggle.addEventListener('keydown', (e) => {
  const order = ['lab', 'split', 'exp'];
  const i = order.indexOf(currentView());
  let j = -1;
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') j = (i + 1) % order.length;
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') j = (i - 1 + order.length) % order.length;
  else if (e.key === 'Home') j = 0;
  else if (e.key === 'End') j = order.length - 1;
  if (j >= 0) {
    e.preventDefault();
    setView(order[j]);
    viewToggle.querySelector(`button[data-view="${order[j]}"]`).focus();
    announce(VIEW_NAME[order[j]] + ' view.');
  }
});

// ── Keyboard orbit/zoom for the 3D apparatus (WCAG 2.1.1) ────────────────────
// OrbitControls handles the pointer; this gives focus-on-viewport keyboard
// users the same rotate/zoom by walking the camera around the orbit target in
// spherical space. No-ops gracefully under reduced-motion-sensitive use (it is
// user-driven, discrete, not auto-animated).
const viewportEl = $('viewport');
function orbit(dTheta, dPhi, dDolly) {
  if (!lab) return;
  const off = lab.camera.position.clone().sub(lab.controls.target);
  const sph = new THREE.Spherical().setFromVector3(off);
  sph.theta += dTheta;
  sph.phi = THREE.MathUtils.clamp(sph.phi + dPhi, 0.05, lab.controls.maxPolarAngle ?? Math.PI);
  sph.radius = THREE.MathUtils.clamp(sph.radius * dDolly, lab.controls.minDistance, lab.controls.maxDistance);
  off.setFromSpherical(sph);
  lab.camera.position.copy(lab.controls.target).add(off);
  lab.controls.update();
}
viewportEl.addEventListener('keydown', (e) => {
  const STEP = 0.18;
  let handled = true;
  switch (e.key) {
    case 'ArrowLeft':  orbit(-STEP, 0, 1); break;
    case 'ArrowRight': orbit(STEP, 0, 1); break;
    case 'ArrowUp':    orbit(0, -STEP, 1); break;
    case 'ArrowDown':  orbit(0, STEP, 1); break;
    case '+': case '=': orbit(0, 0, 0.9); break;
    case '-': case '_': orbit(0, 0, 1.1); break;
    default: handled = false;
  }
  if (handled) e.preventDefault();
});

// Dismiss the drag hint on first interaction (pointer or keyboard).
const viewportHint = $('viewportHint');
const dismissHint = () => viewportHint && viewportHint.classList.add('gone');
viewportEl.addEventListener('pointerdown', dismissHint, { once: true });
viewportEl.addEventListener('keydown', dismissHint, { once: true });
// Honour a mid-session switch to reduced motion: stop the running instrument.
if (reduceMotion.addEventListener) reduceMotion.addEventListener('change', (e) => { if (e.matches) setRunning(false); });

// ── Build the stage index ────────────────────────────────────────────────────
const nav = $('stageNav');
// Mark X — each stage card carries its hero micrograph as a backdrop. Files live
// in ../generated/web10/; a missing PNG just leaves --hero unset → solid card.
const HERO_FILES = [
  'stage00_miller_urey.png', 'stage01_reaction_diffusion.png', 'stage02_raf.png',
  'stage03_vesicles.png', 'stage04_vent.png', 'stage05_minerals.png',
  'stage06_chirality.png', 'stage07_rna.png', 'stage08_code.png',
  'stage09_coacervate.png', 'stage10_selection.png', 'stage11_luca.png',
  'stage12_stromatolite.png',
];
STAGES.forEach((m, i) => {
  const plate = plateOf(m);
  const b = document.createElement('button');
  b.className = 'stage-btn' + (m.placeholder ? ' pending' : '');
  b.type = 'button';
  b.dataset.id = m.id;
  const hero = HERO_FILES[i];
  if (hero) b.style.setProperty('--hero', `url("../generated/web10/${hero}")`);
  b.innerHTML =
    `<span class="stage-numeral">${plate.numeral}</span>` +
    `<span class="stage-text"><span class="stage-name">${plate.name}</span>` +
    `<span class="stage-sub">${m.title || ''}</span></span>`;
  b.onclick = () => loadStage(m);
  nav.appendChild(b);
});
$('stageCount').textContent = `0–${toRoman(STAGES.length - 2)} · ✦`;

// Mobile stage switcher — the index rail is display:none ≤860px, so without
// this there would be no way to change stages on a phone (review P0).
const stageSelect = $('stageSelect');
STAGES.forEach((m) => {
  const p = plateOf(m);
  const o = document.createElement('option');
  o.value = m.id;
  o.textContent = `${p.numeral} · ${p.name}`;
  stageSelect.appendChild(o);
});
stageSelect.onchange = () => {
  const m = STAGES.find(s => s.id === stageSelect.value);
  if (m) loadStage(m);
};

// ── Mark X timeline scrubber — a node per stage + ◀/▶ stepping ────────────────
const tlTrack = $('tlTrack');
if (tlTrack) {
  STAGES.forEach((m) => {
    const p = plateOf(m);
    const n = document.createElement('button');
    n.className = 'tl-node';
    n.type = 'button';
    n.dataset.id = m.id;
    n.title = `${p.numeral} · ${p.name}`;
    n.setAttribute('aria-label', n.title);
    n.innerHTML = `<span class="tl-dot"></span><span class="tl-num">${p.numeral}</span>`;
    n.onclick = () => loadStage(m);
    tlTrack.appendChild(n);
  });
  const tlStep = (d) => {
    const i = STAGES.findIndex((s) => s.id === currentMeta?.id);
    const j = Math.max(0, Math.min(STAGES.length - 1, (i < 0 ? 0 : i) + d));
    loadStage(STAGES[j]);
  };
  $('tlPrev')?.addEventListener('click', () => tlStep(-1));
  $('tlNext')?.addEventListener('click', () => tlStep(1));
}

// Keyboard navigation of the index — Up/Down move focus, Home/End jump, the
// button's native Enter/Space activates. (Correct vertical-menu semantics.)
nav.addEventListener('keydown', (e) => {
  const btns = [...nav.querySelectorAll('.stage-btn')];
  const i = btns.indexOf(document.activeElement);
  if (i < 0) return;
  let j = -1;
  if (e.key === 'ArrowDown') j = Math.min(i + 1, btns.length - 1);
  else if (e.key === 'ArrowUp') j = Math.max(i - 1, 0);
  else if (e.key === 'Home') j = 0;
  else if (e.key === 'End') j = btns.length - 1;
  if (j >= 0) { e.preventDefault(); btns[j].focus(); }
});

// ── Per-stage readout label ───────────────────────────────────────────────────
const READOUT_LABEL = {
  'stage0-miller-urey': 'organics collected',
  'stage4-vent': 'reaction extent',
  'stage7-rna': 'replication cycles',
  'stage10-selection': 'mean fitness',
  'stage11-luca': 'core distilled',
};

// ── Render loop ───────────────────────────────────────────────────────────────
const clock = new THREE.Clock();
const readoutEl = $('readout');
let lastReadout = '';
function tick() {
  const inExp = currentView() === 'exp';
  const dt = Math.min(clock.getDelta(), 0.05);
  current?.userData?.anim?.update(dt, clock.elapsedTime);
  // In Micrograph view the 3-D pane is hidden → skip controls damping + the
  // (expensive) WebGL composer pass entirely; the apparatus anim still advances
  // so the progress readout stays live.
  if (!inExp) { lab.controls.update(); lab.composer.render(); }
  const isSpecimen = currentMeta?.id?.startsWith('capstone');
  let txt = '';
  if (!currentMeta?.placeholder && !isSpecimen) {
    const p = current?.userData?.anim?.getProgress?.() ?? 0;
    const label = READOUT_LABEL[currentMeta?.id] || 'experiment extent';
    txt = `${label} · ${(p * 100).toFixed(0)}%`;
  }
  if (txt !== lastReadout) { readoutEl.textContent = txt; lastReadout = txt; }   // write only on change
  requestAnimationFrame(tick);
}

function disposeTree(obj) {
  const TEX = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap', 'envMap', 'alphaMap',
    'transmissionMap', 'thicknessMap', 'clearcoatNormalMap', 'clearcoatRoughnessMap',
    'sheenColorMap', 'iridescenceMap', 'specularColorMap', 'specularIntensityMap'];   // incl. MeshPhysical slots
  obj.traverse(o => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(mt => {
      for (const k of TEX) if (mt[k]?.dispose) mt[k].dispose();   // baked CanvasTextures would otherwise leak per stage
      mt.dispose();
    });
  });
}

if (lab) {
  setView('split');      // normalize mode-label + aria-checked + roving tabindex through one path
  loadStage(STAGES[0]);
  tick();
  window.__labReady = true;   // tell the index.html failsafe the lab booted
} else {
  failLab(hasWebGL() ? 'the apparatus could not be initialised'
                     : 'this exhibit requires WebGL, which is unavailable here');
}
