// Standalone single-rule verifier — `node verify_one.mjs <abs-path-to-rule.js>`.
// Mirrors smoke.mjs's exercise() for ONE rule file so a new rule can be gated
// before it's wired into RULE_FILES. Exits non-zero on any contract failure.
import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";

const file = process.argv[2];
if (!file) { console.error("usage: node verify_one.mjs <abs-path-to-rule.js>"); process.exit(2); }

globalThis.window = { CA: { RULES: {} } };
globalThis.CA = globalThis.window.CA;

let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error("  ✗ " + m); };
const ok = () => { checks++; };
const assert = (c, m) => { c ? ok() : fail(m); };
const allFinite = (a) => { for (let i = 0; i < a.length; i++) if (!Number.isFinite(a[i])) return i; return -1; };

try { vm.runInThisContext(fs.readFileSync(file, "utf8"), { filename: path.basename(file) }); }
catch (e) { console.error("load failed: " + e.message); process.exit(1); }

const ids = Object.keys(window.CA.RULES);
assert(ids.length >= 1, "no rule registered");
const id = ids[ids.length - 1];
const make = window.CA.RULES[id];
assert(typeof make === "function", "registry entry is not a factory");
if (typeof make !== "function") { console.log(`${file}: ${checks} checks, ${failures} failure(s)`); process.exit(1); }
const rule = make();

assert(typeof rule.id === "string" && rule.id.length > 0, "missing id");
assert(typeof rule.label === "string", "missing label");
assert(typeof rule.whatThisIs === "string" && rule.whatThisIs.length > 20, "whatThisIs missing/too short");
assert(typeof rule.aboutStage === "string" && rule.aboutStage.length > 40, "aboutStage missing/too short");
assert(Number.isInteger(rule.width) && rule.width > 0, "bad width");
assert(Number.isInteger(rule.height) && rule.height > 0, "bad height");

const W = rule.width, H = rule.height, params = rule.params || {};
for (const [n, s] of Object.entries(params)) {
  if (s.type === "bool") assert(typeof s.value === "boolean", `param ${n}: bool value not boolean`);
  else if (s.type === "enum") { assert(Array.isArray(s.options), `param ${n}: enum missing options`); assert(s.options.includes(s.value) || s.value === "", `param ${n}: enum value not in options`); }
  else { assert(Number.isFinite(s.min) && Number.isFinite(s.max) && s.min < s.max, `param ${n}: bad min/max`); assert(s.value >= s.min && s.value <= s.max, `param ${n}: default ${s.value} outside [${s.min},${s.max}]`); }
}
const cc = rule.controlConsequence || {};
for (const k of Object.keys(cc)) assert(k in params, `controlConsequence references unknown param "${k}"`);
for (const n of Object.keys(params)) if (!(n in cc)) console.warn(`  ⚠ param "${n}" has no controlConsequence hint`);

try { rule.reset(); for (let s = 0; s < 8; s++) rule.step(); } catch (e) { fail("reset/step threw: " + e.message); }
const px = new Float64Array(W * H * 4);
try { rule.render(px); } catch (e) { fail("render threw: " + e.message); }
const bp = allFinite(px); assert(bp === -1, `render non-finite at index ${bp}`);
let alpha = true; for (let i = 3; i < px.length; i += 4) if (px[i] !== 255) { alpha = false; break; }
assert(alpha, "render left some alpha != 255");
assert(typeof rule.renderHeight === "function", "missing renderHeight");
if (typeof rule.renderHeight === "function") { const ht = new Float32Array(W * H); try { rule.renderHeight(ht); } catch (e) { fail("renderHeight threw: " + e.message); } const bh = allFinite(ht); assert(bh === -1, `renderHeight non-finite at index ${bh}`); }
assert(typeof rule.population() === "string" && rule.population().length > 0, "population() must return non-empty string");
assert(Number.isFinite(rule.generation()) && rule.generation() >= 0, "generation() must be finite >= 0");
try { rule.paint(W >> 1, H >> 1, 3, "draw"); rule.paint(W >> 1, H >> 1, 3, "erase"); } catch (e) { fail("paint threw: " + e.message); }
try { rule.clear(); rule.randomize(); } catch (e) { fail("clear/randomize threw: " + e.message); }
if ("presets" in rule) {
  assert(Array.isArray(rule.presets) && rule.presets.length > 0, "presets must be a non-empty array when present");
  for (const p of rule.presets || []) {
    assert(typeof p.label === "string" && p.label.length > 0, "preset missing label");
    assert(p.values && typeof p.values === "object", `preset "${p.label}" missing values`);
    for (const [k, v] of Object.entries(p.values || {})) { const s = params[k]; assert(!!s, `preset "${p.label}" unknown param "${k}"`); if (s && s.type !== "bool" && s.type !== "enum") assert(v >= s.min && v <= s.max, `preset "${p.label}" ${k}=${v} outside [${s.min},${s.max}]`); }
    try { for (const [k, v] of Object.entries(p.values || {})) { if (params[k]) params[k].value = v; if (typeof rule.onParamChange === "function") rule.onParamChange(k); } if (p.reseed && rule.reset) rule.reset(); rule.step(); const p2 = new Float64Array(W * H * 4); rule.render(p2); const b = allFinite(p2); assert(b === -1, `preset "${p.label}" render non-finite at ${b}`); } catch (e) { fail(`preset "${p.label}" threw: ${e.message}`); }
  }
}
console.log(`${id}: ${checks} checks, ${failures} failure(s)`);
process.exit(failures === 0 ? 0 : 1);
