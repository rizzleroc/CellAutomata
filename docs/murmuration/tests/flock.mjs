// Murmuration — the SCIENCE gate. Zero-dependency: the engine is framework-free,
// so this runs the real simulation headlessly and asserts it behaves like a
// flock, not merely that it executes. Guards against the failure mode where a
// smoke test passes on garbage output:
//
//   - determinism: same seed ⇒ identical trajectories (reproducible science),
//   - ORDER emerges: polarization climbs from disorder toward alignment,
//   - the flock stays FINITE and BOUNDED (no bird escapes to infinity),
//   - spacing holds: nearest-neighbour distance tracks the personal-space knob,
//   - the flight envelope is respected (speed within [stall, max], near cruise),
//   - banking is real (birds roll to turn — the Flightsim signature),
//   - the peregrine SCATTERS the flock (radius spikes, polarization dips).
//
// Exits non-zero on the first hard failure so it gates CI.

import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const { Flock, defaultParams, PARAMS } = await import(pathToFileURL(path.join(HERE, '..', 'flock.js')).href);

let fails = 0, checks = 0;
const ok = () => { checks++; };
const fail = (m) => { fails++; console.error(`  ✗ ${m}`); };
const assert = (c, m) => (c ? ok() : fail(m));

console.log('Running Murmuration science gate…\n');

// helper: run a flock forward and return it
function run(params, steps, dt = 0.02, seed = 0xC0FFEE) {
  const f = new Flock(params, seed);
  for (let i = 0; i < steps; i++) f.step(dt);
  return f;
}
const allFinite = (f) => {
  for (let i = 0; i < f.n; i++)
    if (!Number.isFinite(f.px[i] + f.py[i] + f.pz[i] + f.vx[i] + f.vy[i] + f.vz[i])) return false;
  return true;
};

// 1. determinism — same seed, same run
{
  const a = run({ birds: 400 }, 200);
  const b = run({ birds: 400 }, 200);
  let same = true;
  for (let i = 0; i < a.n; i++) if (a.px[i] !== b.px[i] || a.vz[i] !== b.vz[i]) { same = false; break; }
  assert(same, 'not deterministic: identical seeds diverged');
}

// 2. order emerges — the LOCAL order parameter climbs out of initial disorder.
// (Global polarization is a poor test here: a flock wheeling around its roost
// has birds heading every way, so global |mean heading| stays low even when
// every bird is locally aligned. localOrder is the honest measure.)
{
  const f = new Flock({ birds: 1000 }, 0xC0FFEE);
  const loc0 = f.metrics.localOrder;
  for (let i = 0; i < 500; i++) f.step(0.02);
  const loc1 = f.metrics.localOrder;
  assert(loc0 < 0.3, `initial flock should be locally disordered (localOrder0=${loc0.toFixed(3)})`);
  assert(loc1 > 0.6, `flock failed to order (localOrder only ${loc1.toFixed(3)} after warmup)`);
  assert(loc1 > loc0 + 0.25, `local order did not rise meaningfully (${loc0.toFixed(3)}→${loc1.toFixed(3)})`);
}

// 3. finite + bounded — no bird escapes
{
  const f = run({ birds: 1200 }, 600);
  assert(allFinite(f), 'non-finite position/velocity somewhere in the flock');
  const B = f.params.boundary, cy = B * 0.2;
  let maxR = 0;
  for (let i = 0; i < f.n; i++) maxR = Math.max(maxR, Math.hypot(f.px[i], f.py[i] - cy, f.pz[i]));
  assert(maxR <= B * 1.45, `a bird escaped containment (max radius ${maxR.toFixed(1)} > ${(B * 1.45).toFixed(1)})`);
}

// 4. spacing holds — mean NN distance is in a sane band around personal space
{
  const f = run({ birds: 1500, sepRadius: 4 }, 500);
  const nn = f.metrics.nnDist;
  assert(nn > 1.5 && nn < 20, `nearest-neighbour distance out of band (${nn.toFixed(2)} m)`);
}

// 5. flight envelope — mean speed sits inside [stall, max], near cruise
{
  const f = run({ birds: 800 }, 500);
  const { speed } = f.metrics, P = f.params;
  assert(speed >= P.minSpeed && speed <= P.maxSpeed, `mean speed ${speed.toFixed(1)} outside [${P.minSpeed}, ${P.maxSpeed}]`);
  assert(Math.abs(speed - P.cruiseSpeed) < 6, `mean speed ${speed.toFixed(1)} far from cruise ${P.cruiseSpeed}`);
}

// 6. banking is real — a flocking bird rolls to turn (Flightsim signature)
{
  const f = run({ birds: 1000 }, 400);
  assert(f.metrics.bank > 3, `flock shows no banking (mean bank ${f.metrics.bank.toFixed(1)}° — birds aren't turning)`);
  assert(f.metrics.bank < 75, `implausible mean bank ${f.metrics.bank.toFixed(1)}°`);
}

// 7. the peregrine scatters the flock. RMS radius is the WRONG measure here —
// the whole flock flows away from the hunter, so its spread about its own
// (translating) centroid barely changes. The honest signatures are that local
// alignment collapses and the predator carves a VOID it can dive through.
{
  // calm steady-state local order, averaged post-warmup
  const cf = new Flock({ birds: 1000, predator: 0 }, 7);
  let cs = 0, cn = 0;
  for (let i = 0; i < 300; i++) { cf.step(0.033); if (i >= 140) { cs += cf.metrics.localOrder; cn++; } }
  const calmOrder = cs / cn;

  // let a flock order first, THEN unleash the predator so we isolate its effect
  const f = new Flock({ birds: 1000 }, 7);
  for (let i = 0; i < 140; i++) f.step(0.033);
  f.setParam('predator', 1); f.setParam('fear', 3.5); f.setParam('fearRadius', 30);
  let minOrder = 1, minNear = Infinity;
  for (let i = 0; i < 160; i++) {
    f.step(0.033);
    minOrder = Math.min(minOrder, f.metrics.localOrder);
    let near = 0;
    for (let k = 0; k < f.n; k++)
      if (Math.hypot(f.px[k] - f.pred.x, f.py[k] - f.pred.y, f.pz[k] - f.pred.z) < 12) near++;
    minNear = Math.min(minNear, near);
  }
  assert(calmOrder > 0.6, `calm flock not well-ordered (localOrder ${calmOrder.toFixed(2)}) — bad baseline`);
  assert(minOrder < calmOrder - 0.15, `predator did not disrupt alignment (order ${calmOrder.toFixed(2)}→${minOrder.toFixed(2)})`);
  assert(minNear <= 3, `predator carved no void — ${minNear} birds still crowd it (fear steer broken)`);
}

// 8. parameter schema is complete — the full real knob set + a big regime range
{
  const need = ['birds', 'viewRadius', 'fov', 'neighbors', 'separation', 'alignment',
    'cohesion', 'sepRadius', 'cruiseSpeed', 'maxSpeed', 'minSpeed', 'maxBank', 'predator'];
  const keys = new Set(PARAMS.map((p) => p.key));
  for (const k of need) assert(keys.has(k), `PARAMS missing required knob: ${k}`);
  const d = defaultParams();
  assert(Object.keys(d).length === PARAMS.length, 'defaultParams() does not cover every PARAM');
}

// 9. performance sanity — the engine keeps up at scale
{
  const f = new Flock({ birds: 2000 }, 1);
  const t0 = Date.now();
  for (let i = 0; i < 60; i++) f.step(0.016);
  const perStep = (Date.now() - t0) / 60;
  assert(perStep < 40, `too slow at 2000 birds: ${perStep.toFixed(1)} ms/step`);
  console.log(`    · 2000 birds → ${perStep.toFixed(1)} ms/step`);
}

console.log(`\n${checks} checks passed, ${fails} failure(s).`);
process.exit(fails ? 1 : 0);
