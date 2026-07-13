// web7 apparatus ANIMATION-RICHNESS verification — the "is the experiment
// actually running?" gate. Run with three installed:
//   npm install three@0.162.0 --no-save && node docs/web7/tests/anim.mjs
//
// runtime.mjs proves each apparatus BUILDS and its anim contract doesn't throw.
// This goes further: it proves that pressing "Run experiment" makes the scene
// VISIBLY CHANGE — bubbles rising, fluid filling, sparks/glows flickering, a
// micrograph field evolving, parts turning. A "static parts, no phenomenon"
// apparatus (the bug the user reported) fails here.
//
// We separate two kinds of motion:
//   • KINETIC  — transforms, light intensity, material colour/opacity/emissive.
//                This is the physical phenomenon a viewer feels (bubbling,
//                flow, glow, fill, rotation). Every apparatus must have some.
//   • TEXTURE  — CanvasTexture.version bumps (the evolving micrograph field).
//                Reported for info; can't substitute for kinetic motion.
// Primary gate: KINETIC over 90 running frames exceeds a floor.
// Calm gate:    after a short settle, idle kinetic motion is much less than
//               running — so "Run/Stop" is a real state, not always-on decor.
//
// Skips cleanly (exit 0) if three isn't installed, like runtime.mjs.

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.join(HERE, "..", "apparatus");

try { await import("three"); }
catch { console.log("• three not installed — skipping animation verification (install three@0.162.0 to enable)"); process.exit(0); }

// Headless browser stubs (same shape as runtime.mjs). CanvasTexture.version
// still increments on `needsUpdate = true`, so texture-driven animation is
// observable even though the 2-D drawing itself is a no-op.
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

await import("three");

const MODULES = [
  "miller_urey", "grayscott_dish", "raf_flask", "vesicle_microscope", "vent_reactor",
  "mineral_flask", "chirality_polarimeter", "rna_thermocycler", "code_bench",
  "coacervate_microscope", "microfluidic_chip", "luca_console", "stromatolite",
];
// Optional CLI filter (`node tests/anim.mjs mineral_flask`) so a builder can
// verify ONE apparatus in isolation while others are mid-edit.
const ONLY = process.argv[2];
const RUN = ONLY ? MODULES.filter((m) => m === ONLY) : MODULES;

// Two fingerprints of everything a viewer could perceive.
function signature(group) {
  const kin = [], tex = [];
  group.traverse((o) => {
    if (o.isObject3D) {
      const p = o.position, r = o.rotation, c = o.scale;
      kin.push(p.x, p.y, p.z, r.x, r.y, r.z, c.x, c.y, c.z, o.visible ? 1 : 0);
      if (o.isLight && typeof o.intensity === "number") kin.push(o.intensity * 0.5);
    }
    const mats = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
    for (const m of mats) {
      if (!m) continue;
      if (typeof m.opacity === "number") kin.push(m.opacity);
      if (m.color) kin.push(m.color.r, m.color.g, m.color.b);
      if (m.emissive) kin.push(m.emissive.r, m.emissive.g, m.emissive.b);
      if (typeof m.emissiveIntensity === "number") kin.push(m.emissiveIntensity);
      for (const slot of ["map", "emissiveMap", "alphaMap"]) {
        const t = m[slot];
        if (t && typeof t.version === "number") tex.push(t.version);
      }
    }
  });
  return { kin, tex };
}
const energy = (a, b) => {
  let e = 0; const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) e += Math.abs(a[i] - b[i]);
  return e;
};
function run(anim, frames, t0) {
  let t = t0;
  for (let i = 0; i < frames; i++) { t += 0.016; anim.update(0.016, t); }
  return t;
}

const KFLOOR = 0.4;          // minimum perceptible PHYSICAL motion while running (90 frames)
const SPECIMEN = new Set(["stromatolite"]);  // capstone hand-specimen: gentler floor
let fails = 0;
console.log(`Running web7 apparatus animation verification (${RUN.length} apparatus)…\n`);

for (const name of RUN) {
  try {
    const { meta } = await import(pathToFileURL(path.join(APP, `${name}.js`)).href);
    const group = meta.build();
    const anim = group.userData?.anim;
    if (!anim) throw new Error("no anim contract");

    if (typeof anim.reset === "function") anim.reset();
    anim.setRunning(true);
    let t = 0;
    const a = signature(group);
    t = run(anim, 90, t);
    const b = signature(group);
    const kinetic = energy(a.kin, b.kin);
    const texture = energy(a.tex, b.tex);

    // Stop, let it settle for 12 frames (hiding particles etc. is a one-off
    // transient, not ongoing animation), then measure idle kinetic motion.
    anim.setRunning(false);
    t = run(anim, 12, t);
    const c = signature(group);
    t = run(anim, 90, t);
    const d = signature(group);
    const idle = energy(c.kin, d.kin);

    const floor = SPECIMEN.has(name) ? KFLOOR * 0.5 : KFLOOR;
    const liveOk = kinetic > floor;
    const calmsOk = idle < kinetic * 0.5 + 0.02;   // Stop must meaningfully calm the phenomenon
    const tag = `kin=${kinetic.toFixed(2).padStart(8)}  tex=${String(texture).padStart(5)}  idle=${idle.toFixed(2).padStart(7)}`;
    if (!liveOk) { console.error(`  ✗ ${name.padEnd(24)} ${tag}  — no visible physical phenomenon (≤ floor ${floor})`); fails++; }
    else if (!calmsOk) { console.error(`  ✗ ${name.padEnd(24)} ${tag}  — Stop does not calm it (ignores running state)`); fails++; }
    else console.log(`  ✓ ${name.padEnd(24)} ${tag}`);
  } catch (e) {
    console.error(`  ✗ ${name}: ${e.message}`);
    fails++;
  }
}

console.log(`\n${RUN.length - fails}/${RUN.length} apparatus visibly run their experiment.`);
process.exit(fails ? 1 : 0);
