// web7 controls contract (zero-dep). Guards the two systemic control fixes:
//
//   1. Preset integrity — every rule's `presets` regimes set REAL params within
//      their slider bounds, so the "Regime" picker (main.js buildParamPanel)
//      actually moves something. (Presets shipped dead for ~10 stages before.)
//   2. Mineral catalysis (REV-18) — `minerals` is a genuine surface-catalysis
//      model, not the old Gray-Scott stand-in: polymer must localise ON the clay,
//      and the "no catalysis" control regime must erase that localisation.
//
// Loads the rule classic-scripts the browser way (IIFEs registering window.CA.RULES)
// in a vm sandbox — no three, no DOM, no SEM needed (we never call render()).
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const expDir = join(here, '..', 'experiment');

let pass = 0;
const fails = [];
const ok = (cond, msg) => { if (cond) pass++; else fails.push(msg); };

// The rule IIFEs do `window.CA = window.CA || {RULES:{}}` then read a BARE `CA`,
// so the sandbox global object must BE the window (window.CA === globalThis.CA).
const win = {};
win.window = win; win.self = win; win.console = console; win.CA = { RULES: {} };
vm.createContext(win);
const run = (rel) => vm.runInContext(readFileSync(join(expDir, rel), 'utf8'), win, { filename: rel });

try { run('viridis.js'); } catch { /* VIRIDIS_LUT is only read by render(), unused here */ }
const RULE_FILES = ['soup', 'grayscott', 'raf', 'vesicles', 'vents', 'minerals',
  'chirality', 'rna', 'code', 'coacervate', 'natural_selection', 'luca', 'life'];
for (const f of RULE_FILES) { try { run(`rules/${f}.js`); } catch (e) { console.error(`(skip ${f}: ${e.message})`); } }
const RULES = win.CA.RULES;

console.log('Running web7 controls tests…\n');

// ── 1. Preset integrity across every registered rule ────────────────────────
let rulesWithPresets = 0;
for (const id of Object.keys(RULES)) {
  let rule;
  try { rule = RULES[id](); } catch { continue; }   // instantiation failures are smoke.mjs's job
  if (!Array.isArray(rule.presets) || !rule.presets.length) continue;
  rulesWithPresets++;
  const params = rule.params || {};
  rule.presets.forEach((p, i) => {
    ok(p && typeof p.label === 'string' && p.label.length > 0, `${id} preset[${i}] has no label`);
    ok(p && p.values && typeof p.values === 'object', `${id} preset "${p?.label}" has no values map`);
    for (const k of Object.keys(p.values || {})) {
      const spec = params[k];
      ok(!!spec, `${id} preset "${p.label}" sets unknown param "${k}" (picker would no-op)`);
      if (spec && spec.min !== undefined && spec.max !== undefined) {
        const v = p.values[k];
        ok(v >= spec.min && v <= spec.max,
          `${id} preset "${p.label}" ${k}=${v} is outside the slider range [${spec.min}, ${spec.max}]`);
      }
    }
  });
}
ok(rulesWithPresets >= 9, `expected ≥9 rules to ship named regimes, found ${rulesWithPresets}`);

// ── 2. Mineral catalysis is real (REV-18) ───────────────────────────────────
function onClayVsBulk(rule, steps) {
  rule.reset();
  for (let i = 0; i < steps; i++) rule.step();
  const m = rule.population().match(/on-clay\s+(\d+)\s*\/\s*bulk\s+(\d+)/);
  return m ? { on: +m[1], bulk: +m[2] } : null;
}
const minerals = RULES.minerals && RULES.minerals();
ok(!!minerals, 'minerals rule is registered (CA.RULES.minerals)');
if (minerals) {
  ok(minerals.id === 'minerals' && minerals.params && minerals.params.kClay,
    'minerals exposes a kClay catalysis control');

  const cat = onClayVsBulk(minerals, 300);
  ok(!!cat, `minerals population string should report on-clay/bulk (got "${minerals.population()}")`);
  if (cat) {
    ok(cat.on > cat.bulk * 2,
      `surface catalysis: polymer must localise on clay (on-clay ${cat.on} ≫ bulk ${cat.bulk})`);
    ok(cat.on >= 5, `surface catalysis: clay should accumulate real polymer (on-clay ${cat.on})`);
  }

  // "no catalysis (control)" regime sets k_bulk = k_clay → localisation vanishes.
  const ctrl = (minerals.presets || []).find((p) => /no catalysis/i.test(p.label));
  ok(!!ctrl, 'minerals ships a "no catalysis (control)" regime');
  if (ctrl) {
    for (const k of Object.keys(ctrl.values)) if (minerals.params[k]) minerals.params[k].value = ctrl.values[k];
    const flat = onClayVsBulk(minerals, 300);
    if (flat) {
      ok(flat.on <= flat.bulk * 1.5 + 3,
        `no-catalysis control: localisation should collapse (on-clay ${flat.on} ≈ bulk ${flat.bulk})`);
    }
  }
}

// ── Report ──────────────────────────────────────────────────────────────────
if (fails.length) console.error('\n' + fails.map((f) => '  ✗ ' + f).join('\n'));
console.log(`\n${pass} checks passed, ${fails.length} failure(s).`);
process.exit(fails.length ? 1 : 0);
