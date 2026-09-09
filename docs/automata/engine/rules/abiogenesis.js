// abiogenesis.js — the origin-of-life lab, inside the Automata Lab.
//
// The canonical lab (docs/web7) ships thirteen stage simulations as classic
// scripts that register factories on window.CA.RULES — Miller–Urey soup,
// Gray–Scott, RAF sets, vesicles, vents, minerals, chirality, the RNA world,
// the genetic code, coacervates, protocell selection, LUCA and the Avida-style
// digital life capstone. This adapter presents ALL of them as one family under
// the lab's registry contract, so the rule desk exposes every stage's real
// knob set and named regimes, the SEM feed shows the stage's own micrograph,
// and the measurement layer runs over its projected lattice.
//
// The page loads web7's rule files BY REFERENCE (../web7/experiment/rules/…),
// not as copies, so this client can never drift from the canonical lab.
//
// Reproducibility: the web7 rules draw from Math.random. The adapter swaps
// Math.random for the lab's seeded generator for the duration of every
// reset() and step(), so a (seed, stage, params) triple replays exactly.
//
// Projection: renderHeight() gives a [0,1] height field; the adapter quantises
// it into LEVELS bands (0 = substrate, 1..LEVELS-1 = specimen relief) to give
// the lattice view, population/activity/entropy and the age tint something
// discrete to read. The SEM feed uses the raw height field.

export const LEVELS = 6;
export const SUBSTRATE = 0.2;   // heights below this are "substrate" (state 0)

export const STAGES = [
  { id: 'soup',              num: '0',  name: 'Primordial soup',        apparatus: 'Miller–Urey spark discharge (1953)' },
  { id: 'grayscott',         num: 'I',  name: 'Reaction–diffusion',     apparatus: 'Gray–Scott / Belousov–Zhabotinsky dish' },
  { id: 'raf',               num: 'II', name: 'Autocatalytic sets',     apparatus: 'RAF reaction flask' },
  { id: 'vesicles',          num: 'III', name: 'Vesicles',              apparatus: 'Allen–Cahn + Helfrich membranes' },
  { id: 'vents',             num: 'IV', name: 'Hydrothermal vent',      apparatus: 'Alkaline-vent reactor · proton gradient' },
  { id: 'minerals',          num: 'V',  name: 'Mineral catalysis',      apparatus: 'Montmorillonite clay reactor' },
  { id: 'chirality',         num: 'VI', name: 'Homochirality',          apparatus: 'Frank 1953 autocatalysis + polarimeter' },
  { id: 'rna',               num: 'VII', name: 'RNA world',             apparatus: 'Eigen quasispecies thermocycler' },
  { id: 'code',              num: 'VIII', name: 'Genetic code',         apparatus: 'Glauber code-evolution bench' },
  { id: 'coacervate',        num: 'IX', name: 'Coacervates',            apparatus: 'Oparin droplets · Cahn–Hilliard' },
  { id: 'natural-selection', num: 'X',  name: 'Protocell selection',    apparatus: 'Microfluidic culture chip' },
  { id: 'luca',              num: 'XI', name: 'LUCA',                   apparatus: 'Genomics console · conserved core' },
  { id: 'life',              num: '✦',  name: 'Digital life',           apparatus: 'Avida-style organisms · stromatolite capstone' },
];
export const stageById = (id) => STAGES.find((s) => s.id === id) || null;

// The web7 factories, read lazily so the module imports cleanly in node.
export function registry() {
  const w = typeof window !== 'undefined' ? window : globalThis.window;
  return (w && w.CA && w.CA.RULES) || null;
}
export const available = () => { const R = registry(); return !!R && STAGES.every((s) => typeof R[s.id] === 'function'); };

const instances = new Map();
export function instance(stageId) {
  const R = registry();
  if (!R || typeof R[stageId] !== 'function') throw new Error(`abiogenesis stage "${stageId}" is not loaded (web7 rule scripts missing)`);
  if (!instances.has(stageId)) instances.set(stageId, R[stageId]());
  return instances.get(stageId);
}

// Swap Math.random for the seeded generator while fn runs.
export function withRandom(rng, fn) {
  const saved = Math.random;
  Math.random = rng;
  try { return fn(); } finally { Math.random = saved; }
}

// The rule desk schema for a given stage: `stage` picker + the stage's own params.
export function schema(values = {}) {
  const stageId = stageById(values.stage) ? values.stage : STAGES[0].id;
  const out = {
    stage: { label: 'Stage', type: 'enum', value: stageId, options: STAGES.map((s) => s.id),
      labels: STAGES.map((s) => `${s.num} · ${s.name}`), rebuild: true },
  };
  if (!registry()) return out;
  const inner = instance(stageId);
  const cc = inner.controlConsequence || {};
  for (const [k, p] of Object.entries(inner.params || {})) {
    if (p.type === 'enum') out[k] = { label: p.label || k, type: 'enum', value: p.value, options: p.options.slice(), help: cc[k] || '' };
    else out[k] = { label: p.label || k, type: 'number', value: p.value, min: p.min, max: p.max, step: p.step || 1, help: cc[k] || '' };
  }
  return out;
}

function presetsOf(stageId) {
  if (!registry()) return [];
  const inner = instance(stageId);
  return (inner.presets || []).map((p) => ({
    label: p.label, hint: p.hint || '', values: Object.assign({ stage: stageId }, p.values || {}), reseed: !!p.reseed,
  }));
}
// Every regime of every stage (the static list the tests iterate); the UI
// filters to the current stage with presetsFor().
export function allPresets() { return STAGES.flatMap((s) => presetsOf(s.id)); }
export const presetsFor = (values) => presetsOf(stageById(values.stage) ? values.stage : STAGES[0].id);

// Push values into the inner rule (only `changed` keys, in schema order, so
// onParamChange cascades — e.g. a Gray–Scott preset writing F and k — win
// over stale sibling values), then read the whole schema back.
export function apply(values, changed) {
  const inner = instance(values.stage);
  const keys = changed || Object.keys(values);
  for (const k of Object.keys(inner.params || {})) {
    if (!keys.includes(k) || !(k in values)) continue;
    const p = inner.params[k];
    const v = p.type === 'enum' ? String(values[k]) : Number(values[k]);
    if (p.value === v) continue;
    p.value = v;
    if (typeof inner.onParamChange === 'function') inner.onParamChange(k);
  }
  const out = { stage: values.stage };
  for (const [k, p] of Object.entries(inner.params || {})) out[k] = p.value;
  return out;
}

export function make(values, changed) {
  const stage = stageById(values.stage) || STAGES[0];
  const inner = instance(stage.id);
  apply(Object.assign({ stage: stage.id }, values), changed);
  const N = inner.width * inner.height;
  const H = new Float32Array(N);
  const rule = {
    family: 'abiogenesis',
    spec: { stage: stage.id },
    stage, inner,
    states: LEVELS,
    fixedSize: { width: inner.width, height: inner.height },
    stepsPerSec: inner.stepsPerSec || 30,
    paintable: false,
    rng: Math.random,
    describe: () => `${stage.num} · ${stage.name}`,
    readout: () => (typeof inner.population === 'function' ? String(inner.population()) : ''),
    // the raw micrograph height field (for the SEM feed)
    height(out) { withRandom(this.rng, () => inner.renderHeight(out)); return out; },
    project(grid) {
      withRandom(this.rng, () => inner.renderHeight(H));
      const c = grid.cells;
      for (let i = 0; i < N; i++) {
        const h = H[i];
        c[i] = h < SUBSTRATE ? 0 : Math.min(LEVELS - 1, 1 + Math.floor(((h - SUBSTRATE) / (1 - SUBSTRATE)) * (LEVELS - 1)));
      }
    },
    init(grid, rng) {
      if (grid.width !== inner.width || grid.height !== inner.height) throw new Error(`abiogenesis stage ${stage.id} needs a ${inner.width}×${inner.height} lattice`);
      this.rng = rng || Math.random;
      withRandom(this.rng, () => inner.reset());
      this.project(grid);
    },
    step(grid) {
      withRandom(this.rng, () => inner.step());
      this.project(grid);
      grid.generation++;
    },
  };
  return rule;
}
