// Pond Water Analyzer — LOCOMOTION verification. Run with three installed:
//   npm install three@0.162.0 --no-save && node .../locomotion.mjs
//
// life.mjs proves each organism's *intrinsic* anim moves its organs. This gate
// proves the other half — that each species travels through the water with its
// real gait, not one shared drift. It drives every swimmer headlessly and
// asserts the behavioural SIGNATURE that a microscopist would recognise:
//   - run-tumble  : long straight runs punctuated by a few sharp re-orientations
//   - ciliate-helix: turns continuously but NEVER snaps (smooth spiral glide)
//   - hop-sink    : a bursty saw-tooth in height — repeated up-jerks then sinks
//   - all gaits   : stay finite + bounded to the field, move when running,
//                   and FREEZE when paused (Pause is a real state).
//
// Skips cleanly (exit 0) if three isn't installed, like life.mjs / the lab gate.

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const MOD = path.join(HERE, "..", "locomotion.js");
const ORG = path.join(HERE, "..", "organisms");

try { await import("three"); }
catch { console.log("• three not installed — skipping locomotion verification (install three@0.162.0 to enable)"); process.exit(0); }

const THREE = await import("three");
const { makeSwimmer, FIELD, GAIT_NAMES } = await import(pathToFileURL(MOD).href);

// A tiny seeded RNG so runs are reproducible (mulberry32).
function rng(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const DT = 0.016, STEPS = 320;
let fails = 0;
const check = (cond, msg) => { if (!cond) { console.error(`  ✗ ${msg}`); fails++; } };

// Run a swimmer, capturing per-step heading + position so we can profile it.
function run(kind, opts = {}) {
  const sw = makeSwimmer(kind, { rand: rng(opts.seed ?? 7), brownian: opts.brownian ?? 0, ...opts });
  const headings = [], ys = [], vys = [];
  let prev = sw.state.heading.clone();
  const turns = [];
  for (let i = 0; i < STEPS; i++) {
    sw.step(DT);
    const h = sw.state.heading.clone();
    turns.push(prev.angleTo(h));
    headings.push(h); ys.push(sw.state.pos.y); vys.push(sw.state.vel.y);
    prev = h;
  }
  return { sw, turns, ys, vys, pos: sw.state.pos.clone() };
}

console.log(`Running Pond Water Analyzer locomotion verification (${GAIT_NAMES.length} gaits)…\n`);

// ── 0. Every gait: finite, bounded to the field, and actually travels ────────
for (const kind of GAIT_NAMES) {
  const { pos } = run(kind, { seed: 3, brownian: kind === "run-tumble" ? 0.35 : 0 });
  check([pos.x, pos.y, pos.z].every(Number.isFinite), `${kind}: position went non-finite`);
  check(Math.abs(pos.x) < FIELD.x * 1.6 && Math.abs(pos.y) < FIELD.y * 1.6 && Math.abs(pos.z) < FIELD.z * 1.6,
    `${kind}: escaped the field (${pos.x.toFixed(1)},${pos.y.toFixed(1)},${pos.z.toFixed(1)})`);
  check(pos.length() > 0.05, `${kind}: never travelled from the origin`);
}

// ── 1. Pause is a real state: a paused swimmer does not move ──────────────────
for (const kind of GAIT_NAMES) {
  const sw = makeSwimmer(kind, { rand: rng(9) });
  sw.setRunning(false);
  const p0 = sw.state.pos.clone();
  for (let i = 0; i < 60; i++) sw.step(DT);
  check(sw.state.pos.distanceTo(p0) < 1e-9, `${kind}: moved while paused — Pause is not a real state`);
}

// ── 2. run-tumble: bimodal — long straight runs + a few sharp tumbles ─────────
{
  const { turns } = run("run-tumble", { seed: 5, brownian: 0 });
  const sharp = turns.filter((a) => a > 0.12).length;     // fast re-orientation steps = a tumble
  const straight = turns.filter((a) => a < 0.05).length;  // < ~3° = cruising a run
  check(sharp >= 3, `run-tumble: expected ≥3 sharp-turn tumble steps, got ${sharp}`);
  check(straight > STEPS * 0.4, `run-tumble: expected mostly-straight runs, only ${straight}/${STEPS} straight steps`);
}

// ── 3. ciliate-helix: turns continuously but never snaps ──────────────────────
{
  const { turns } = run("ciliate-helix", { seed: 5 });
  const maxTurn = Math.max(...turns);
  const total = turns.reduce((a, b) => a + b, 0);
  check(maxTurn < 0.35, `ciliate-helix: a snap turn of ${(maxTurn * 57.3).toFixed(0)}° — should glide smoothly`);
  check(total > 0.4, `ciliate-helix: barely turned (${(total * 57.3).toFixed(0)}° total) — should spiral`);
}

// ── 4. hop-sink: a bursty saw-tooth in height (repeated up-jerks, then sinks) ─
{
  const { vys } = run("hop-sink", { seed: 4 });
  // count power strokes: a step where upward velocity jumps by a real impulse
  let hops = 0;
  for (let i = 1; i < vys.length; i++) if (vys[i] - vys[i - 1] > 0.3) hops++;
  const sank = vys.filter((v) => v < -0.05).length;       // spends real time sinking
  check(hops >= 3, `hop-sink: expected ≥3 power-stroke hops, got ${hops}`);
  check(sank > STEPS * 0.2, `hop-sink: never sinks between hops (${sank} sinking steps) — not a saw-tooth`);
}

// ── 5. contrast: the ciliate glides far smoother than the bacterium tumbles ──
{
  const cil = run("ciliate-helix", { seed: 8 });
  const bac = run("run-tumble", { seed: 8 });
  check(Math.max(...bac.turns) > Math.max(...cil.turns) * 2,
    "run-tumble should turn far more sharply than the smooth ciliate glide");
}

// ── 5b. applyTo drives a real carrier group: position tracks, quaternion stays
//        finite and unit (this is exactly what main.js does each frame) ───────
{
  const carrier = new THREE.Group();
  const sw = makeSwimmer("run-tumble", { rand: rng(2), forwardAxis: new THREE.Vector3(0, 1, 0) });
  sw.applyTo(carrier, 1);
  for (let i = 0; i < 40; i++) { sw.step(DT); sw.applyTo(carrier); }
  carrier.updateMatrixWorld(true);
  check(carrier.position.distanceTo(new THREE.Vector3()) > 1e-3, "applyTo never moved the carrier group");
  const q = carrier.quaternion;
  check([q.x, q.y, q.z, q.w].every(Number.isFinite), "applyTo left a non-finite quaternion on the carrier");
  check(Math.abs(q.length() - 1) < 1e-3, "applyTo left a non-unit quaternion on the carrier");
}

// ── 6. every organism declares a gait this module implements ─────────────────
const ORGANISMS = ["bacterium", "paramecium", "rotifer", "tardigrade", "nematode", "daphnia"];
for (const name of ORGANISMS) {
  const { meta } = await import(pathToFileURL(path.join(ORG, `${name}.js`)).href);
  check(typeof meta.locomotion === "string" && GAIT_NAMES.includes(meta.locomotion),
    `${name}: meta.locomotion "${meta.locomotion}" is not an implemented gait`);
}

console.log(fails === 0
  ? `\n✓ all locomotion signatures verified (${GAIT_NAMES.length} gaits).`
  : `\n${fails} locomotion check(s) failed.`);
process.exit(fails ? 1 : 0);
