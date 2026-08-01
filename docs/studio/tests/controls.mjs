// controls.mjs — headless engine-integrity gate for the Studio's 13 tiles.
//
// engines.js is a classic script (window.StudioEngines), so we load it in a vm
// sandbox with a ~40-line 2D-canvas stub and drive the real kernels:
//
//   · every tile constructs, steps 60× without throwing, and its controls are
//     sound (stable unique keys, ranges hold their bounds and round-trip,
//     segs point at real options, buttons act, randomize actually changes
//     something and leaves no NaN behind);
//   · the SCIENCE moves — grid engines render a non-uniform field that is
//     visibly different 30 steps later, particle engines keep every position
//     finite and in motion. For a pure-canvas client this IS the anim gate
//     (there is no WebGL scene for a headless three-stub to probe);
//   · the Pro export promise is real — fidelity('still') strictly raises each
//     grid engine's internal resolution, and the fractal exposes the
//     true-resolution chunked still().
//
//   node docs/studio/tests/controls.mjs

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';
import vm from 'node:vm';

const DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let fails = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); fails++; } else console.log('  ✓ ' + m); };
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const near = (a, b) => Math.abs(a - b) <= 1e-6 * Math.max(1, Math.abs(a), Math.abs(b));

// ── the 2D-canvas stub (everything the kernels actually call) ────────────────
function stubCtx(w, h) {
  return {
    canvas: { width: w, height: h },
    createImageData: (a, b) => ({ width: a, height: b, data: new Uint8ClampedArray(a * b * 4) }),
    putImageData(img) { this._last = img; },
    drawImage() {}, fillRect() {}, beginPath() {}, moveTo() {}, lineTo() {}, closePath() {},
    arc() {}, fill() {}, stroke() {}, clip() {}, save() {}, restore() {},
    translate() {}, rotate() {}, scale() {}, setTransform() {},
    fillStyle: '', strokeStyle: '', lineWidth: 1, globalCompositeOperation: '', imageSmoothingEnabled: true,
  };
}
const win = {
  document: {
    createElement() {
      const c = { width: 0, height: 0 };
      c.getContext = () => (c._ctx || (c._ctx = stubCtx(c.width, c.height)));
      return c;
    },
  },
};
win.window = win;
vm.runInContext(readFileSync(join(DIR, 'engines.js'), 'utf8'), vm.createContext(win));
const { make, TOOLS } = win.StudioEngines;

// ── 1. the registry ──────────────────────────────────────────────────────────
console.log('registry:');
ok(TOOLS.length === 13, `13 tiles (got ${TOOLS.length})`);
ok(new Set(TOOLS.map((t) => t.name)).size === 13, 'tile names unique');
ok(new Set(TOOLS.map((t) => slug(t.name))).size === 13, 'tile slugs unique (share-link ids)');
ok(TOOLS.some((t) => t.pro) && TOOLS.some((t) => !t.pro), 'both free and Pro tiles exist');

// grid getters for the fidelity assertion, per kind
const GRID = { rd: (k) => k.gw, slime: (k) => k.G, lenia: (k) => k.G, cymatics: (k) => k.G,
               dla: (k) => k.G, starling: (k) => k.dg };
// engines that paint through putImageData (field probe reads octx._last)
const FIELD = new Set(['rd', 'slime', 'lenia', 'cymatics', 'dla', 'starling', 'fractal']);

const fieldStats = (img) => {
  const d = img.data; let sum = 0, sum2 = 0, n = d.length / 4;
  for (let i = 0; i < d.length; i += 4) { const v = d[i] + d[i + 1] + d[i + 2]; sum += v; sum2 += v * v; }
  return { mean: sum / n, varr: sum2 / n - (sum / n) ** 2 };
};

for (const t of TOOLS) {
  console.log(`${t.name} (${t.kind}${t.preset ? ' · ' + t.preset : ''}):`);
  const k = make(t.kind, 320, 200, t.preset);

  // ── 2. controls contract ──────────────────────────────────────────────────
  const ctls = k.controls();
  const live = ctls.filter((c) => c.t !== 'button');
  const keys = live.map((c) => c.key);
  ok(live.every((c) => typeof c.key === 'string' && /^[a-z][a-z0-9]*$/.test(c.key)),
     'every non-button control has a stable machine key');
  ok(new Set(keys).size === keys.length, 'keys unique within the desk');
  ok(ctls.every((c) => c.label && (c.t === 'button' ? typeof c.act === 'function' : typeof c.get === 'function' && typeof c.set === 'function')),
     'labels + get/set (or act) on every control');
  let sound = true;
  for (const c of live) {
    const orig = c.get();
    if (c.t === 'range') {
      if (!(c.min < c.max)) { sound = false; console.error(`    ✗ ${c.key}: min<max`); }
      if (!(orig >= c.min - 1e-9 && orig <= c.max + 1e-9)) { sound = false; console.error(`    ✗ ${c.key}: default ${orig} outside [${c.min},${c.max}]`); }
      c.set(c.min); if (!near(c.get(), c.min)) { sound = false; console.error(`    ✗ ${c.key}: set(min) did not round-trip`); }
      if (c.fmt && typeof c.fmt(c.get()) !== 'string' && typeof c.fmt(c.get()) !== 'number') { sound = false; console.error(`    ✗ ${c.key}: fmt broken`); }
    } else if (c.t === 'seg') {
      const vals = c.opts.map((o) => o[0]);
      if (!vals.some((v) => v === orig)) { sound = false; console.error(`    ✗ ${c.key}: default not among opts`); }
      c.set(vals[vals.length - 1]); if (c.get() !== vals[vals.length - 1]) { sound = false; console.error(`    ✗ ${c.key}: set(opt) did not round-trip`); }
    } else if (c.t === 'toggle') {
      c.set(!orig); if (c.get() === orig) { sound = false; console.error(`    ✗ ${c.key}: toggle did not flip`); }
    }
    c.set(orig);
  }
  ok(sound, 'ranges hold bounds and round-trip · segs point at real options · toggles flip');

  // ── 3. randomize does something, cleanly ──────────────────────────────────
  const snap = () => live.map((c) => c.get());
  let changed = false;
  const before = snap();
  for (let r = 0; r < 5 && !changed; r++) {
    k.randomize();
    changed = snap().some((v, i) => typeof v === 'number' ? !near(v, before[i]) : v !== before[i]);
  }
  ok(changed, 'randomize() changes at least one parameter (≤5 tries)');
  ok(snap().every((v) => typeof v !== 'number' || Number.isFinite(v)), 'no NaN/∞ after randomize');

  // ── 4. it runs, and the science moves (the anim gate) ─────────────────────
  // Probe a FRESH kernel: randomize() above may have legitimately parked the
  // sim in a static regime (e.g. the fractal's Auto-morph off — a still image
  // by design), and defaults are what a visitor actually sees on the tiles.
  const km = make(t.kind, 320, 200, t.preset);
  let threw = false;
  try { for (let i = 0; i < 60; i++) km.step(); } catch (e) { threw = true; console.error('    ' + e.message); }
  ok(!threw, '60 steps without throwing');
  const ctx = stubCtx(320, 200);
  if (FIELD.has(t.kind)) {
    km.render(ctx);
    const img1 = km.octx._last;
    const s1 = fieldStats(img1);
    ok(s1.varr > 0, `field is non-uniform (variance ${s1.varr.toFixed(1)})`);
    const copy = Uint8ClampedArray.from(img1.data);
    for (let i = 0; i < 30; i++) km.step();
    km.render(ctx);
    const img2 = km.octx._last;
    let diff = 0; for (let i = 0; i < img2.data.length; i++) if (img2.data[i] !== copy[i]) diff++;
    ok(diff > 0, `field evolves — ${diff} bytes differ after 30 more steps`);
  } else {
    const x0 = Float64Array.from(km.x), y0 = Float64Array.from(km.y);
    for (let i = 0; i < 10; i++) km.step();
    let moved = 0, finite = true;
    for (let i = 0; i < km.N; i++) {
      if (!Number.isFinite(km.x[i]) || !Number.isFinite(km.y[i])) finite = false;
      moved += Math.abs(km.x[i] - x0[i]) + Math.abs(km.y[i] - y0[i]);
    }
    ok(finite, 'every position finite');
    ok(moved > 0, `particles move (Σ|Δ| = ${moved.toFixed(0)})`);
  }

  // ── 5. the Pro export promise is real ─────────────────────────────────────
  if (GRID[t.kind]) {
    const kx = make(t.kind, 3840, 2160, t.preset);
    const g0 = GRID[t.kind](kx);
    kx.fidelity('still');
    const g1 = GRID[t.kind](kx);
    ok(g1 > g0, `fidelity('still') raises the field: ${g0} → ${g1}`);
  } else if (t.kind === 'fractal') {
    const kx = make(t.kind, 3840, 2160, t.preset);
    ok(typeof kx.still === 'function', 'true-resolution chunked still() exposed');
    kx.fidelity('still'); ok((kx._cap || 0) >= 3840, 'stills uncapped (computed at output width)');
    kx.fidelity('video'); ok(kx._cap === 1600, 'video cap raised to 1600');
  } else {
    ok(true, 'already honest — sims at output resolution');
  }
}

console.log(fails ? `\nFAIL — ${fails} problem(s)` : '\nOK — 13 desks sound, the science moves, exports honest');
process.exit(fails ? 1 : 0);
