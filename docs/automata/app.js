// app.js — The Automata Lab controller.
//
// Everything on the page is generated from engine data: the family tabs and
// the rule editor from rules/index.js (params schema + presets), the brush
// from the family palette, the pattern library from patterns.js. The loop is
// fixed-timestep (generations · s⁻¹), every generation is measured
// (measure.js) and logged for the sparkline / CSV, and the SEM feed reads the
// lattice as a height field through the shared depth-shader (window.SEM).
// A run is reproducible from its URL hash: family, rule values, lattice size,
// boundary, seed and (optionally) the placed pattern.
//
// Families that are "watch-and-tune" (the abiogenesis stages: continuous
// fields at a fixed lattice size) switch the desk into that mode: the brush
// and pattern steps hide, the size picker locks, and the micrograph is the
// stage's own renderHeight() rather than the quantised lattice.

import { Grid, mulberry32, BOUNDARIES } from './engine/grid.js';
import { FAMILIES, familyById, valuesOf, schemaOf, presetsOf, palette, lifelike } from './engine/rules/index.js';
import { LIBRARY, byId, libraryPattern, parseRLE, parsePlain, toRLE, fromGrid } from './engine/patterns.js';
import * as M from './engine/measure.js';

const $ = (id) => document.getElementById(id);
const els = {};
for (const id of ['cells', 'feed', 'semPanel', 'plate', 'spark', 'play', 'stepBtn', 'resetBtn', 'clearBtn', 'soupBtn', 'speed', 'vSpeed',
  'density', 'vDensity', 'densityWrap', 'famTabs', 'famBlurb', 'preset', 'presetHint', 'paramList', 'ruleErr', 'applyBtn', 'randomRuleBtn', 'labLink',
  'size', 'boundary', 'seed', 'semMode', 'ageTint', 'drawStep', 'brush', 'radius', 'vRadius', 'pattern', 'patternNote', 'placeBtn', 'placeClearBtn',
  'rleIn', 'rleLoadBtn', 'csvBtn', 'pngBtn', 'rleBtn', 'linkBtn', 'rPop', 'rDens', 'rAct', 'rEnt', 'rLambda', 'rClass', 'rWhy', 'stageWrap', 'rStage',
  'mRule', 'mGen', 'mSize', 'mSeed', 'viewLabel', 'toast']) els[id] = $(id);

// ── State ───────────────────────────────────────────────────────────────────
const S = {
  family: FAMILIES[0], values: valuesOf(FAMILIES[0]), rule: null, grid: null,
  width: 200, height: 150, boundary: 'torus', seed: 1, rng: mulberry32(1),
  running: false, gps: 30, acc: 0, last: 0, density: 0.35,
  brushState: 1, radius: 1, pattern: null, patternCustom: null,
  age: null, prev: null, log: new M.RunLog(2400), colors: [], semMode: 'on', ageTint: true,
  img: null, imgCtx: null, semImg: null, semCtx: null, semH: null, semPx: null,
};
const paintable = () => S.family.paintable !== false;
const ROMAN = ['', 'I', 'II', 'III', 'IV'];

// ── Build: family tabs, presets, params, brush, patterns ────────────────────
function buildFamilyTabs() {
  els.famTabs.innerHTML = '';
  for (const f of FAMILIES) {
    const b = document.createElement('button');
    b.type = 'button'; b.setAttribute('role', 'tab'); b.textContent = f.short; b.dataset.id = f.id; b.title = f.name;
    b.setAttribute('aria-selected', String(f === S.family));
    b.onclick = () => selectFamily(f.id);
    els.famTabs.appendChild(b);
  }
}
function buildPresets() {
  els.preset.innerHTML = '';
  const blank = document.createElement('option'); blank.value = ''; blank.textContent = 'custom'; els.preset.appendChild(blank);
  presetsOf(S.family, S.values).forEach((p, i) => {
    const o = document.createElement('option'); o.value = String(i);
    o.textContent = p.label + (p.cls ? `  · class ${ROMAN[p.cls]}` : '');
    els.preset.appendChild(o);
  });
  els.presetHint.textContent = '';
}
function buildParams() {
  els.paramList.innerHTML = '';
  const P = schemaOf(S.family, S.values);
  if (!Object.keys(P).length) {
    const p = document.createElement('p'); p.className = 'hint'; p.textContent = 'One rule, no free parameters — draw circuits with the brush or load a pattern.';
    els.paramList.appendChild(p); return;
  }
  for (const [key, spec] of Object.entries(P)) {
    const lab = document.createElement('label'); lab.className = 'p' + (spec.type === 'text' ? ' wide' : '');
    const name = document.createElement('span'); name.textContent = spec.label || key; lab.appendChild(name);
    let input, mirror = null;
    if (spec.type === 'enum') {
      input = document.createElement('select');
      spec.options.forEach((o, i) => { const opt = document.createElement('option'); opt.value = o; opt.textContent = (spec.labels && spec.labels[i]) || o || '—'; input.appendChild(opt); });
      input.value = String(S.values[key]);
      lab.appendChild(input);
    } else if (spec.type === 'number') {
      const wrap = document.createElement('div'); wrap.className = 'num';
      input = document.createElement('input'); input.type = 'range'; input.min = spec.min; input.max = spec.max; input.step = spec.step || 1; input.value = S.values[key];
      mirror = document.createElement('input'); mirror.type = 'number'; mirror.min = spec.min; mirror.max = spec.max; mirror.step = spec.step || 1; mirror.value = S.values[key];
      mirror.setAttribute('aria-label', (spec.label || key) + ' value');
      wrap.append(input, mirror); lab.appendChild(wrap);
    } else {
      input = document.createElement('input'); input.type = 'text'; input.value = S.values[key]; input.spellcheck = false; input.autocomplete = 'off';
      lab.appendChild(input);
    }
    input.dataset.key = key; input.setAttribute('aria-label', spec.label || key);
    const commit = (raw) => {
      const v = spec.type === 'number' ? Number(raw) : raw;
      S.values[key] = v;
      if (mirror) { mirror.value = v; input.value = v; }
      els.preset.value = '';           // a hand edit drops out of the named regime
      if (spec.rebuild) { S.values = valuesOf(S.family, { [key]: v }); buildParams(); buildPresets(); applyRule({ keepGrid: false, changed: [key] }); return; }
      const err = S.family.validate(S.values); els.ruleErr.textContent = err || '';
      if (spec.type !== 'text' && !err) applyRule({ keepGrid: true, changed: [key] });
    };
    input.oninput = () => commit(input.value);
    if (mirror) mirror.onchange = () => commit(mirror.value);
    input.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); applyRule({ keepGrid: true, changed: [key] }); } };
    if (spec.help) { const h = document.createElement('small'); h.textContent = spec.help; lab.appendChild(h); }
    els.paramList.appendChild(lab);
  }
}
function syncParamInputs() {
  for (const input of els.paramList.querySelectorAll('[data-key]')) {
    input.value = S.values[input.dataset.key];
    const m = input.parentElement && input.parentElement.querySelector('input[type=number]'); if (m) m.value = S.values[input.dataset.key];
  }
}
function buildBrush() {
  els.brush.innerHTML = '';
  const n = S.rule.states, names = S.family.paint;
  for (let s = 0; s < n && s < 24; s++) {
    const b = document.createElement('button'); b.type = 'button'; b.setAttribute('role', 'radio');
    const c = S.colors[s]; b.style.background = `rgb(${c[0]},${c[1]},${c[2]})`;
    b.textContent = names ? names[s][0].toUpperCase() : String(s);
    b.title = names ? names[s] : `state ${s}`;
    b.setAttribute('aria-label', b.title); b.setAttribute('aria-checked', String(s === S.brushState));
    b.onclick = () => { S.brushState = s; buildBrush(); };
    els.brush.appendChild(b);
  }
  if (S.brushState >= n) S.brushState = 1;
}
function buildPatterns() {
  els.pattern.innerHTML = '';
  const mine = LIBRARY.filter((p) => p.family === S.family.id);
  const none = document.createElement('option'); none.value = ''; none.textContent = mine.length ? '— choose —' : '— none for this family —'; els.pattern.appendChild(none);
  for (const p of mine) { const o = document.createElement('option'); o.value = p.id; o.textContent = p.name + (p.rule ? ` (${p.rule})` : ''); els.pattern.appendChild(o); }
  if (S.patternCustom) { const o = document.createElement('option'); o.value = '__custom'; o.textContent = 'pasted pattern'; els.pattern.appendChild(o); }
  els.pattern.value = S.pattern || '';
  els.pattern.onchange = () => {
    S.pattern = els.pattern.value || null;
    const e = S.pattern && S.pattern !== '__custom' ? byId(S.pattern) : null;
    els.patternNote.textContent = e ? [e.note, e.period ? `period ${e.period}` : '', e.speed || ''].filter(Boolean).join(' · ') : '';
  };
  els.pattern.onchange();
}
// Which desk parts apply to this family.
function setMode() {
  const p = paintable();
  els.drawStep.hidden = !p;
  els.plate.classList.toggle('locked', !p);
  els.densityWrap.hidden = !p || !!S.rule.init && S.family.id !== 'elementary' && S.family.id !== 'turmite';
  els.size.disabled = !!S.rule.fixedSize;
  els.ageTint.disabled = !p;
  els.rleBtn.disabled = !p;
  els.stageWrap.hidden = !S.rule.readout;
  els.labLink.hidden = S.family.id !== 'abiogenesis';
  els.viewLabel.textContent = S.running ? 'running' : (p ? 'paint with the pointer' : 'watch · tune the knobs');
}

// ── Rule / grid lifecycle ───────────────────────────────────────────────────
function selectFamily(id, { values = null } = {}) {
  S.family = familyById(id) || FAMILIES[0];
  S.values = valuesOf(S.family, values || {});
  S.brushState = 1;
  for (const b of els.famTabs.children) b.setAttribute('aria-selected', String(b.dataset.id === S.family.id));
  els.famBlurb.textContent = S.family.blurb;
  S.pattern = S.family.defaultPattern || null;
  buildPresets(); buildParams();
  applyRule({ keepGrid: false });
  buildPatterns();
  els.preset.value = '';
}
function applyRule({ keepGrid = false, changed = null } = {}) {
  const err = S.family.validate(S.values);
  els.ruleErr.textContent = err || '';
  if (err) return false;
  S.rule = S.family.make(S.values, changed || undefined);
  if (S.family.schema) { S.values = valuesOf(S.family, S.values); }      // read cascaded values back
  syncParamInputs();
  S.colors = palette(S.family.id, S.rule.states);
  if (S.rule.fixedSize) { S.width = S.rule.fixedSize.width; S.height = S.rule.fixedSize.height; }
  else if (S.grid && S.grid.width !== +els.size.value.split('x')[0]) { const [w, h] = els.size.value.split('x').map(Number); S.width = w; S.height = h; }
  if (S.rule.stepsPerSec && changed === null) { S.gps = Math.min(120, S.rule.stepsPerSec); els.speed.value = S.gps; els.vSpeed.textContent = `${S.gps} s⁻¹`; }
  els.mRule.textContent = S.rule.describe();
  els.rLambda.textContent = S.rule.lambda !== undefined ? S.rule.lambda.toFixed(3) : '—';
  buildBrush(); setMode();
  if (!keepGrid || !S.grid || S.grid.width !== S.width || S.grid.height !== S.height) resetRun();
  else { clampStates(); render(); }
  writeHash();
  return true;
}
function clampStates() { const c = S.grid.cells, n = S.rule.states; for (let i = 0; i < c.length; i++) if (c[i] >= n) c[i] = 0; }
function makeGrid() {
  S.grid = new Grid(S.width, S.height, { boundary: S.boundary });
  S.age = new Uint16Array(S.grid.size); S.prev = new Uint8Array(S.grid.size);
  S.img = new ImageData(S.width, S.height);
  const off = document.createElement('canvas'); off.width = S.width; off.height = S.height; S.imgCtx = off.getContext('2d');
  S.semH = new Float32Array(S.grid.size); S.semPx = new Uint8ClampedArray(S.grid.size * 4);
  const semOff = document.createElement('canvas'); semOff.width = S.width; semOff.height = S.height; S.semCtx = semOff.getContext('2d');
  S.semImg = new ImageData(S.width, S.height);
  els.mSize.textContent = `${S.width}×${S.height}`;
  els.cells.style.aspectRatio = els.feed.style.aspectRatio = `${S.width} / ${S.height}`;   // never stretch the lattice
}
// Reset = re-seed the RNG and rebuild the initial condition for the current rule.
function resetRun() {
  if (!S.grid || S.grid.width !== S.width || S.grid.height !== S.height || S.grid.boundary !== S.boundary) makeGrid();
  S.rng = mulberry32(S.seed);
  S.grid.clear(); S.grid.row = 0; S.age.fill(0); S.log.clear();
  if (S.rule.init) S.rule.init(S.grid, S.rng);
  else if (!S.family.defaultPattern && !S.pattern) S.grid.randomize(S.rng, S.density, S.rule.states);
  const pat = paintable() ? currentPattern() : null;
  if (pat) S.grid.stampCentered(pat);
  S.prev.set(S.grid.cells);
  els.mSeed.textContent = String(S.seed);
  measure(0); render();
}
function currentPattern() {
  if (S.pattern === '__custom') return S.patternCustom;
  const e = S.pattern ? byId(S.pattern) : null;
  return e ? libraryPattern(e) : null;
}
function soup() {
  if (!paintable()) { resetRun(); return; }
  S.rng = mulberry32(S.seed);
  S.grid.clear(); S.grid.row = 0; S.age.fill(0); S.log.clear();
  if (S.rule.oneD) { for (let x = 0; x < S.width; x++) S.grid.cells[x] = S.rng() < S.density ? 1 : 0; }
  else if (S.family.id === 'turmite') { S.rule.init(S.grid, S.rng); }
  else S.grid.randomize(S.rng, S.density, S.rule.states);
  S.prev.set(S.grid.cells); measure(0); render();
}
function clearAll() {
  if (!paintable()) { resetRun(); return; }
  S.grid.clear(); S.grid.row = 0; S.age.fill(0); S.log.clear();
  if (S.family.id === 'turmite' && S.rule.init) S.rule.init(S.grid, S.rng);
  S.prev.set(S.grid.cells); measure(0); render();
}

// ── Stepping + measurement ──────────────────────────────────────────────────
function stepOnce() {
  S.prev.set(S.grid.cells);
  S.rule.step(S.grid);
  const c = S.grid.cells, a = S.age, p = S.prev;
  for (let i = 0; i < c.length; i++) a[i] = c[i] ? (p[i] === c[i] ? Math.min(65535, a[i] + 1) : 1) : 0;
  measure(M.activity(S.grid, S.prev));
}
function measure(act) {
  const g = S.grid, pop = g.population();
  const row = { generation: g.generation, population: pop, density: pop / g.size, activity: act, entropy: M.blockEntropy(g) };
  S.log.push(row);
  els.rPop.textContent = String(pop);
  els.rDens.textContent = (row.density * 100).toFixed(1) + '%';
  els.rAct.textContent = (act * 100).toFixed(1) + '%';
  els.rEnt.textContent = row.entropy.toFixed(2) + ' b';
  els.mGen.textContent = String(g.generation);
  const cls = M.classify(S.log.series('activity'));
  els.rClass.textContent = cls.label; els.rWhy.textContent = cls.why;
  if (S.rule.readout) els.rStage.textContent = S.rule.readout();
}

// ── Rendering ───────────────────────────────────────────────────────────────
function render() {
  const g = S.grid, c = g.cells, d = S.img.data, cols = S.colors, tint = S.ageTint && S.rule.states === 2 && !S.rule.oneD;
  for (let i = 0, j = 0; i < c.length; i++, j += 4) {
    const s = c[i]; const col = cols[s] || cols[0];
    if (tint && s === 1) {
      const t = Math.min(1, S.age[i] / 48);             // teal newborn → bone veteran
      d[j] = col[0] + (230 - col[0]) * t; d[j + 1] = col[1] + (224 - col[1]) * t; d[j + 2] = col[2] + (208 - col[2]) * t;
    } else { d[j] = col[0]; d[j + 1] = col[1]; d[j + 2] = col[2]; }
    d[j + 3] = 255;
  }
  if (S.rule.oneD && g.row !== undefined) {            // a hairline marks the present row
    const y = g.row; for (let x = 0; x < g.width; x++) { const j = (y * g.width + x) * 4; if (!c[y * g.width + x]) { d[j] = 20; d[j + 1] = 40; d[j + 2] = 44; } }
  }
  if (S.family.id === 'turmite') for (const ant of S.rule.agents) if (ant.alive) { const j = (ant.y * g.width + ant.x) * 4; d[j] = 215; d[j + 1] = 123; d[j + 2] = 255; }
  S.imgCtx.putImageData(S.img, 0, 0);
  blit(els.cells, S.imgCtx.canvas);
  if (S.semMode !== 'off' && window.SEM) renderSEM();
}
function blit(canvas, src) {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = Math.max(1, Math.round(canvas.clientWidth * dpr)), h = Math.max(1, Math.round(canvas.clientHeight * dpr));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  const ctx = canvas.getContext('2d'); ctx.imageSmoothingEnabled = false;
  ctx.drawImage(src, 0, 0, w, h);
}
// The lattice as a height field: the living state is a raised plateau,
// dying / coloured states graded by index — or, for a stage rule, its own
// renderHeight() micrograph — then the shared depth-shader.
function renderSEM() {
  const g = S.grid, c = g.cells, H = S.semH, n = S.rule.states;
  if (S.rule.height) S.rule.height(H);
  else {
    const multi = n > 2 && (S.family.id === 'cyclic' || S.family.id === 'turmite');
    for (let i = 0; i < c.length; i++) {
      const s = c[i];
      H[i] = s === 0 ? 0.08 : (multi ? 0.25 + 0.7 * (s / (n - 1)) : s === 1 ? 0.85 : 0.85 - 0.6 * ((s - 1) / Math.max(1, n - 1)));
    }
  }
  window.SEM.render(H, g.width, g.height, S.semPx, { palette: S.semMode === 'cool' ? 'cool-mono' : 'warm-sepia', scale: 1, relief: 1.2 });
  S.semImg.data.set(S.semPx);
  S.semCtx.putImageData(S.semImg, 0, 0);
  blit(els.feed, S.semCtx.canvas);
}
function renderSpark() {
  const ctx = els.spark.getContext('2d'), W = els.spark.width, Hh = els.spark.height;
  ctx.fillStyle = '#080b10'; ctx.fillRect(0, 0, W, Hh);
  const rows = S.log.rows.slice(-W); if (rows.length < 2) return;
  const draw = (key, color, max) => {
    ctx.strokeStyle = color; ctx.lineWidth = 1.2; ctx.beginPath();
    rows.forEach((r, i) => { const x = i * (W / (rows.length - 1)); const y = Hh - 3 - (Hh - 6) * Math.min(1, r[key] / max); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
  };
  draw('density', '#3fe0d0', Math.max(0.05, ...rows.map((r) => r.density)));
  draw('activity', '#d77bff', Math.max(0.05, ...rows.map((r) => r.activity)));
}

// ── Loop ────────────────────────────────────────────────────────────────────
function frame(t) {
  requestAnimationFrame(frame);
  if (!S.running) return;
  const dt = Math.min(0.25, (t - S.last) / 1000 || 0); S.last = t; S.acc += dt * S.gps;
  let n = Math.min(12, Math.floor(S.acc)); S.acc -= n;
  if (n <= 0) return;
  while (n-- > 0) stepOnce();
  render(); renderSpark();
}
function setRunning(on) {
  S.running = on; S.last = performance.now(); S.acc = 0;
  els.play.setAttribute('aria-pressed', String(on)); els.play.textContent = on ? '❚❚ Pause' : '▶ Run';
  setMode();
}

// ── Painting ────────────────────────────────────────────────────────────────
let painting = false, paintState = 1;
function cellAt(ev) {
  const r = els.cells.getBoundingClientRect();
  return { x: Math.floor((ev.clientX - r.left) / r.width * S.width), y: Math.floor((ev.clientY - r.top) / r.height * S.height) };
}
function paint(ev) {
  const { x, y } = cellAt(ev), R = S.radius - 1;
  for (let dy = -R; dy <= R; dy++) for (let dx = -R; dx <= R; dx++) if (dx * dx + dy * dy <= R * R + 0.5) S.grid.set(x + dx, y + dy, paintState);
  if (S.family.id === 'turmite' && S.rule.agents.length && ev.altKey) { S.rule.agents[0].x = x; S.rule.agents[0].y = y; }
  render();
}
els.cells.addEventListener('contextmenu', (e) => e.preventDefault());
els.cells.addEventListener('pointerdown', (e) => {
  if (!paintable()) return;
  if (e.shiftKey) { const p = currentPattern(); if (p) { const { x, y } = cellAt(e); S.grid.stamp(p, x - (p.width >> 1), y - (p.height >> 1)); render(); } return; }
  painting = true; paintState = e.button === 2 ? 0 : S.brushState; els.cells.setPointerCapture(e.pointerId); paint(e);
});
els.cells.addEventListener('pointermove', (e) => { if (painting) paint(e); });
const stopPaint = () => { painting = false; };
els.cells.addEventListener('pointerup', stopPaint); els.cells.addEventListener('pointercancel', stopPaint);

// ── Controls ────────────────────────────────────────────────────────────────
els.play.onclick = () => setRunning(!S.running);
els.stepBtn.onclick = () => { stepOnce(); render(); renderSpark(); };
els.resetBtn.onclick = () => { resetRun(); renderSpark(); toast('Reset · seed ' + S.seed); };
els.clearBtn.onclick = () => { clearAll(); renderSpark(); };
els.soupBtn.onclick = () => { soup(); renderSpark(); toast(paintable() ? `Soup · ${Math.round(S.density * 100)}% · seed ${S.seed}` : 'Re-seeded · seed ' + S.seed); };
els.speed.oninput = () => { S.gps = +els.speed.value; els.vSpeed.textContent = `${S.gps} s⁻¹`; };
els.density.oninput = () => { S.density = +els.density.value / 100; els.vDensity.textContent = `${els.density.value}%`; };
els.preset.onchange = () => {
  const p = presetsOf(S.family, S.values)[+els.preset.value]; if (!p) { els.presetHint.textContent = ''; return; }
  Object.assign(S.values, p.values); syncParamInputs();
  if (p.pattern) S.pattern = p.pattern;
  applyRule({ keepGrid: false, changed: Object.keys(p.values) }); buildPatterns();
  els.presetHint.textContent = p.hint || '';
  toast(p.label);
};
els.applyBtn.onclick = () => { if (applyRule({ keepGrid: !S.rule.oneD && paintable(), changed: Object.keys(S.values) })) toast('Rule applied · ' + S.rule.describe()); };
els.randomRuleBtn.onclick = () => {
  const rng = mulberry32(Date.now() & 0xffffffff);
  const f = S.family.id;
  if (f === 'lifelike') S.values.rule = lifelike.formatRule(lifelike.randomRule(rng, { states: 2 }));
  else if (f === 'elementary') S.values.rule = Math.floor(rng() * 256);
  else if (f === 'turmite') { let s = ''; const k = 2 + Math.floor(rng() * 8); for (let i = 0; i < k; i++) s += rng() < 0.5 ? 'L' : 'R'; S.values.rule = s; }
  else if (f === 'cyclic') { S.values.states = 3 + Math.floor(rng() * 14); S.values.threshold = 1 + Math.floor(rng() * 4); S.values.range = 1 + Math.floor(rng() * 3); }
  else if (f === 'ltl') { const r = 2 + Math.floor(rng() * 6), box = (2 * r + 1) ** 2; const b0 = Math.floor(box * (0.25 + rng() * 0.2)), s0 = Math.floor(box * (0.2 + rng() * 0.2)); S.values.rule = `R${r},C0,M1,S${s0}..${s0 + Math.floor(box * 0.25)},B${b0}..${b0 + Math.floor(box * 0.12)}`; }
  else if (f === 'abiogenesis') {             // a random point in the stage's own knob space
    const P = schemaOf(S.family, S.values);
    for (const [k, spec] of Object.entries(P)) { if (k === 'stage') continue; if (spec.type === 'number') { const steps = Math.round((spec.max - spec.min) / (spec.step || 1)); S.values[k] = +(spec.min + Math.floor(rng() * (steps + 1)) * (spec.step || 1)).toFixed(6); } }
  }
  else return toast('Wireworld is a single rule');
  syncParamInputs(); els.preset.value = '';
  if (applyRule({ keepGrid: false, changed: Object.keys(S.values) })) toast('Random rule · ' + S.rule.describe() + (S.rule.lambda !== undefined ? ` · λ ${S.rule.lambda.toFixed(3)}` : ''));
};
els.size.onchange = () => { if (S.rule.fixedSize) return; const [w, h] = els.size.value.split('x').map(Number); S.width = w; S.height = h; resetRun(); writeHash(); };
els.boundary.onchange = () => { S.boundary = els.boundary.value; resetRun(); writeHash(); };
els.seed.onchange = () => { S.seed = Math.max(1, +els.seed.value | 0); els.seed.value = S.seed; resetRun(); writeHash(); };
els.semMode.onchange = () => { S.semMode = els.semMode.value; els.semPanel.hidden = S.semMode === 'off'; render(); };
els.ageTint.onchange = () => { S.ageTint = els.ageTint.value === 'on'; render(); };
els.radius.oninput = () => { S.radius = +els.radius.value; els.vRadius.textContent = String(S.radius); };
els.placeBtn.onclick = () => { const p = currentPattern(); if (!p) return toast('Choose a pattern first'); S.grid.stampCentered(p); render(); writeHash(); };
els.placeClearBtn.onclick = () => { const p = currentPattern(); if (!p) return toast('Choose a pattern first'); clearAll(); S.grid.stampCentered(p); S.prev.set(S.grid.cells); render(); writeHash(); };
els.rleLoadBtn.onclick = () => {
  const txt = els.rleIn.value.trim(); if (!txt) return;
  try {
    S.patternCustom = /[$!]/.test(txt) || /^x\s*=/.test(txt) ? parseRLE(txt) : parsePlain(txt);
    S.pattern = '__custom'; buildPatterns(); els.pattern.value = '__custom';
    els.patternNote.textContent = `pasted · ${S.patternCustom.width}×${S.patternCustom.height}`;
    toast('Pattern loaded — Place it, or shift-click to stamp');
  } catch (e) { toast('Could not parse: ' + e.message); }
};

// ── Exports ─────────────────────────────────────────────────────────────────
function download(name, blob) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); }
const slug = () => (S.rule.describe().replace(/[^\w.-]+/g, '_')) + `_g${S.grid.generation}`;
els.csvBtn.onclick = () => download(`automata_${slug()}.csv`, new Blob([S.log.toCSV()], { type: 'text/csv' }));
els.rleBtn.onclick = () => download(`automata_${slug()}.rle`, new Blob([toRLE(fromGrid(S.grid), S.rule.describe())], { type: 'text/plain' }));
els.pngBtn.onclick = () => {
  const scale = Math.max(1, Math.min(8, Math.floor(4000 / Math.max(S.width, S.height))));   // hard-bounded plate ≤ 4000²
  const out = document.createElement('canvas'); out.width = S.width * scale; out.height = S.height * scale;
  const ctx = out.getContext('2d'); ctx.imageSmoothingEnabled = false;
  ctx.drawImage(S.semMode !== 'off' ? S.semCtx.canvas : S.imgCtx.canvas, 0, 0, out.width, out.height);
  out.toBlob((b) => b && download(`automata_${slug()}_${out.width}x${out.height}.png`, b), 'image/png');
};
els.linkBtn.onclick = async () => { writeHash(); try { await navigator.clipboard.writeText(location.href); toast('Run link copied'); } catch { toast('Link is in the address bar'); } };

// ── URL hash ────────────────────────────────────────────────────────────────
function writeHash() {
  const q = new URLSearchParams();
  q.set('f', S.family.id);
  for (const [k, v] of Object.entries(S.values)) q.set('v.' + k, String(v));
  if (!S.rule.fixedSize) { q.set('w', S.width); q.set('h', S.height); }
  q.set('b', S.boundary); q.set('seed', S.seed);
  if (S.pattern && S.pattern !== '__custom' && paintable()) q.set('pat', S.pattern);
  history.replaceState(null, '', '#' + q.toString());
}
function readHash() {
  const q = new URLSearchParams(location.hash.slice(1));
  const fam = familyById(q.get('f') || '') || FAMILIES[0];
  const values = {};
  for (const [k, v] of q.entries()) if (k.startsWith('v.')) values[k.slice(2)] = v;
  const P = schemaOf(fam, values);
  for (const k of Object.keys(values)) { const spec = P[k]; if (!spec) delete values[k]; else if (spec.type === 'number') values[k] = Number(values[k]); }
  const w = +q.get('w') | 0, h = +q.get('h') | 0;
  if (w >= 16 && h >= 16 && w <= 640 && h <= 480) { S.width = w; S.height = h; els.size.value = `${w}x${h}`; }
  if (BOUNDARIES.includes(q.get('b'))) { S.boundary = q.get('b'); els.boundary.value = S.boundary; }
  if (+q.get('seed') > 0) { S.seed = +q.get('seed') | 0; els.seed.value = S.seed; }
  const pat = q.get('pat');
  return { fam, values, pat: pat && byId(pat) ? pat : null };
}

// ── Keyboard + toast + boot ─────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName)) return;
  if (e.key === ' ') { e.preventDefault(); setRunning(!S.running); }
  else if (e.key === 'n') els.stepBtn.onclick();
  else if (e.key === 'r') els.resetBtn.onclick();
  else if (e.key === 'c') els.clearBtn.onclick();
  else if (e.key === 's') els.soupBtn.onclick();
});
let toastT = 0;
function toast(msg) { els.toast.textContent = msg; els.toast.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(() => els.toast.classList.remove('show'), 1800); }
window.addEventListener('resize', () => { render(); renderSpark(); });

(function boot() {
  buildFamilyTabs();
  const { fam, values, pat } = readHash();
  selectFamily(fam.id, { values });
  if (pat) { S.pattern = pat; els.pattern.value = pat; els.pattern.onchange(); resetRun(); }
  writeHash(); renderSpark();
  requestAnimationFrame(frame);
})();

// Exposed for the smoke harness + console experiments.
window.AutomataLab = { state: S, step: stepOnce, render, applyRule, selectFamily, FAMILIES, LIBRARY };
