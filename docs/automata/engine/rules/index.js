// rules/index.js — the family registry. Every family exposes the SAME
// contract the web7 control panel reads (a params schema + named presets), so
// the lab's rule desk is generated from data, never hand-wired:
//
//   family = { id, name, blurb, params: { key: {label, type:'text'|'number'|
//              'enum', value, min, max, step, options, help} },
//              presets: [{label, hint, values:{key:val}, pattern?}],
//              make(values) → rule, validate(values) → null | error string,
//              defaultPattern?: library id, soupDensity,
//              schema?(values) → params (families whose knob set depends on a
//              value, e.g. the abiogenesis stage picker; a param flagged
//              `rebuild` re-derives the schema when it changes),
//              presetsFor?(values) → the presets relevant to `values` }
//   rule    = { family, spec, states, describe(), step(grid), init?(grid,rng),
//               lambda?, oneD? }

import * as lifelike from './lifelike.js';
import * as ltl from './ltl.js';
import * as elementary from './elementary.js';
import * as cyclic from './cyclic.js';
import * as wireworld from './wireworld.js';
import * as turmite from './turmite.js';
import * as abiogenesis from './abiogenesis.js';

const tryValidate = (fn) => { try { fn(); return null; } catch (e) { return e.message; } };

export const FAMILIES = [
  {
    id: 'lifelike', name: 'Life-like · Generations', short: 'Life-like',
    blurb: 'Outer-totalistic B/S rules on the Moore or von Neumann neighbourhood, with optional Generations decay states.',
    params: {
      rule: { label: 'Rule', type: 'text', value: 'B3/S23', help: 'B3/S23 · 23/3 · B2/S/C3 · suffix V for von Neumann', mono: true },
    },
    presets: lifelike.CATALOG.map((c) => ({ label: c.name, hint: c.note, values: { rule: c.rule }, cls: c.cls })),
    soupDensity: 0.35,
    validate: (v) => tryValidate(() => lifelike.parseRule(v.rule)),
    make: (v) => lifelike.make(lifelike.parseRule(v.rule)),
  },
  {
    id: 'ltl', name: 'Larger than Life', short: 'LtL',
    blurb: 'Evans’ interval rules on a (2r+1)² box: at large range the lattice behaves like a continuous medium of gliding "bugs".',
    params: {
      rule: { label: 'Rule', type: 'text', value: 'R5,C0,M1,S34..58,B34..45', help: 'R range, C states, M centre counts, S/B intervals', mono: true },
    },
    presets: ltl.CATALOG.map((c) => ({ label: c.name, hint: c.note, values: { rule: c.rule } })),
    soupDensity: 0.5,
    validate: (v) => tryValidate(() => ltl.parseLtl(v.rule)),
    make: (v) => ltl.make(ltl.parseLtl(v.rule)),
  },
  {
    id: 'elementary', name: 'Elementary (1-D)', short: '1-D',
    blurb: 'Wolfram’s 256 elementary rules (and the 5-cell totalistic codes) drawn as a space–time sheet: time runs down the plate.',
    params: {
      rule: { label: 'Rule number', type: 'number', value: 30, min: 0, max: 255, step: 1 },
      totalistic: { label: 'Table', type: 'enum', value: 'elementary', options: ['elementary', 'totalistic r=2'] },
      init: { label: 'Seed', type: 'enum', value: 'single', options: ['single', 'soup'] },
    },
    presets: elementary.CATALOG.map((c) => ({ label: c.name, hint: c.note, values: { rule: c.rule, totalistic: 'elementary' }, cls: c.cls })),
    validate: (v) => tryValidate(() => elementary.make({ rule: v.rule, totalistic: v.totalistic !== 'elementary' })),
    make: (v) => elementary.make({ rule: v.rule, totalistic: v.totalistic !== 'elementary', init: v.init }),
  },
  {
    id: 'cyclic', name: 'Cyclic · Greenberg–Hastings', short: 'Excitable',
    blurb: 'Excitable media: cyclic colour rings that self-organise into spirals, and the Greenberg–Hastings model of excitation, refractoriness and rest.',
    params: {
      model: { label: 'Model', type: 'enum', value: 'cyclic', options: ['cyclic', 'gh'] },
      states: { label: 'States', type: 'number', value: 14, min: 3, max: 64, step: 1 },
      threshold: { label: 'Threshold', type: 'number', value: 1, min: 1, max: 24, step: 1 },
      range: { label: 'Range', type: 'number', value: 1, min: 1, max: 4, step: 1 },
      neighbourhood: { label: 'Neighbourhood', type: 'enum', value: 'moore', options: ['moore', 'vn'] },
    },
    presets: cyclic.CATALOG.map((c) => ({ label: c.name, hint: c.note, values: c.values })),
    validate: (v) => tryValidate(() => cyclic.make(v)),
    make: (v) => cyclic.make(v),
  },
  {
    id: 'wireworld', name: 'Wireworld', short: 'Wireworld',
    blurb: 'Silverman’s four-state circuit automaton: electrons run along wires, and the 1-or-2-heads rule makes diodes, gates and clocks.',
    params: {},
    presets: [
      { label: 'Loop clock', hint: 'One electron circulating a wire loop.', values: {}, pattern: 'ww_loop' },
      { label: 'Diode', hint: 'Passes electrons one way only.', values: {}, pattern: 'ww_diode' },
      { label: 'Two clocks', hint: 'A 32-cell loop and a 24-cell loop, each tapping its own wire.', values: {}, pattern: 'ww_clocks' },
    ],
    defaultPattern: 'ww_loop',
    paint: ['empty', 'wire', 'head', 'tail'],
    validate: () => null,
    make: () => wireworld.make(),
  },
  {
    id: 'turmite', name: 'Turmites · Langton’s ant', short: 'Turmites',
    blurb: 'Ants that turn by the colour they stand on, recolour it, and step: Langton’s ant and the multi-colour turmite family.',
    params: {
      rule: { label: 'Turn string', type: 'text', value: 'RL', help: 'one letter per colour: L left, R right, U u-turn, N straight', mono: true },
      ants: { label: 'Ants', type: 'number', value: 1, min: 1, max: 64, step: 1 },
      movesPerGen: { label: 'Moves / generation', type: 'number', value: 8, min: 1, max: 2000, step: 1 },
    },
    presets: turmite.CATALOG.map((c) => ({ label: c.name, hint: c.note, values: { rule: c.rule, ants: 1, movesPerGen: 8 } })),
    validate: (v) => tryValidate(() => turmite.parseTurmite(v.rule)),
    make: (v) => turmite.make(v),
  },
  {
    id: 'abiogenesis', name: 'Abiogenesis · the 13-stage lab', short: 'Abiogenesis',
    blurb: 'The origin-of-life lab’s thirteen stage simulations — loaded by reference from the canonical lab (web7), each with its full knob set and named regimes, seeded for reproducible runs. Watch-and-tune: the fields are continuous, so the brush is off.',
    params: abiogenesis.schema({}),
    schema: (v) => abiogenesis.schema(v),
    get presets() { return abiogenesis.allPresets(); },
    presetsFor: (v) => abiogenesis.presetsFor(v),
    paintable: false,
    validate: (v) => (abiogenesis.available() ? (abiogenesis.stageById(v.stage) ? null : `unknown stage "${v.stage}"`) : 'the abiogenesis rule scripts are not loaded'),
    make: (v, changed) => abiogenesis.make(v, changed),
  },
];

export const familyById = (id) => FAMILIES.find((f) => f.id === id) || null;

// Current values of a family's params (schema → plain object). `base` seeds
// the derivation for families with a value-dependent schema.
export function valuesOf(family, base = {}) {
  const P = family.schema ? family.schema(base) : family.params;
  const out = {};
  for (const [k, p] of Object.entries(P)) out[k] = k in base ? base[k] : p.value;
  return out;
}
export const schemaOf = (family, values) => (family.schema ? family.schema(values) : family.params);
export const presetsOf = (family, values) => (family.presetsFor ? family.presetsFor(values) : family.presets);

// Palette per family: state → [r,g,b]. Catalytic-Silence grammar: obsidian
// ground, teal for the living state, bone for structure, magenta accents.
export function palette(familyId, states) {
  const cols = [[8, 11, 16]];
  if (familyId === 'wireworld') return [[8, 11, 16], [96, 84, 60], [63, 224, 208], [232, 120, 255]];
  if (familyId === 'abiogenesis') {          // substrate → specimen relief, obsidian → teal → bone
    for (let s = 1; s < states; s++) {
      const t = (s - 1) / Math.max(1, states - 2);
      cols.push([Math.round(30 + 200 * t), Math.round(120 + 104 * t), Math.round(130 + 78 * t)]);
    }
    return cols;
  }
  if (familyId === 'cyclic') {
    for (let s = 1; s < states; s++) {
      const t = s / states;
      cols.push(hsl(190 + 170 * t, 0.62, 0.32 + 0.35 * Math.sin(Math.PI * t)));
    }
    return cols;
  }
  if (familyId === 'turmite') {
    for (let s = 1; s < states; s++) {
      const t = (s - 1) / Math.max(1, states - 1);
      cols.push(hsl(175 + 130 * t, 0.55, 0.42 + 0.3 * t));
    }
    return cols;
  }
  // Life-like / LtL / 1-D: state 1 teal, dying states fade through magenta to ground.
  cols.push([63, 224, 208]);
  for (let s = 2; s < states; s++) {
    const t = (s - 2) / Math.max(1, states - 2);
    cols.push([Math.round(215 - 190 * t), Math.round(123 - 100 * t), Math.round(255 - 220 * t)]);
  }
  return cols;
}
function hsl(h, s, l) {
  const k = (n) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return [Math.round(255 * f(0)), Math.round(255 * f(8)), Math.round(255 * f(4))];
}

export { lifelike, ltl, elementary, cyclic, wireworld, turmite, abiogenesis };
