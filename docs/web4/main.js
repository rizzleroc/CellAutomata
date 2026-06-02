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
let expLayers = {};            // SEM_LAYERS entry for the active rule (tint/sprites)
let expColorBuf = null;        // native-res RGBA scratch for the colour-tint pass
let expRuleId = '';            // active web3 rule id (for sprites/caption)

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

// ── ROOT CAUSE 1: composite color + sprites OVER the hi-res SEM base ─────────
// renderExperimentFrame ONLY shaded the height field — it never injected the
// rule's render() hue (handedness/clade/species) or its sprites() annotations.
// SEM_LAYERS, keyed by web3 rule id, opts each stage into the extra layers:
//   tint:    alpha-blend the rule's render() colour over the SEM pixel while
//            preserving SEM luminance/depth (chroma carries the science).
//   sprites: composite the rule's sprites() (cells/glyphs/droplets) on top.
// Stages with a pure depth story (grayscott domes, rna cloud, …) stay {}.
const SEM_LAYERS = {
  soup: { tint: 0.50, sprites: true }, grayscott: {}, raf: {},
  vesicles: { sprites: true }, vents: {},
  chirality: { tint: 0.60, sprites: true }, rna: {}, code: {},
  coacervate: { sprites: true },
  'natural-selection': { tint: 0.55, sprites: true },
  luca: { tint: 0.60 }, life: {},
};

// ── ROOT CAUSE 2: maturity gate ──────────────────────────────────────────────
// Several renderHeight fields are ~flat at seed (chirality |L−R|≈0 before the
// symmetry breaks; luca coreField=0 from a random soup; grayscott's 7px seed;
// coacervate pre-spinodal; vesicles un-nucleated). Each stage gets warmed up
// headless to a scientifically-legible state before the first paint — an
// optional reseeding preset plus N silent step()s. The live RAF loop keeps
// running afterwards; this only fast-forwards the INITIAL state.
const MATURITY = {
  chirality:          { preset: 'homochiral sweep',  steps: 120 },
  luca:               { preset: 'sharp LUCA',        steps: 60  },
  coacervate:         { preset: 'few large droplets', steps: 80 },
  vesicles:           { preset: 'stiff spheres',     steps: 80  },
  'natural-selection': { steps: 40 },
  soup:               { steps: 60  },
  vents:              { steps: 120 },
  raf:                { steps: 30  },
  rna:                { steps: 80  },
  code:               { steps: 60  },
  life:               { steps: 60  },
  // FIX 3 — minerals (stage5) shares the grayscott rule. The 'mitosis' Pearson
  // regime is the live spot-mitosis attractor. The lone central 7px seed divides
  // too slowly to fill the dish, so we re-seed with randomize() (8 scattered
  // nucleation patches) first: the spots then proliferate across the WHOLE field
  // in the warm-up, so BOTH stage1 and stage5 show a real, dish-filling
  // reaction–diffusion pattern (never an empty plate).
  grayscott:          { preset: 'mitosis', seed: 'randomize', steps: 600 },
};

// Apply a named preset to a rule with NO DOM. Handles both shapes seen in the
// web3 rules: (a) a `presets` array of {label, reseed?, values:{k:v}}, and
// (b) an enum `params.preset` whose onParamChange derives the other params
// (Gray–Scott's Pearson selector). Returns true if a preset was applied.
function applyPreset(rule, label) {
  if (!rule || !label) return false;
  // (a) presets[] array (chirality, luca, coacervate, vesicles, …).
  if (Array.isArray(rule.presets)) {
    const p = rule.presets.find((pr) => pr.label === label);
    if (p) {
      if (p.values) {
        for (const k in p.values) {
          if (rule.params[k]) { rule.params[k].value = p.values[k]; rule.onParamChange?.(k); }
        }
      }
      if (p.reseed) rule.reset();
      return true;
    }
  }
  // (b) enum params.preset (Gray–Scott): set it and let onParamChange derive F/k.
  const pe = rule.params && rule.params.preset;
  if (pe && Array.isArray(pe.options) && pe.options.includes(label)) {
    pe.value = label;
    rule.onParamChange?.('preset');
    return true;
  }
  return false;
}

// Fast-forward a freshly-reset rule to a legible state (see MATURITY). Applies
// any preset (sets the regime params, may reseed), then an optional explicit
// re-seed method (e.g. grayscott.randomize() to scatter nucleation sites), then
// runs `steps` headless step()s.
function warmUpExperiment(rule, ruleId) {
  const cfg = MATURITY[ruleId];
  if (!cfg) return;
  if (cfg.preset) applyPreset(rule, cfg.preset);
  if (cfg.seed && typeof rule[cfg.seed] === 'function') rule[cfg.seed]();
  const steps = cfg.steps | 0;
  for (let s = 0; s < steps; s++) rule.step();
}

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
  expRuleId = ruleId;
  expLayers = SEM_LAYERS[ruleId] || {};                // which extra layers this rule opts into
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
  // Native-res RGBA scratch for the colour-tint pass (FIX 1 — only the tint
  // stages ever fill it, but allocate once per stage so the hot path is alloc-free).
  expColorBuf  = new Uint8ClampedArray(expRule.width * expRule.height * 4);
  // FIX 2 — fast-forward to a scientifically-legible state BEFORE the first
  // paint (preset + headless warm-up). The live loop still runs afterwards.
  warmUpExperiment(expRule, ruleId);
  expCaption.textContent = 'LIVE SEM · ' + (m.label || ruleId);
  updateExpCaption(m);                                 // FIX 4 — add the live phenomenon readout
  renderExperimentFrame();                             // paint one frame immediately (even if paused)
}

// FIX 4 — make the caption self-describing: stage label + the rule's own live
// readout (handedness ee%, clade count, master%, …) from population(). Called
// on select and each rendered frame so the panel narrates what it's showing.
function updateExpCaption(m) {
  if (!expRule) return;
  const label = (m && m.label) || (currentMeta && currentMeta.label) || expRuleId;
  let readout = '';
  try { readout = expRule.population ? String(expRule.population()) : ''; } catch (e) { readout = ''; }
  expCaption.textContent = 'LIVE SEM · ' + label + (readout ? ' · ' + readout : '');
}

// Colour-tint pass (FIX 1). The SEM base in `pix` (hi-res RGBA) is pure depth
// shading — it preserves relief but throws away the rule's render() hue, which
// is where stages like chirality (handedness), luca (clades), soup/selection
// (species) actually encode their science. Sample the rule's NATIVE-res colour
// under each hi-res pixel; keep the SEM pixel's luminance L; if the native
// colour is essentially grey (chroma ~0 → empty substrate / bone-cream peaks)
// leave the SEM pixel untouched; otherwise re-scale that hue to luminance L and
// alpha-blend it over the SEM pixel by `amount`. SEM depth survives, hue rides in.
function _tintSemWithColour(pix, w2, h2, colour, gw, scale, amount) {
  const inv = 1 / 255;
  for (let y = 0; y < h2; y++) {
    const ny = (y / scale) | 0;
    for (let x = 0; x < w2; x++) {
      const nx = (x / scale) | 0;
      const ci = (ny * gw + nx) * 4;
      let cr = colour[ci], cg = colour[ci + 1], cb = colour[ci + 2];
      // Chroma = max−min across channels. ~0 ⇒ achromatic (background / bone) → keep SEM.
      const cmax = cr > cg ? (cr > cb ? cr : cb) : (cg > cb ? cg : cb);
      const cmin = cr < cg ? (cr < cb ? cr : cb) : (cg < cb ? cg : cb);
      if (cmax - cmin < 12) continue;                  // no usable hue here → pure SEM
      const p = (y * w2 + x) * 4;
      // SEM pixel luminance (Rec.601) — the depth/shading we want to preserve.
      const L = 0.299 * pix[p] + 0.587 * pix[p + 1] + 0.114 * pix[p + 2];
      // Scale the native hue to that luminance (so shading rides through the hue).
      const cl = 0.299 * cr + 0.587 * cg + 0.114 * cb;
      const g = cl > 1 ? L / cl : L;                   // luminance-preserving rescale
      let tr = cr * g, tg = cg * g, tb = cb * g;
      if (tr > 255) tr = 255; if (tg > 255) tg = 255; if (tb > 255) tb = 255;
      // Alpha-blend the luminance-matched hue over the SEM pixel.
      pix[p]     = (pix[p]     * (1 - amount) + tr * amount) | 0;
      pix[p + 1] = (pix[p + 1] * (1 - amount) + tg * amount) | 0;
      pix[p + 2] = (pix[p + 2] * (1 - amount) + tb * amount) | 0;
    }
  }
  void inv;
}

// EXACT web3 render() SEM branch (main.js:551-558), now COMPOSITED: SEM depth
// base → optional colour tint (render() hue) → putImageData → optional sprite
// overlay (sprites() annotations), per the active rule's SEM_LAYERS entry.
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
    // FIX 1a — colour tint OVER the hi-res SEM base, BEFORE putImageData.
    if (expLayers.tint && typeof expRule.render === 'function') {
      expRule.render(expColorBuf);                     // native-res RGBA hue
      _tintSemWithColour(expImageData.data, expW2, expH2, expColorBuf,
                         expRule.width, expScale, expLayers.tint);
    }
  } else {
    expRule.render(expImageData.data);                 // defensive fallback to rule's own RGBA
  }
  expCtx.putImageData(expImageData, 0, 0);
  // FIX 1b — sprite overlay AFTER putImageData (putImageData wipes the canvas,
  // so canvas-drawn sprites must come last). sprites() coords are NATIVE grid;
  // scale the ctx so 1 grid unit == expScale canvas px, then compose, then
  // restore the transform. SPRITES is a classic-script global; guard for it.
  if (expLayers.sprites && window.SPRITES && typeof expRule.sprites === 'function') {
    const sprites = expRule.sprites();
    if (sprites && sprites.length) {
      expCtx.save();
      expCtx.setTransform(expScale, 0, 0, expScale, 0, 0);   // grid → hi-res canvas
      SPRITES.compose(expCtx, sprites, expRule.width, expRule.height,
                      SEM.PALETTES[EXP_PALETTE]);
      expCtx.restore();
    }
  }
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
  if (advanced && currentView() !== 'lab') {
    renderExperimentFrame();
    // FIX 4 — refresh the live phenomenon readout, throttled (~2 Hz) since some
    // population()s do real work (flood-fill, distinct-genome scans).
    if (now - expLastCaption > 500) { updateExpCaption(currentMeta); expLastCaption = now; }
  }
  expRaf = requestAnimationFrame(expTick);
}
let expLastCaption = 0;
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
