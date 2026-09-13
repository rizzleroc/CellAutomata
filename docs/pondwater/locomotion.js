// Pond Water Analyzer — locomotion.
//
// The organism builders animate *intrinsic* motion (cilia beating, a heart
// beating, the nematode's S-wave). This module animates the other half of what
// sells a live wet-mount: how the whole animal *travels through the water*.
// Real microfauna do not all drift the same way — each taxon has a signature
// gait, and a microscopist recognises the organism as much by how it moves as
// by how it looks:
//
//   • run-tumble  (bacterium) — straight, flagellum-driven "runs" punctuated by
//     abrupt random re-orientations, the whole cell quivering with Brownian
//     buffeting (real at that size).
//   • ciliate-helix (paramecium) — a smooth forward glide that spirals as the
//     cell rolls on its long axis, with the occasional "avoiding reaction".
//   • hop-sink   (daphnia) — the jerk-upward-then-sink saw-tooth that literally
//     names the "water flea": an antennal power-stroke throws it forward/up,
//     then it sinks passively under gravity + drag.
//   • undulate   (nematode) — slow, meandering net progress along the thrash.
//   • creep      (rotifer)  — slow gliding broken by long anchored pauses (it
//     grips the substrate with its foot to feed).
//   • crawl      (tardigrade) — a very slow lobopod bumble with pauses.
//
// A swimmer owns a `pos` and a unit `heading`; each step advances them by its
// gait. `applyTo(carrier)` writes the pose onto the organism's carrier group
// (position + a heading-aligned, slerp-smoothed orientation), so the intrinsic
// anim keeps running in the carrier's frame. Pure (imports only three) so the
// headless test harness can drive it and assert each gait's signature.

import * as THREE from 'three';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const DEFAULT_FWD = V(1, 0, 0);
const _q = new THREE.Quaternion();

// The drop field half-extents — matches the sample box main.js spawns into.
export const FIELD = { x: 15, y: 11, z: 15 };

// A cheap approximately-normal deviate (sum of uniforms), for wander/Brownian.
function gauss(rand) {
  return rand() + rand() + rand() + rand() + rand() + rand() - 3;
}
// Uniform direction on the unit sphere.
function randUnit(rand) {
  const u = rand() * 2 - 1, th = rand() * Math.PI * 2;
  const r = Math.sqrt(Math.max(0, 1 - u * u));
  return V(r * Math.cos(th), u, r * Math.sin(th));
}
// Steer a direction/velocity vector back toward the field centre as `pos`
// nears a wall — organisms turn away from the coverslip, they don't teleport.
// Returns how hard it was pushed (0 = free water) so a gait can react (a
// bacterium tumbles off the wall, a paramecium fires an avoiding reaction).
function contain(pos, vec, dt, gain) {
  let hit = 0;
  for (const ax of ['x', 'y', 'z']) {
    const lim = FIELD[ax], soft = lim * 0.72;
    const over = Math.abs(pos[ax]) - soft;
    if (over > 0) {
      const f = (over / (lim - soft));
      vec[ax] -= Math.sign(pos[ax]) * f * gain * dt * 3;
      hit = Math.max(hit, f);
    }
  }
  return hit;
}

// ── Gaits ───────────────────────────────────────────────────────────────────
// Each mutates state.pos and state.heading (and, for hop-sink, state.vel).
const GAITS = {
  // Straight runs + abrupt tumbles; the tiny cell also visibly quivers.
  'run-tumble'(s, dt) {
    const RUN = 0.95 * s.speedScale;
    if (s.tumbling > 0) {
      s.tumbling -= dt;
      s.heading.lerp(s._to, Math.min(1, dt * 14)).normalize();
    } else {
      s.runTimer -= dt;
      const wall = contain(s.pos, s.heading, dt, 1.4);
      if (s.runTimer <= 0 || wall > 0.6) {
        s.tumbling = 0.12 + s.rand() * 0.06;
        s.runTimer = 0.5 + s.rand() * 1.6;
        s._to = randUnit(s.rand);
      } else {
        s.heading.x += gauss(s.rand) * dt * 0.15;
        s.heading.y += gauss(s.rand) * dt * 0.15;
        s.heading.z += gauss(s.rand) * dt * 0.15;
        s.heading.normalize();
      }
    }
    const spd = s.tumbling > 0 ? RUN * 0.2 : RUN;
    s.pos.addScaledVector(s.heading, spd * dt);
    // Brownian buffeting — a real hallmark of a micron-scale swimmer.
    const bj = s.brownian * Math.sqrt(dt);
    s.pos.x += gauss(s.rand) * bj;
    s.pos.y += gauss(s.rand) * bj;
    s.pos.z += gauss(s.rand) * bj;
  },

  // Smooth forward glide with slowly-curving heading (a broad helix through the
  // field), and an occasional avoiding reaction (back up + swing to a new line).
  'ciliate-helix'(s, dt) {
    const SPD = 0.7 * s.speedScale;
    if (s.avoid > 0) {
      s.avoid -= dt;
      s.pos.addScaledVector(s.heading, -SPD * 0.5 * dt);       // back-paddle
      s.heading.lerp(s._to, Math.min(1, dt * 5)).normalize();  // swing, not snap
    } else {
      const turn = dt * 0.9;
      s.heading.x += Math.sin(s.t * 0.7) * turn * 0.5;
      s.heading.y += Math.cos(s.t * 0.5 + 1) * turn * 0.5;
      s.heading.z += Math.sin(s.t * 0.9 + 2) * turn * 0.5;
      s.heading.normalize();
      s.pos.addScaledVector(s.heading, SPD * dt);
      s.avoidTimer -= dt;
      const wall = contain(s.pos, s.heading, dt, 1.1);
      if (s.avoidTimer <= 0 || wall > 0.5) {
        s.avoid = 0.4; s._to = randUnit(s.rand);
        s.avoidTimer = 3 + s.rand() * 4;
      }
    }
  },

  // Slow sinuous meander — the body does the visible thrash; the path drifts.
  'undulate'(s, dt) {
    const SPD = 0.5 * s.speedScale;
    s.heading.x += Math.sin(s.t * 1.1) * dt * 0.28;
    s.heading.y += Math.sin(s.t * 0.8 + 2) * dt * 0.20;
    s.heading.z += Math.cos(s.t * 0.6) * dt * 0.22;
    s.heading.normalize();
    s.pos.addScaledVector(s.heading, SPD * dt);
    contain(s.pos, s.heading, dt, 1.1);
  },

  // Slow glide broken by long anchored pauses (the foot grips to feed).
  'creep'(s, dt) {
    const SPD = 0.34 * s.speedScale;
    if (s.pauseTimer > 0) {
      s.pauseTimer -= dt;
      s.pos.addScaledVector(s.heading, SPD * 0.04 * dt);
    } else {
      s.heading.x += gauss(s.rand) * dt * 0.2;
      s.heading.y += gauss(s.rand) * dt * 0.2;
      s.heading.z += gauss(s.rand) * dt * 0.2;
      s.heading.normalize();
      s.pos.addScaledVector(s.heading, SPD * dt);
      s.moveTimer -= dt;
      if (s.moveTimer <= 0) { s.pauseTimer = 0.8 + s.rand() * 2; s.moveTimer = 2 + s.rand() * 3; }
    }
    contain(s.pos, s.heading, dt, 1.0);
  },

  // A very slow lobopod bumble, with pauses.
  'crawl'(s, dt) {
    const SPD = 0.2 * s.speedScale;
    if (s.pauseTimer > 0) {
      s.pauseTimer -= dt;
    } else {
      s.heading.x += gauss(s.rand) * dt * 0.15;
      s.heading.y += gauss(s.rand) * dt * 0.10;
      s.heading.z += gauss(s.rand) * dt * 0.15;
      s.heading.normalize();
      s.pos.addScaledVector(s.heading, SPD * dt);
      s.moveTimer -= dt;
      if (s.moveTimer <= 0) { s.pauseTimer = 0.6 + s.rand() * 1.5; s.moveTimer = 2 + s.rand() * 3; }
    }
    contain(s.pos, s.heading, dt, 0.9);
  },

  // Antennal power-stroke → a reliably UPWARD-and-forward impulse (the antennae
  // push the animal up whichever way it is currently drifting); then a passive
  // sink under gravity + water drag. The signature saw-tooth of the water flea.
  // `swimDir` holds the near-horizontal travel line; `heading` (the visible
  // nose) follows the true velocity, so it pitches up on the jump and noses down
  // as it sinks — exactly as a Daphnia does under the scope.
  'hop-sink'(s, dt) {
    const GRAV = 0.9, DRAG = 1.6, IMP = 1.9 * s.speedScale;
    if (!s.swimDir) {
      s.swimDir = s.heading.clone(); s.swimDir.y *= 0.2;
      if (s.swimDir.lengthSq() < 1e-4) s.swimDir.set(1, 0, 0);
      s.swimDir.normalize();
    }
    s.hopTimer -= dt;
    if (s.hopTimer <= 0) {
      // strong world-up + a forward lean along the (horizontal) travel line
      const dir = s.swimDir.clone().multiplyScalar(0.7); dir.y += 1.0; dir.normalize();
      s.vel.addScaledVector(dir, IMP);
      s.hopTimer = 0.8 + s.rand() * 0.6;
      if (s.rand() < 0.5) {                       // re-aim the next hop's line (stays horizontal)
        const a = s.rand() * Math.PI * 2;
        s.swimDir.lerp(V(Math.cos(a), s.swimDir.y * 0.5, Math.sin(a)), 0.4).normalize();
      }
    }
    s.vel.y -= GRAV * dt;                          // sink
    s.vel.multiplyScalar(Math.max(0, 1 - DRAG * dt));
    contain(s.pos, s.vel, dt, 2.0);               // bounce the velocity, not the heading
    contain(s.pos, s.swimDir, dt, 1.0); s.swimDir.normalize();
    s.pos.addScaledVector(s.vel, dt);
    if (s.vel.lengthSq() > 1e-4) s.heading.copy(s.vel).normalize();  // nose follows travel
  },

  // Fallback: gentle isotropic random walk (also used if a gait is unknown).
  drift(s, dt) {
    s.heading.x += gauss(s.rand) * dt * 0.3;
    s.heading.y += gauss(s.rand) * dt * 0.3;
    s.heading.z += gauss(s.rand) * dt * 0.3;
    s.heading.normalize();
    s.pos.addScaledVector(s.heading, 0.4 * s.speedScale * dt);
    contain(s.pos, s.heading, dt, 1.0);
  },
};

export const GAIT_NAMES = Object.keys(GAITS);

// Build a swimmer for `kind`. `rand` seeds the per-instance timers/directions so
// a re-drawn sample is reproducible; `forwardAxis` is the organism's own "nose"
// axis (default +x; the rotifer swims corona-first, +y).
export function makeSwimmer(kind, {
  rand = Math.random, start = V(), heading = null,
  forwardAxis = DEFAULT_FWD, speedScale = 1, brownian = 0,
} = {}) {
  const s = {
    kind,
    pos: start.clone(),
    heading: (heading ? heading.clone() : randUnit(rand)).normalize(),
    vel: V(),
    running: true,
    t: 0,
    rand, speedScale, brownian,
    forwardAxis: forwardAxis.clone().normalize(),
    // gait timers (each gait reads only the ones it needs)
    runTimer: 0.4 + rand() * 1.2,
    tumbling: 0,
    avoid: 0,
    avoidTimer: 2 + rand() * 4,
    hopTimer: 0.3 + rand() * 0.8,
    pauseTimer: 0,
    moveTimer: 2 + rand() * 3,
    _to: null,
  };
  s._to = s.heading.clone();
  const gait = GAITS[kind] || GAITS.drift;
  let inited = false;

  return {
    state: s,
    setRunning(v) { s.running = v; },
    step(dt) {
      if (!s.running || !(dt > 0)) return s;
      s.t += dt;
      gait(s, dt);
      if (!(s.heading.lengthSq() > 1e-8)) s.heading.set(1, 0, 0);  // NaN/zero guard
      return s;
    },
    // Write the pose onto a carrier group. Orientation slerps toward the heading
    // so turns read as real turning; the first apply snaps (spawn pose).
    applyTo(carrier, k = 0.12) {
      carrier.position.copy(s.pos);
      _q.setFromUnitVectors(s.forwardAxis, s.heading);
      if (inited) carrier.quaternion.slerp(_q, k);
      else { carrier.quaternion.copy(_q); inited = true; }
    },
  };
}
