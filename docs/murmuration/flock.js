// Murmuration — the flocking engine.
//
// This is a faithful re-implementation of the model in Rama Hoetzlein's
// *Flock2: A model for orientation-based social flocking* (J. Theor. Biol.
// 2024, arXiv:2404.17804), adapted to run in the browser at interactive
// scale. Two ideas make it "Flock2" rather than a classic Reynolds boid:
//
//   1. ORIENTATION-BASED SOCIAL FLOCKING.  A bird does not sum avoidance /
//      alignment / cohesion into an acceleration vector. It reads its
//      neighbours through a limited visual field and forms a single *desired
//      heading* — a wish to TURN. Social pressure controls orientation, never
//      acceleration directly.
//
//   2. FLIGHTSIM — a single-body fixed-wing aerodynamic model.  The wish to
//      turn is realised the way a bird actually turns: it BANKS. Rolling tips
//      the lift vector sideways; the horizontal component curves the path, the
//      vertical component shrinks, so a banked bird sinks (altitude loss in
//      turns). Lift, gravity, thrust and drag are integrated every step, so
//      birds speed up in dives, slow climbing, and stall if pushed past the
//      critical angle of attack. These are the behaviours the paper highlights,
//      and they emerge here rather than being scripted.
//
// The engine is deliberately framework-free — plain Float32 arrays, no three,
// no DOM — so it runs unchanged under the headless `tests/flock.mjs` science
// gate and inside the WebGL client. `main.js` reads the state arrays each
// frame to drive an InstancedMesh; the tests read them to assert the physics.
//
// State is Structure-of-Arrays for cache-friendliness, neighbour queries go
// through a uniform spatial hash (O(n) per step), and a seeded mulberry32 RNG
// matches the determinism convention used elsewhere in this repo.

// ── seeded RNG (mulberry32) ────────────────────────────────────────────────
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ── the parameter schema — every knob the model exposes ─────────────────────
// Each entry drives the control panel AND documents the default. Groups keep
// the UI legible: the social rules, the flight envelope, the world, the hunter.
export const PARAMS = [
  // — flock size —
  { key: 'birds',        group: 'Flock',   label: 'Birds',            min: 50,   max: 4000, step: 50,   value: 1200, unit: '' },

  // — orientation-based social rules (all are *turning* pressures) —
  { key: 'viewRadius',   group: 'Vision',  label: 'Vision radius',    min: 4,    max: 40,   step: 0.5,  value: 16,   unit: 'm' },
  { key: 'fov',          group: 'Vision',  label: 'Field of view',    min: 120,  max: 360,  step: 5,    value: 300,  unit: '°' },
  { key: 'neighbors',    group: 'Vision',  label: 'Interaction cap',  min: 3,    max: 20,   step: 1,    value: 7,    unit: '' },
  { key: 'separation',   group: 'Rules',   label: 'Separation',       min: 0,    max: 3,    step: 0.05, value: 1.5,  unit: '' },
  { key: 'alignment',    group: 'Rules',   label: 'Alignment',        min: 0,    max: 3,    step: 0.05, value: 1.1,  unit: '' },
  { key: 'cohesion',     group: 'Rules',   label: 'Cohesion',         min: 0,    max: 3,    step: 0.05, value: 1.6,  unit: '' },
  { key: 'sepRadius',    group: 'Rules',   label: 'Personal space',   min: 1,    max: 12,   step: 0.25, value: 4,    unit: 'm' },
  { key: 'boundary',     group: 'World',   label: 'Roost radius',     min: 40,   max: 220,  step: 5,    value: 110,  unit: 'm' },
  { key: 'boundaryPull', group: 'World',   label: 'Roost pull',       min: 0,    max: 3,    step: 0.05, value: 1.0,  unit: '' },
  { key: 'wind',         group: 'World',   label: 'Wind',             min: 0,    max: 8,    step: 0.25, value: 0,    unit: 'm/s' },

  // — Flightsim aerodynamic envelope (single-body fixed-wing) —
  { key: 'cruiseSpeed',  group: 'Flight',  label: 'Cruise speed',     min: 6,    max: 24,   step: 0.5,  value: 12,   unit: 'm/s' },
  { key: 'maxSpeed',     group: 'Flight',  label: 'Max speed',        min: 12,   max: 40,   step: 1,    value: 22,   unit: 'm/s' },
  { key: 'minSpeed',     group: 'Flight',  label: 'Stall speed',      min: 3,    max: 12,   step: 0.5,  value: 7,    unit: 'm/s' },
  { key: 'maxBank',      group: 'Flight',  label: 'Max bank',         min: 15,   max: 75,   step: 1,    value: 45,   unit: '°' },
  { key: 'agility',      group: 'Flight',  label: 'Agility',          min: 0.3,  max: 4,    step: 0.05, value: 1.6,  unit: '' },
  { key: 'liftComp',     group: 'Flight',  label: 'Turn lift comp.',  min: 0,    max: 1,    step: 0.02, value: 0.5,  unit: '' },
  { key: 'power',        group: 'Flight',  label: 'Wing power',       min: 0.2,  max: 4,    step: 0.05, value: 1.4,  unit: '' },

  // — the hunter —
  { key: 'predator',     group: 'Hunter',  label: 'Peregrine',        min: 0,    max: 1,    step: 1,    value: 0,    unit: '', bool: true },
  { key: 'fear',         group: 'Hunter',  label: 'Fear',             min: 0,    max: 6,    step: 0.1,  value: 3,    unit: '' },
  { key: 'fearRadius',   group: 'Hunter',  label: 'Fear radius',      min: 8,    max: 60,   step: 1,    value: 28,   unit: 'm' },
];

export function defaultParams() {
  const p = {};
  for (const d of PARAMS) p[d.key] = d.value;
  return p;
}

// Fixed physical constants of the single-body flight model. These are the
// starling's airframe (Sturnus vulgaris, ~80 g) — deliberately not exposed as
// sliders because they define *what a bird is*, not how the flock behaves.
const AIR = {
  rho: 1.225,       // air density, kg/m³
  mass: 0.08,       // bird mass, kg (an 80 g starling)
  wingArea: 0.024,  // reference wing area, m²
  gravity: 9.81,    // m/s²
  clMax: 1.3,       // maximum lift coefficient — the stall ceiling
  cd0: 0.028,       // parasite drag coefficient
  inducedK: 0.045,  // induced-drag factor (drag ∝ Cl²)
};

// small vec3 scratch helpers on flat arrays -----------------------------------
const clamp = (x, lo, hi) => (x < lo ? lo : x > hi ? hi : x);

export class Flock {
  constructor(params = {}, seed = 0x9e3779b9) {
    this.params = { ...defaultParams(), ...params };
    this.rng = mulberry32(seed);
    this.time = 0;
    this.metrics = { polarization: 0, localOrder: 0, speed: 0, nnDist: 0, bank: 0, stalls: 0, centroid: [0, 0, 0], radius: 0 };
    // the hunter's state (a diving peregrine); inert until `predator` is on
    this.pred = { x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, active: false };
    this._alloc(this.params.birds);
    this.reset();
  }

  _alloc(n) {
    this.n = n | 0;
    this.px = new Float32Array(n); this.py = new Float32Array(n); this.pz = new Float32Array(n);
    this.vx = new Float32Array(n); this.vy = new Float32Array(n); this.vz = new Float32Array(n);
    this.bank = new Float32Array(n);     // current roll angle (rad) — for rendering
    this.phase = new Float32Array(n);    // wing-flap phase offset
    this.stalled = new Uint8Array(n);
  }

  // Re-seed the whole flock into a loose sphere around the roost, all birds
  // cruising in randomised headings. Resizes arrays if the bird count changed.
  reset() {
    if ((this.params.birds | 0) !== this.n) this._alloc(this.params.birds | 0);
    const r = this.rng, R = this.params.boundary * 0.5, s = this.params.cruiseSpeed;
    for (let i = 0; i < this.n; i++) {
      // uniform-ish point in a ball
      const u = r(), v = r(), w = r();
      const rad = R * Math.cbrt(r());
      const th = 2 * Math.PI * u, ph = Math.acos(2 * v - 1);
      this.px[i] = rad * Math.sin(ph) * Math.cos(th);
      this.py[i] = rad * Math.cos(ph) * 0.5 + this.params.boundary * 0.15; // sit a touch high
      this.pz[i] = rad * Math.sin(ph) * Math.sin(th);
      // random heading, mostly horizontal
      const hd = 2 * Math.PI * w, pitch = (r() - 0.5) * 0.4;
      this.vx[i] = s * Math.cos(pitch) * Math.cos(hd);
      this.vy[i] = s * Math.sin(pitch);
      this.vz[i] = s * Math.cos(pitch) * Math.sin(hd);
      this.bank[i] = 0;
      this.phase[i] = r() * Math.PI * 2;
      this.stalled[i] = 0;
    }
    this.time = 0;
    this._resetPredator();
    this._measure();
  }

  _resetPredator() {
    const B = this.params.boundary;
    this.pred.x = B * 1.1; this.pred.y = B * 0.4; this.pred.z = 0;
    this.pred.vx = -this.params.maxSpeed; this.pred.vy = 0; this.pred.vz = 0;
    this.pred.active = !!this.params.predator;
  }

  setParam(key, value) {
    this.params[key] = value;
    if (key === 'birds' && (value | 0) !== this.n) this.reset();
    if (key === 'predator') { this.pred.active = !!value; if (value) this._resetPredator(); }
  }

  // Apply a whole preset param-set at once, reseeding only if the count moved.
  applyParams(p) {
    const countChanged = (p.birds | 0) && (p.birds | 0) !== this.n;
    Object.assign(this.params, p);
    if (countChanged) this.reset();
    this.pred.active = !!this.params.predator;
  }

  // ── one integration step ──────────────────────────────────────────────────
  // dt is real seconds; we sub-step so the flight model stays stable when the
  // frame is long or the birds are agile.
  step(dt) {
    const sub = dt > 0.02 ? 2 : 1;
    const h = dt / sub;
    for (let s = 0; s < sub; s++) this._integrate(h);
    this.time += dt;
    this._measure();
  }

  _integrate(dt) {
    const P = this.params, n = this.n;
    const grid = this._buildGrid();
    const head = grid.head, next = grid.next;

    const view2 = P.viewRadius * P.viewRadius;
    const sep2 = P.sepRadius * P.sepRadius;
    const cosFov = Math.cos((P.fov * Math.PI / 180) / 2);
    const maxBank = P.maxBank * Math.PI / 180;
    const A = AIR;

    // hunter integrates first so birds react to its new position this step
    if (this.pred.active) this._stepPredator(dt);

    // accumulate the LOCAL order parameter — mean over birds of how aligned
    // their neighbourhood is. Unlike global polarization (which a wheeling
    // roost flock drives near zero), this stays high whenever birds are locally
    // coherent, so it is the honest "is this a flock?" measure.
    let sumLocal = 0, nLocal = 0;

    for (let i = 0; i < n; i++) {
      const pxi = this.px[i], pyi = this.py[i], pzi = this.pz[i];
      let vxi = this.vx[i], vyi = this.vy[i], vzi = this.vz[i];
      let sp = Math.hypot(vxi, vyi, vzi) || 1e-4;
      const fx = vxi / sp, fy = vyi / sp, fz = vzi / sp; // forward (heading)

      // — perceive neighbours through the spatial hash + visual field —
      // topological cap: keep only the `neighbors` nearest that fall inside the
      // field of view (starlings interact with ~7 neighbours regardless of
      // density — Ballerini et al. 2008).
      let sepX = 0, sepY = 0, sepZ = 0;           // avoidance (push away, 1/d)
      let aliX = 0, aliY = 0, aliZ = 0;           // mean neighbour heading
      let cohX = 0, cohY = 0, cohZ = 0;           // mean neighbour position
      let count = 0;

      const cx = Math.floor(pxi / grid.size), cy = Math.floor(pyi / grid.size), cz = Math.floor(pzi / grid.size);
      for (let dx = -1; dx <= 1; dx++)
        for (let dy = -1; dy <= 1; dy++)
          for (let dz = -1; dz <= 1; dz++) {
            const c = grid.hash(cx + dx, cy + dy, cz + dz);
            for (let j = head[c]; j !== -1; j = next[j]) {
              if (j === i) continue;
              const rx = this.px[j] - pxi, ry = this.py[j] - pyi, rz = this.pz[j] - pzi;
              const d2 = rx * rx + ry * ry + rz * rz;
              if (d2 > view2 || d2 < 1e-6) continue;
              const d = Math.sqrt(d2);
              // visual field: neighbour must be within the FOV cone
              if ((rx * fx + ry * fy + rz * fz) / d < cosFov) continue;
              count++;
              // cohesion: toward neighbour centroid
              cohX += this.px[j]; cohY += this.py[j]; cohZ += this.pz[j];
              // alignment: sum neighbour headings
              const njs = Math.hypot(this.vx[j], this.vy[j], this.vz[j]) || 1e-4;
              aliX += this.vx[j] / njs; aliY += this.vy[j] / njs; aliZ += this.vz[j] / njs;
              // separation: only for the too-close, weighted by 1/d
              if (d2 < sep2) { const inv = 1 / d; sepX -= rx * inv; sepY -= ry * inv; sepZ -= rz * inv; }
            }
          }

      // — assemble the desired heading (a wish to turn, not a force) —
      let dxh = fx, dyh = fy, dzh = fz;  // default: hold course
      if (count > 0) {
        // cohesion vector: from me to the neighbour centroid
        cohX = cohX / count - pxi; cohY = cohY / count - pyi; cohZ = cohZ / count - pzi;
        const cl = Math.hypot(cohX, cohY, cohZ) || 1; cohX /= cl; cohY /= cl; cohZ /= cl;
        const al = Math.hypot(aliX, aliY, aliZ) || 1;
        sumLocal += Math.hypot(aliX, aliY, aliZ) / count; nLocal++;   // neighbourhood alignment ∈ [0,1]
        aliX /= al; aliY /= al; aliZ /= al;
        const sl = Math.hypot(sepX, sepY, sepZ); if (sl > 0) { sepX /= sl; sepY /= sl; sepZ /= sl; }
        dxh = fx + P.alignment * aliX + P.cohesion * cohX + P.separation * sepX;
        dyh = fy + P.alignment * aliY + P.cohesion * cohY + P.separation * sepY;
        dzh = fz + P.alignment * aliZ + P.cohesion * cohZ + P.separation * sepZ;
      }

      // — soft roost containment: turn back when leaving the boundary sphere.
      // Starts well inside the edge (0.6 R) so a bird has room to complete its
      // turn radius before it breaches, and grows sharply past the rim.
      const oy = pyi - P.boundary * 0.2;
      const rr = Math.hypot(pxi, oy, pzi);
      if (rr > P.boundary * 0.6) {
        const t = (rr - P.boundary * 0.6) / (P.boundary * 0.4);
        const k = P.boundaryPull * (t * t) * 3.5;
        dxh -= (pxi / rr) * k; dyh -= (oy / rr) * k; dzh -= (pzi / rr) * k;
      }

      // — predator terror: a strong steer directly away, scaled by nearness —
      if (this.pred.active) {
        const ex = pxi - this.pred.x, ey = pyi - this.pred.y, ez = pzi - this.pred.z;
        const ed = Math.hypot(ex, ey, ez);
        if (ed < P.fearRadius && ed > 1e-3) {
          const k = P.fear * (1 - ed / P.fearRadius);
          dxh += (ex / ed) * k; dyh += (ey / ed) * k; dzh += (ez / ed) * k;
        }
      }

      // — wind biases the desired heading slightly (birds head into it) —
      if (P.wind > 0) dxh -= P.wind * 0.03;

      // normalise the desired heading
      const dl = Math.hypot(dxh, dyh, dzh) || 1; dxh /= dl; dyh /= dl; dzh /= dl;

      // ── Flightsim: realise the turn by banking, then integrate forces ──────
      // Build the body frame. right = fwd × worldUp = (fz, 0, −fx); up = right × fwd.
      let rxv = fz, ryv = 0, rzv = -fx;
      let rl = Math.hypot(rxv, ryv, rzv);
      if (rl < 1e-4) { rxv = 1; ryv = 0; rzv = 0; rl = 1; } // near-vertical: pick arbitrary right
      rxv /= rl; ryv /= rl; rzv /= rl;
      // up = right × fwd
      const uxv = ryv * fz - rzv * fy, uyv = rzv * fx - rxv * fz, uzv = rxv * fy - ryv * fx;

      // how far off-heading is the desire, split into lateral (turn) & vertical
      const latR = dxh * rxv + dyh * ryv + dzh * rzv;   // want-to-turn-right amount [-1,1]
      const latU = dxh * uxv + dyh * uyv + dzh * uzv;   // want-to-climb amount

      // commanded bank ∝ lateral demand, capped; agility scales the response
      const bankCmd = clamp(P.agility * latR * 2.2, -1, 1) * maxBank;
      // ease the roll toward the command (birds can't snap-roll)
      this.bank[i] += (bankCmd - this.bank[i]) * clamp(P.agility * dt * 6, 0, 1);
      const roll = this.bank[i];

      // — lift — the airframe pulls the required load, but only partly
      // compensates for the bank (liftComp<1 ⇒ the classic altitude loss).
      const q = 0.5 * A.rho * sp * sp * A.wingArea;    // dynamic pressure × area
      const clLevel = (A.mass * A.gravity) / (q || 1e-4);
      const loadFactor = 1 + P.liftComp * (1 / Math.max(0.25, Math.cos(roll)) - 1)
                           + latU * 0.6;               // pitch demand adds load
      let cl = clLevel * loadFactor;
      const stalled = cl > A.clMax;                    // exceeded the lift ceiling
      if (stalled) cl = A.clMax * 0.85;                // stall: lift collapses a bit
      this.stalled[i] = stalled ? 1 : 0;
      const lift = q * cl;

      // lift acts along the body up-vector, rolled about the heading by `roll`.
      // rolled-up = up·cos(roll) + right·sin(roll)  ⇒ +right for a right bank,
      // so the horizontal component curves the path toward the turn.
      const cr = Math.cos(roll), sr = Math.sin(roll);
      const lux = uxv * cr + rxv * sr, luy = uyv * cr + ryv * sr, luz = uzv * cr + rzv * sr;

      // — drag — parasite + induced, opposing velocity —
      const cd = A.cd0 + A.inducedK * cl * cl;
      const drag = q * cd;

      // — thrust — the wingbeat only has to overcome drag to hold speed; a
      //   proportional trim then chases cruise. Dives/climbs let gravity do the
      //   rest, so speed changes emerge from the geometry, not a scripted rule.
      let thrust = drag + (P.cruiseSpeed - sp) * A.mass * (2.4 * P.power);
      if (thrust < 0) thrust = 0;                        // birds don't reverse-thrust
      const maxThrust = A.mass * A.gravity * 2 * P.power; // wingbeat ceiling
      if (thrust > maxThrust) thrust = maxThrust;

      // — sum forces → acceleration —  F = thrust·fwd + lift·liftUp − drag·fwd + gravity
      const ax = (fx * thrust + lux * lift - fx * drag) / A.mass;
      const ay = (fy * thrust + luy * lift - fy * drag) / A.mass - A.gravity;
      const az = (fz * thrust + luz * lift - fz * drag) / A.mass;

      vxi += ax * dt; vyi += ay * dt; vzi += az * dt;
      if (P.wind > 0) vxi -= P.wind * dt * 0.5;        // steady headwind drift

      // clamp speed into the flight envelope
      sp = Math.hypot(vxi, vyi, vzi) || 1e-4;
      const lo = P.minSpeed, hi = P.maxSpeed;
      if (sp < lo) { const k = lo / sp; vxi *= k; vyi *= k; vzi *= k; sp = lo; }
      else if (sp > hi) { const k = hi / sp; vxi *= k; vyi *= k; vzi *= k; sp = hi; }

      this.vx[i] = vxi; this.vy[i] = vyi; this.vz[i] = vzi;
      this.px[i] = pxi + vxi * dt; this.py[i] = pyi + vyi * dt; this.pz[i] = pzi + vzi * dt;
      // never let a bird fall through the ground
      if (this.py[i] < 2) { this.py[i] = 2; if (this.vy[i] < 0) this.vy[i] *= -0.3; }
      // hard safety cap: no bird ever escapes beyond 1.4·R (redirect it inward)
      const oy2 = this.py[i] - P.boundary * 0.2;
      const rr2 = Math.hypot(this.px[i], oy2, this.pz[i]);
      const cap = P.boundary * 1.4;
      if (rr2 > cap) {
        const s2 = cap / rr2;
        this.px[i] *= s2; this.py[i] = P.boundary * 0.2 + oy2 * s2; this.pz[i] *= s2;
        // kill the outward component of velocity so it heads home
        const nx = this.px[i] / rr2, ny = oy2 / rr2, nz = this.pz[i] / rr2;
        const vd = this.vx[i] * nx + this.vy[i] * ny + this.vz[i] * nz;
        if (vd > 0) { this.vx[i] -= 1.5 * vd * nx; this.vy[i] -= 1.5 * vd * ny; this.vz[i] -= 1.5 * vd * nz; }
      }
    }

    this.metrics.localOrder = nLocal > 0 ? sumLocal / nLocal : 0;
  }

  // The peregrine: a ballistic hunter that stoops toward the flock centroid,
  // overshoots, banks around and re-attacks. Deliberately faster than the prey.
  _stepPredator(dt) {
    const p = this.pred, P = this.params;
    const cx = this.metrics.centroid[0], cy = this.metrics.centroid[1], cz = this.metrics.centroid[2];
    let tx = cx - p.x, ty = cy - p.y, tz = cz - p.z;
    const td = Math.hypot(tx, ty, tz) || 1; tx /= td; ty /= td; tz /= td;
    const spd = P.maxSpeed * 1.35;
    // steer velocity toward the flock, but keep momentum (so it overshoots)
    p.vx += (tx * spd - p.vx) * clamp(dt * 1.2, 0, 1);
    p.vy += (ty * spd - p.vy) * clamp(dt * 1.2, 0, 1);
    p.vz += (tz * spd - p.vz) * clamp(dt * 1.2, 0, 1);
    const s = Math.hypot(p.vx, p.vy, p.vz) || 1e-4, k = spd / s;
    p.vx *= k; p.vy *= k; p.vz *= k;
    p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
    if (p.y < 4) { p.y = 4; p.vy = Math.abs(p.vy); }
  }

  // ── uniform spatial hash — O(n) neighbour queries ─────────────────────────
  _buildGrid() {
    const n = this.n, size = Math.max(2, this.params.viewRadius);
    // hash into a fixed table; collisions are fine (we re-check distances)
    const bits = 12, mask = (1 << bits) - 1, tableSize = 1 << bits;
    if (!this._head || this._head.length !== tableSize) this._head = new Int32Array(tableSize);
    if (!this._next || this._next.length !== n) this._next = new Int32Array(n);
    const head = this._head, next = this._next;
    head.fill(-1);
    const hash = (x, y, z) => (((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) & mask) >>> 0;
    for (let i = 0; i < n; i++) {
      const c = hash(Math.floor(this.px[i] / size), Math.floor(this.py[i] / size), Math.floor(this.pz[i] / size));
      next[i] = head[c]; head[c] = i;
    }
    return { size, head, next, hash };
  }

  // ── flock-level observables (the science the tests assert) ────────────────
  _measure() {
    const n = this.n; if (n === 0) return;
    let mfx = 0, mfy = 0, mfz = 0, msp = 0, cx = 0, cy = 0, cz = 0, stalls = 0;
    for (let i = 0; i < n; i++) {
      const s = Math.hypot(this.vx[i], this.vy[i], this.vz[i]) || 1e-4;
      mfx += this.vx[i] / s; mfy += this.vy[i] / s; mfz += this.vz[i] / s;
      msp += s; cx += this.px[i]; cy += this.py[i]; cz += this.pz[i];
      stalls += this.stalled[i];
    }
    // polarization = |mean heading| ∈ [0,1] — the flock order parameter
    const pol = Math.hypot(mfx, mfy, mfz) / n;
    cx /= n; cy /= n; cz /= n;
    // flock radius (RMS distance to centroid) + mean bank
    let rad = 0, bank = 0;
    for (let i = 0; i < n; i++) {
      const dx = this.px[i] - cx, dy = this.py[i] - cy, dz = this.pz[i] - cz;
      rad += dx * dx + dy * dy + dz * dz;
      bank += Math.abs(this.bank[i]);
    }
    rad = Math.sqrt(rad / n);
    // approximate mean nearest-neighbour distance from density in the flock ball
    const vol = (4 / 3) * Math.PI * Math.pow(Math.max(rad, 1), 3);
    const nnDist = 0.554 * Math.cbrt(vol / n); // 0.554·(V/N)^(1/3): ideal-gas NN
    this.metrics.polarization = pol;
    this.metrics.speed = msp / n;
    this.metrics.nnDist = nnDist;
    this.metrics.bank = (bank / n) * 180 / Math.PI;
    this.metrics.stalls = stalls;
    this.metrics.centroid[0] = cx; this.metrics.centroid[1] = cy; this.metrics.centroid[2] = cz;
    this.metrics.radius = rad;
  }
}

export default Flock;
