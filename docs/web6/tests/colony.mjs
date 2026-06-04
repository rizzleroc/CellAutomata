// web6 living-colony tests — `node docs/web6/tests/colony.mjs`.
//
// Unit-tests the pure-math blob geometry (the JS port of cellauto/blobgeom.py,
// mirroring the Python side's headless geometry tests) and structurally gates
// the natural-selection living-colony render wiring: hiRes + renderPhotoreal,
// the SEM path kept intact, and the classic-script load order in index.html.
// Zero-dependency; exits non-zero on the first failure so it gates CI.

import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB6 = path.join(HERE, "..");
let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (c, m) => (c ? ok() : fail(m));
const read = (rel) => fs.readFileSync(path.join(WEB6, rel), "utf8");
const exists = (rel) => fs.existsSync(path.join(WEB6, rel));
const J = JSON.stringify;

console.log("Running web6 living-colony tests…\n");

// 1. Files exist + pass `node --check`.
for (const rel of ["experiment/blobgeom.js", "experiment/rules/natural_selection.js"]) {
  assert(exists(rel), `missing ${rel}`);
  if (!exists(rel)) continue;
  try { execFileSync(process.execPath, ["--check", path.join(WEB6, rel)], { stdio: "pipe" }); ok(); }
  catch (e) { fail(`syntax error in ${rel}: ${String(e.stderr || e).slice(0, 200)}`); }
}

// 2. Load blobgeom.js the way the browser does (classic script → window.CA.blob).
const sandbox = { window: {}, Math, console };
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(read("experiment/blobgeom.js"), sandbox, { filename: "blobgeom.js" });
const blob = sandbox.window.CA && sandbox.window.CA.blob;
assert(blob && typeof blob.blobPoints === "function", "blobgeom did not install window.CA.blob.blobPoints");

if (blob) {
  // 2a. Default outline has BLOB_N (14) finite points.
  const p = blob.blobPoints(50, 50, 10, 10, { seed: 0x1234 });
  assert(Array.isArray(p) && p.length === blob.BLOB_N, `blobPoints returned ${p.length}, expected ${blob.BLOB_N}`);
  assert(p.every((pt) => pt.length === 2 && pt.every(Number.isFinite)), "blobPoints emitted non-finite points");

  // 2b. Deterministic: identical args → identical points (pure function).
  assert(J(p) === J(blob.blobPoints(50, 50, 10, 10, { seed: 0x1234 })), "blobPoints is not deterministic");

  // 2c. Phase advances the membrane (breathing); seed individuates it.
  assert(J(p) !== J(blob.blobPoints(50, 50, 10, 10, { seed: 0x1234, phase: 1.0 })),
    "advancing phase did not move the membrane");
  assert(J(p) !== J(blob.blobPoints(50, 50, 10, 10, { seed: 0x9999 })),
    "a different seed produced an identical membrane");

  // 2d. Outline hugs the base ellipse: radius deviation ≤ wobble bound (12%).
  let maxDev = 0;
  for (const [x, y] of p) maxDev = Math.max(maxDev, Math.abs(Math.hypot(x - 50, y - 50) - 10) / 10);
  assert(maxDev <= 0.16, `membrane deviates ${(maxDev * 100).toFixed(1)}% from base radius (expected ≤ ~12%)`);

  // 2e. gazeOffset never leaves the eye-white: |offset| ≤ maxOff across many samples.
  let gMax = 0;
  for (let f = 0; f < 600; f += 7) for (const s of [0x1, 0xABCD, 0xFFFF, 0x42, 0x73A1]) {
    const [gx, gy] = blob.gazeOffset(f, s, 3.0);
    gMax = Math.max(gMax, Math.hypot(gx, gy));
  }
  assert(gMax <= 3.0 + 1e-6, `gazeOffset escaped maxOff: ${gMax.toFixed(3)} > 3.0`);

  // 2f. lighten brightens toward white; isLight is a sane luma test.
  const [lr, lg, lb] = blob.lighten(0, 0, 0);
  assert(lr > 0 && lg > 0 && lb > 0, "lighten(black) did not brighten");
  assert(blob.isLight(255, 255, 255) === true && blob.isLight(0, 0, 0) === false, "isLight luma test is wrong");

  // 2g. hash01 ∈ [0,1).
  let hOK = true;
  for (let i = 0; i < 64; i++) { const h = blob.hash01(i, i * 3 + 1); if (!(h >= 0 && h < 1)) hOK = false; }
  assert(hOK, "hash01 produced a value outside [0,1)");
}

// 3. natural_selection.js wires the living-colony render path AND keeps the SEM path.
const ns = read("experiment/rules/natural_selection.js");
assert(/hiRes:\s*true/.test(ns), "natural_selection.js does not set hiRes:true");
assert(/renderPhotoreal\s*\(/.test(ns), "natural_selection.js has no renderPhotoreal (living-colony path)");
assert(/CA\.blob/.test(ns), "natural_selection.js never reaches the blob geometry (CA.blob)");
assert(/drawFace\s*\(/.test(ns), "natural_selection.js never draws faces");
assert(/renderHeight\s*\(/.test(ns) && /render\s*\(\s*pixels\s*\)/.test(ns),
  "natural_selection.js dropped its SEM path (renderHeight/render must stay for the smoke)");

// 4. index.html loads blobgeom.js as a CLASSIC script, before natural_selection.js and main.js.
const html = read("index.html");
assert(/<script\s+src="\.\/experiment\/blobgeom\.js"\s*>/.test(html), "index.html does not load experiment/blobgeom.js");
const bi = html.indexOf('src="./experiment/blobgeom.js"');
const mi = html.indexOf('src="./main.js"');
const nsi = html.indexOf('src="./experiment/rules/natural_selection.js"');
assert(bi > -1 && mi > -1 && bi < mi, "blobgeom.js must load before the module main.js");
assert(bi > -1 && nsi > -1 && bi < nsi, "blobgeom.js must load before natural_selection.js");

// 5. BEHAVIOUR: load blobgeom.js + natural_selection.js as the browser does and
//    actually run renderPhotoreal against a recording canvas stub — proving the
//    ported draw code executes (substrate + membrane blobs + faces) without a
//    real browser. Catches runtime errors the structural regexes above cannot.
const rctx = (() => {
  const calls = {};
  const rec = (n) => () => { calls[n] = (calls[n] || 0) + 1; };
  return {
    _calls: calls,
    set fillStyle(v) {}, set strokeStyle(v) {}, set lineWidth(v) {},
    fillRect: rec("fillRect"), beginPath: rec("beginPath"), moveTo: rec("moveTo"),
    quadraticCurveTo: rec("quadraticCurveTo"), closePath: rec("closePath"),
    fill: rec("fill"), ellipse: rec("ellipse"), arc: rec("arc"), stroke: rec("stroke"),
  };
})();
try {
  const sb = {
    window: { CA: { RULES: {} } }, Math, console,
    Uint8Array, Uint16Array, Date, performance: { now: () => 4321 },
  };
  sb.CA = sb.window.CA;   // bare `CA` (rule's last line) resolves to window.CA in a real browser
  sb.globalThis = sb;
  vm.createContext(sb);
  vm.runInContext(read("experiment/blobgeom.js"), sb, { filename: "blobgeom.js" });
  vm.runInContext(read("experiment/rules/natural_selection.js"), sb, { filename: "natural_selection.js" });
  const factory = sb.window.CA.RULES["natural-selection"];
  assert(typeof factory === "function", "CA.RULES['natural-selection'] is not a factory");
  if (typeof factory === "function") {
    const rule = factory();
    assert(rule.hiRes === true && typeof rule.renderPhotoreal === "function",
      "natural-selection rule is missing the hiRes/renderPhotoreal living-colony surface");
    rule.reset();
    // Step until amoebas have formed (Phase-2 pair combination), capped.
    let amoebas = 0;
    for (let s = 0; s < 400 && amoebas === 0; s++) {
      rule.step();
      const m = /^(\d+)\s+amoebas/.exec(rule.population());
      amoebas = m ? +m[1] : 0;
    }
    assert(amoebas > 0, "no amoebas formed after 400 steps — cannot exercise the colony render");
    rule.renderPhotoreal(rctx, 720, 720);          // must not throw
    ok();
    assert((rctx._calls.fillRect || 0) > 0, "renderPhotoreal drew no substrate tiles (fillRect)");
    assert((rctx._calls.quadraticCurveTo || 0) > 0, "renderPhotoreal drew no membrane blobs (quadraticCurveTo)");
    assert((rctx._calls.ellipse || 0) > 0, "renderPhotoreal drew no faces (ellipse) at 9px cells");
    assert((rctx._calls.fill || 0) > 0, "renderPhotoreal never filled a shape");
  }
} catch (e) {
  fail(`renderPhotoreal behaviour test threw: ${String(e && e.stack || e).slice(0, 300)}`);
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
