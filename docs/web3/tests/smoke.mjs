// Web3 rule smoke tests — run with `node docs/web3/tests/smoke.mjs`.
//
// The browser has no test runner, so this is a zero-dependency node
// harness that loads every rule module against a minimal `window` stub
// and exercises the full lifecycle (seed → step → render → paint) of
// each one. It catches the silent regressions a static site otherwise
// ships unnoticed: a NaN leaking into the pixel buffer, a renamed param
// that breaks a controlConsequence/preset reference, a preset value that
// falls outside its slider range, a method that throws.
//
// Pure assertions; no framework. Exits non-zero on the first hard
// failure so it can gate CI.

import fs from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RULES_DIR = path.join(HERE, "..", "rules");

// Rule modules are browser IIFEs that attach to window.CA.RULES, and
// their last line registers via the bare global `CA` (which the browser
// auto-creates when you assign window.CA). node's vm has no such magic,
// so we expose both `window` and `CA` pointing at the same object.
globalThis.window = { CA: { RULES: {} } };
globalThis.CA = globalThis.window.CA;

const RULE_FILES = [
  "conway.js",
  "wolfram1d.js",
  "grayscott.js",
  "soup.js",
  "natural_selection.js",
  "chirality.js",
  "coacervate.js",
  "vents.js",
  "vesicles.js",
  "raf.js",
  "rna.js",
  "code.js",
  "luca.js",
  "life.js",
];

let failures = 0;
let checks = 0;

function fail(rule, msg) {
  failures++;
  console.error(`  ✗ [${rule}] ${msg}`);
}
function ok() {
  checks++;
}
function assert(rule, cond, msg) {
  if (cond) ok();
  else fail(rule, msg);
}

// --- Load every rule module -------------------------------------------------
for (const file of RULE_FILES) {
  const code = fs.readFileSync(path.join(RULES_DIR, file), "utf8");
  try {
    vm.runInThisContext(code, { filename: file });
  } catch (e) {
    fail(file, `failed to load: ${e.message}`);
  }
}

const RULES = globalThis.window.CA.RULES;
const ids = Object.keys(RULES);
assert("registry", ids.length === RULE_FILES.length,
  `expected ${RULE_FILES.length} rules registered, got ${ids.length} (${ids.join(", ")})`);

// --- Helpers ----------------------------------------------------------------
function allFinite(arr) {
  for (let i = 0; i < arr.length; i++) {
    if (!Number.isFinite(arr[i])) return i;
  }
  return -1;
}

function exercise(id, rule) {
  // Identity / metadata.
  assert(id, typeof rule.id === "string" && rule.id.length > 0, "missing id");
  assert(id, typeof rule.label === "string", "missing label");
  assert(id, typeof rule.whatThisIs === "string" && rule.whatThisIs.length > 20,
    "whatThisIs (P0-A1) missing or too short");
  assert(id, typeof rule.aboutStage === "string" && rule.aboutStage.length > 40,
    "aboutStage (P1-A4) missing or too short");
  assert(id, Number.isInteger(rule.width) && rule.width > 0, "bad width");
  assert(id, Number.isInteger(rule.height) && rule.height > 0, "bad height");

  const W = rule.width, H = rule.height;
  const params = rule.params || {};

  // Param slots are internally consistent.
  for (const [name, slot] of Object.entries(params)) {
    if (slot.type === "bool") {
      assert(id, typeof slot.value === "boolean", `param ${name}: bool value not boolean`);
    } else if (slot.type === "enum") {
      assert(id, Array.isArray(slot.options), `param ${name}: enum missing options`);
      assert(id, slot.options.includes(slot.value) || slot.value === "",
        `param ${name}: enum value "${slot.value}" not in options`);
    } else {
      assert(id, Number.isFinite(slot.min) && Number.isFinite(slot.max) && slot.min < slot.max,
        `param ${name}: bad min/max`);
      assert(id, slot.value >= slot.min && slot.value <= slot.max,
        `param ${name}: default ${slot.value} outside [${slot.min}, ${slot.max}]`);
    }
  }

  // controlConsequence (P0-G2) keys must all name real params — catches
  // a renamed param that would silently lose its hint.
  const cc = rule.controlConsequence || {};
  for (const key of Object.keys(cc)) {
    assert(id, key in params, `controlConsequence references unknown param "${key}"`);
  }
  for (const name of Object.keys(params)) {
    if (!(name in cc)) {
      console.warn(`  ⚠ [${id}] param "${name}" has no controlConsequence hint`);
    }
  }

  // Lifecycle: reset → step ×8 → render → renderHeight → paint.
  try {
    rule.reset();
    for (let s = 0; s < 8; s++) rule.step();
  } catch (e) {
    fail(id, `reset/step threw: ${e.message}`);
    return;
  }

  // render() into a NaN-preserving buffer so we catch non-finite math.
  const px = new Float64Array(W * H * 4);
  try {
    rule.render(px);
  } catch (e) {
    fail(id, `render threw: ${e.message}`);
  }
  const badPx = allFinite(px);
  assert(id, badPx === -1, `render produced non-finite value at index ${badPx}`);
  // Alpha channel should be opaque everywhere.
  let alphaSet = true;
  for (let i = 3; i < px.length; i += 4) {
    if (px[i] !== 255) { alphaSet = false; break; }
  }
  assert(id, alphaSet, "render left some alpha values != 255");

  // renderHeight() — every rule implements it for SEM mode.
  assert(id, typeof rule.renderHeight === "function", "missing renderHeight");
  if (typeof rule.renderHeight === "function") {
    const ht = new Float32Array(W * H);
    try {
      rule.renderHeight(ht);
    } catch (e) {
      fail(id, `renderHeight threw: ${e.message}`);
    }
    const badHt = allFinite(ht);
    assert(id, badHt === -1, `renderHeight produced non-finite value at index ${badHt}`);
  }

  // population() / generation() contracts (the readout bar depends on these).
  assert(id, typeof rule.population() === "string" && rule.population().length > 0,
    "population() must return a non-empty string");
  assert(id, Number.isFinite(rule.generation()) && rule.generation() >= 0,
    "generation() must return a finite, non-negative number");

  // paint() must tolerate both modes without throwing.
  try {
    rule.paint(W >> 1, H >> 1, 3, "draw");
    rule.paint(W >> 1, H >> 1, 3, "erase");
  } catch (e) {
    fail(id, `paint threw: ${e.message}`);
  }

  // clear() / randomize() must not throw.
  try {
    rule.clear();
    rule.randomize();
  } catch (e) {
    fail(id, `clear/randomize threw: ${e.message}`);
  }

  // Preset (P1-D2) contract.
  if ("presets" in rule) {
    assert(id, Array.isArray(rule.presets) && rule.presets.length > 0,
      "presets must be a non-empty array when present");
    for (const preset of rule.presets || []) {
      assert(id, typeof preset.label === "string" && preset.label.length > 0,
        "preset missing label");
      assert(id, preset.values && typeof preset.values === "object",
        `preset "${preset.label}" missing values`);
      for (const [k, v] of Object.entries(preset.values || {})) {
        const slot = params[k];
        assert(id, !!slot, `preset "${preset.label}" sets unknown param "${k}"`);
        if (slot && slot.type !== "bool" && slot.type !== "enum") {
          assert(id, v >= slot.min && v <= slot.max,
            `preset "${preset.label}" value ${k}=${v} outside [${slot.min}, ${slot.max}]`);
        }
      }
      // Applying a preset then stepping must stay finite.
      try {
        for (const [k, v] of Object.entries(preset.values || {})) {
          if (params[k]) params[k].value = v;
          if (typeof rule.onParamChange === "function") rule.onParamChange(k);
        }
        if (preset.reseed && typeof rule.reset === "function") rule.reset();
        rule.step();
        const p2 = new Float64Array(W * H * 4);
        rule.render(p2);
        const bad = allFinite(p2);
        assert(id, bad === -1,
          `preset "${preset.label}" → render non-finite at index ${bad}`);
      } catch (e) {
        fail(id, `preset "${preset.label}" threw: ${e.message}`);
      }
    }
  }
}

// --- Run --------------------------------------------------------------------
console.log(`Running web3 rule smoke tests (${ids.length} rules)…\n`);
for (const id of ids) {
  const make = RULES[id];
  if (typeof make !== "function") {
    fail(id, "registry entry is not a factory function");
    continue;
  }
  let rule;
  try {
    rule = make();
  } catch (e) {
    fail(id, `factory threw: ${e.message}`);
    continue;
  }
  exercise(id, rule);
  if (failures === 0 || true) console.log(`  • ${id} (${rule.label})`);
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
