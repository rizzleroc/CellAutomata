// web7 apparatus RUNTIME verification — run with three.js installed:
//   npm install three@0.162.0 --no-save && node docs/web7/tests/runtime.mjs
//
// The structural smoke test (smoke.mjs) is zero-dependency and gates the page
// statically. This one goes further: it executes every apparatus against the
// REAL three.js (geometry/material/mesh construction needs no WebGL — only
// rendering does) and runs the animation loop, catching runtime errors the
// regex checks can't — undefined vars, bad THREE calls, NaN positions, or an
// exception inside update()/a texture-draw callback.
//
// Skips gracefully (exit 0) if `three` isn't installed, so it never breaks a
// zero-dependency checkout; CI installs three before invoking it.

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.join(HERE, "..", "apparatus");

// Bail cleanly if three isn't available (keeps a bare checkout green).
try { await import("three"); }
catch { console.log("• three not installed — skipping runtime verification (install three@0.162.0 to enable)"); process.exit(0); }

// ── Headless browser stubs: canvas 2D + document, so makeDynamicTexture /
//    labelSprite / CanvasTexture work without WebGL. ──────────────────────────
const ctx2d = new Proxy({}, {
  get(_t, p) {
    if (p === "canvas") return { width: 256, height: 256 };
    if (p === "getImageData") return () => ({ data: new Uint8ClampedArray(256 * 256 * 4) });
    if (p === "createLinearGradient" || p === "createRadialGradient") return () => ({ addColorStop() {} });
    if (p === "measureText") return () => ({ width: 10 });
    return () => {};
  },
});
const fakeCanvas = () => ({ width: 256, height: 256, getContext: () => ctx2d, style: {} });
globalThis.document = { createElement: (t) => (t === "canvas" ? fakeCanvas() : { style: {} }) };
globalThis.window = { devicePixelRatio: 1, addEventListener() {}, location: { search: "" } };

const MODULES = [
  "miller_urey", "grayscott_dish", "raf_flask", "vesicle_microscope", "vent_reactor",
  "mineral_flask", "chirality_polarimeter", "rna_thermocycler", "code_bench",
  "coacervate_microscope", "microfluidic_chip", "luca_console", "stromatolite",
];
const isFiniteVec = (v) => v && [v.x, v.y, v.z].every(Number.isFinite);

let fails = 0;
console.log(`Running web7 apparatus runtime verification (${MODULES.length} apparatus)…\n`);
for (const name of MODULES) {
  try {
    const { meta } = await import(pathToFileURL(path.join(APP, `${name}.js`)).href);
    if (!meta || typeof meta.build !== "function") throw new Error("meta.build missing");

    const group = meta.build();
    if (!group?.isObject3D) throw new Error("build() did not return an Object3D");

    let named = 0, bad = null;
    group.traverse((o) => {
      if (o.isMesh && o.name) named++;
      if (o.isObject3D && !isFiniteVec(o.position)) bad = o.name || o.type;
    });
    if (bad) throw new Error(`non-finite position on "${bad}"`);
    if (named < 3) throw new Error(`only ${named} named meshes (expected ≥3)`);

    const anim = group.userData?.anim;
    for (const m of ["setRunning", "getProgress", "update"]) {
      if (typeof anim?.[m] !== "function") throw new Error(`anim.${m} is not a function`);
    }
    anim.setRunning(true);
    for (let i = 0; i < 60; i++) anim.update(0.016, i * 0.016);
    const p = anim.getProgress();
    if (!Number.isFinite(p)) throw new Error(`getProgress() returned ${p}`);
    anim.setRunning(false);
    for (let i = 0; i < 10; i++) anim.update(0.016, i * 0.016);
    if (typeof anim.reset === "function") anim.reset();

    group.traverse((o) => { if (o.isObject3D && !isFiniteVec(o.position)) bad = o.name || o.type; });
    if (bad) throw new Error(`position went non-finite after update: "${bad}"`);

    console.log(`  ✓ ${name.padEnd(24)} ${String(meta.id).padEnd(22)} ${named} meshes, progress→${p.toFixed(2)}`);
  } catch (e) {
    console.error(`  ✗ ${name}: ${e.message}`);
    fails++;
  }
}

console.log(`\n${MODULES.length - fails}/${MODULES.length} apparatus executed cleanly.`);
process.exit(fails ? 1 : 0);
