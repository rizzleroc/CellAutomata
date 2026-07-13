// Pond Water Analyzer — organism RUNTIME + anatomy verification. Run with
// three installed:  npm install three@0.162.0 --no-save && node .../life.mjs
//
// smoke.mjs gates the page statically. This executes every organism against
// the REAL three.js (geometry/material/mesh construction needs no WebGL) and:
//   - builds it, asserting a real Object3D with named internal meshes,
//   - checks the anatomy contract: an anim (setRunning/getProgress/update/
//     reset) AND a registered organ set (the thing the zoom engine reveals),
//   - runs the animation loop 90 frames and proves the creature VISIBLY MOVES
//     (organs displace/scale — a static specimen fails here) while every
//     position stays finite,
//   - confirms organ reveal-fractions span the dive (some gross-body organs at
//     ~0, some fine detail near 1) so "infinite zoom to organ level" has tiers.
//
// Skips cleanly (exit 0) if three isn't installed, like the lab's runtime gate.

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ORG = path.join(HERE, "..", "organisms");

try { await import("three"); }
catch { console.log("• three not installed — skipping life verification (install three@0.162.0 to enable)"); process.exit(0); }

// Headless browser stubs (canvas 2D + document/window) so CanvasTexture etc.
// construct without a GL context.
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

const ORGANISMS = ["bacterium", "paramecium", "rotifer", "tardigrade", "nematode", "daphnia"];
const ONLY = process.argv[2];
const RUN = ONLY ? ORGANISMS.filter((m) => m === ONLY) : ORGANISMS;
const isFiniteVec = (v) => v && [v.x, v.y, v.z].every(Number.isFinite);

let fails = 0;
console.log(`Running Pond Water Analyzer life verification (${RUN.length} organisms)…\n`);

for (const name of RUN) {
  try {
    const { meta } = await import(pathToFileURL(path.join(ORG, `${name}.js`)).href);
    if (!meta || typeof meta.build !== "function") throw new Error("meta.build missing");
    for (const f of ["id", "name", "taxon", "kingdom", "micronLength"]) {
      if (meta[f] === undefined) throw new Error(`meta.${f} missing`);
    }
    if (!(meta.micronLength > 0)) throw new Error(`micronLength must be > 0 (got ${meta.micronLength})`);

    const group = meta.build();
    if (!group?.isObject3D) throw new Error("build() did not return an Object3D");

    // named internal meshes — the organism is actually assembled from parts
    let named = 0, bad = null;
    group.traverse((o) => {
      if ((o.isMesh || o.isInstancedMesh) && o.name) named++;
      if (o.isObject3D && !isFiniteVec(o.position)) bad = o.name || o.type;
    });
    if (bad) throw new Error(`non-finite position on "${bad}"`);
    if (named < 3) throw new Error(`only ${named} named meshes (expected ≥3)`);

    // anim contract
    const anim = group.userData?.anim;
    for (const m of ["setRunning", "getProgress", "update", "reset"]) {
      if (typeof anim?.[m] !== "function") throw new Error(`anim.${m} is not a function`);
    }

    // organ registry — the thing the zoom engine reveals at organ level
    const organs = group.userData?.organs;
    if (!Array.isArray(organs) || organs.length < 3) throw new Error(`expected ≥3 registered organs, got ${organs?.length}`);
    let minRF = 1, maxRF = 0;
    for (const org of organs) {
      if (!org.object?.isObject3D) throw new Error(`organ "${org.name}" has no object`);
      if (typeof org.name !== "string" || !org.name) throw new Error("organ missing name");
      if (typeof org.blurb !== "string" || org.blurb.length < 8) throw new Error(`organ "${org.name}" has no real blurb`);
      if (!(org.revealFrac >= 0 && org.revealFrac <= 1)) throw new Error(`organ "${org.name}" revealFrac out of [0,1]: ${org.revealFrac}`);
      minRF = Math.min(minRF, org.revealFrac); maxRF = Math.max(maxRF, org.revealFrac);
    }
    if (minRF > 0.15) throw new Error("no gross-body organ near reveal 0 (nothing shows at organism scale)");
    if (maxRF < 0.4) throw new Error("no deep organ near reveal 1 (no organ-level tier to dive to)");

    // ── prove it VISIBLY MOVES: sample organ world-positions/scales, run the
    //    loop, and require meaningful displacement somewhere in the body ─────
    const probes = [];
    group.updateMatrixWorld(true);
    for (const org of organs) {
      const p = org.object.getWorldPosition(new (await import("three")).Vector3());
      probes.push({ obj: org.object, p0: p.clone(), s0: org.object.scale.clone() });
    }
    anim.setRunning(true);
    for (let i = 0; i < 90; i++) anim.update(0.016, i * 0.016);
    group.updateMatrixWorld(true);

    let motion = 0;
    const THREE = await import("three");
    for (const pr of probes) {
      const p1 = pr.obj.getWorldPosition(new THREE.Vector3());
      motion += p1.distanceTo(pr.p0);
      motion += Math.abs(pr.obj.scale.x - pr.s0.x) + Math.abs(pr.obj.scale.y - pr.s0.y);
    }
    if (!(motion > 1e-3)) throw new Error("organism is static — no organ moved over 90 running frames");

    const prog = anim.getProgress();
    if (!Number.isFinite(prog)) throw new Error(`getProgress() returned ${prog}`);

    // calm gate: paused, motion is far less than when running
    anim.setRunning(false);
    group.updateMatrixWorld(true);
    const rest = organs.map((o) => o.object.getWorldPosition(new THREE.Vector3()));
    for (let i = 0; i < 30; i++) anim.update(0, i * 0.016);
    group.updateMatrixWorld(true);
    let idle = 0;
    organs.forEach((o, i) => { idle += o.object.getWorldPosition(new THREE.Vector3()).distanceTo(rest[i]); });
    if (idle > motion) throw new Error("paused organism moves as much as running — Pause is not a real state");

    anim.reset();
    group.traverse((o) => { if (o.isObject3D && !isFiniteVec(o.position)) bad = o.name || o.type; });
    if (bad) throw new Error(`position went non-finite after update: "${bad}"`);

    console.log(`  ✓ ${name.padEnd(12)} ${String(meta.taxon).padEnd(22)} ${named} meshes, ${organs.length} organs, reveal ${minRF.toFixed(2)}–${maxRF.toFixed(2)}, motion ${motion.toFixed(3)}`);
  } catch (e) {
    console.error(`  ✗ ${name}: ${e.message}`);
    fails++;
  }
}

console.log(`\n${RUN.length - fails}/${RUN.length} organisms verified.`);
process.exit(fails ? 1 : 0);
