// Nematode — a free-living roundworm, the most abundant animal on Earth.
// A translucent cylinder that thrashes in an S-wave: a muscular pharynx with a
// pumping bulb draws in bacteria, a straight intestine runs the length of the
// body, a nerve ring circles the pharynx, and the gonad coils alongside the
// gut. ~600 µm in life.

import { THREE, cuticle, organ, nucleus, registerOrgan, rng, TAU, clamp } from './lib.js';

export const meta = {
  id: 'nematode',
  name: 'Nematode',
  taxon: 'Rhabditis sp.',
  kingdom: 'Animalia',
  micronLength: 620,
  locomotion: 'undulate',     // slow, meandering net progress along the S-wave thrash
  blurb: 'A roundworm — the most numerous animal alive. It thrashes in an S-shaped wave; a pumping pharynx feeds a straight gut running the whole body.',
  build,
};

const N = 84;               // centreline rings (smooth, low faceting)
const RADIAL = 26;          // radial segments on the body tube
const LEN = 5.2;

function build() {
  const g = new THREE.Group();
  g.name = 'nematode';
  const r = rng(63);

  // Each frame the worm's tubes are *morphed in place* — the ring vertices are
  // recomputed against a live S-wave centreline and written back into the
  // existing buffers. No geometry is reallocated per frame (the old build
  // disposed + rebuilt every tube each frame); the S-wave is real body motion.
  const bodyMat = cuticle(0xefe9d8, 0.18, {
    transmission: 0.55, thickness: 1.4, normal: false,
    attenuationColor: new THREE.Color(0xcbb98a), attenuationDistance: 1.5,
    rim: { color: 0xf0ead2, power: 2.9, intensity: 1.0 },
  });
  const body = new THREE.Mesh(makeTube(RADIAL), bodyMat);
  body.name = 'body';
  body.renderOrder = 12;
  g.add(body);
  registerOrgan(g, body, 'Cuticle & body wall', 'A tough collagen cuticle over longitudinal muscle — antagonised against the internal pressure, it drives the S-wave.', 0.0);

  // ── Pharynx with terminal bulb (head) ────────────────────────────────────
  const pharynx = new THREE.Group(); pharynx.name = 'pharynx';
  const pharyTube = new THREE.Mesh(
    new THREE.CylinderGeometry(0.12, 0.18, 0.9, 18),
    organ(0xc98a76, { emissive: new THREE.Color(0x3a1f18), transparent: true, opacity: 0.92, transmission: 0.25 }),
  );
  pharyTube.rotation.z = Math.PI / 2;
  pharynx.add(pharyTube);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.24, 24, 18), organ(0xd0937d, { emissive: new THREE.Color(0x3a1f18), transmission: 0.2 }));
  bulb.position.x = -0.55;
  pharynx.add(bulb);
  pharynx.userData.bulb = bulb;
  g.add(pharynx);
  registerOrgan(g, pharynx, 'Pharynx & bulb', 'A muscular pump: the terminal bulb contracts rhythmically to suck in bacteria and drive them into the gut.', 0.35);

  // ── Nerve ring around the pharynx ────────────────────────────────────────
  const nerve = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.03, 10, 24), nucleus(0xffd27a, { emissive: new THREE.Color(0x4a3410) }));
  nerve.name = 'nerve-ring';
  nerve.rotation.y = Math.PI / 2;
  nerve.position.x = -0.1;
  g.add(nerve);
  registerOrgan(g, nerve, 'Nerve ring', 'The worm\'s brain — a ring of neurons circling the pharynx, coordinating the whole nervous system.', 0.6);

  // ── Intestine (runs the length) + gonad coil ─────────────────────────────
  const gut = new THREE.Mesh(makeTube(10), organ(0x9a7a4a, { transparent: true, opacity: 0.9, transmission: 0.2 }));
  gut.name = 'intestine';
  g.add(gut);
  registerOrgan(g, gut, 'Intestine', 'A single tube of gut cells the length of the body, absorbing digested bacteria.', 0.45);

  const gonad = new THREE.Mesh(makeTube(8), nucleus(0xbfe0ff, { emissive: new THREE.Color(0x1e2c44), transparent: true, opacity: 0.85 }));
  gonad.name = 'gonad';
  g.add(gonad);
  registerOrgan(g, gonad, 'Gonad', 'The reproductive tract coils beside the gut — in a gravid female you can see eggs lined up inside.', 0.65);

  // precomputed ring angles (no per-frame trig-table allocation)
  const ang = (radial) => { const c = [], s = []; for (let j = 0; j <= radial; j++) { const a = (j / radial) * TAU; c.push(Math.cos(a)); s.push(Math.sin(a)); } return { c, s }; };
  const aBody = ang(RADIAL), aGut = ang(10), aGon = ang(8);

  g.userData.focusRadius = 7.6;

  let running = true, phase = 0;
  const rebuild = (t) => {
    morphTube(body.geometry, RADIAL, aBody, (u) => radiusFn(u), 0, 0, t);
    morphTube(gut.geometry, 10, aGut, () => 0.06, 0, 0.02, t);
    morphTube(gonad.geometry, 8, aGon, (u) => 0.05 * Math.sin(u * Math.PI), 0.14, 0.05, t);
    // head follows the leading tangent of the wave
    const hx = -0.5 * LEN, hy = wave(0, t);
    const nx = 1 / N, hy2 = wave(nx, t);
    pharynx.position.set(hx, hy, 0);
    nerve.position.set(hx + 0.12, (hy + hy2) * 0.5, 0);
    pharynx.rotation.z = Math.atan2(hy2 - hy, LEN * nx);
  };

  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase * 0.2) % 1,
    reset: () => { phase = 0; rebuild(0); },
    update: (dt) => {
      if (running) phase += dt;
      rebuild(phase);
      pharynx.userData.bulb.scale.setScalar(1 + Math.max(0, Math.sin(phase * 8)) * 0.25);
    },
  };
  rebuild(0);
  return g;
}

function radiusFn(t) {
  // tapered at both ends, fattest at the mid-body
  return 0.32 * Math.sin(clamp(t, 0, 1) * Math.PI) ** 0.5 + 0.05;
}

// the travelling sinusoid — undulatory swimming, as a y-displacement of x
function wave(u, t) {
  return Math.sin(u * TAU * 1.6 - t * 4) * (0.9 * Math.sin(u * Math.PI));
}
function waveTangent(u, t) {
  const A = u * TAU * 1.6 - t * 4;
  const env = 0.9 * Math.sin(u * Math.PI);
  const dEnv = 0.9 * Math.PI * Math.cos(u * Math.PI);
  const dy = Math.cos(A) * (TAU * 1.6) * env + Math.sin(A) * dEnv;
  const dx = LEN;
  const inv = 1 / Math.hypot(dx, dy);
  return { tx: dx * inv, ty: dy * inv };
}

// A straight tube along x used only as a buffer template; morphTube overwrites
// its positions each frame, so its initial radius/pose is irrelevant.
function makeTube(radial) {
  const pts = [];
  for (let i = 0; i <= N; i++) pts.push(new THREE.Vector3((i / N - 0.5) * LEN, 0, 0));
  const geo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), N, 0.1, radial, false);
  return geo;
}

// Overwrite a tube's ring vertices against the live wave centreline. Frame is
// stable (constant z "up"), so the tube never twists or flips. In-place: no
// allocation beyond computeVertexNormals' small scratch.
function morphTube(geo, radial, angles, radFn, yOff, zOff, t) {
  const pos = geo.attributes.position.array;
  const { c, s } = angles;
  for (let i = 0; i <= N; i++) {
    const u = i / N;
    const cx = (u - 0.5) * LEN;
    const cy = wave(u, t) + yOff;
    const rr = Math.max(0.0001, radFn(u));
    const { tx, ty } = waveTangent(u, t);
    // V = cross((0,0,1), T) = (-ty, tx, 0); U = (0,0,1)
    const vx = -ty, vy = tx;
    const rowBase = i * (radial + 1) * 3;
    for (let j = 0; j <= radial; j++) {
      const idx = rowBase + j * 3;
      const rc = rr * c[j], rs = rr * s[j];
      pos[idx] = cx + rc * vx;
      pos[idx + 1] = cy + rc * vy;
      pos[idx + 2] = zOff + rs;
    }
  }
  geo.attributes.position.needsUpdate = true;
  geo.computeVertexNormals();
}
